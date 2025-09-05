# App Service Module Variables

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "resource_suffix" {
  description = "Suffix for resource naming"
  type        = string
}

variable "subnet_id" {
  description = "ID of the subnet for VNet integration"
  type        = string
}

variable "sku_name" {
  description = "SKU name for the App Service Plan"
  type        = string
  default     = "P1v3"
}

variable "app_insights_connection_string" {
  description = "Application Insights connection string"
  type        = string
  sensitive   = true
}

variable "key_vault_id" {
  description = "ID of the Key Vault"
  type        = string
}

variable "key_vault_uri" {
  description = "URI of the Key Vault"
  type        = string
  default     = ""
}

variable "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

