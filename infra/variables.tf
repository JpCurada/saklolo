variable "project" {
  description = "Project name, used as the prefix for every resource name."
  type        = string
  default     = "saklolo"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "demo"], var.environment)
    error_message = "environment must be one of: dev, demo."
  }
}

variable "aws_region" {
  description = "AWS region. Check Bedrock model availability before changing it."
  type        = string
  default     = "ap-southeast-1"
}
