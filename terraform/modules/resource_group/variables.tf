variable "resource_group_name" {
  description = "Name of the Resource Group (RG) for Azure Subscription"
  type        = string
  default     = "test-rg"
}

variable "tags" {
  description = "Tags to apply to the resource group for cost centre verification and identification"
  type        = map(string)
  default = {
    department  = "dev"
    app         = "wearthe"
    environment = "dev"
    lead_dev    = "Test"
    lead_email  = "test@test.test"
  }
}

variable "location" {
  description = "Azure region for the resource group"
  type        = string
  default     = "westeurope"
}

variable "project_name" {
  description = "Name of the project for tagging"
  type        = string
  default     = "wearthe"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}
