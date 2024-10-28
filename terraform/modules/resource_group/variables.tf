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

variable "vnet_name" {
  description = "Name of the virtual network"
  type        = string
  default     = "Test vnet"
}

variable "address_space" {
  description = "Address space for the virtual network"
  type        = list(string)
  default     = ["*"]
}

variable "subnets" {
  description = "Map of subnet names to address prefixes"
  type        = map(string)
}
