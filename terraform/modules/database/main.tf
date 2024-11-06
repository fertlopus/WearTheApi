resource "azurerm_postgresql_flexible_server" "main" {
  name                = "psql-${var.project_name}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  version            = "13"
  
  administrator_login    = var.admin_username
  administrator_password = var.admin_password
  
  storage_mb = var.storage_mb
  sku_name   = var.sku_name
  
  backup_retention_days = var.backup_retention_days
  geo_redundant_backup_enabled = var.environment == "production"
  
  zone = "1"
  
  high_availability {
    mode = var.environment == "production" ? "ZoneRedundant" : "Disabled"
  }
  
  tags = var.tags
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = var.database_name
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_redis_cache" "main" {
  name                = "redis-${var.project_name}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  capacity           = var.redis_capacity
  family             = var.redis_family
  sku_name           = var.redis_sku
  
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
  
  redis_configuration {
    maxmemory_reserved = var.redis_maxmemory_reserved
    maxmemory_delta    = var.redis_maxmemory_delta
    maxmemory_policy   = "allkeys-lru"
  }
  
  tags = var.tags
}

# Create Key Vault secrets for database credentials
resource "azurerm_key_vault_secret" "postgres_user" {
  name         = "POSTGRES-USER"
  value        = var.admin_username
  key_vault_id = var.key_vault_id
}

resource "azurerm_key_vault_secret" "postgres_password" {
  name         = "POSTGRES-PASSWORD"
  value        = var.admin_password
  key_vault_id = var.key_vault_id
}

resource "azurerm_key_vault_secret" "postgres_host" {
  name         = "POSTGRES-HOST"
  value        = azurerm_postgresql_flexible_server.main.fqdn
  key_vault_id = var.key_vault_id
}

resource "azurerm_key_vault_secret" "redis_host" {
  name         = "REDIS-HOST"
  value        = azurerm_redis_cache.main.hostname
  key_vault_id = var.key_vault_id
}

resource "azurerm_key_vault_secret" "redis_password" {
  name         = "REDIS-PASSWORD"
  value        = azurerm_redis_cache.main.primary_access_key
  key_vault_id = var.key_vault_id
}

variable "admin_username" {
  description = "Database admin username"
  type        = string
}

variable "admin_password" {
  description = "Database admin password"
  type        = string
  sensitive   = true
}

variable "database_name" {
  description = "Name of the database"
  type        = string
}

variable "storage_mb" {
  description = "Storage in MB"
  type        = number
  default     = 32768
}

variable "sku_name" {
  description = "SKU name for PostgreSQL"
  type        = string
  default     = "B_Standard_B1ms"
}

variable "backup_retention_days" {
  description = "Backup retention days"
  type        = number
  default     = 7
}

variable "redis_capacity" {
  description = "Redis capacity"
  type        = number
  default     = 1
}

variable "redis_family" {
  description = "Redis family"
  type        = string
  default     = "C"
}

variable "redis_sku" {
  description = "Redis SKU"
  type        = string
  default     = "Standard"
}

variable "redis_maxmemory_reserved" {
  description = "Redis maxmemory reserved"
  type        = number
  default     = 50
}

variable "redis_maxmemory_delta" {
  description = "Redis maxmemory delta"
  type        = number
  default     = 50
}

variable "key_vault_id" {
  description = "Key Vault ID for storing secrets"
  type        = string
}

# outputs.tf
output "postgres_server_name" {
  value = azurerm_postgresql_flexible_server.main.name
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "redis_hostname" {
  value = azurerm_redis_cache.main.hostname
}

output "redis_primary_access_key" {
  value     = azurerm_redis_cache.main.primary_access_key
  sensitive = true
}