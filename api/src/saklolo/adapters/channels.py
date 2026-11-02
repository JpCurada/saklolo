"""Replies go back through the app the resident wrote from.

Chat apps identify residents by an app-specific ID, so their sender is stored as
`<channel>:<id>` (for example `telegram:12345`). Phone numbers have no prefix and
stay with the SMS path.
"""

import logging
from collections.abc import Callable, Mapping

import httpx

from saklolo.adapters.outbox import Outbox
from saklolo.domain.errors import SakloloError
from saklolo.domain.models import Channel

logger = logging.getLogger(__name__)

# httpx logs every request URL at INFO, and Telegram puts the bot token in the URL.
logging.getLogger("httpx").setLevel(logging.WARNING)

HTTP_TIMEOUT_S = 10.0

# Senders from the simulated resident phones, for example `telegram:demo-1`.
DEMO_ID_PREFIX = "demo-"


class ChannelError(SakloloError):
    """A chat app refused or failed a call. Never carries a URL or token."""


def address(channel: Channel, app_id: str | int) -> str:
    return f"{channel.value}:{app_id}"


def split_address(recipient: str) -> tuple[str, str] | None:
    """(channel, app id) for a chat-app sender; None for a phone number."""
    channel, sep, app_id = recipient.partition(":")
    return (channel, app_id) if sep and app_id else None


def post_json(http: httpx.Client, url: str, what: str, **kwargs: object) -> dict[str, object]:
    """POST and return the JSON body, raising ChannelError without the URL on failure."""
    try:
        response = http.post(url, timeout=HTTP_TIMEOUT_S, **kwargs)  # type: ignore[arg-type]
    except httpx.HTTPError as error:
        raise ChannelError(f"{what} failed: {type(error).__name__}") from None
    if response.status_code >= 400:
        raise ChannelError(f"{what} failed: HTTP {response.status_code}")
    body: dict[str, object] = response.json()
    return body


Send = Callable[[str, str], None]


class ChannelNotifier:
    """Notifier that keeps every reply in the outbox and forwards chat-app replies."""

    def __init__(self, outbox: Outbox, senders: Mapping[Channel, Send]) -> None:
        self._outbox = outbox
        self._senders = {channel.value: send for channel, send in senders.items()}

    def send_text(self, recipient: str, body: str) -> None:
        self._outbox.send_text(recipient, body)
        parts = split_address(recipient)
        send = self._senders.get(parts[0]) if parts else None
        if parts is None or send is None or parts[1].startswith(DEMO_ID_PREFIX):
            return
        try:
            send(parts[1], body)
        except ChannelError as error:
            # The dispatcher's action still stands; the reply is in the outbox.
            logger.warning("reply not delivered: %s", error)
