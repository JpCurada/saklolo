output "name" {
  description = "Table name."
  value       = aws_dynamodb_table.this.name
}

output "arn" {
  description = "Table ARN (for IAM policies)."
  value       = aws_dynamodb_table.this.arn
}
