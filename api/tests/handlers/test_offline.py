"""The offline demo: no AWS, recorded calls, and nothing is lost on a miss."""

import json
from datetime import UTC, datetime

from saklolo.adapters.outbox import InMemoryOutbox
from saklolo.config import REPO_ROOT, Settings
from saklolo.dataset.io import load_dataset
from saklolo.dispatch.service import DispatchService
from saklolo.domain.models import Channel, InboundMessage
from saklolo.handlers.wiring import build_offline_deps

DEMO_CACHE = REPO_ROOT / "demo" / "cache"


def offline_service() -> DispatchService:
    return DispatchService(build_offline_deps(Settings(), DEMO_CACHE), InMemoryOutbox())


def inbound(text: str) -> InboundMessage:
    return InboundMessage(
        sender="+639000000901",
        text=text,
        channel=Channel.SMS,
        received_at=datetime(2026, 11, 10, 1, tzinfo=UTC),
    )


def test_the_manifest_names_the_recorded_model() -> None:
    manifest = json.loads((DEMO_CACHE / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["model_id"]
    assert manifest["embedding_key"]


def test_a_recorded_dev_message_is_triaged_without_aws() -> None:
    dataset, _ = load_dataset(REPO_ROOT / "data")
    rescue = next(m for m in dataset.messages if m.truth.message_type == "rescue")

    record = offline_service().receive(inbound(rescue.text)).record

    assert record.error is None
    assert record.outcome is not None and record.outcome.priority is not None
    assert any("(recorded)" in (step.service or "") for step in record.trace)


def test_a_message_never_recorded_is_kept_for_a_human() -> None:
    service = offline_service()

    result = service.receive(inbound("isang mensaheng hindi pa nakikita ng cache, tulong po"))

    assert result.record.error is not None
    assert len(service.messages()) == 1
    assert result.replies  # the resident is still acknowledged
