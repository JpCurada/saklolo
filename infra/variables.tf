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

variable "zone_name" {
  description = "Route 53 hosted zone the dashboard and API names are created in."
  type        = string
  default     = "jpcurada.dev"
}

variable "web_domain" {
  description = "Dashboard address. The API is served at api.<web_domain>."
  type        = string
  default     = "saklolo.jpcurada.dev"
}

variable "image_tag" {
  description = "Tag of the API image in ECR. Null creates everything but the Lambdas and API."
  type        = string
  default     = null
}

variable "fast_model_id" {
  description = "Bedrock model for extraction and triage (SAKLOLO_FAST_MODEL_ID)."
  type        = string
  default     = "apac.amazon.nova-lite-v1:0"
}

variable "monthly_budget_usd" {
  description = "Monthly cost budget for the account, alerting at 80% and 100%."
  type        = number
  default     = 20
}

variable "alert_email" {
  description = "Where budget alerts go. Null: no budget is created."
  type        = string
  default     = null
}

variable "cognito_domain_prefix" {
  description = "Prefix of the hosted sign-in page, <prefix>.auth.<region>.amazoncognito.com. Globally unique."
  type        = string
  default     = "saklolo-dispatch"
}
