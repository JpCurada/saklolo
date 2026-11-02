"""The triage pipeline as a Strands Graph.

normalize → prefilter ─(not spam)→ extract → geolocate → dedupe → triage

Nodes share one PipelineState through invocation_state instead of passing text
between them, so every step reads and writes typed data. A node runs when any
satisfied edge reaches it.
Verify and the Swarm escalation are added in later steps (docs/architecture.md).
"""

import asyncio
import time
from collections.abc import Callable
from typing import Any

from strands.multiagent import GraphBuilder
from strands.multiagent.base import MultiAgentBase, MultiAgentResult, Status
from strands.multiagent.graph import Graph, GraphState
from strands.types.multiagent import MultiAgentInput

from saklolo.agents.deps import PipelineDeps
from saklolo.agents.nodes.dedupe import dedupe
from saklolo.agents.nodes.extract import extract
from saklolo.agents.nodes.geolocate import geolocate
from saklolo.agents.nodes.normalize import normalize
from saklolo.agents.nodes.prefilter import needs_model, prefilter
from saklolo.agents.nodes.triage import triage
from saklolo.agents.state import STATE_KEY, PipelineState, pipeline_state
from saklolo.agents.trace import record, with_skipped
from saklolo.domain.errors import PipelineError
from saklolo.domain.models import InboundMessage

Step = Callable[[PipelineState], None]

MAX_NODE_EXECUTIONS = 10  # each node runs once today; this guards future loops
NODE_TIMEOUT_S = 60.0
GRAPH_TIMEOUT_S = 120.0


class StepNode(MultiAgentBase):
    """A Graph node that runs one step on the shared PipelineState."""

    def __init__(self, node_id: str, step: Step, deps: PipelineDeps) -> None:
        super().__init__()
        self.id = node_id
        self._step = step
        self._deps = deps

    async def invoke_async(
        self, task: MultiAgentInput, invocation_state: dict[str, Any] | None = None, **kwargs: Any
    ) -> MultiAgentResult:
        state = pipeline_state(invocation_state)
        model_calls = len(state.usage)
        started = time.perf_counter()
        # Steps may call a model synchronously; keep that off the event loop.
        await asyncio.to_thread(self._step, state)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        record(self.id, state, self._deps, elapsed_ms, model_calls)
        return MultiAgentResult(status=Status.COMPLETED, execution_time=elapsed_ms)


def _passes_prefilter(state: GraphState, *, invocation_state: dict[str, Any], **_: Any) -> bool:
    return needs_model(pipeline_state(invocation_state))


def build_triage_graph(deps: PipelineDeps) -> Graph:
    steps: dict[str, Step] = {
        "normalize": normalize,
        "prefilter": prefilter,
        "extract": lambda s: extract(s, deps.model, deps.prompts.extract),
        "geolocate": lambda s: geolocate(s, deps.geocoder),
        "dedupe": lambda s: dedupe(s, deps),
        "triage": lambda s: triage(s, deps.model, deps.prompts.triage),
    }
    builder = GraphBuilder()
    for node_id, step in steps.items():
        builder.add_node(StepNode(node_id, step, deps), node_id)
    builder.add_edge("normalize", "prefilter")
    builder.add_edge("prefilter", "extract", condition=_passes_prefilter)
    builder.add_edge("extract", "geolocate")
    builder.add_edge("geolocate", "dedupe")
    builder.add_edge("dedupe", "triage")
    builder.set_entry_point("normalize")
    builder.set_max_node_executions(MAX_NODE_EXECUTIONS)
    builder.set_execution_timeout(GRAPH_TIMEOUT_S)
    builder.set_node_timeout(NODE_TIMEOUT_S)
    return builder.build()


def run_pipeline(message: InboundMessage, deps: PipelineDeps) -> PipelineState:
    """Run one message through a fresh graph (graphs hold per-run state)."""
    state = PipelineState(message=message)
    result = build_triage_graph(deps)("triage message", invocation_state={STATE_KEY: state})
    if result.status != Status.COMPLETED:
        raise PipelineError(f"graph finished with status {result.status.value}")
    state.trace = with_skipped(state)
    return state
