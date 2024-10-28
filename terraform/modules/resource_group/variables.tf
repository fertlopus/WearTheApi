variable "resource_group_name" {
  description = "Name of the Resource Group (RG) for Azure Subscription"
  type        = string
  default     = "test-rg"
}

variable "location" {
  description = "Azure region for the Resource Group (RG)"
  type        = string
  default     = "westeurope"
}

variable "tags" {
  description = "Tags to apply to the resource group for cost centre verification and identification"
  type        = map(string)
  default     = {
    department = "dev"
    app        = "wearthe"
    environment= "dev"
    lead_dev   = "Test"
    lead_email = "test@test.test"
  }
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "wearthe"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}
