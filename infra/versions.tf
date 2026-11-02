terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Values come from an untracked backend.hcl (see backend.hcl.example).
  backend "s3" {}
}
