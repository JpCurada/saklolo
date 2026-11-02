"""Record demo/cache for the offline demo, from an existing call cache. Costs nothing.

Replays the dev split with nothing but `--source`, so no model is called, and keeps
the calls the replay used. Re-run it when a prompt changes, after an eval has refreshed
the source cache.

Run: uv run python -m saklolo.handlers.record_demo_cache --source ../eval/cache
"""

import argparse
import json
from pathlib import Path

from saklolo.adapters.call_cache import JsonlCache
from saklolo.adapters.offline import CopyingCache
from saklolo.adapters.outbox import InMemoryOutbox
from saklolo.config import REPO_ROOT, get_settings
from saklolo.dataset.io import load_dataset
from saklolo.dispatch.replay import Replayer
from saklolo.dispatch.service import DispatchService
from saklolo.handlers.wiring import (
    EMBEDDINGS_FILE,
    MANIFEST_FILE,
    MODEL_CALLS_FILE,
    recorded_deps,
)

DEFAULT_MODEL_ID = "apac.amazon.nova-lite-v1:0"
DEFAULT_EMBEDDING_KEY = "amazon.titan-embed-text-v2:0:256"
REPLAY_SPEED = 1e9


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Directory with a call cache")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "demo" / "cache")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--embedding-key", default=DEFAULT_EMBEDDING_KEY)
    args = parser.parse_args()

    for name in (MODEL_CALLS_FILE, EMBEDDINGS_FILE):
        (args.out / name).unlink(missing_ok=True)
    deps = recorded_deps(
        get_settings(),
        CopyingCache(
            JsonlCache(args.source / MODEL_CALLS_FILE), JsonlCache(args.out / MODEL_CALLS_FILE)
        ),
        CopyingCache(
            JsonlCache(args.source / EMBEDDINGS_FILE), JsonlCache(args.out / EMBEDDINGS_FILE)
        ),
        args.model_id,
        args.embedding_key,
    )
    dataset, problems = load_dataset(REPO_ROOT / "data")
    if problems:
        raise SystemExit("Dataset is invalid; run `python -m saklolo.dataset.validate`.")
    service = DispatchService(deps, InMemoryOutbox())
    Replayer(service, dataset).run("dev", REPLAY_SPEED, 0.0)

    manifest = {"model_id": args.model_id, "embedding_key": args.embedding_key}
    (args.out / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    records = service.messages()
    missed = sum(1 for record in records if record.error)
    print(f"Recorded {len(records) - missed} of {len(records)} messages to {args.out}")


if __name__ == "__main__":
    main()
