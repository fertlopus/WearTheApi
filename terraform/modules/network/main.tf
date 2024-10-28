resource "azurerm_virtual_network" "vnet" {
  address_space       = var.address_space
  location            = var.location
  name                = var.vnet_name
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_subnet" "subnets" {
  for_each             = var.subnets
  address_prefixes     = [each.value]
  name                 = each.key
  resource_group_name  = var.resource_group_name
  virtual_network_name = var.vnet_name
}

resource "azurerm_network_security_group" "nsg" {
  location            = "${var.vnet_name}-nsg"
  name                = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
  # Default Security rules
  security_rule {
    name                       = "deny-all-inbound"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_virtual_network_gateway" "vnet_gateway" {
  location            = var.location
  name                = "${var.vnet_name}-gateway"
  resource_group_name = var.resource_group_name
  sku                 = "VpnGw1"
  type                = "Vpn"
  vpn_type            = "RouteBased"
  active_active       = false
  enable_bgp          = false
  ip_configuration {
    name                 = "${var.vnet_name}-gateway-ipconfig"
    public_ip_address_id = azurerm_public_ip.vnet_gateway_public_ip.id
    subnet_id            = azurerm_subnet.subnets["snet-gateway"].id
  }
}

resource "azurerm_public_ip" "vnet_gateway_public_ip" {
  allocation_method   = "Dynamic"
  location            = var.location
  name                = "${var.vnet_name}-gateway-ip"
  resource_group_name = var.resource_group_name
}