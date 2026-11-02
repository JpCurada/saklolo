locals {
  name_prefix = "${var.project}-${var.environment}"
}

# Incoming messages from every channel, processed by the agent worker.
module "intake_queue" {
  source = "./modules/sqs_queue"

  name = "${local.name_prefix}-intake"
}

# One row per incoming message (raw text, sender, channel, case link).
module "messages_table" {
  source = "./modules/dynamodb_table"

  name     = "${local.name_prefix}-messages"
  hash_key = "message_id"
}

# One row per deduplicated case (priority, verification, location, status).
module "cases_table" {
  source = "./modules/dynamodb_table"

  name     = "${local.name_prefix}-cases"
  hash_key = "case_id"
}

# One row per case with the dispatcher's decisions and who made each one.
module "dispatch_table" {
  source = "./modules/dynamodb_table"

  name     = "${local.name_prefix}-dispatch"
  hash_key = "case_id"
}

# Past dispatcher corrections, found by meaning for unsure cases (ADR 0007).
resource "aws_bedrockagentcore_memory" "corrections" {
  name                  = "${replace(local.name_prefix, "-", "_")}_corrections"
  description           = "Dispatcher priority corrections, consulted by the escalation Swarm."
  event_expiry_duration = 7
}

resource "aws_bedrockagentcore_memory_strategy" "corrections" {
  memory_id           = aws_bedrockagentcore_memory.corrections.id
  name                = "dispatcher_corrections"
  type                = "SEMANTIC"
  namespace_templates = ["/dispatcher-corrections"]
}

# Next: API Gateway + intake Lambda, worker Lambda, AgentCore runtime,
# Location Service place index, geocode cache table, IAM roles.
# Use the terraform-aws skill and have infra-reviewer check each addition.
