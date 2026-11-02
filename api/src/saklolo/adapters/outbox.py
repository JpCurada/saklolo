"""Notifier that keeps outgoing texts in memory, for the demo's phone simulator.

AWS End User Messaging replaces it for real SMS.
"""

from datetime import UTC, datetime
from typing import Protocol

from saklolo.domain.models import OutboundMessage


class Outbox(Protocol):
    def send_text(self, recipient: str, body: str) -> None: ...

    def sent(self, recipient: str | None = None) -> list[OutboundMessage]: ...


class InMemoryOutbox:
    def __init__(self) -> None:
        self._sent: list[OutboundMessage] = []

    def send_text(self, recipient: str, body: str) -> None:
        self._sent.append(
            OutboundMessage(recipient=recipient, body=body, sent_at=datetime.now(UTC))
        )

    def sent(self, recipient: str | None = None) -> list[OutboundMessage]:
        return [m for m in self._sent if recipient is None or m.recipient == recipient]
