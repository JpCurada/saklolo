variable "name" {
  description = "Queue name. The dead-letter queue is named \"<name>-dlq\"."
  type        = string
}

variable "visibility_timeout_seconds" {
  description = "Must exceed the consumer's timeout so messages aren't processed twice."
  type        = number
  default     = 180
}

variable "fifo" {
  description = "FIFO queue (and dead-letter queue). Senders must set group and deduplication IDs."
  type        = bool
  default     = false
}

variable "max_receive_count" {
  description = "Receives before a message moves to the dead-letter queue."
  type        = number
  default     = 3
}
