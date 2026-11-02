from collections.abc import Sequence

from saklolo.dataset.io import Dataset
from saklolo.dispatch.models import QueuedMessage, ReplayStatus
from saklolo.dispatch.queued_replay import IntakeWorker, QueuedReplay
from tests.dispatch.test_service import make_service, message
from tests.handlers.test_demo_api import dataset_message


class FakeState:
    def __init__(self) -> None:
        self.run: str | None = None
        self.split: str | None = None
        self.sent = 0
        self.total = 0
        self.stopped = False

    def status(self) -> ReplayStatus:
        running = not self.stopped and self.sent < self.total
        return ReplayStatus(running=running, split=self.split, sent=self.sent, total=self.total)

    def begin(self, run_id: str, split: str, total: int) -> None:
        self.run, self.split, self.total = run_id, split, total

    def stop(self) -> None:
        self.stopped = True

    def is_active(self, run_id: str) -> bool:
        return run_id == self.run and not self.stopped

    def add(self, sent: int = 0, total: int = 0) -> None:
        self.sent += sent
        self.total += total


class FakeQueue:
    def __init__(self) -> None:
        self.messages: list[QueuedMessage] = []

    def send(self, messages: Sequence[QueuedMessage]) -> None:
        self.messages.extend(messages)


def rig() -> tuple[QueuedReplay, IntakeWorker, FakeQueue]:
    service, _ = make_service()
    state, queue = FakeState(), FakeQueue()
    dataset = Dataset(
        households=[],
        messages=[
            dataset_message("msg-0001", 9.0, "nasa bubong kami tapat ng 7-11", "Malanday po")
        ],
        archive=[],
    )
    return QueuedReplay(state, queue, dataset), IntakeWorker(service, state, queue), queue


def drain(worker: IntakeWorker, queue: FakeQueue) -> None:
    while queue.messages:
        worker.handle(queue.messages.pop(0))


def test_replay_finishes_through_the_queue_with_the_ask_back_reply() -> None:
    replay, worker, queue = rig()

    replay.start("dev", speed=3600, max_delay_s=2)
    drain(worker, queue)

    assert replay.status() == ReplayStatus(running=False, split="dev", sent=2, total=2)


def test_a_stopped_replay_skips_what_is_left() -> None:
    replay, worker, queue = rig()
    replay.start("dev", speed=3600, max_delay_s=2)

    replay.stop()
    drain(worker, queue)

    assert replay.status().sent == 0


def test_a_redelivered_message_is_not_triaged_twice() -> None:
    service, outbox = make_service()
    worker = IntakeWorker(service, FakeState(), FakeQueue())
    queued = QueuedMessage(message_id="m-1", message=message("nasa bubong kami"))

    worker.handle(queued)
    worker.handle(queued)

    assert len(service.messages()) == 1
    assert len(outbox.sent()) == 1
