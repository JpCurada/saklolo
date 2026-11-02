"""Feed a drill set into the demo API, and export what Saklolo made of it.

Feed at the start of the Saklolo round, export at the 15-minute mark:
  uv run python -m saklolo.drill.api_round feed ../drill/sets/set-a.jsonl
  uv run python -m saklolo.drill.api_round export ../drill/results/v1-saklolo.json

Start each round from an empty API (restart `make demo`), so one volunteer's
decisions don't carry into the next round.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from saklolo.dataset.scenario import scenario_time

DEFAULT_API = "http://127.0.0.1:8000"
TIMEOUT_S = 120.0  # one message can take several model calls


def feed(set_path: Path, api: str) -> int:
    rows = [json.loads(line) for line in set_path.read_text(encoding="utf-8").splitlines() if line]
    with httpx.Client(base_url=api, timeout=TIMEOUT_S) as client:
        for row in rows:
            response = client.post(
                "/messages",
                json={
                    "sender": row["sender"],
                    "text": row["text"],
                    "channel": row["channel"],
                    "received_at": scenario_time(row["scenario_hour"]).isoformat(),
                },
            )
            response.raise_for_status()
    return len(rows)


def export(out: Path, api: str) -> None:
    with httpx.Client(base_url=api, timeout=TIMEOUT_S) as client:
        messages = client.get("/messages").raise_for_status().json()
        cases = client.get("/cases", params={"include_closed": "true"}).raise_for_status().json()
    out.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {"exported_at": datetime.now(UTC).isoformat(), "messages": messages, "cases": cases}
    out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["feed", "export"])
    parser.add_argument("path", type=Path, help="Set file to feed, or snapshot file to write")
    parser.add_argument("--api", default=DEFAULT_API)
    args = parser.parse_args()
    if args.action == "feed":
        print(f"Fed {feed(args.path, args.api)} messages")
    else:
        export(args.path, args.api)
        print(f"Wrote {args.path}")


if __name__ == "__main__":
    main()
