# ruff: noqa: S105, S106  (fake secrets for tests)
"""Telegram and Messenger channels, with httpx's mock transport: no real app calls."""

import hashlib
import hmac
import json
import logging
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from saklolo.adapters.channels import ChannelError, ChannelNotifier
from saklolo.adapters.messenger import MessengerClient, parse_webhook, signature_ok
from saklolo.adapters.outbox import InMemoryOutbox
from saklolo.adapters.telegram import TelegramBot, TelegramPoller, parse_update
from saklolo.config import ChannelSettings
from saklolo.dispatch import replies
from saklolo.domain.models import Channel, InboundMessage

TOKEN = "123:secret-bot-token"
APP_SECRET = "app-secret"


def http(handler: Any) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def telegram_update(update_id: int, text: str | None, chat_type: str = "private") -> dict[str, Any]:
    message: dict[str, Any] = {"date": 1_794_000_000, "chat": {"id": 555, "type": chat_type}}
    if text is not None:
        message["text"] = text
    return {"update_id": update_id, "message": message}


# --- Telegram


def test_a_private_text_becomes_a_message_and_the_rest_is_skipped() -> None:
    message = parse_update(telegram_update(1, "nasa bubong kami"))

    assert message is not None
    assert (message.sender, message.channel) == ("telegram:555", Channel.TELEGRAM)
    assert parse_update(telegram_update(2, "spam", chat_type="group")) is None
    assert parse_update(telegram_update(3, None)) is None


class FakeBot:
    def __init__(self, batches: list[list[dict[str, Any]]]) -> None:
        self.batches = batches
        self.offsets: list[int | None] = []
        self.sent: list[tuple[str, str]] = []

    def updates(self, offset: int | None) -> list[dict[str, Any]]:
        self.offsets.append(offset)
        return self.batches.pop(0) if self.batches else []

    def send(self, chat_id: str, text: str) -> None:
        self.sent.append((chat_id, text))


def test_start_gets_a_welcome_and_messages_reach_the_service() -> None:
    received: list[InboundMessage] = []
    bot = FakeBot([[telegram_update(7, "/start"), telegram_update(8, "tulong po")]])
    poller = TelegramPoller(bot, received.append)  # type: ignore[arg-type]

    poller.poll_once()
    poller.poll_once()

    assert bot.sent == [("555", replies.WELCOME)]
    assert [m.text for m in received] == ["tulong po"]
    assert bot.offsets == [None, 9]


def test_a_message_that_fails_to_store_is_fetched_again() -> None:
    attempts: list[str] = []

    def flaky(message: InboundMessage) -> None:
        attempts.append(message.text)
        if len(attempts) == 1:
            raise RuntimeError("store down")

    update = telegram_update(20, "tulong po")
    bot = FakeBot([[update], [update]])
    poller = TelegramPoller(bot, flaky)  # type: ignore[arg-type]

    with pytest.raises(RuntimeError):
        poller.poll_once()
    poller.poll_once()

    assert attempts == ["tulong po", "tulong po"]
    assert bot.offsets == [None, None]


