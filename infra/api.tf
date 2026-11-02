# The API and the worker: one container image, two Lambdas.
#
#   dashboard ─► API Gateway (api.<web_domain>) ─► API Lambda ─► SQS FIFO ─► worker Lambda
#                                                   reads and dispatcher actions   └─ Strands pipeline
#
# The Lambdas and the API exist only once an image is pushed (var.image_tag); see
# `make deploy`.

locals {
  deployed               = var.image_tag != null
  api_domain             = "api.${var.web_domain}"
  worker_timeout_seconds = 300

  tables = {
    SAKLOLO_CASES_TABLE    = module.cases_table
    SAKLOLO_MESSAGES_TABLE = module.messages_table
    SAKLOLO_DISPATCH_TABLE = module.dispatch_table
    SAKLOLO_OUTBOX_TABLE   = module.outbox_table
  }

  app_environment = merge(
    { for name, table in local.tables : name => table.name },
    {
      SAKLOLO_INTAKE_QUEUE_URL        = module.intake_queue.queue_url
      SAKLOLO_MEMORY_ID               = aws_bedrockagentcore_memory.corrections.id
      SAKLOLO_MEMORY_STRATEGY_ID      = aws_bedrockagentcore_memory_strategy.corrections.memory_strategy_id
      SAKLOLO_FAST_MODEL_ID           = var.fast_model_id
      SAKLOLO_FAST_MODEL_INPUT_PRICE  = "0.06"
      SAKLOLO_FAST_MODEL_OUTPUT_PRICE = "0.24"
      SAKLOLO_DASHBOARD_ORIGINS       = jsonencode(["https://${var.web_domain}"])
      SAKLOLO_EMBEDDING_REGION        = "us-east-1"
      SAKLOLO_LOCATION_REGION         = "ap-southeast-2"
      SAKLOLO_COGNITO_REGION          = var.aws_region
      SAKLOLO_COGNITO_USER_POOL_ID    = aws_cognito_user_pool.dispatchers.id
      SAKLOLO_COGNITO_CLIENT_ID       = aws_cognito_user_pool_client.dashboard.id
    },
  )
}

data "aws_caller_identity" "current" {}

resource "aws_ecr_repository" "api" {
  name                 = "${local.name_prefix}-api"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true # demo images only; destroy removes them

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the last five images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 5 }
      action       = { type = "expire" }
    }]
  })
}

# --- Permissions: each Lambda gets only what its side of the queue needs.

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "shared" {
  statement {
    sid       = "Tables"
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Scan"]
    resources = [for table in local.tables : table.arn]
  }
  statement {
    sid       = "Intake"
    actions   = ["sqs:SendMessage"]
    resources = [module.intake_queue.queue_arn]
  }
}

data "aws_iam_policy_document" "api" {
  source_policy_documents = [data.aws_iam_policy_document.shared.json]
  statement {
    sid       = "RememberCorrections"
    actions   = ["bedrock-agentcore:BatchCreateMemoryRecords"]
    resources = [aws_bedrockagentcore_memory.corrections.arn]
  }
}

data "aws_iam_policy_document" "worker" {
  source_policy_documents = [data.aws_iam_policy_document.shared.json]
  statement {
    sid       = "ConsumeIntake"
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [module.intake_queue.queue_arn]
  }
  statement {
    sid     = "Models"
    actions = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = [
      "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/${var.fast_model_id}",
      # A cross-region profile routes to the model in any of its regions.
      "arn:aws:bedrock:*::foundation-model/${replace(var.fast_model_id, "/^[a-z]+\\./", "")}",
      "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
    ]
  }
  statement {
    sid       = "Geocode"
    actions   = ["geo-places:Geocode"]
    resources = ["arn:aws:geo-places:ap-southeast-2::provider/default"]
  }
  statement {
    sid       = "ReadCorrections"
    actions   = ["bedrock-agentcore:RetrieveMemoryRecords"]
    resources = [aws_bedrockagentcore_memory.corrections.arn]
  }
}

