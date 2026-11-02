"""Telegram bot channel. Long polling, so the demo needs no public URL.

A message counts as read only after Saklolo stores it: if storing fails, the same
update is fetched again, so a rescue request is never dropped.
"""

import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx

from saklolo.adapters.channels import HTTP_TIMEOUT_S, ChannelError, address, post_json
from saklolo.dispatch import replies
from saklolo.domain.models import Channel, InboundMessage

logger = logging.getLogger(__name__)

API_URL = "https://api.telegram.org"
POLL_TIMEOUT_S = 25
RETRY_DELAY_S = 5.0


class TelegramBot:
    def __init__(self, token: str, http: httpx.Client) -> None:
        self._base = f"{API_URL}/bot{token}"
        self._http = http

    def updates(self, offset: int | None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"timeout": POLL_TIMEOUT_S, "allowed_updates": '["message"]'}
        if offset is not None:
            params["offset"] = offset
        try:
            response = self._http.get(
                f"{self._base}/getUpdates", params=params, timeout=POLL_TIMEOUT_S + HTTP_TIMEOUT_S
            )
        except httpx.HTTPError as error:
            raise ChannelError(f"telegram getUpdates failed: {type(error).__name__}") from None
        if response.status_code >= 400:
            raise ChannelError(f"telegram getUpdates failed: HTTP {response.status_code}")
        result: list[dict[str, Any]] = response.json()["result"]
        return result

    def send(self, chat_id: str, text: str) -> None:
        post_json(
            self._http,
            f"{self._base}/sendMessage",
            "telegram sendMessage",
            json={"chat_id": chat_id, "text": text},
        )


def parse_update(update: dict[str, Any]) -> InboundMessage | None:
    """A resident's text from a private chat. Groups, photos, and stickers are skipped."""
    message = update.get("message") or {}
    text = message.get("text")
    chat = message.get("chat") or {}
    if not text or chat.get("type") != "private":
        return None
    return InboundMessage(
        sender=address(Channel.TELEGRAM, chat["id"]),
        text=text,
        channel=Channel.TELEGRAM,
        received_at=datetime.fromtimestamp(message["date"], UTC),
    )


class TelegramPoller:
    def __init__(self, bot: TelegramBot, receive: Callable[[InboundMessage], object]) -> None:
        self._bot = bot
        self._receive = receive
        self._offset: int | None = None

    def poll_once(self) -> None:
        for update in self._bot.updates(self._offset):
            self._handle(update)
            self._offset = update["update_id"] + 1

    def run(self, stop: threading.Event) -> None:
        while not stop.is_set():
            try:
                self.poll_once()
            except Exception as error:  # keep polling; the update is fetched again
                logger.warning("telegram polling paused: %s", type(error).__name__)
                stop.wait(RETRY_DELAY_S)

    def _handle(self, update: dict[str, Any]) -> None:
        message = parse_update(update)
        if message is None:
            return
        if message.text.strip().startswith("/start"):
            self._bot.send(str(update["message"]["chat"]["id"]), replies.WELCOME)
            return
        self._receive(message)