def test_errors_and_logs_never_show_the_bot_token(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    bot = TelegramBot(TOKEN, http(lambda request: httpx.Response(401)))

    with pytest.raises(ChannelError) as raised:
        bot.send("555", "hello")

    assert TOKEN not in str(raised.value)
    assert TOKEN not in caplog.text


# --- Messenger


def sign(body: bytes) -> str:
    return "sha256=" + hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()


def messenger_payload(*events: dict[str, Any]) -> dict[str, Any]:
    return {"object": "page", "entry": [{"messaging": list(events)}]}


def text_event(psid: str, text: str, echo: bool = False) -> dict[str, Any]:
    message: dict[str, Any] = {"text": text}
    if echo:
        message["is_echo"] = True
    return {"sender": {"id": psid}, "timestamp": 1_794_000_000_000, "message": message}


def test_signatures_must_match_the_app_secret() -> None:
    body = b'{"object":"page"}'

    assert signature_ok(APP_SECRET, body, sign(body))
    assert not signature_ok(APP_SECRET, body, sign(b"tampered"))
    assert not signature_ok(APP_SECRET, body, None)


def test_page_echoes_are_not_read_as_residents() -> None:
    messages = parse_webhook(
        messenger_payload(text_event("42", "nasa bubong"), text_event("page", "ok", echo=True))
    )

    assert [(m.sender, m.text) for m in messages] == [("messenger:42", "nasa bubong")]


def test_messenger_send_uses_the_send_api_as_a_response() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"message_id": "m"})

    MessengerClient("page-token", "v23.0", http(handler)).send("42", "hello")

    [call] = calls
    assert call.url.path == "/v23.0/me/messages"
    assert json.loads(call.content) == {
        "recipient": {"id": "42"},
        "messaging_type": "RESPONSE",
        "message": {"text": "hello"},
    }


# --- Replies go back through the resident's app


def test_replies_follow_the_sender_and_a_failure_doesnt_break_the_action() -> None:
    outbox = InMemoryOutbox()
    delivered: list[tuple[str, str]] = []

    def broken(app_id: str, body: str) -> None:
        raise ChannelError("messenger send failed: HTTP 500")

    notifier = ChannelNotifier(
        outbox,
        {
            Channel.TELEGRAM: lambda app_id, body: delivered.append((app_id, body)),
            Channel.MESSENGER: broken,
        },
    )

    notifier.send_text("telegram:555", "on the way")
    notifier.send_text("messenger:42", "on the way")
    notifier.send_text("+639000000001", "on the way")

    assert delivered == [("555", "on the way")]
    assert len(outbox.sent()) == 3


# --- The webhook, end to end


def messenger_client() -> tuple[TestClient, list[InboundMessage]]:
    from saklolo.handlers.demo_api import create_app

    received: list[InboundMessage] = []

    class Service:
        def receive(self, message: InboundMessage) -> None:
            received.append(message)

    channels = ChannelSettings(
        messenger_page_token="page-token",
        messenger_app_secret=APP_SECRET,
        messenger_verify_token="verify-me",
    )
    app = create_app(Service(), None, InMemoryOutbox(), channels)  # type: ignore[arg-type]
    return TestClient(app), received


def test_meta_can_verify_the_webhook_but_a_wrong_token_cannot() -> None:
    client, _ = messenger_client()
    query = {"hub.mode": "subscribe", "hub.challenge": "abc"}

    ok = client.get("/webhooks/messenger", params={**query, "hub.verify_token": "verify-me"})
    wrong = client.get("/webhooks/messenger", params={**query, "hub.verify_token": "guess"})

    assert (ok.status_code, ok.text) == (200, "abc")
    assert wrong.status_code == 403


def test_only_signed_webhooks_reach_the_service() -> None:
    client, received = messenger_client()
    body = json.dumps(messenger_payload(text_event("42", "tulong po"))).encode()
    headers = {"content-type": "application/json"}

    forged = client.post("/webhooks/messenger", content=body, headers=headers)
    signed = client.post(
        "/webhooks/messenger", content=body, headers={**headers, "x-hub-signature-256": sign(body)}
    )

    assert forged.status_code == 403
    assert signed.status_code == 200
    assert [(m.sender, m.text) for m in received] == [("messenger:42", "tulong po")]


def test_simulated_accounts_are_never_sent_to_the_real_apps() -> None:
    outbox = InMemoryOutbox()
    delivered: list[str] = []
    notifier = ChannelNotifier(
        outbox, {Channel.TELEGRAM: lambda app_id, body: delivered.append(app_id)}
    )

    notifier.send_text("telegram:demo-1", "on the way")

    assert delivered == []
    assert [m.recipient for m in outbox.sent()] == ["telegram:demo-1"]
