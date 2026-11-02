output "intake_queue_url" {
  description = "URL of the intake queue (SAKLOLO_INTAKE_QUEUE_URL)."
  value       = module.intake_queue.queue_url
}

output "messages_table_name" {
  description = "Messages table name (SAKLOLO_MESSAGES_TABLE)."
  value       = module.messages_table.name
}

output "dispatch_table_name" {
  description = "Dispatch decisions table name (SAKLOLO_DISPATCH_TABLE)."
  value       = module.dispatch_table.name
}

output "cases_table_name" {
  description = "Cases table name (SAKLOLO_CASES_TABLE)."
  value       = module.cases_table.name
}

output "memory_id" {
  description = "AgentCore Memory ID for dispatcher corrections (SAKLOLO_MEMORY_ID)."
  value       = aws_bedrockagentcore_memory.corrections.id
}

output "memory_strategy_id" {
  description = "Semantic strategy ID (SAKLOLO_MEMORY_STRATEGY_ID)."
  value       = aws_bedrockagentcore_memory_strategy.corrections.memory_strategy_id
}

output "outbox_table_name" {
  description = "Outbox table name (SAKLOLO_OUTBOX_TABLE)."
  value       = module.outbox_table.name
}

output "ecr_repository_url" {
  description = "Where `make deploy` pushes the API image."
  value       = aws_ecr_repository.api.repository_url
}

output "web_bucket" {
  description = "Bucket the dashboard's static export is uploaded to."
  value       = aws_s3_bucket.web.id
}

output "web_distribution_id" {
  description = "CloudFront distribution to invalidate after an upload."
  value       = aws_cloudfront_distribution.web.id
}

output "web_url" {
  description = "The dashboard."
  value       = "https://${var.web_domain}"
}

output "api_url" {
  description = "The API (NEXT_PUBLIC_API_URL for the dashboard build)."
  value       = "https://${local.api_domain}"
}

output "cognito_user_pool_id" {
  description = "Dispatcher user pool, for inviting dispatchers."
  value       = aws_cognito_user_pool.dispatchers.id
}

output "cognito_authority" {
  description = "NEXT_PUBLIC_COGNITO_AUTHORITY for the dashboard build."
  value       = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.dispatchers.id}"
}

output "cognito_client_id" {
  description = "NEXT_PUBLIC_COGNITO_CLIENT_ID for the dashboard build."
  value       = aws_cognito_user_pool_client.dashboard.id
}

output "cognito_domain" {
  description = "NEXT_PUBLIC_COGNITO_DOMAIN: the hosted sign-in page, used to sign out."
  value       = "https://${aws_cognito_user_pool_domain.hosted_ui.domain}.auth.${var.aws_region}.amazoncognito.com"
}
