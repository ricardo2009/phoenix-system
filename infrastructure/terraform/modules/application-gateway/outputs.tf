# Application Gateway Module Outputs

output "application_gateway_id" {
  description = "ID of the Application Gateway"
  value       = azurerm_application_gateway.main.id
}

output "application_gateway_name" {
  description = "Name of the Application Gateway"
  value       = azurerm_application_gateway.main.name
}

output "public_ip_id" {
  description = "ID of the public IP"
  value       = azurerm_public_ip.main.id
}

output "public_ip_address" {
  description = "Public IP address"
  value       = azurerm_public_ip.main.ip_address
}

output "public_ip_fqdn" {
  description = "FQDN of the public IP"
  value       = azurerm_public_ip.main.fqdn
}

output "backend_address_pool_id" {
  description = "ID of the backend address pool"
  value       = azurerm_application_gateway.main.backend_address_pool[0].id
}

