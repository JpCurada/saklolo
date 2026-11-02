"""Registry of predictors the eval CLI can run."""

from collections.abc import Callable

from saklolo.eval.baselines import KeywordBaseline
from saklolo.eval.graph_predictor import build_graph_predictor
from saklolo.eval.types import Predictor

PREDICTORS: dict[str, Callable[[], Predictor]] = {
    KeywordBaseline.name: KeywordBaseline,
    "graph": build_graph_predictor,
}
