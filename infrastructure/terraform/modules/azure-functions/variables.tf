# Azure Functions Module Variables

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

variable "sku_name" {
  description = "SKU name for the Function App Service Plan"
  type        = string
  default     = "EP1"
}

variable "storage_account_name" {
  description = "Name of the storage account"
  type        = string
}

variable "storage_account_access_key" {
  description = "Access key for the storage account"
  type        = string
  sensitive   = true
}

variable "app_insights_connection_string" {
  description = "Application Insights connection string"
  type        = string
  sensitive   = true
}

variable "cosmos_db_endpoint" {
  description = "Cosmos DB endpoint"
  type        = string
}

variable "cosmos_db_key" {
  description = "Cosmos DB key"
  type        = string
  sensitive   = true
}

variable "eventhub_connection_string" {
  description = "Event Hub connection string"
  type        = string
  sensitive   = true
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

