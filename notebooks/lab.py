"""Shared helpers for the experiment notebooks.

Experiments live in notebooks/, never in api/src/saklolo/agents (inference only).
Every helper goes through the same eval runner as `make eval`, so a notebook
number means the same thing as a CLI number.
"""

import json
import time
from dataclasses import dataclass, field, replace
from datetime import timedelta
from functools import cache
from pathlib import Path
from typing import Any

import pandas as pd
from IPython.display import Markdown, display

from saklolo.adapters.memory import InMemoryCaseStore
from saklolo.adapters.outbox import InMemoryOutbox
from saklolo.agents.deps import PipelineDeps
from saklolo.agents.nodes.normalize import mask_phones
from saklolo.agents.prompts import PromptSet
from saklolo.config import REPO_ROOT, Settings, get_settings
from saklolo.dataset.io import Dataset, load_dataset
from saklolo.dataset.scenario import scenario_time
from saklolo.dispatch.service import DispatchService
from saklolo.domain.errors import ServiceUnavailableError
from saklolo.domain.models import InboundMessage, Location, TriageDecision
from saklolo.domain.ports import EscalationReview, ModelUsage
from saklolo.eval.baselines import keyword_priority, normalize
from saklolo.eval.graph_predictor import GraphPredictor
from saklolo.eval.ground_truth import GroundTruthSource
from saklolo.eval.report import rows
from saklolo.eval.runner import EvalRun, evaluate
from saklolo.handlers.wiring import build_pipeline_deps

CALL_CACHE_DIR = REPO_ROOT / "eval" / "cache"  # gitignored; delete it to force fresh calls
EVAL_RUNS_DIR = REPO_ROOT / "eval" / "runs"  # gitignored; written by `python -m saklolo.eval`
PROMPT_VARIANTS_DIR = Path(__file__).parent / "prompts"
EXPERIMENT_SPLITS = {"dev", "calibration"}  # never the eval split


@cache
def dataset() -> Dataset:
    data, problems = load_dataset(REPO_ROOT / "data")
    if problems:
        raise ValueError(f"dataset is invalid: {problems[:3]}")
    return data


def ground_truth_source(split: str = "dev") -> GroundTruthSource:
    """Human labels once they exist; generator intent (provisional) until then."""
    messages = [m for m in dataset().messages if m.split == split]
    if all(m.labels is not None for m in messages):
        return GroundTruthSource.LABELS
    print("Labels not ready: scoring against generator intent (PROVISIONAL).")
    return GroundTruthSource.INTENT


PRICE_FIELDS = {"fast_model_input_price", "fast_model_output_price"}


def settings(**overrides: Any) -> Settings:
    """Settings from .env plus overrides, e.g. settings(fast_model_id="...", <prices>)."""
    if "fast_model_id" in overrides and not overrides.keys() >= PRICE_FIELDS:
        raise ValueError(f"a model override needs its prices too: {sorted(PRICE_FIELDS)}")
    return get_settings().model_copy(update=overrides)


def build_deps(run_settings: Settings, prompts: PromptSet | None = None) -> PipelineDeps:
    """Real AWS dependencies with model and embedding calls cached on disk."""
    return build_pipeline_deps(run_settings, prompts=prompts, call_cache_dir=CALL_CACHE_DIR)


def run(deps: PipelineDeps, run_settings: Settings, split: str = "dev") -> EvalRun:
    """One eval run with a fresh case store, so runs don't leak cases into each other."""
    if split not in EXPERIMENT_SPLITS:
        raise ValueError(f"experiments may not use the {split!r} split")
    fresh = replace(deps, cases=InMemoryCaseStore())
    return evaluate(
        dataset(), split, GraphPredictor(fresh, run_settings), ground_truth_source(split)
    )


def with_dedupe_threshold(deps: PipelineDeps, threshold: float) -> PipelineDeps:
    return replace(deps, dedupe=replace(deps.dedupe, similarity_threshold=threshold))


