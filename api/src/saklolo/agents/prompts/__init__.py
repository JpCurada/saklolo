"""System prompts, one Markdown file per model-calling node."""

from dataclasses import dataclass
from functools import cache
from importlib.resources import files


@cache
def load_prompt(name: str) -> str:
    return files(__package__).joinpath(f"{name}.md").read_text(encoding="utf-8")


@dataclass(frozen=True)
class PromptSet:
    """The prompts the pipeline runs with. Experiments swap these in; production uses default()."""

    extract: str
    triage: str

    @classmethod
    def default(cls) -> "PromptSet":
        return cls(extract=load_prompt("extract"), triage=load_prompt("triage"))
