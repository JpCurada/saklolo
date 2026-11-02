"""Facebook Messenger channel: a Page webhook in, the Send API out.

Meta signs each webhook with the app secret; unsigned or wrongly signed calls are
refused, so nobody can inject fake rescue requests.
"""

import hashlib
import hmac
from datetime import UTC, datetime
from typing import Any

import httpx

from saklolo.adapters.channels import address, post_json
from saklolo.domain.models import Channel, InboundMessage

GRAPH_URL = "https://graph.facebook.com"


def signature_ok(app_secret: str, body: bytes, header: str | None) -> bool:
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


def parse_webhook(payload: dict[str, Any]) -> list[InboundMessage]:
    """Residents' text messages. The Page's own echoes and attachments are skipped."""
    if payload.get("object") != "page":
        return []
    messages = []
    for entry in payload.get("entry", []):
        for event in entry.get("messaging", []):
            message = event.get("message") or {}
            if message.get("is_echo") or not message.get("text"):
                continue
            messages.append(
                InboundMessage(
                    sender=address(Channel.MESSENGER, event["sender"]["id"]),
                    text=message["text"],
                    channel=Channel.MESSENGER,
                    received_at=datetime.fromtimestamp(event["timestamp"] / 1000, UTC),
                )
            )
    return messages


class MessengerClient:
    def __init__(self, page_token: str, graph_version: str, http: httpx.Client) -> None:
        self._url = f"{GRAPH_URL}/{graph_version}/me/messages"
        self._token = page_token
        self._http = http

    def send(self, psid: str, text: str) -> None:
        # A reply within 24 hours of the resident's last message. Later replies need
        # a message tag, which Meta grants only after app review.
        post_json(
            self._http,
            self._url,
            "messenger send",
            params={"access_token": self._token},
            json={
                "recipient": {"id": psid},
                "messaging_type": "RESPONSE",
                "message": {"text": text},
            },
        )
