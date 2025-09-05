# Azure Functions Module Outputs

output "service_plan_id" {
  description = "ID of the Function App Service Plan"
  value       = azurerm_service_plan.functions.id
}

output "orchestrator_function_app_id" {
  description = "ID of the Orchestrator Function App"
  value       = azurerm_linux_function_app.orchestrator.id
}

output "orchestrator_function_app_name" {
  description = "Name of the Orchestrator Function App"
  value       = azurerm_linux_function_app.orchestrator.name
}

output "orchestrator_default_hostname" {
  description = "Default hostname of the Orchestrator Function App"
  value       = azurerm_linux_function_app.orchestrator.default_hostname
}

output "diagnostic_function_app_id" {
  description = "ID of the Diagnostic Function App"
  value       = azurerm_linux_function_app.diagnostic.id
}

output "diagnostic_function_app_name" {
  description = "Name of the Diagnostic Function App"
  value       = azurerm_linux_function_app.diagnostic.name
}

output "diagnostic_default_hostname" {
  description = "Default hostname of the Diagnostic Function App"
  value       = azurerm_linux_function_app.diagnostic.default_hostname
}

output "resolution_function_app_id" {
  description = "ID of the Resolution Function App"
  value       = azurerm_linux_function_app.resolution.id
}

output "resolution_function_app_name" {
  description = "Name of the Resolution Function App"
  value       = azurerm_linux_function_app.resolution.name
}

output "resolution_default_hostname" {
  description = "Default hostname of the Resolution Function App"
  value       = azurerm_linux_function_app.resolution.default_hostname
}

output "communication_function_app_id" {
  description = "ID of the Communication Function App"
  value       = azurerm_linux_function_app.communication.id
}

output "communication_function_app_name" {
  description = "Name of the Communication Function App"
  value       = azurerm_linux_function_app.communication.name
}

output "communication_default_hostname" {
  description = "Default hostname of the Communication Function App"
  value       = azurerm_linux_function_app.communication.default_hostname
}

# Identity outputs for each function app
output "orchestrator_identity_principal_id" {
  description = "Principal ID of the Orchestrator Function App identity"
  value       = azurerm_linux_function_app.orchestrator.identity[0].principal_id
}

output "diagnostic_identity_principal_id" {
  description = "Principal ID of the Diagnostic Function App identity"
  value       = azurerm_linux_function_app.diagnostic.identity[0].principal_id
}

output "resolution_identity_principal_id" {
  description = "Principal ID of the Resolution Function App identity"
  value       = azurerm_linux_function_app.resolution.identity[0].principal_id
}

output "communication_identity_principal_id" {
  description = "Principal ID of the Communication Function App identity"
  value       = azurerm_linux_function_app.communication.identity[0].principal_id
}

