resource "azurerm_resource_group" "rg" {
  location = var.location
  name     = "rg-${var.project_name}-${var.environment}"
  tags = merge(var.tags, {
    Name = "rg-${var.project_name}-${var.environment}"
  })
}
