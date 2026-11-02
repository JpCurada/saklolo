"""One eval run, shared by the CLI and the experiment notebooks."""

from dataclasses import dataclass

from saklolo.dataset.io import Dataset
from saklolo.eval.ground_truth import (
    GroundTruthSource,
    ground_truth,
    split_messages,
    to_eval_message,
)
from saklolo.eval.metrics import Metric, compute_metrics
from saklolo.eval.types import GroundTruth, Prediction, Predictor


@dataclass(frozen=True)
class EvalRun:
    predictor_name: str
    split: str
    source: GroundTruthSource
    truths: list[GroundTruth]
    predictions: list[Prediction]
    metrics: list[Metric]

    @property
    def failed(self) -> list[Prediction]:
        return [p for p in self.predictions if p.error]


def evaluate(
    dataset: Dataset, split: str, predictor: Predictor, source: GroundTruthSource
) -> EvalRun:
    """Raises MissingLabelsError when scoring against labels that don't exist yet."""
    messages = split_messages(dataset, split)
    truths = ground_truth(dataset, messages, source)
    predictions = predictor.predict([to_eval_message(m) for m in messages])
    return EvalRun(
        predictor_name=predictor.name,
        split=split,
        source=source,
        truths=truths,
        predictions=predictions,
        metrics=compute_metrics(truths, predictions),
    )