def prompt_variant(name: str) -> str:
    return (PROMPT_VARIANTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def compare(runs: dict[str, EvalRun]) -> pd.DataFrame:
    """Metrics side by side, one column per run, in the run-evals report format."""
    return pd.DataFrame(
        {label: {name: value for name, value, _ in rows(r.metrics)} for label, r in runs.items()}
    )


def metric(eval_run: EvalRun, name: str) -> float | None:
    return next((m.value for m in eval_run.metrics if m.name == name), None)


def priority_changes(before: EvalRun, after: EvalRun) -> pd.DataFrame:
    """Messages whose predicted priority differs between two runs, with the expected one."""
    texts = {m.id: m.text for m in dataset().messages}
    expected = {t.message_id: t.priority for t in after.truths}
    old = {p.message_id: p.priority for p in before.predictions}
    changed = [p for p in after.predictions if p.priority != old[p.message_id]]
    return pd.DataFrame(
        [
            {
                "message": texts[p.message_id],
                "expected": expected[p.message_id],
                "before": old[p.message_id],
                "after": p.priority,
            }
            for p in changed
        ]
    )


# Walkthrough notebook: one view per message, a scorecard computed from the runs.

INJECTED = "injected"  # model id on fake reviews, so the trace can't pass them off as Bedrock
PRIORITY_LABELS = {
    "P1": "🔴 **P1 Critical**",
    "P2": "🟠 **P2 High**",
    "P3": "🟡 **P3 Moderate**",
    "P4": "⚪ **P4 Info**",
}
# Metrics a reader can compare; latency is left out, because these runs replay cached calls.
EVAL_ROWS = (
    "Critical recall",
    "Critical precision",
    "Macro-F1 (priority)",
    "Dedupe precision",
    "Dedupe recall",
    "Correct barangay %",
    "Recycled flagged %",
    "False-flag rate",
)


class Desk:
    """A dispatch desk with its own empty queue, running the deployed DispatchService."""

    def __init__(self, deps: PipelineDeps) -> None:
        self.deps = replace(deps, cases=InMemoryCaseStore())
        self.outbox = InMemoryOutbox()
        self.service = DispatchService(self.deps, self.outbox)

    def inbound(
        self,
        message_id: str,
        text: str | None = None,
        later_minutes: int = 0,
        sender: str | None = None,
    ) -> InboundMessage:
        """A dev message at its storm time. `text` is a follow-up from the same sender."""
        m = next(m for m in dataset().messages if m.id == message_id and m.split == "dev")
        return InboundMessage(
            sender=sender or m.sender,
            text=text or m.text,
            channel=m.channel,
            received_at=scenario_time(m.scenario_hour) + timedelta(minutes=later_minutes),
        )

    def send(self, message_id: str, **changes: Any) -> Any:
        return self.service.receive(self.inbound(message_id, **changes))


def show(result: Any, gloss: str = "") -> None:
    """What the dispatcher sees for one message, then the agents' trace."""
    record, outcome = result.record, result.record.outcome
    lines = [f"**Resident:** {mask_phones(record.message.text)}"]
    if gloss:
        lines.append(f"**In English:** {gloss}")
    if outcome is not None:
        mark = PRIORITY_LABELS.get(outcome.priority.value) if outcome.priority else "No priority"
        lines.append(f"**Priority:** {mark} · {outcome.reason}")
        lines.append(f"**Location:** {outcome.location.barangay or 'not known yet'}")
        if outcome.suspicion_reasons:
            flags = ", ".join(reason.value for reason in outcome.suspicion_reasons)
            lines.append(f"**Flagged, kept for review:** {flags}")
    lines.append(f"**Case:** {record.case_id or 'none'}")
    sent = " / ".join(reply.body for reply in result.replies) or "none"
    lines.append(f"**Reply to the resident:** {sent}")
    display(Markdown("\n\n".join(lines)))
    display(trace_table(record.trace))


def trace_table(trace: list[Any]) -> Any:
    steps = [
        {
            "step": step.step,
            "status": step.status.value,
            "time": f"{step.duration_ms} ms",
            "service": _service(step.service),
            "conclusion": step.detail,
        }
        for step in trace
    ]
    return pd.DataFrame(steps).style.hide(axis="index")


def _service(service: str | None) -> str:
    if service is None:
        return "code"
    return "injected fake, no model" if INJECTED in service else service


def queue_table(desk: Desk) -> Any:
    cases = [
        {
            "case": case.case_id,
            "priority": case.priority.value if case.priority else "none",
            "status": case.status.value,
            "barangay": case.location.barangay,
            "summary": case.english_summary,
            "badges": ", ".join(badge.value for badge in case.badges),
            "messages": len(case.sources),
        }
        for case in desk.service.cases()
    ]
    return pd.DataFrame(cases).style.hide(axis="index")


@dataclass
class Scorecard:
    """Every check is computed from a run in this notebook, never typed in."""

    rows: list[dict[str, str]] = field(default_factory=list)

    def check(self, scenario: str, expected: str, actual: Any, passed: bool, source: str) -> None:
        verdict = "✅ pass" if passed else "❌ fail"
        self.rows.append(
            {
                "scenario": scenario,
                "expected": expected,
                "actual": str(actual),
                "run": source,
                "result": verdict,
            }
        )
        display(Markdown(f"**Check:** {verdict} · {actual}"))

    def table(self) -> Any:
        return pd.DataFrame(self.rows).style.hide(axis="index")

    @property
    def summary(self) -> str:
        passed = sum(row["result"].endswith("pass") for row in self.rows)
        return f"{passed} of {len(self.rows)} checks passed"


def fake_review(deps: PipelineDeps, review: Any) -> PipelineDeps:
    """Swap the Swarm for a scripted review, through the Escalation port."""
    return replace(deps, escalation=review, escalation_model_id=INJECTED)


@dataclass
class ScriptedReview:
    """Answers like a Swarm would. `decision=None` means the reviewers never submitted."""

    decision: TriageDecision | None

    def review(self, brief: str) -> EscalationReview:
        return EscalationReview(
            decision=self.decision,
            agents=("triage_reviewer",),
            usage=ModelUsage(input_tokens=0, output_tokens=0),
            lookups=(),
        )


class FailingReview:
    def review(self, brief: str) -> EscalationReview:
        raise TimeoutError("injected: reviewers unreachable")


class DownGeocoder:
    def geocode(self, query: str) -> Location | None:
        raise ServiceUnavailableError("injected: Amazon Location is down")


def wait_for_memory(deps: PipelineDeps, summary: str, timeout_s: float = 180) -> list[Any]:
    """AgentCore indexes a new record in the background, so a search may lag the write."""
    deadline = time.monotonic() + timeout_s
    while True:
        found = deps.corrections.similar(summary) if deps.corrections else []
        if found or time.monotonic() > deadline:
            return found
        time.sleep(10)


def _latest_metrics(kind: str) -> dict[str, Any]:
    runs = sorted(EVAL_RUNS_DIR.glob(f"*-{kind}-dev"))
    if not runs:
        raise FileNotFoundError(f"no {kind} run yet: python -m saklolo.eval --split dev")
    metrics = json.loads((runs[-1] / "metrics.json").read_text(encoding="utf-8"))
    return {m["name"]: m for m in metrics}


def _formatted(name: str, value: float) -> str:
    return f"{value:.3f}" if name.startswith("Macro") else f"{value:.1%}"


def eval_table() -> Any:
    """The latest Graph and keyword runs on the dev split, side by side."""
    graph = _latest_metrics("graph")
    keyword = _latest_metrics("keyword")
    metrics = [
        {
            "metric": name,
            "Saklolo": _formatted(name, graph[name]["value"]),
            "keyword baseline": _formatted(name, keyword[name]["value"]),
        }
        for name in EVAL_ROWS
    ]
    return pd.DataFrame(metrics).style.hide(axis="index")


def keyword_says(text: str) -> str:
    priority = keyword_priority(normalize(text))
    return priority.value if priority else "none"


def ran(result: Any, step: str) -> bool:
    return any(s.step == step and s.status.value == "ran" for s in result.record.trace)


def detail(result: Any, step: str) -> str:
    return next((s.detail for s in result.record.trace if s.step == step), "")


def summary_of(desk: Desk, message_id: str) -> str:
    """The extract agent's English summary, used to search memory before the message runs."""
    text = desk.inbound(message_id).text
    quiet = Desk(replace(desk.deps, escalation=None, corrections=None))
    return quiet.service.receive(
        quiet.inbound(message_id, text=text)
    ).record.outcome.english_summary
