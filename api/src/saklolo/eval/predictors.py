"""Registry of predictors the eval CLI can run."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from saklolo.eval.baselines import KeywordBaseline
from saklolo.eval.graph_predictor import build_graph_predictor
from saklolo.eval.types import Predictor


@dataclass(frozen=True)
class PredictorOptions:
    # Reuse cached model and embedding calls (eval/cache); predictors without paid calls ignore it.
    call_cache_dir: Path | None = None


PREDICTORS: dict[str, Callable[[PredictorOptions], Predictor]] = {
    KeywordBaseline.name: lambda _: KeywordBaseline(),
    "graph": lambda options: build_graph_predictor(options.call_cache_dir),
}
