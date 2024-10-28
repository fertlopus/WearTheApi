terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.11"
    }
  }

  backend "azurerm" {
    # TODO : Configure backends later when the infra is up and ready
    resource_group_name  = "rg-wearthe-terraform-state"
    storage_account_name = "weartheterraformstate"
    container_name       = "tfstate"
    key                  = "dev/wear-the-infrastructure.tfstate"
  }
}

provider "azurerm" {
  features {}
  subscription_id = ""
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "wearthe"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "westeurope"
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}