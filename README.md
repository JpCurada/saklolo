<div align="center">

<img src="web/public/assets/logo-mark.svg" width="96" alt="Saklolo logo: a beacon over a wave">

# Saklolo

**When a typhoon floods the city, every plea reaches the right person first.**

Saklolo turns floods of messy, Taglish rescue messages into a ranked, deduplicated,
mapped dispatch queue. Agents read and sort. A named human decides.

[![API checks](https://github.com/JpCurada/saklolo/actions/workflows/api.yml/badge.svg)](https://github.com/JpCurada/saklolo/actions/workflows/api.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Built with Strands Agents](https://img.shields.io/badge/built%20with-Strands%20Agents-orange.svg)](https://strandsagents.com)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](api/pyproject.toml)

[See it](#see-it) · [How it works](#what-happens-to-a-message) · [Try it](#quick-start) · [What's built](#built-and-planned)

<img src=".github/assets/dashboard.webp" width="100%" alt="The dispatcher dashboard: a ranked queue, a case with its original Taglish and English summary, a map with a flood-hazard layer, and the incoming message feed">

</div>

*Saklolo* means "help" or "rescue" in Filipino. It's built for Marikina City, which
floods badly, and every safety promise below is enforced in code and tests. The system
never closes a case, and never tells a resident help is coming on its own.

> **Status:** a hackathon project for "Strands SDK: Workshop to Ship". It runs on
> synthetic data and hasn't been used in a real response.

## See it

| How the agents decided | Human review lane |
|---|---|
| <img src=".github/assets/agent-trace.webp" alt="The agent trace: every step, how long it took, which model it called, and what it decided"> | <img src=".github/assets/review-lane.webp" alt="The human review lane: unsure cases waiting for a dispatcher"> |
| **Map: OpenStreetMap with Project NOAH flood hazard** | **Resident phones: SMS, Telegram, Messenger** |
| <img src=".github/assets/map.webp" alt="Marikina on OpenStreetMap with Project NOAH's flood-hazard layer and a P1 case pin"> | <img src=".github/assets/resident-phones.webp" alt="Resident phones for SMS, Telegram, and Messenger"> |

## What happens to a message

A resident writes by SMS, Telegram, or Messenger, for example *"nasa bubong na kami,
5 kami, may lola"*. Each message runs through a **Strands Graph**
([`api/src/saklolo/agents/graph.py`](api/src/saklolo/agents/graph.py)):

<img src=".github/assets/architecture.png" width="100%" alt="Saklolo architecture: residents write on Telegram, Messenger, or SMS; webhooks reach API Gateway and the API Lambda, which queues messages in SQS for a worker Lambda running Strands Agents with Bedrock, Titan, Amazon Location, DynamoDB, and AgentCore Memory; the dispatcher loads the dashboard from CloudFront and S3">

1. A resident writes on Telegram, Messenger, or SMS.
2. Each channel calls a webhook on Amazon API Gateway, and replies go back on the same channel.
3. API Gateway invokes the API Lambda. Both Lambdas run as container images from Amazon ECR.
4. The API Lambda queues new messages in an Amazon SQS FIFO queue.
5. The worker Lambda takes them in order and runs the Strands Agents: an 8-step Graph, and a 3-agent Swarm for unsure cases.
6. Amazon Nova Lite on Bedrock extracts details and sets the priority.
7. Titan embeddings let dedupe merge reports of one household, and Amazon Location finds the barangay from landmarks.
8. The agents keep cases in DynamoDB and read past dispatcher corrections from AgentCore Memory.
9. The API reads cases for the dashboard and records every dispatcher decision.
10. The dispatcher loads the dashboard from CloudFront and S3, then calls the API through API Gateway. Route 53 and Certificate Manager serve both addresses, CloudWatch keeps the logs, and AWS Budgets alerts on cost. The map uses OpenStreetMap tiles and Project NOAH's flood hazard layer.


| Step | What it does | Calls |
|---|---|---|
| normalize | Cleans the text and masks phone numbers before any model sees it | code |
| prefilter | Flags obvious spam and prompt injection; spam never reaches a model, and nothing is deleted | code |
| extract | Reads people, vulnerable members, water level, place words, and an English summary | Bedrock (Nova Lite), structured output |
| geolocate | Finds the barangay from the text or Amazon Location; if none, asks the resident one question | Amazon Location |
| dedupe | Merges reports of the same household: same sender, or similar text nearby within a time window | Titan embeddings |
| verify | Flags recycled posts and unusual senders, and adds Project NOAH flood-hazard context | code |
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
| Channels | Telegram (long polling), Messenger (signed webhook), and a resident phone page for SMS | Real SMS intake: no two-way SMS in the Philippines through AWS  |
| Dashboard | Queue, human review lane, case detail with map, agent trace, decision history, dispatcher on duty, design system with visual regression tests | Sign-in (Amazon Cognito); delivery receipts and team status updates |
| Infra | Terraform for SQS and three DynamoDB tables | The rest of the deployment above |
| Evaluation | Eval harness with domain metrics (Critical recall, dedupe precision and recall, cost per 10,000 messages) on a synthetic dev split | Human labels, a held-out eval split, and a tabletop drill; until then no results are reported |

## Quick start

Needs Python 3.12 with [uv](https://docs.astral.sh/uv/), Node 22, and make.

```bash
make install       # API (uv) and web (npm) dependencies
make test          # unit tests: no network, no AWS
```

**Run the demo.** Real Bedrock and Amazon Location calls, which cost money
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
| [design/](design/) | Design tokens, rules, and visual regression baselines |

Want to help? See [CONTRIBUTING.md](CONTRIBUTING.md). Found a security problem? See
[SECURITY.md](SECURITY.md).

## Data notice

All rescue messages in this repository are **synthetic**. They follow the patterns of
public typhoon posts but contain no real names, numbers, or posts.

## License

Code: [Apache-2.0](LICENSE), copyright 2026 John Paul Curada. Flood-hazard data in
[`data/hazard/`](data/hazard/) is from Project NOAH and its contributors, under
[ODC-ODbL 1.0](data/hazard/README.md).
