# api

Python backend: intake handlers and the Strands agent pipeline.
Rules: [python](../.agents/rules/python.md), [AI engineering](../.agents/rules/ai-engineering.md).

```bash
uv sync          # install
uv run pytest    # unit tests
```

| Package | Contents |
|---|---|
| `saklolo/config.py` | Settings from `SAKLOLO_*` env vars |
| `saklolo/domain/` | Models, enums, ports, errors (no I/O) |
| `saklolo/agents/` | Strands Graph, Swarm, nodes, prompts |
| `saklolo/adapters/` | AWS implementations of ports |
| `saklolo/dispatch/` | Application layer: runs the pipeline per message, keeps the dispatcher's view |
| `saklolo/handlers/` | Entrypoints: demo API, Lambda, AgentCore |

## Demo API

```bash
make demo        # from the repo root; API on http://127.0.0.1:8000, docs at /docs
```

| Endpoint | Does |
|---|---|
| `POST /messages` | Any channel. A short reply that resolves a location resumes a case awaiting one (ask-back); anything else runs the pipeline |
| `GET /messages` | Every received message with its outcome (failed ones keep their error) |
| `GET /cases` | The queue, most urgent first: summary, priority, reason, location, sources, badges |
| `POST /cases/{id}/assign` | Assign a team; only now are residents told help is coming |
| `POST /cases/{id}/override` | Set the priority, with a reason |
| `POST /cases/{id}/confirm-safe` | Close the case (only a dispatcher closes cases) |
| `GET /outbox` | Texts residents would receive (the phone simulator reads this) |
| `POST /replay` / `GET` / `DELETE` | Stream a split in timeline order; `speed` 3600 = one storm hour per second |

`--call-cache` reuses cached model and embedding calls, so replaying the dev
split costs nothing after its first run. The store is in memory: restart to reset.
