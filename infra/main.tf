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

# Next: API Gateway + intake Lambda, worker Lambda, AgentCore runtime,
# Location Service place index, geocode cache table, IAM roles.
# Use the terraform-aws skill and have infra-reviewer check each addition.
