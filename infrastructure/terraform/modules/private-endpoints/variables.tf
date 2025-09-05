# Private Endpoints Module Variables

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
  description = "ID of the subnet for private endpoints"
  type        = string
}

variable "virtual_network_id" {
  description = "ID of the virtual network"
  type        = string
}

variable "key_vault_id" {
  description = "ID of the Key Vault"
  type        = string
}

variable "storage_account_id" {
  description = "ID of the Storage Account"
  type        = string
}

variable "cosmos_db_account_id" {
  description = "ID of the Cosmos DB Account"
  type        = string
}

variable "cognitive_account_id" {
  description = "ID of the Cognitive Services Account"
  type        = string
}

variable "search_service_id" {
  description = "ID of the Search Service"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

