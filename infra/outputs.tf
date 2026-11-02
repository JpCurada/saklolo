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
