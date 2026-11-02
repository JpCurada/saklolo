"""Worker Lambda: triages messages from the intake queue, one at a time."""

from functools import lru_cache
from typing import Any

import boto3
import httpx

from saklolo.adapters.sqs import SqsIntakeQueue
from saklolo.config import ChannelSettings, get_settings
from saklolo.dispatch.models import QueuedMessage
from saklolo.dispatch.queued_replay import IntakeWorker
from saklolo.dispatch.service import DispatchService
from saklolo.handlers.demo_api import build_notifier
from saklolo.handlers.wiring import build_pipeline_deps, deployed_stores


@lru_cache
def _worker() -> IntakeWorker:
    settings = get_settings()
    cases, store, outbox, replay_state = deployed_stores(settings)
    notifier, _ = build_notifier(outbox, ChannelSettings(), httpx.Client())
    service = DispatchService(build_pipeline_deps(settings, cases=cases), notifier, store)
    session = boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)
    queue = SqsIntakeQueue(session.client("sqs"), settings.intake_queue_url)
    return IntakeWorker(service, replay_state, queue)


def handler(event: dict[str, Any], context: Any) -> None:
    # Batch size is 1 on a FIFO queue: a failure retries only this message, in order.
    for record in event["Records"]:
        _worker().handle(QueuedMessage.model_validate_json(record["body"]))
