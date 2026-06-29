# Distillatron — Infrastructure
#
# Cloud-agnostic Terraform configuration. Choose a provider at deploy time.
# This skeleton is intentionally minimal; add providers and resources once
# the deployment target is selected (AWS, GCP, or other).

terraform {
  required_version = ">= 1.5"

  # Uncomment and configure backend once cloud provider is chosen:
  # backend "s3" {
  #   bucket = "distillatron-tfstate"
  #   key    = "terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# Example: AWS provider (uncomment when ready)
# provider "aws" {
#   region = var.region
# }
