# Saklolo

**Saklolo turns the flood of messy, multilingual typhoon rescue requests into a
verified, deduplicated, prioritized dispatch queue, so responders reach the most
urgent people first. A human always decides who gets sent.**

Built with the [Strands Agents SDK](https://strandsagents.com) on AWS for the
"Strands SDK: Workshop to Ship" hackathon.

> Status: scaffolding. See [docs/plan.md](docs/plan.md) for the build plan.

## Quick start

```bash
make install   # API (uv) + web (npm) dependencies
make test      # unit tests, no AWS needed
make demo      # local end-to-end demo with synthetic data
```

## Layout

| Path | Purpose |
|---|---|
| [api/](api/) | Python backend and Strands agent pipeline |
| [web/](web/) | Dispatcher dashboard (Next.js) |
| [infra/](infra/) | Terraform for AWS |
| [docs/](docs/) | Plan, architecture, rubric, ADRs |

Contributors (human or AI): start with [AGENTS.md](AGENTS.md).

## Data notice

All rescue messages in this repository are **synthetic**. They follow the
patterns of public typhoon posts but contain no real names, numbers, or posts.
