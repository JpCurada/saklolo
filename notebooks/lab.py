"""Shared helpers for the experiment notebooks.

Experiments live in notebooks/, never in api/src/saklolo/agents (inference only).
Every helper goes through the same eval runner as `make eval`, so a notebook
number means the same thing as a CLI number.
"""

from dataclasses import replace
from functools import cache
from pathlib import Path
from typing import Any

import pandas as pd

from saklolo.adapters.memory import InMemoryCaseStore
from saklolo.agents.deps import PipelineDeps
from saklolo.agents.prompts import PromptSet
from saklolo.config import REPO_ROOT, Settings, get_settings
from saklolo.dataset.io import Dataset, load_dataset
from saklolo.eval.graph_predictor import GraphPredictor
from saklolo.eval.ground_truth import GroundTruthSource
from saklolo.eval.report import rows
from saklolo.eval.runner import EvalRun, evaluate
from saklolo.handlers.wiring import build_pipeline_deps

CALL_CACHE_DIR = REPO_ROOT / "eval" / "cache"  # gitignored; delete it to force fresh calls
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
