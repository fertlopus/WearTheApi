module "resource_group" {
  source              = "../../modules/resource_group"
  resource_group_name = "rg-wearthe-dev"
  location            = "westeurope"
  project_name        = "WearThe"
  environment         = "dev"
  tags = {
    Environment = "Development"
    Project     = "WearThe"
  }
}

module "network" {
  source              = "../../modules/network"
  vnet_name           = "vnet-wearthe-dev"
  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.resource_group_location
  address_space       = ["10.0.0.0/16"]

  subnets = {
    "snet-gateway"    = "10.0.0.0/24"
    "snet-frontend"   = "10.0.1.0/24"
    "snet-backend"    = "10.0.2.0/24"
    "snet-database"   = "10.0.3.0/24"
    "snet-management" = "10.0.4.0/24"
  }

  security_rules = {
    "allow-ssh" = {
      priority                   = 1001
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "22"
      source_address_prefix      = "*"
      destination_address_prefix = "*"
    }
  }

  tags = {
    Environment = "Development"
    Project     = "WearThe"
  }
}
