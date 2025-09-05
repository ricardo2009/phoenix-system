# Private Endpoints Module for Phoenix System

# Private DNS Zones
resource "azurerm_private_dns_zone" "key_vault" {
  name                = "privatelink.vaultcore.azure.net"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone" "storage_blob" {
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone" "cosmos_db" {
  name                = "privatelink.documents.azure.com"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone" "cognitive_services" {
  name                = "privatelink.cognitiveservices.azure.com"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone" "search_service" {
  name                = "privatelink.search.windows.net"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

# Link Private DNS Zones to Virtual Network
resource "azurerm_private_dns_zone_virtual_network_link" "key_vault" {
  name                  = "link-kv-${var.resource_suffix}"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.key_vault.name
  virtual_network_id    = var.virtual_network_id
  tags                  = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "storage_blob" {
  name                  = "link-blob-${var.resource_suffix}"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.storage_blob.name
  virtual_network_id    = var.virtual_network_id
  tags                  = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "cosmos_db" {
  name                  = "link-cosmos-${var.resource_suffix}"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.cosmos_db.name
  virtual_network_id    = var.virtual_network_id
  tags                  = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "cognitive_services" {
  name                  = "link-cog-${var.resource_suffix}"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.cognitive_services.name
  virtual_network_id    = var.virtual_network_id
  tags                  = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "search_service" {
  name                  = "link-search-${var.resource_suffix}"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.search_service.name
  virtual_network_id    = var.virtual_network_id
  tags                  = var.tags
}

# Private Endpoint for Key Vault
resource "azurerm_private_endpoint" "key_vault" {
  name                = "pe-kv-${var.resource_suffix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id
  
  private_service_connection {
    name                           = "psc-kv-${var.resource_suffix}"
    private_connection_resource_id = var.key_vault_id
    subresource_names              = ["vault"]
    is_manual_connection           = false
  }
  
  private_dns_zone_group {
    name                 = "pdz-group-kv"
    private_dns_zone_ids = [azurerm_private_dns_zone.key_vault.id]
  }
  
  tags = var.tags
}

# Private Endpoint for Storage Account (Blob)
resource "azurerm_private_endpoint" "storage_blob" {
  name                = "pe-blob-${var.resource_suffix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id
  
  private_service_connection {
    name                           = "psc-blob-${var.resource_suffix}"
    private_connection_resource_id = var.storage_account_id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }
  
  private_dns_zone_group {
    name                 = "pdz-group-blob"
    private_dns_zone_ids = [azurerm_private_dns_zone.storage_blob.id]
  }
  
  tags = var.tags
}

# Private Endpoint for Cosmos DB
resource "azurerm_private_endpoint" "cosmos_db" {
  name                = "pe-cosmos-${var.resource_suffix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id
  
  private_service_connection {
    name                           = "psc-cosmos-${var.resource_suffix}"
    private_connection_resource_id = var.cosmos_db_account_id
    subresource_names              = ["Sql"]
    is_manual_connection           = false
  }
  
  private_dns_zone_group {
    name                 = "pdz-group-cosmos"
    private_dns_zone_ids = [azurerm_private_dns_zone.cosmos_db.id]
  }
  
  tags = var.tags
}

# Private Endpoint for Cognitive Services
resource "azurerm_private_endpoint" "cognitive_services" {
  name                = "pe-cog-${var.resource_suffix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id
  
  private_service_connection {
    name                           = "psc-cog-${var.resource_suffix}"
    private_connection_resource_id = var.cognitive_account_id
    subresource_names              = ["account"]
    is_manual_connection           = false
  }
  
  private_dns_zone_group {
    name                 = "pdz-group-cog"
    private_dns_zone_ids = [azurerm_private_dns_zone.cognitive_services.id]
  }
  
  tags = var.tags
}

# Private Endpoint for Search Service
resource "azurerm_private_endpoint" "search_service" {
  name                = "pe-search-${var.resource_suffix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id
  
  private_service_connection {
    name                           = "psc-search-${var.resource_suffix}"
    private_connection_resource_id = var.search_service_id
    subresource_names              = ["searchService"]
    is_manual_connection           = false
  }
  
  private_dns_zone_group {
    name                 = "pdz-group-search"
    private_dns_zone_ids = [azurerm_private_dns_zone.search_service.id]
  }
  
  tags = var.tags
}

