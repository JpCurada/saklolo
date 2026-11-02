# ruff: noqa: S106  (fake secrets for tests)
"""Dispatcher sign-in on the API, with a fake token decoder (no Cognito, no network)."""

from collections.abc import Mapping
from typing import Any

import pytest
from fastapi.testclient import TestClient

from saklolo.auth import AuthenticationError, AuthSettings, dispatcher_dependency
from saklolo.config import ChannelSettings
from saklolo.dataset.io import Dataset
from saklolo.dispatch.replay import Replayer
from saklolo.handlers.demo_api import create_app
from tests.dispatch.test_service import make_service
from tests.handlers.test_demo_api import client_and_replayer

POOL = AuthSettings(cognito_user_pool_id="ap-southeast-1_pool", cognito_client_id="web-client")


def claims(username: str = "ana", groups: list[str] | None = None) -> dict[str, Any]:
    return {
        "token_use": "access",
        "client_id": "web-client",
        "username": username,
        "cognito:groups": ["dispatchers"] if groups is None else groups,
    }


class FakeDecoder:
    """Tokens are names of claim sets; anything else is invalid."""

    TOKENS: Mapping[str, dict[str, Any]] = {
        "ana-token": claims("ana"),
        "outsider-token": claims("bob", groups=[]),
        "other-app-token": {**claims("ana"), "client_id": "someone-else"},
        "id-token": {**claims("ana"), "token_use": "id"},
    }

    def decode(self, token: str) -> Mapping[str, Any]:
        if token not in self.TOKENS:
            raise AuthenticationError("bad signature")
        return self.TOKENS[token]


def build_service() -> tuple[Any, Replayer, Any]:
    service, outbox = make_service()
    return service, Replayer(service, Dataset(households=[], messages=[], archive=[])), outbox


def make_client() -> TestClient:
    service, replayer, outbox = build_service()
    return TestClient(create_app(service, replayer, outbox, auth=POOL, decoder=FakeDecoder()))


def bearer(token: str) -> dict[str, str]:
    return {"authorization": f"Bearer {token}"}


@pytest.mark.parametrize("path", ["/cases", "/messages", "/outbox", "/replay"])
def test_dispatcher_routes_need_a_token(path: str) -> None:
    response = make_client().get(path)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("token", ["forged", "other-app-token", "id-token"])
def test_invalid_tokens_are_refused(token: str) -> None:
    assert make_client().get("/cases", headers=bearer(token)).status_code == 401


def test_a_signed_in_non_dispatcher_is_forbidden() -> None:
    assert make_client().get("/cases", headers=bearer("outsider-token")).status_code == 403


def test_the_history_records_the_signed_in_dispatcher_not_the_typed_name() -> None:
    client = make_client()
    client.post(
        "/messages",
        json={"sender": "+639000000001", "text": "nasa bubong kami"},
        headers=bearer("ana-token"),
    )
    [case] = client.get("/cases", headers=bearer("ana-token")).json()

    assigned = client.post(
        f"/cases/{case['case_id']}/assign",
        json={"team": "Team Bravo", "dispatcher": "Somebody Else"},
        headers=bearer("ana-token"),
    )

    assert assigned.status_code == 200
    assert assigned.json()["history"][-1]["dispatcher"] == "ana"


def test_health_stays_public() -> None:
    assert make_client().get("/health").status_code == 200


def test_messenger_webhook_stays_public_and_checks_its_own_signature() -> None:
    service, replayer, outbox = build_service()
    channels = ChannelSettings(
        messenger_page_token="page",
        messenger_app_secret="secret",
        messenger_verify_token="verify",
    )
    client = TestClient(
        create_app(service, replayer, outbox, channels, auth=POOL, decoder=FakeDecoder())
    )

    unsigned = client.post("/webhooks/messenger", content=b"{}")

    assert unsigned.status_code == 403  # its own check, not a sign-in requirement


def test_an_open_api_is_refused_on_lambda() -> None:
    with pytest.raises(RuntimeError, match="Sign-in is required on AWS"):
        dispatcher_dependency(AuthSettings(lambda_function="saklolo-api"))


def test_without_cognito_the_local_api_stays_open() -> None:
    plain, _ = client_and_replayer()

    assert plain.get("/cases").status_code == 200
