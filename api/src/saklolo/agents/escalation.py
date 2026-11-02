"""The escalation Swarm: three Strands agents that review one low-confidence triage.

The triage reviewer leads. It can hand off to the location resolver (which can look
places up with Amazon Location) or the conflict resolver, and it submits the final
priority with a typed tool, because a Swarm has no structured output of its own.
Agents are built per review, so nothing from one household leaks into the next.
"""

from typing import Any

from strands import Agent, tool
from strands.models import Model
from strands.multiagent import Swarm

from saklolo.agents.prompts import load_prompt
from saklolo.domain.errors import ServiceUnavailableError
from saklolo.domain.models import Priority, TriageDecision
from saklolo.domain.ports import EscalationReview, Geocoder, ModelUsage, PlaceLookup

MAX_HANDOFFS = 6
SWARM_TIMEOUT_S = 45.0  # inside the graph's 60-second node timeout
AGENT_TIMEOUT_S = 20.0


def review_tools(
    verdicts: list[TriageDecision], geocoder: Geocoder, lookups: list[PlaceLookup] | None = None
) -> tuple[Any, Any]:
    """The reviewer's submit tool and the location resolver's lookup tool.

    Every lookup is recorded in `lookups`, so the trace shows what was searched and found.
    """
    record = lookups if lookups is not None else []

    @tool
    def submit_review(priority: str, reason: str, confidence: float) -> dict[str, str]:
        """Submit the final rescue priority. Call it exactly once, then stop.

        Args:
            priority: P1, P2, P3, or P4.
            reason: One short English sentence a dispatcher can check at a glance.
            confidence: How sure you are, from 0 to 1.
        """
        try:
            decision = TriageDecision(
                priority=Priority(priority.strip().upper()),
                reason=reason.strip()[:200],
                confidence=confidence,
            )
        except ValueError as error:
            return {"status": "error", "message": str(error)[:200]}
        verdicts.append(decision)
        return {"status": "ok"}

    @tool
    def find_place(place_words: str) -> dict[str, str]:
        """Look up place words (a landmark, street, or purok) in Marikina.

        Args:
            place_words: The words the resident used for their location.

        Returns status "ok" with the barangay, "empty" if nothing matched,
        "already_tried" for words searched before, or "unavailable" if the lookup
        service is down.
        """
        query = place_words.strip()[:200]
        if any(lookup.query.casefold() == query.casefold() for lookup in record):
            return {"status": "already_tried", "message": "Try different words, or report back."}
        try:
            location = geocoder.geocode(query)
        except ServiceUnavailableError:
            record.append(PlaceLookup(query=query, location=None, unavailable=True))
            return {"status": "unavailable"}
        if location is None or location.barangay is None:
            record.append(PlaceLookup(query=query, location=None))
            return {"status": "empty"}
        record.append(PlaceLookup(query=query, location=location))
        return {"status": "ok", "barangay": location.barangay}

    return submit_review, find_place


class StrandsSwarmEscalation:
    def __init__(self, model: Model, geocoder: Geocoder) -> None:
        self._model = model
        self._geocoder = geocoder

    def review(self, brief: str) -> EscalationReview:
        verdicts: list[TriageDecision] = []
        lookups: list[PlaceLookup] = []
        submit_review, find_place = review_tools(verdicts, self._geocoder, lookups)
        reviewer = self._agent("triage_reviewer", "escalation_reviewer", [submit_review])
        swarm = Swarm(
            [
                reviewer,
                self._agent("location_resolver", "escalation_location", [find_place]),
                self._agent("conflict_resolver", "escalation_conflict", []),
            ],
            entry_point=reviewer,
            max_handoffs=MAX_HANDOFFS,
            max_iterations=MAX_HANDOFFS + 2,
            execution_timeout=SWARM_TIMEOUT_S,
            node_timeout=AGENT_TIMEOUT_S,
        )
        result = swarm(brief)
        usage = result.accumulated_usage
        return EscalationReview(
            decision=verdicts[-1] if verdicts else None,
            agents=tuple(node.node_id for node in result.node_history),
            usage=ModelUsage(
                input_tokens=usage["inputTokens"], output_tokens=usage["outputTokens"]
            ),
            lookups=tuple(lookups),
        )

    def _agent(self, name: str, prompt: str, tools: list[Any]) -> Agent:
        return Agent(
            name=name,
            model=self._model,
            system_prompt=load_prompt(prompt),
            tools=tools,
            callback_handler=None,
        )
