from typing import Any

from fastapi.testclient import TestClient

from saklolo.dataset.io import Dataset
from saklolo.dataset.schema import DatasetMessage
from saklolo.dispatch.replay import Replayer
from saklolo.handlers.demo_api import create_app
from tests.dispatch.test_service import make_service


def dataset_message(message_id: str, hour: float, text: str, reply: str | None) -> DatasetMessage:
    row: dict[str, Any] = {
        "id": message_id,
        "split": "dev",
        "scenario_hour": hour,
        "channel": "sms",
        "sender": "+639000000001",
        "text": text,
        "ask_back_reply": reply,
        "truth": {
            "message_type": "vague_location" if reply else "rescue",
            "household_id": "hh-0001",
            "recycled_from": None,
            "location_resolvable": reply is None,
        },
        "labels": None,
        "label_meta": {"status": "pending", "rubric_version": "1.0"},
        "generator_intent": {"priority": "P1"},
    }
    return DatasetMessage.model_validate(row)


def client_and_replayer() -> tuple[TestClient, Replayer]:
    service, outbox = make_service()
    dataset = Dataset(
        households=[],
        messages=[
            dataset_message("msg-0001", 9.0, "nasa bubong kami tapat ng 7-11", "Malanday po")
        ],
        archive=[],
    )
    replayer = Replayer(service, dataset)
    return TestClient(create_app(service, replayer, outbox)), replayer


def test_message_to_queue_to_assignment() -> None:
    client, _ = client_and_replayer()

    posted = client.post("/messages", json={"sender": "+639000000001", "text": "nasa bubong kami"})
    queue = client.get("/cases").json()
    assigned = client.post(f"/cases/{queue[0]['case_id']}/assign", json={"team": "Team Bravo"})

    assert posted.status_code == 201
    assert queue[0]["priority"] == "P1"
    assert assigned.json()["status"] == "assigned"
    assert "Team Bravo" in client.get("/outbox?recipient=%2B639000000001").json()[-1]["body"]


def test_unknown_case_is_404_and_closed_case_is_409() -> None:
    client, _ = client_and_replayer()
    client.post("/messages", json={"sender": "+639000000001", "text": "nasa bubong kami"})
    case_id = client.get("/cases").json()[0]["case_id"]

    missing = client.post("/cases/case-9999/assign", json={"team": "Team Bravo"})
    client.post(f"/cases/{case_id}/confirm-safe")
    late = client.post(f"/cases/{case_id}/assign", json={"team": "Team Bravo"})

    assert missing.status_code == 404
    assert late.status_code == 409


def test_empty_text_is_rejected() -> None:
    client, _ = client_and_replayer()

    response = client.post("/messages", json={"sender": "+639000000001", "text": "   "})

    assert response.status_code == 422


def test_replay_sends_messages_and_the_ask_back_reply() -> None:
    client, replayer = client_and_replayer()

    replayer.run("dev", speed=1e9, max_delay_s=0)

    status = client.get("/replay").json()
    [case] = client.get("/cases").json()
    assert status == {"running": False, "split": "dev", "sent": 2, "total": 2}
    assert case["location"]["barangay"] == "Malanday"
