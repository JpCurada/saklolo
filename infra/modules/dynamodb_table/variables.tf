variable "name" {
  description = "Table name."
  type        = string
}

variable "hash_key" {
  description = "Partition key attribute name (string)."
  type        = string
}

variable "ttl_attribute" {
  description = "Attribute holding an expiry epoch. Null disables TTL; never set it on tables of rescue cases."
  type        = string
  default     = null
}

variable "range_key" {
  description = "Optional sort key attribute name (string)."
  type        = string
  default     = null
}
