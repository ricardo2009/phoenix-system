# App Service Module Outputs

output "app_service_id" {
  description = "ID of the App Service"
  value       = azurerm_linux_web_app.main.id
}

output "app_service_name" {
  description = "Name of the App Service"
  value       = azurerm_linux_web_app.main.name
}

output "default_hostname" {
  description = "Default hostname of the App Service"
  value       = azurerm_linux_web_app.main.default_hostname
}

output "outbound_ip_addresses" {
  description = "Outbound IP addresses of the App Service"
  value       = azurerm_linux_web_app.main.outbound_ip_addresses
}

output "possible_outbound_ip_addresses" {
  description = "Possible outbound IP addresses of the App Service"
  value       = azurerm_linux_web_app.main.possible_outbound_ip_addresses
}

output "identity_principal_id" {
  description = "Principal ID of the App Service managed identity"
  value       = azurerm_linux_web_app.main.identity[0].principal_id
}

output "identity_tenant_id" {
  description = "Tenant ID of the App Service managed identity"
  value       = azurerm_linux_web_app.main.identity[0].tenant_id
}

output "staging_slot_id" {
  description = "ID of the staging slot"
  value       = azurerm_linux_web_app_slot.staging.id
}

output "staging_slot_hostname" {
  description = "Hostname of the staging slot"
  value       = azurerm_linux_web_app_slot.staging.default_hostname
}

output "service_plan_id" {
  description = "ID of the App Service Plan"
  value       = azurerm_service_plan.main.id
}

