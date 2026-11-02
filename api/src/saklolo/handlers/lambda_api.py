"""API Lambda: the dashboard's reads and dispatcher actions. New messages go to the queue."""

from functools import lru_cache
from typing import Any

import boto3
import httpx
from fastapi import FastAPI
from mangum import Mangum

from saklolo.adapters.sqs import SqsIntakeQueue
from saklolo.config import REPO_ROOT, ChannelSettings, get_settings
from saklolo.dataset.io import load_dataset
from saklolo.dispatch.queued_replay import QueuedReplay
from saklolo.dispatch.service import DispatchService
from saklolo.handlers.demo_api import build_notifier, create_app
from saklolo.handlers.wiring import build_pipeline_deps, deployed_stores


def build_app() -> FastAPI:
    settings = get_settings()
    cases, store, outbox, replay_state = deployed_stores(settings)
    channels = ChannelSettings()
    notifier, _ = build_notifier(outbox, channels, httpx.Client())
    # Dispatcher actions need the pipeline's stores and memory, never its models.
    service = DispatchService(build_pipeline_deps(settings, cases=cases), notifier, store)
    session = boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)
    queue = SqsIntakeQueue(session.client("sqs"), settings.intake_queue_url)
    dataset, problems = load_dataset(REPO_ROOT / "data")
    if problems:
        raise RuntimeError("Dataset is invalid; run `python -m saklolo.dataset.validate`.")
    replay = QueuedReplay(replay_state, queue, dataset)
    return create_app(service, replay, outbox, channels, settings.dashboard_origins, queue)


@lru_cache
def _adapter() -> Mangum:
    return Mangum(build_app(), lifespan="off")


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    response: dict[str, Any] = _adapter()(event, context)
    return response
