"""Replay and intake for the deployed system, where a queue sits between API and worker.

A replay puts the whole split on the intake queue at once. The worker takes one
message at a time, so the queue paces the replay and a run can outlast any one
Lambda invocation. Speed settings don't apply here.
"""

import uuid
from collections.abc import Sequence
from datetime import timedelta
from typing import Protocol

from saklolo.dataset.io import Dataset
from saklolo.dataset.scenario import scenario_time
from saklolo.dispatch.models import QueuedMessage, ReceiveResult, ReplayStatus
from saklolo.dispatch.replay import REPLY_AFTER_HOURS, ReplayBusyError
from saklolo.dispatch.service import DispatchService
from saklolo.domain.models import InboundMessage


class ReplayState(Protocol):
    def status(self) -> ReplayStatus: ...

    def begin(self, run_id: str, split: str, total: int) -> None: ...

    def stop(self) -> None: ...

    def is_active(self, run_id: str) -> bool: ...

    def add(self, sent: int = 0, total: int = 0) -> None: ...


class IntakeSender(Protocol):
    def send(self, messages: Sequence[QueuedMessage]) -> None: ...


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


class QueuedReplay:
    def __init__(self, state: ReplayState, queue: IntakeSender, dataset: Dataset) -> None:
        self._state = state
        self._queue = queue
        self._dataset = dataset

    def start(self, split: str, speed: float, max_delay_s: float) -> ReplayStatus:
        if self._state.status().running:
            raise ReplayBusyError("a replay is already running")
        chosen = sorted(
            (m for m in self._dataset.messages if m.split == split),
            key=lambda m: (m.scenario_hour, m.id),
        )
        run_id = _new_id()
        self._state.begin(run_id, split, len(chosen))
        self._queue.send(
            [
                QueuedMessage(
                    message_id=_new_id(),
                    message=InboundMessage(
                        sender=m.sender,
                        text=m.text,
                        channel=m.channel,
                        received_at=scenario_time(m.scenario_hour),
                    ),
                    replay_run=run_id,
                    reply_if_asked=m.ask_back_reply,
                )
                for m in chosen
            ]
        )
        return self.status()

    def stop(self) -> ReplayStatus:
        self._state.stop()
        return self.status()

    def status(self) -> ReplayStatus:
        return self._state.status()


class IntakeWorker:
    """Handles one message from the intake queue."""

    def __init__(self, service: DispatchService, state: ReplayState, queue: IntakeSender) -> None:
        self._service = service
        self._state = state
        self._queue = queue

    def handle(self, queued: QueuedMessage) -> None:
        run = queued.replay_run
        if run is not None and not self._state.is_active(run):
            return  # stopped, or replaced by a newer run
        result = self._service.receive_once(queued.message, queued.message_id)
        if run is None:
            return
        if result is not None:
            self._send_reply(queued, result, run)
        self._state.add(sent=1)

    def _send_reply(self, queued: QueuedMessage, result: ReceiveResult, run: str) -> None:
        """When the system asks for a location, the dataset's prepared answer follows."""
        outcome = result.record.outcome
        if outcome is None or not outcome.ask_back_question or not queued.reply_if_asked:
            return
        self._state.add(total=1)
        reply = queued.message.model_copy(
            update={
                "text": queued.reply_if_asked,
                "received_at": queued.message.received_at + timedelta(hours=REPLY_AFTER_HOURS),
            }
        )
        self._queue.send([QueuedMessage(message_id=_new_id(), message=reply, replay_run=run)])
