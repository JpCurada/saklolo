locals {
  # FIFO queues must be named "<name>.fifo".
  suffix = var.fifo ? ".fifo" : ""
}

resource "aws_sqs_queue" "dead_letter" {
  name                      = "${var.name}-dlq${local.suffix}"
  fifo_queue                = var.fifo
  message_retention_seconds = 1209600 # 14 days, the SQS maximum
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue" "this" {
  name                       = "${var.name}${local.suffix}"
  fifo_queue                 = var.fifo
  visibility_timeout_seconds = var.visibility_timeout_seconds
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter.arn
    maxReceiveCount     = var.max_receive_count
  })
}
