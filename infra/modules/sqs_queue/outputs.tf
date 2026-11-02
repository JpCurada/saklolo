output "queue_url" {
  description = "URL of the main queue."
  value       = aws_sqs_queue.this.url
}

output "queue_arn" {
  description = "ARN of the main queue (for IAM policies and event source mappings)."
  value       = aws_sqs_queue.this.arn
}

output "dead_letter_queue_arn" {
  description = "ARN of the dead-letter queue (for alarms)."
  value       = aws_sqs_queue.dead_letter.arn
}
