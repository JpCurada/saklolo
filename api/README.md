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
| `saklolo/handlers/` | Lambda and AgentCore entrypoints |

Not built yet: `saklolo.eval` and `saklolo.demo` (targets of `make eval` / `make demo`).
