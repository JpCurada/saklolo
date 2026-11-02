from typing import Any

from saklolo.dataset.schema import ArchivePost, DatasetMessage, Household
from saklolo.dataset.validate import find_problems

HOUSEHOLD = Household(
    household_id="hh-0001",
    barangay="Tumana",
    street_or_landmark="Purok 4",
    lat=14.656,
    lng=121.096,
    members=4,
    vulnerable=[],
    contact_names=["Test Person"],
    senders=["+639000000001"],
)


def message(
    message_id: str,
    message_type: str,
    hour: float,
    household_id: str | None = "hh-0001",
    **overrides: Any,
) -> DatasetMessage:
    row: dict[str, Any] = {
        "id": message_id,
        "split": "dev",
        "scenario_hour": hour,
        "channel": "sms",
        "sender": "+639000000001",
        "text": "trapped kami sa 2nd floor",
        "ask_back_reply": None,
        "truth": {
            "message_type": message_type,
            "household_id": household_id,
            "recycled_from": None,
            "location_resolvable": True,
        },
        "labels": None,
        "label_meta": {"status": "pending", "rubric_version": "1.0"},
        "generator_intent": {"priority": "P2"},
    }
    row.update(overrides)
    return DatasetMessage.model_validate(row)


def problems_for(*messages: DatasetMessage, archive: list[ArchivePost] | None = None) -> list[str]:
    return find_problems([HOUSEHOLD], list(messages), archive or [])


def test_consistent_rows_have_no_problems() -> None:
    assert (
        problems_for(message("msg-0001", "rescue", 9), message("msg-0002", "duplicate", 10)) == []
    )


def test_duplicate_before_any_first_report_is_rejected() -> None:
    problems = problems_for(message("msg-0001", "duplicate", 8), message("msg-0002", "rescue", 9))

    assert any("no earlier rescue" in p for p in problems)


def test_household_spanning_two_splits_is_rejected() -> None:
    problems = problems_for(
        message("msg-0001", "rescue", 9), message("msg-0002", "duplicate", 10, split="eval")
    )

    assert any("several splits" in p for p in problems)


def test_real_looking_phone_number_in_text_is_rejected() -> None:
    problems = problems_for(message("msg-0001", "rescue", 9, text="call 09170000000"))

    assert any("outside the fake range" in p for p in problems)


def test_vague_location_without_ask_back_reply_is_rejected() -> None:
    problems = problems_for(message("msg-0001", "vague_location", 9))

    assert any("ask_back_reply" in p for p in problems)


def test_spam_with_a_priority_is_rejected() -> None:
    problems = problems_for(message("msg-0001", "spam", 9, household_id=None))

    assert any("priority must be null" in p for p in problems)
