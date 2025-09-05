# Application Gateway Module Variables

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
  description = "ID of the subnet for Application Gateway"
  type        = string
}

variable "sku_name" {
  description = "SKU name for Application Gateway"
  type        = string
  default     = "WAF_v2"
}

variable "sku_tier" {
  description = "SKU tier for Application Gateway"
  type        = string
  default     = "WAF_v2"
}

variable "capacity" {
  description = "Capacity for Application Gateway"
  type        = number
  default     = 2
}

variable "backend_address_pool_fqdns" {
  description = "FQDNs for the backend address pool"
  type        = list(string)
  default     = []
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

