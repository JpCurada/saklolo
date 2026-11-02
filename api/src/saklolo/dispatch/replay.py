"""Replay a dataset split through the dispatch service, in timeline order.

Scenario hours are compressed by `speed` (3600 = one storm hour per second),
with each wait capped so quiet stretches don't stall a demo. When the system
asks a resident for their location, the dataset's prepared reply is sent
shortly after, so replays exercise ask-back too.
"""

import heapq
import threading
from dataclasses import dataclass, field
from typing import Protocol

from saklolo.dataset.io import Dataset
from saklolo.dataset.scenario import scenario_time
from saklolo.dispatch.models import ReplayStatus
from saklolo.dispatch.service import DispatchService
from saklolo.domain.errors import SakloloError
from saklolo.domain.models import Channel, InboundMessage

REPLY_AFTER_HOURS = 0.05  # residents answer the ask-back a few minutes later


class ReplayBusyError(SakloloError):
    """A replay is already running."""


@dataclass(order=True)
class _Scheduled:
    hour: float
    order: int
    sender: str = field(compare=False)
    text: str = field(compare=False)
    channel: Channel = field(compare=False)
    reply_if_asked: str | None = field(compare=False, default=None)


class ReplayControl(Protocol):
    def start(self, split: str, speed: float, max_delay_s: float) -> ReplayStatus: ...

    def stop(self) -> ReplayStatus: ...

    def status(self) -> ReplayStatus: ...


class Replayer:
    def __init__(self, service: DispatchService, dataset: Dataset) -> None:
        self._service = service
        self._dataset = dataset
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._status = ReplayStatus(running=False, split=None, sent=0, total=0)

    def start(self, split: str, speed: float, max_delay_s: float) -> ReplayStatus:
        if self._thread is not None and self._thread.is_alive():
            raise ReplayBusyError("a replay is already running")
        self._stop.clear()
        self._thread = threading.Thread(
            target=self.run, args=(split, speed, max_delay_s), daemon=True, name="replay"
        )
        self._thread.start()
        return self.status()

    def stop(self) -> ReplayStatus:
        self._stop.set()
        return self.status()

    def status(self) -> ReplayStatus:
        return self._status.model_copy()

    def run(self, split: str, speed: float, max_delay_s: float) -> None:
        """Blocking replay; start() runs it on a background thread."""
        queue = self._schedule(split)
        self._status = ReplayStatus(running=True, split=split, sent=0, total=len(queue))
        previous_hour = queue[0].hour if queue else 0.0
        try:
            while queue and not self._stop.is_set():
                item = heapq.heappop(queue)
                delay = min((item.hour - previous_hour) * 3600 / speed, max_delay_s)
                if delay > 0 and self._stop.wait(timeout=delay):
                    break
                previous_hour = item.hour
                self._send(item, queue)
        finally:
            self._status = self._status.model_copy(update={"running": False})

    def _schedule(self, split: str) -> list[_Scheduled]:
        messages = sorted(
            (m for m in self._dataset.messages if m.split == split),
            key=lambda m: (m.scenario_hour, m.id),
        )
        queue = [
            _Scheduled(m.scenario_hour, n, m.sender, m.text, m.channel, m.ask_back_reply)
            for n, m in enumerate(messages)
        ]
        heapq.heapify(queue)
        return queue

    def _send(self, item: _Scheduled, queue: list[_Scheduled]) -> None:
        message = InboundMessage(
            sender=item.sender,
            text=item.text,
            channel=item.channel,
            received_at=scenario_time(item.hour),
        )
        result = self._service.receive(message)
        outcome = result.record.outcome
        if outcome is not None and outcome.ask_back_question and item.reply_if_asked:
            reply_hour = item.hour + REPLY_AFTER_HOURS
            reply = _Scheduled(
                reply_hour, -item.order - 1, item.sender, item.reply_if_asked, item.channel
            )
            heapq.heappush(queue, reply)
            self._status = self._status.model_copy(update={"total": self._status.total + 1})
        self._status = self._status.model_copy(update={"sent": self._status.sent + 1})
