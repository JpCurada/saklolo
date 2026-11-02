# infra

Terraform for Saklolo's AWS resources. Rules: [.agents/rules/terraform.md](../.agents/rules/terraform.md).

## First-time setup
1. Create an S3 bucket for state (once, manually).
2. `cp backend.hcl.example backend.hcl` and `cp terraform.tfvars.example terraform.tfvars`, then fill in.
3. `make plan` from the repo root. Review the plan; apply only with team approval.

## Modules
| Module | Creates |
|---|---|
| `modules/sqs_queue` | Queue + dead-letter queue, SSE on |
| `modules/dynamodb_table` | On-demand table, SSE, point-in-time recovery, optional TTL (off by default; never on cases) |

## Not yet in Terraform
Record manual or CLI steps here (with the reason) until provider support exists:
- AgentCore runtime: check AWS provider support first.
- End User Messaging origination number / Philippine sender ID registration.
