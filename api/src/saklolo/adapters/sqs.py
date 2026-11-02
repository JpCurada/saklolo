"""The intake queue: FIFO with one message group, so the worker triages in arrival order.

Dedupe compares each message with the cases before it, so order matters more than
throughput here.
"""

import uuid
from collections.abc import Sequence
from itertools import batched
from typing import Any

from saklolo.dispatch.models import QueuedMessage
from saklolo.domain.models import InboundMessage

MESSAGE_GROUP = "intake"
MAX_BATCH = 10  # the SQS limit per SendMessageBatch


class SqsIntakeQueue:
    def __init__(self, sqs: Any, queue_url: str) -> None:
        self._sqs = sqs
        self._url = queue_url

    def enqueue(self, message: InboundMessage) -> None:
        self.send([QueuedMessage(message_id=uuid.uuid4().hex[:12], message=message)])

    def send(self, messages: Sequence[QueuedMessage]) -> None:
        for batch in batched(messages, MAX_BATCH):
            entries = [
                {
                    "Id": queued.message_id,
                    "MessageBody": queued.model_dump_json(),
                    "MessageGroupId": MESSAGE_GROUP,
                    "MessageDeduplicationId": queued.message_id,
                }
                for queued in batch
            ]
            response = self._sqs.send_message_batch(QueueUrl=self._url, Entries=entries)
            if response.get("Failed"):
                raise RuntimeError(f"SQS refused {len(response['Failed'])} intake messages")
