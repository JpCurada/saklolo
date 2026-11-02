"""Score the Strands triage Graph with the same harness as the baselines."""

import time
from collections.abc import Sequence
from pathlib import Path

from saklolo.agents.ask_back import apply_reply
from saklolo.agents.deps import PipelineDeps
from saklolo.agents.graph import run_pipeline
from saklolo.config import Settings, get_settings
from saklolo.dataset.scenario import scenario_time
from saklolo.domain.models import InboundMessage, TriageOutcome
from saklolo.domain.ports import ModelUsage
from saklolo.eval.types import EvalMessage, Prediction
from saklolo.handlers.wiring import build_pipeline_deps


class GraphPredictor:
    """Runs messages one at a time in timeline order: dedupe depends on earlier cases."""

    name = "graph"

    def __init__(self, deps: PipelineDeps, settings: Settings) -> None:
        self._deps = deps
        self._settings = settings

    def predict(self, messages: Sequence[EvalMessage]) -> list[Prediction]:
        ordered = sorted(messages, key=lambda m: (m.scenario_hour, m.id))
        return [self._predict_one(message) for message in ordered]

    def _predict_one(self, message: EvalMessage) -> Prediction:
        started = time.perf_counter()
        try:
            state = run_pipeline(to_inbound(message), self._deps)
        except Exception as error:  # one failed message must not stop the run
            return _failed(message, error, time.perf_counter() - started)
        outcome = state.outcome(self._deps.escalation_threshold)
        barangay, asked_back = self._resume_if_asked(outcome, message)
        return Prediction(
            message_id=message.id,
            priority=outcome.priority,
            case_key=outcome.case_id,
            barangay=barangay,
            is_suspicious=outcome.is_suspicious,
            asked_back=asked_back,
            latency_s=time.perf_counter() - started,
            cost_usd=self._cost(state.usage),
        )

    def _resume_if_asked(
        self, outcome: TriageOutcome, message: EvalMessage
    ) -> tuple[str | None, bool]:
        """Simulate the resident answering the ask-back question (dataset-spec §8)."""
        if outcome.ask_back_question is None or outcome.case_id is None:
            return outcome.location.barangay, False
        if message.reply_if_asked is None:
            return outcome.location.barangay, True
        location = apply_reply(
            outcome.case_id, message.reply_if_asked, self._deps.cases, self._deps.geocoder
        )
        return location.barangay, True

    def _cost(self, usage: list[ModelUsage]) -> float:
        """Model tokens only; embeddings and geocoding cost a small fraction of this."""
        settings = self._settings
        tokens_in = sum(u.input_tokens for u in usage)
        tokens_out = sum(u.output_tokens for u in usage)
        dollars = tokens_in * settings.fast_model_input_price
        dollars += tokens_out * settings.fast_model_output_price
        return dollars / 1_000_000


def to_inbound(message: EvalMessage) -> InboundMessage:
    return InboundMessage(
        sender=message.sender,
        text=message.text,
        channel=message.channel,
        received_at=scenario_time(message.scenario_hour),
    )


def _failed(message: EvalMessage, error: Exception, elapsed: float) -> Prediction:
    return Prediction(
        message_id=message.id,
        priority=None,
        case_key=None,
        barangay=None,
        is_suspicious=False,
        latency_s=elapsed,
        cost_usd=0.0,
        error=f"{type(error).__name__}: {error}",
    )


def build_graph_predictor(call_cache_dir: Path | None = None) -> GraphPredictor:
    """Composition root for evals: real AWS services, fresh in-memory case store."""
    settings = get_settings()
    deps = build_pipeline_deps(settings, call_cache_dir=call_cache_dir)
    return GraphPredictor(deps, settings)
