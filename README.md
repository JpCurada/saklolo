# Saklolo

**Saklolo turns the flood of messy, Taglish typhoon rescue requests into a ranked,
deduplicated, mapped dispatch queue for Marikina City, so responders see the most
urgent households first. A named human dispatcher always decides who gets sent;
the system never closes a case or tells a resident help is coming on its own.**

Built with the [Strands Agents SDK](https://strandsagents.com) on AWS for the
"Strands SDK: Workshop to Ship" hackathon. Copyright 2026 John Paul Curada, licensed under [Apache-2.0](LICENSE). Flood-hazard data in `data/hazard/` is from Project NOAH and its contributors, under [ODC-ODbL 1.0](data/hazard/README.md).

## What happens to a message

A resident writes by SMS, Telegram, or Messenger, for example *"nasa bubong na kami,
5 kami, may lola"*. Each message runs through a **Strands Graph**
([`api/src/saklolo/agents/graph.py`](api/src/saklolo/agents/graph.py)):

```
normalize → prefilter ─(not spam)→ extract → geolocate → dedupe → verify → triage
                                                                            │
                                         (confidence < 0.75) ─► escalate: Strands Swarm
```

| Step | What it does | Calls |
|---|---|---|
| normalize | Cleans the text and masks phone numbers before any model sees it | code |
| prefilter | Flags obvious spam and prompt injection; spam never reaches a model, and nothing is deleted | code |
| extract | Reads people, vulnerable members, water level, place words, and an English summary | Bedrock (Nova Lite), structured output |
| geolocate | Finds the barangay from the text or Amazon Location; if none, asks the resident one question | Amazon Location |
| dedupe | Merges reports of the same household: same sender, or similar text nearby within a time window | Titan embeddings |
| verify | Flags recycled posts: copies of known past-typhoon posts, or a date in an earlier year | code |
| triage | Sets P1–P4 with a one-line reason a dispatcher can check | Bedrock (Nova Lite) |
| escalate | Unsure cases go to a Swarm: a triage reviewer, a location resolver with a lookup tool, and a conflict resolver. It may raise a priority, never lower one; still unsure means a human decides | Strands Swarm on Bedrock |

Every step is recorded as it runs, and the dashboard shows that trace on each case:
how long each step took, which model or service it called, and what it decided.

Promises enforced in code and tests:
- Residents get an honest "received, not yet confirmed" reply; "a team is on the way"
  goes out only after a dispatcher assigns one.
- Only a dispatcher closes a case, with two deliberate clicks. "Rescued na" marks it
  *reported safe* and waits for that confirmation.
- Spam, recycled posts, and failed messages are flagged and kept, never dropped.
- Every assign, override, and close records the dispatcher's name.

## Built and planned

| Area | Built | Planned |
|---|---|---|
| Agents | Strands Graph with conditional edges; Strands Swarm escalation with typed tools; ask-back pause and resume across messages; AgentCore Memory of dispatcher corrections, consulted only for unsure cases | Escalation on conflicting reports; measuring whether corrections improve accuracy |
| Verification | Recycled-post check (known old posts, past dates); sender-pattern check; Project NOAH flood-hazard map layer and context; Corroborated badge for 2+ senders | Flood-hazard plausibility flag (needs house-level locations) |
| AWS services | Bedrock (Nova Lite, Titan Text Embeddings V2), Amazon Location Places, DynamoDB (cases, messages, decisions) | AgentCore Runtime and Observability; API Gateway, SQS, and Lambda intake; End User Messaging SMS |
| Channels | Telegram (long polling), Messenger (signed webhook), and simulated resident phones for demos | Real SMS intake: no two-way SMS in the Philippines through AWS (ADR 0001) |
| Dashboard | Queue, human review lane, case detail with map, agent trace, decision history, dispatcher on duty, design system with visual regression tests | Sign-in (Amazon Cognito); delivery receipts and team status updates |
| Infra | Terraform for SQS and three DynamoDB tables | The rest of the deployment above |
| Evaluation | Eval harness with domain metrics (Critical recall, dedupe precision and recall, cost per 10,000 messages) on a synthetic dev split | Human labels, a held-out eval split, and a tabletop drill; until then no results are reported |

## Quick start

Needs Python 3.12 with [uv](https://docs.astral.sh/uv/), Node 22, and make.

```bash
make install       # API (uv) and web (npm) dependencies
make test          # 151 unit tests: no network, no AWS
```

**Offline demo, no AWS account needed.** Model and embedding calls for the synthetic
dev split are replayed from a recorded cache in [`demo/cache/`](demo/cache/).

```bash
make demo-offline  # API on :8000
make demo-web      # dashboard on :3000, with replay and the /resident phones
```

Open <http://127.0.0.1:3000>, press **Replay dev split**, and open
<http://127.0.0.1:3000/resident> to send messages. Offline, a message the cache has
never seen is kept for a human instead of being triaged, places only resolve when the
barangay is named, and the Swarm is off.

**Live demo, with AWS.** Real Bedrock and Amazon Location calls, which cost money
(a few cents for a demo run). Needs an AWS profile with Bedrock access to Nova Lite
in `ap-southeast-1` and Titan embeddings in `us-east-1`; copy `.env.example` to
`.env` and fill it in.

```bash
make demo          # API on :8000, reusing recorded calls where they exist
make demo-web
```

## Repo map

| Path | Contents |
|---|---|
| [api/](api/) | Python backend: the Strands Graph and Swarm, adapters, the demo API |
| [web/](web/) | Dispatcher dashboard and resident phones (Next.js) |
| [infra/](infra/) | Terraform |
| [data/](data/) | Synthetic messages and past-typhoon posts |
| [demo/](demo/) | Recorded calls for the offline demo |
| [docs/](docs/) | Architecture, triage rubric, dataset spec, decisions (ADRs) |
| [design/](design/) | Design tokens, rules, and visual regression baselines |
| [video/](video/) | Storyboard and Playwright capture for the demo video |

Contributors (human or AI): start with [AGENTS.md](AGENTS.md).

## Data notice

All rescue messages in this repository are **synthetic**. They follow the patterns of
public typhoon posts but contain no real names, numbers, or posts.
