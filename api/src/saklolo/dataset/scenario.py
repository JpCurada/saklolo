"""The synthetic storm's clock."""

from datetime import datetime, timedelta, timezone

# Hour 0 of "Typhoon Dalisay (synthetic)", Philippine time.
SCENARIO_START = datetime(2026, 11, 10, tzinfo=timezone(timedelta(hours=8)))


def scenario_time(hour: float) -> datetime:
    return SCENARIO_START + timedelta(hours=hour)
