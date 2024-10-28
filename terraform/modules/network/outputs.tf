output "subnet_ids" {
  value = { for key, subnet in azurerm_subnet.subnets : key => subnet.id }
}

output "nsg_id" {
  value = azurerm_network_security_group.nsg.id
}

output "vnet_gateway_ip" {
  value = azurerm_public_ip.vnet_gateway_public_ip.ip_address
}

output "vnet_id" {
  value = azurerm_virtual_network.vnet.id
}
