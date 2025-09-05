# Phoenix System - Terraform Variables Values

# Environment Configuration
environment = "dev"
location    = "East US"

# Network Configuration
vnet_address_space = ["10.0.0.0/16"]

# App Service Configuration
app_service_sku = "P1v3"

# AKS Configuration
aks_node_count         = 3
aks_node_vm_size      = "Standard_D2s_v3"
aks_kubernetes_version = "1.28"

# Cosmos DB Configuration
cosmos_db_consistency_level = "Session"
cosmos_db_throughput       = 400

# Azure AI Configuration
cognitive_services_sku = "S0"

# Search Service Configuration
search_service_sku = "standard"

# Event Hub Configuration
eventhub_sku      = "Standard"
eventhub_capacity = 1

# Log Analytics Configuration
log_analytics_retention_days = 30

# Security Configuration
enable_private_endpoints        = true
enable_network_security_groups = true
allowed_ip_ranges              = []

# Monitoring Configuration
enable_monitoring           = true
enable_diagnostic_settings = true

# Backup Configuration
enable_backup           = true
backup_retention_days   = 30

# Feature Flags
deploy_bastion             = false
deploy_firewall           = false
deploy_application_gateway = true
deploy_aks                = true
deploy_functions          = true

# Agent Configuration
agent_configurations = {
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

# Additional Tags
additional_tags = {
  Owner       = "Phoenix Team"
  CostCenter  = "IT-Innovation"
  Environment = "Development"
  Project     = "Phoenix Autonomous System"
}

