variable "vnet_name" {
  description = "Name of the virtual network"
  type        = string
  default     = "Test-vnet"
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

variable "location" {
  description = "Location"
  type = string
  default = "westeurope"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "security_rules" {
  description = "Security rules for network security group"
  type        = map(object({
    priority                   = number
    direction                  = string
    access                     = string
    protocol                   = string
    source_port_range          = string
    destination_port_range     = string
    source_address_prefix      = string
    destination_address_prefix = string
  }))
}

variable "tags" {
  description = "Tags to apply to network resources"
  type        = map(string)
  default     = {}
}