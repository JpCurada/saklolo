"""PostArchive over a JSONL file of past-typhoon posts (data/archive.jsonl).

A recycled post is an old plea shared again: an exact copy, a lightly edited one, a
screenshot transcription, or "repost lang po" plus the old text. Two scores catch
these without a model: how alike the texts are overall, and how much of the old post
appears inside the new message.
"""

import json
import re
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

from saklolo.domain.ports import ArchiveMatch

# Tuned on the dev split (notes in tests/adapters/test_archive.py).
MATCH_THRESHOLD = 0.75
MIN_ARCHIVE_WORDS = 5  # shorter posts match too much by chance

WORD = re.compile(r"[^\W_]+")


def words(text: str) -> list[str]:
    """Lowercase words, without punctuation, hashtag marks, or emoji."""
    return WORD.findall(text.casefold())


@dataclass(frozen=True)
class _Post:
    archive_id: str
    posted: date
    words: tuple[str, ...]


class JsonlPostArchive:
    def __init__(self, path: Path) -> None:
        self._posts = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            post_words = tuple(words(row["text"]))
            if len(post_words) >= MIN_ARCHIVE_WORDS:
                self._posts.append(
                    _Post(row["archive_id"], date.fromisoformat(row["posted"]), post_words)
                )

    def match(self, text: str) -> ArchiveMatch | None:
        message = words(text)
        best: ArchiveMatch | None = None
        for post in self._posts:
            score = similarity(message, post.words)
            if score >= MATCH_THRESHOLD and (best is None or score > best.similarity):
                best = ArchiveMatch(post.archive_id, post.posted, round(score, 2))
        return best


def similarity(message: list[str], post: tuple[str, ...]) -> float:
    """The higher of overall likeness and how much of the old post the message contains."""
    if not message or not post:
        return 0.0
    alike = SequenceMatcher(None, message, post, autojunk=False).ratio()
    common = sum(block.size for block in SequenceMatcher(None, message, post).get_matching_blocks())
    contained = common / len(post)
    return max(alike, contained)
