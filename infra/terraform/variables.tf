# ==============================================================================
# TARGET CLOUD REGION
# ==============================================================================

variable "aws_region" {
  type        = string
  description = "The target AWS geographic region where resources will be provisioned."
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]{1}$", var.aws_region))
    error_message = "The aws_region variable must be a valid AWS region identifier format (e.g., us-east-1, eu-west-1)."
  }
}

# ==============================================================================
# DEPLOYMENT ENVIRONMENT
# ==============================================================================

variable "environment" {
  type        = string
  description = "The deployment stage target used to isolate state parameters and resource naming conventions."
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod", "test-env"], var.environment)
    error_message = "The environment variable must be explicitly restricted to 'dev', 'staging', 'prod', or 'test-env'."
  }
}