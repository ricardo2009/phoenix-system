# Private Endpoints Module Outputs

output "key_vault_private_endpoint_id" {
  description = "ID of the Key Vault private endpoint"
  value       = azurerm_private_endpoint.key_vault.id
}

output "storage_blob_private_endpoint_id" {
  description = "ID of the Storage Blob private endpoint"
  value       = azurerm_private_endpoint.storage_blob.id
}

output "cosmos_db_private_endpoint_id" {
  description = "ID of the Cosmos DB private endpoint"
  value       = azurerm_private_endpoint.cosmos_db.id
}

output "cognitive_services_private_endpoint_id" {
  description = "ID of the Cognitive Services private endpoint"
  value       = azurerm_private_endpoint.cognitive_services.id
}

output "search_service_private_endpoint_id" {
  description = "ID of the Search Service private endpoint"
  value       = azurerm_private_endpoint.search_service.id
}

output "private_dns_zone_ids" {
  description = "IDs of the private DNS zones"
  value = {
    key_vault          = azurerm_private_dns_zone.key_vault.id
    storage_blob       = azurerm_private_dns_zone.storage_blob.id
    cosmos_db          = azurerm_private_dns_zone.cosmos_db.id
    cognitive_services = azurerm_private_dns_zone.cognitive_services.id
    search_service     = azurerm_private_dns_zone.search_service.id
  }
}

