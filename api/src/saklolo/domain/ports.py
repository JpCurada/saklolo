"""Interfaces the domain and agents depend on. Adapters implement them."""

from typing import Protocol

from saklolo.domain.models import InboundMessage


class MessageQueue(Protocol):
    def enqueue(self, message: InboundMessage) -> None: ...


class Notifier(Protocol):
    def send_text(self, recipient: str, body: str) -> None: ...
