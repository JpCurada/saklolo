"""Run a predictor on one split and write a report.

Usage:
  uv run python -m saklolo.eval --split dev [--predictor keyword]
      [--ground-truth labels|intent] [--compare RUN_DIR]

Writes eval/runs/<timestamp>-<predictor>-<split>/ with predictions.jsonl,
metrics.json, and report.md, and prints the report.
"""

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from saklolo.config import REPO_ROOT
from saklolo.dataset.io import load_dataset
from saklolo.eval.ground_truth import GroundTruthSource, MissingLabelsError
from saklolo.eval.metrics import Metric
from saklolo.eval.predictors import PREDICTORS
from saklolo.eval.report import render_comparison, render_run
from saklolo.eval.runner import EvalRun, evaluate
from saklolo.eval.types import Prediction

PROVISIONAL_NOTE = (
    "**PROVISIONAL:** scored against generator intent, not human labels. "
    "Do not report these numbers."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["dev", "eval", "calibration"], required=True)
    parser.add_argument("--predictor", choices=sorted(PREDICTORS), default="keyword")
    parser.add_argument(
        "--ground-truth",
        type=GroundTruthSource,
        choices=list(GroundTruthSource),
        default=GroundTruthSource.LABELS,
    )
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "eval" / "runs")
    parser.add_argument("--compare", type=Path, help="An earlier run directory to compare with")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset, problems = load_dataset(args.data_dir)
    if problems:
        print("Dataset is invalid; run `python -m saklolo.dataset.validate`.", file=sys.stderr)
        return 1

    try:
        run = evaluate(dataset, args.split, PREDICTORS[args.predictor](), args.ground_truth)
    except MissingLabelsError as error:
        print(error, file=sys.stderr)
        return 1

    notes = run_notes(run)
    report = render_run(f"Eval: {run.predictor_name} on {run.split}", notes, run.metrics)
    if args.compare:
        report += "\n## Compared with " + args.compare.name + "\n\n"
        report += render_comparison(load_metrics(args.compare), run.metrics)

    run_dir = args.out / f"{datetime.now():%Y%m%d-%H%M%S}-{run.predictor_name}-{run.split}"
    write_run(run_dir, run.predictions, run.metrics, report)
    print(report)
    print(f"Wrote {run_dir}")
    return 0


def run_notes(run: EvalRun) -> list[str]:
    notes = [f"Messages: {len(run.predictions)}", f"Ground truth: {run.source}"]
    if run.source == GroundTruthSource.INTENT:
        notes.insert(0, PROVISIONAL_NOTE)
    if run.failed:
        notes.append(
            f"**{len(run.failed)} messages failed** (scored as misses), e.g. {run.failed[0].error}"
        )
    return notes


def write_run(
    run_dir: Path, predictions: list[Prediction], metrics: list[Metric], report: str
) -> None:
    run_dir.mkdir(parents=True, exist_ok=False)
    with (run_dir / "predictions.jsonl").open("w", encoding="utf-8", newline="\n") as file:
        file.writelines(p.model_dump_json() + "\n" for p in predictions)
    metrics_json = json.dumps([asdict(m) for m in metrics], indent=2)
    (run_dir / "metrics.json").write_text(metrics_json + "\n", encoding="utf-8")
    (run_dir / "report.md").write_text(report, encoding="utf-8")


def load_metrics(run_dir: Path) -> list[Metric]:
    rows = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    return [Metric(**row) for row in rows]


if __name__ == "__main__":
    sys.exit(main())
