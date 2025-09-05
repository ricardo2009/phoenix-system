# Phoenix System - Terraform Variables

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  default     = null
}

variable "tenant_id" {
  description = "Azure tenant ID"
  type        = string
  default     = null
}

# Network Configuration
variable "vnet_address_space" {
  description = "Address space for the virtual network"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

# App Service Configuration
variable "app_service_sku" {
  description = "SKU for the App Service Plan"
  type        = string
  default     = "P1v3"
  
  validation {
    condition     = contains(["B1", "B2", "B3", "S1", "S2", "S3", "P1v2", "P2v2", "P3v2", "P1v3", "P2v3", "P3v3"], var.app_service_sku)
    error_message = "App Service SKU must be a valid Azure App Service plan SKU."
  }
}

# AKS Configuration
variable "aks_node_count" {
  description = "Number of nodes in the AKS cluster"
  type        = number
  default     = 3
  
  validation {
    condition     = var.aks_node_count >= 1 && var.aks_node_count <= 10
    error_message = "AKS node count must be between 1 and 10."
  }
}

variable "aks_node_vm_size" {
  description = "VM size for AKS nodes"
  type        = string
  default     = "Standard_D2s_v3"
}

variable "aks_kubernetes_version" {
  description = "Kubernetes version for AKS cluster"
  type        = string
  default     = "1.28"
}

# Cosmos DB Configuration
variable "cosmos_db_consistency_level" {
  description = "Consistency level for Cosmos DB"
  type        = string
  default     = "Session"
  
  validation {
    condition     = contains(["Eventual", "Session", "Strong", "ConsistentPrefix", "BoundedStaleness"], var.cosmos_db_consistency_level)
    error_message = "Cosmos DB consistency level must be one of: Eventual, Session, Strong, ConsistentPrefix, BoundedStaleness."
  }
}

variable "cosmos_db_throughput" {
  description = "Throughput for Cosmos DB containers"
  type        = number
  default     = 400
  
  validation {
    condition     = var.cosmos_db_throughput >= 400
    error_message = "Cosmos DB throughput must be at least 400 RU/s."
  }
}

# Azure AI Configuration
variable "cognitive_services_sku" {
  description = "SKU for Cognitive Services"
  type        = string
  default     = "S0"
  
  validation {
    condition     = contains(["F0", "S0", "S1", "S2", "S3", "S4"], var.cognitive_services_sku)
    error_message = "Cognitive Services SKU must be one of: F0, S0, S1, S2, S3, S4."
  }
}

# Search Service Configuration
variable "search_service_sku" {
  description = "SKU for Azure Search Service"
  type        = string
  default     = "standard"
  
  validation {
    condition     = contains(["free", "basic", "standard", "standard2", "standard3", "storage_optimized_l1", "storage_optimized_l2"], var.search_service_sku)
    error_message = "Search Service SKU must be a valid Azure Search SKU."
  }
}

# Event Hub Configuration
variable "eventhub_sku" {
  description = "SKU for Event Hub Namespace"
  type        = string
  default     = "Standard"
  
  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.eventhub_sku)
    error_message = "Event Hub SKU must be one of: Basic, Standard, Premium."
  }
}

variable "eventhub_capacity" {
  description = "Capacity for Event Hub Namespace"
  type        = number
  default     = 1
  
  validation {
    condition     = var.eventhub_capacity >= 1 && var.eventhub_capacity <= 20
    error_message = "Event Hub capacity must be between 1 and 20."
  }
}

# Log Analytics Configuration
variable "log_analytics_retention_days" {
  description = "Retention period for Log Analytics workspace"
  type        = number
  default     = 30
  
  validation {
    condition     = var.log_analytics_retention_days >= 30 && var.log_analytics_retention_days <= 730
    error_message = "Log Analytics retention must be between 30 and 730 days."
  }
}

# Security Configuration
variable "enable_private_endpoints" {
  description = "Enable private endpoints for services"
  type        = bool
  default     = true
}

variable "enable_network_security_groups" {
  description = "Enable Network Security Groups"
  type        = bool
  default     = true
}

variable "allowed_ip_ranges" {
  description = "IP ranges allowed to access resources"
  type        = list(string)
  default     = []
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}

variable "enable_diagnostic_settings" {
  description = "Enable diagnostic settings for resources"
  type        = bool
  default     = true
}

# Backup Configuration
variable "enable_backup" {
  description = "Enable backup for applicable resources"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 30
  
  validation {
    condition     = var.backup_retention_days >= 7 && var.backup_retention_days <= 365
    error_message = "Backup retention must be between 7 and 365 days."
  }
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}

# Feature Flags
variable "deploy_bastion" {
  description = "Deploy Azure Bastion for secure access"
  type        = bool
  default     = false
}

variable "deploy_firewall" {
  description = "Deploy Azure Firewall"
  type        = bool
  default     = false
}

variable "deploy_application_gateway" {
  description = "Deploy Application Gateway with WAF"
  type        = bool
  default     = true
}

variable "deploy_aks" {
  description = "Deploy AKS cluster"
  type        = bool
  default     = true
}

variable "deploy_functions" {
  description = "Deploy Azure Functions"
  type        = bool
  default     = true
}

# Agent Configuration
variable "agent_configurations" {
  description = "Configuration for Phoenix agents"
  type = object({
    orchestrator = object({
      response_timeout = number
      max_retries     = number
    })
    diagnostic = object({
      analysis_timeout    = number
      confidence_threshold = number
    })
    resolution = object({
      execution_timeout = number
      rollback_enabled  = bool
    })
    communication = object({
      notification_channels = list(string)
      escalation_timeout   = number
    })
  })
  default = {
    orchestrator = {
      response_timeout = 30
      max_retries     = 3
    }
    diagnostic = {
      analysis_timeout    = 60
      confidence_threshold = 0.85
    }
    resolution = {
      execution_timeout = 120
      rollback_enabled  = true
    }
    communication = {
      notification_channels = ["teams", "email"]
      escalation_timeout   = 300
    }
  }
}

