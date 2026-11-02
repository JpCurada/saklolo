"""Write the demo API's OpenAPI schema, the source the web client's types are generated from.

Usage: uv run python -m saklolo.handlers.openapi_export ../web/lib/api/openapi.json

The schema comes from the route signatures alone, so the app is built with
placeholder dependencies and no AWS credentials are needed.
"""

import json
import sys
from pathlib import Path
from typing import cast

from saklolo.adapters.outbox import InMemoryOutbox
from saklolo.dispatch.replay import Replayer
from saklolo.dispatch.service import DispatchService
from saklolo.handlers.demo_api import create_app


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    # Never called while exporting: only the route signatures are read.
    app = create_app(cast(DispatchService, None), cast(Replayer, None), InMemoryOutbox())
    target = Path(sys.argv[1])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
