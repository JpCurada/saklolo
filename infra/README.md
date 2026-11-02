# infra

Terraform for Saklolo on AWS, in `ap-southeast-1` unless noted.

```
saklolo.jpcurada.dev ─► CloudFront ─► S3 (dashboard, static export)
api.saklolo.jpcurada.dev ─► API Gateway (HTTP, throttled) ─► API Lambda
      └─► SQS FIFO intake (+ DLQ) ─► worker Lambda: Strands pipeline ─► Bedrock, Location, AgentCore Memory
DynamoDB: cases, messages, dispatch decisions, outbox
```

## Deploy

```bash
make deploy    # from the repo root; needs Docker, the AWS CLI, Terraform, and Node
make destroy   # removes everything, tables included
```

`deploy.sh` applies the infrastructure, builds and pushes the API image (one image,
two handlers), applies again with that image, then builds the dashboard as a static
export and uploads it. The pushed tag is kept in `image.auto.tfvars` (gitignored),
so later plans keep the deployed image.

State is local (`backend_override.tf`, gitignored). For a shared S3 backend, create
the bucket once, copy `backend.hcl.example` to `backend.hcl`, and delete the override.

Optional: `TF_VAR_alert_email=you@example.com make deploy` adds an account budget
alert (`monthly_budget_usd`, default 20).

## Before real users

The API has no sign-in. Only throttling (20 requests a second) and the budget alert
limit what anyone with the address can do, so deploy only with synthetic data and
keep the chat channels off. The dashboard is built in demo mode (replay and the
resident phones).

## Modules
| Module | Creates |
|---|---|
| `modules/sqs_queue` | Queue + dead-letter queue, SSE on, optionally FIFO |
| `modules/dynamodb_table` | On-demand table, SSE, point-in-time recovery, optional TTL (off by default; never on cases) |

## Not yet in Terraform
- End User Messaging origination number / Philippine sender ID registration.

## Inviting a dispatcher

Sign-in is invite-only. The username is the name shown in each case's history, so pick
a readable one. Cognito emails a temporary password, valid for 7 days.

```bash
POOL_ID=$(terraform -chdir=infra output -raw cognito_user_pool_id)
aws cognito-idp admin-create-user --region ap-southeast-1   --user-pool-id "$POOL_ID" --username ana   --user-attributes Name=email,Value=ana@example.org Name=email_verified,Value=true   --desired-delivery-mediums EMAIL
aws cognito-idp admin-add-user-to-group --region ap-southeast-1   --user-pool-id "$POOL_ID" --username ana --group-name dispatchers
```

An account outside the `dispatchers` group can sign in but gets "Dispatcher access
required" from the API.