resource "aws_iam_role" "lambda" {
  for_each           = toset(["api", "worker"])
  name               = "${local.name_prefix}-${each.key}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "logs" {
  for_each   = aws_iam_role.lambda
  role       = each.value.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "api" {
  role   = aws_iam_role.lambda["api"].id
  policy = data.aws_iam_policy_document.api.json
}

resource "aws_iam_role_policy" "worker" {
  role   = aws_iam_role.lambda["worker"].id
  policy = data.aws_iam_policy_document.worker.json
}

# --- The Lambdas

resource "aws_cloudwatch_log_group" "lambda" {
  for_each          = toset(["api", "worker"])
  name              = "/aws/lambda/${local.name_prefix}-${each.key}"
  retention_in_days = 14
}

resource "aws_lambda_function" "api" {
  count         = local.deployed ? 1 : 0
  function_name = "${local.name_prefix}-api"
  role          = aws_iam_role.lambda["api"].arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.api.repository_url}:${var.image_tag}"
  architectures = ["x86_64"]
  memory_size   = 1024
  timeout       = 29 # API Gateway's limit

  image_config {
    command = ["saklolo.handlers.lambda_api.handler"]
  }

  environment {
    variables = local.app_environment
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

resource "aws_lambda_function" "worker" {
  count         = local.deployed ? 1 : 0
  function_name = "${local.name_prefix}-worker"
  role          = aws_iam_role.lambda["worker"].arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.api.repository_url}:${var.image_tag}"
  architectures = ["x86_64"]
  memory_size   = 1024
  timeout       = local.worker_timeout_seconds

  image_config {
    command = ["saklolo.handlers.lambda_worker.handler"]
  }

  environment {
    variables = local.app_environment
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

# One message per invocation: a failure retries only that message, still in order,
# and after three tries it moves to the dead-letter queue.
resource "aws_lambda_event_source_mapping" "intake" {
  count            = local.deployed ? 1 : 0
  event_source_arn = module.intake_queue.queue_arn
  function_name    = aws_lambda_function.worker[0].arn
  batch_size       = 1
}

# --- HTTP API on its own name. The execute-api address is off: only the custom
# domain, with its throttling, reaches the Lambda.

resource "aws_apigatewayv2_api" "api" {
  count                        = local.deployed ? 1 : 0
  name                         = "${local.name_prefix}-api"
  protocol_type                = "HTTP"
  disable_execute_api_endpoint = true
}

resource "aws_apigatewayv2_integration" "api" {
  count                  = local.deployed ? 1 : 0
  api_id                 = aws_apigatewayv2_api.api[0].id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api[0].invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "api" {
  count     = local.deployed ? 1 : 0
  api_id    = aws_apigatewayv2_api.api[0].id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.api[0].id}"
}

resource "aws_apigatewayv2_stage" "api" {
  count       = local.deployed ? 1 : 0
  api_id      = aws_apigatewayv2_api.api[0].id
  name        = "$default"
  auto_deploy = true

  # Caps what one dashboard (about 3 requests a second while polling) or anyone else
  # can make the API do, signed in or not.
  default_route_settings {
    throttling_rate_limit  = 20
    throttling_burst_limit = 40
  }
}

resource "aws_lambda_permission" "api" {
  count         = local.deployed ? 1 : 0
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api[0].execution_arn}/*/*"
}

resource "aws_acm_certificate" "api" {
  domain_name       = local.api_domain
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "api_validation" {
  for_each = {
    for option in aws_acm_certificate.api.domain_validation_options : option.domain_name => option
  }
  zone_id         = data.aws_route53_zone.main.zone_id
  name            = each.value.resource_record_name
  type            = each.value.resource_record_type
  records         = [each.value.resource_record_value]
  ttl             = 300
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "api" {
  certificate_arn         = aws_acm_certificate.api.arn
  validation_record_fqdns = [for record in aws_route53_record.api_validation : record.fqdn]
}

resource "aws_apigatewayv2_domain_name" "api" {
  count       = local.deployed ? 1 : 0
  domain_name = local.api_domain

  domain_name_configuration {
    certificate_arn = aws_acm_certificate_validation.api.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_apigatewayv2_api_mapping" "api" {
  count       = local.deployed ? 1 : 0
  api_id      = aws_apigatewayv2_api.api[0].id
  domain_name = aws_apigatewayv2_domain_name.api[0].id
  stage       = aws_apigatewayv2_stage.api[0].id
}

resource "aws_route53_record" "api" {
  count   = local.deployed ? 1 : 0
  zone_id = data.aws_route53_zone.main.zone_id
  name    = local.api_domain
  type    = "A"

  alias {
    name                   = aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}

# --- Cost guard: sign-in limits who can reach the worker, and this caps the bill.

resource "aws_budgets_budget" "monthly" {
  count        = var.alert_email == null ? 0 : 1
  name         = "${local.name_prefix}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = [80, 100]
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.alert_email]
    }
  }
}
