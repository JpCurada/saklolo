"""The JSONL post archive against the real dev data (no model, no network).

Tuning notes (dev split, 150 messages): every recycled post scores 0.80 or more
against data/archive.jsonl, and every other message 0.54 or less, so the threshold
of 0.75 sits in the gap. The dev split's recycled posts were made from this archive,
so this measures matching against a known library of old posts.
"""

import json

from saklolo.adapters.archive import JsonlPostArchive
from saklolo.agents.nodes.normalize import clean, mask_phones
from saklolo.config import REPO_ROOT

DATA = REPO_ROOT / "data"


def dev_messages() -> list[dict]:
    lines = (DATA / "messages.jsonl").read_text(encoding="utf-8").splitlines()
    return [m for m in map(json.loads, filter(None, lines)) if m["split"] == "dev"]


def test_every_recycled_dev_post_matches_its_original() -> None:
    archive = JsonlPostArchive(DATA / "archive.jsonl")

    for message in dev_messages():
        if message["truth"]["message_type"] != "recycled":
            continue
        found = archive.match(mask_phones(clean(message["text"])))
        assert found is not None, message["text"]
        assert found.archive_id == message["truth"]["recycled_from"]


def test_no_other_dev_message_matches_an_old_post() -> None:
    archive = JsonlPostArchive(DATA / "archive.jsonl")

    matched = [
        m["text"]
        for m in dev_messages()
        if m["truth"]["message_type"] != "recycled"
        and archive.match(mask_phones(clean(m["text"]))) is not None
    ]

    assert matched == []
