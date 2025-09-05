# Phoenix System - Main Terraform Configuration
# Sistema Autônomo de Resolução de Incidentes

terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.45"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
    cognitive_account {
      purge_soft_delete_on_destroy = true
    }
  }
}

provider "azuread" {}

# Data sources
data "azurerm_client_config" "current" {}
data "azuread_client_config" "current" {}

# Random suffix for unique naming
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Local variables
locals {
  project_name = "phoenix"
  environment  = var.environment
  location     = var.location
  
  # Naming convention
  resource_suffix = "${local.project_name}-${local.environment}-${random_string.suffix.result}"
  
  # Common tags
  common_tags = {
    Project     = "Phoenix System"
    Environment = local.environment
    ManagedBy   = "Terraform"
    Purpose     = "Autonomous Incident Resolution"
    CreatedBy   = data.azurerm_client_config.current.object_id
  }
  
  # Network configuration
  vnet_address_space = ["10.0.0.0/16"]
  subnets = {
    application_gateway = {
      name             = "snet-agw-${local.resource_suffix}"
      address_prefixes = ["10.0.1.0/24"]
    }
    app_service_integration = {
      name             = "snet-app-${local.resource_suffix}"
      address_prefixes = ["10.0.2.0/24"]
      delegation = {
        name = "Microsoft.Web/serverFarms"
        service_delegation = {
          name = "Microsoft.Web/serverFarms"
        }
      }
    }
    ai_agent_integration = {
      name             = "snet-ai-${local.resource_suffix}"
      address_prefixes = ["10.0.3.0/24"]
    }
    bastion = {
      name             = "AzureBastionSubnet"
      address_prefixes = ["10.0.4.0/27"]
    }
    build_agents = {
      name             = "snet-build-${local.resource_suffix}"
      address_prefixes = ["10.0.5.0/24"]
    }
    private_endpoints = {
      name             = "snet-pe-${local.resource_suffix}"
      address_prefixes = ["10.0.6.0/24"]
    }
    aks = {
      name             = "snet-aks-${local.resource_suffix}"
      address_prefixes = ["10.0.10.0/22"]
    }
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-${local.resource_suffix}"
  location = local.location
  tags     = local.common_tags
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = "vnet-${local.resource_suffix}"
  address_space       = local.vnet_address_space
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.common_tags
}

# Subnets
resource "azurerm_subnet" "subnets" {
  for_each = local.subnets
  
  name                 = each.value.name
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = each.value.address_prefixes
  
  dynamic "delegation" {
    for_each = can(each.value.delegation) ? [each.value.delegation] : []
    content {
      name = delegation.value.name
      service_delegation {
        name = delegation.value.service_delegation.name
      }
    }
  }
}

# Network Security Groups
resource "azurerm_network_security_group" "app_gateway" {
  name                = "nsg-agw-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.common_tags

  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowHTTP"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowGatewayManager"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "65200-65535"
    source_address_prefix      = "GatewayManager"
    destination_address_prefix = "*"
  }
}

# Associate NSG with Application Gateway subnet
resource "azurerm_subnet_network_security_group_association" "app_gateway" {
  subnet_id                 = azurerm_subnet.subnets["application_gateway"].id
  network_security_group_id = azurerm_network_security_group.app_gateway.id
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.common_tags
}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = "appi-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = local.common_tags
}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                = "kv-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
  
  enable_rbac_authorization = true
  purge_protection_enabled  = false
  
  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
  }
  
  tags = local.common_tags
}

# Storage Account
resource "azurerm_storage_account" "main" {
  name                     = "st${replace(local.resource_suffix, "-", "")}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  blob_properties {
    versioning_enabled = true
  }
  
  tags = local.common_tags
}

# Cosmos DB Account
resource "azurerm_cosmosdb_account" "main" {
  name                = "cosmos-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  
  consistency_policy {
    consistency_level = "Session"
  }
  
  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }
  
  tags = local.common_tags
}

# Cosmos DB Database
resource "azurerm_cosmosdb_sql_database" "phoenix" {
  name                = "phoenix-db"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
}

# Cosmos DB Containers
resource "azurerm_cosmosdb_sql_container" "agents_state" {
  name                = "agents-state"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.phoenix.name
  partition_key_path  = "/agentId"
  
  indexing_policy {
    indexing_mode = "consistent"
    
    included_path {
      path = "/*"
    }
  }
}

resource "azurerm_cosmosdb_sql_container" "incidents" {
  name                = "incidents"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.phoenix.name
  partition_key_path  = "/incidentId"
  
  indexing_policy {
    indexing_mode = "consistent"
    
    included_path {
      path = "/*"
    }
  }
}

# Cognitive Services Account for Azure AI Foundry
resource "azurerm_cognitive_account" "ai_foundry" {
  name                = "cog-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "AIServices"
  sku_name            = "S0"
  
  tags = local.common_tags
}

# Azure AI Search
resource "azurerm_search_service" "main" {
  name                = "srch-${local.resource_suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "standard"
  replica_count       = 1
  partition_count     = 1
  
  tags = local.common_tags
}

# Event Hub Namespace
resource "azurerm_eventhub_namespace" "main" {
  name                = "evhns-${local.resource_suffix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Standard"
  capacity            = 1
  
  tags = local.common_tags
}

# Event Hub
resource "azurerm_eventhub" "incidents" {
  name                = "incidents"
  namespace_name      = azurerm_eventhub_namespace.main.name
  resource_group_name = azurerm_resource_group.main.name
  partition_count     = 2
  message_retention   = 1
}

# Module calls
module "app_service" {
  source = "./modules/app-service"
  
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  resource_suffix    = local.resource_suffix
  subnet_id          = azurerm_subnet.subnets["app_service_integration"].id
  
  app_insights_connection_string = azurerm_application_insights.main.connection_string
  key_vault_id                  = azurerm_key_vault.main.id
  
  tags = local.common_tags
}

module "application_gateway" {
  source = "./modules/application-gateway"
  
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  resource_suffix    = local.resource_suffix
  subnet_id          = azurerm_subnet.subnets["application_gateway"].id
  
  backend_address_pool_fqdns = [module.app_service.default_hostname]
  
  tags = local.common_tags
}

module "aks" {
  source = "./modules/aks"
  
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  resource_suffix    = local.resource_suffix
  subnet_id          = azurerm_subnet.subnets["aks"].id
  
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  
  tags = local.common_tags
}

module "azure_functions" {
  source = "./modules/azure-functions"
  
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  resource_suffix    = local.resource_suffix
  
  storage_account_name       = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key
  app_insights_connection_string = azurerm_application_insights.main.connection_string
  
  cosmos_db_endpoint = azurerm_cosmosdb_account.main.endpoint
  cosmos_db_key      = azurerm_cosmosdb_account.main.primary_key
  
  eventhub_connection_string = azurerm_eventhub_namespace.main.default_primary_connection_string
  
  tags = local.common_tags
}

module "private_endpoints" {
  source = "./modules/private-endpoints"
  
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  resource_suffix    = local.resource_suffix
  subnet_id          = azurerm_subnet.subnets["private_endpoints"].id
  virtual_network_id = azurerm_virtual_network.main.id
  
  key_vault_id           = azurerm_key_vault.main.id
  storage_account_id     = azurerm_storage_account.main.id
  cosmos_db_account_id   = azurerm_cosmosdb_account.main.id
  cognitive_account_id   = azurerm_cognitive_account.ai_foundry.id
  search_service_id      = azurerm_search_service.main.id
  
  tags = local.common_tags
}

# Outputs
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "virtual_network_name" {
  description = "Name of the virtual network"
  value       = azurerm_virtual_network.main.name
}

output "application_gateway_public_ip" {
  description = "Public IP of the Application Gateway"
  value       = module.application_gateway.public_ip_address
}

output "app_service_hostname" {
  description = "Hostname of the App Service"
  value       = module.app_service.default_hostname
}

output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = module.aks.cluster_name
}

output "cosmos_db_endpoint" {
  description = "Cosmos DB endpoint"
  value       = azurerm_cosmosdb_account.main.endpoint
  sensitive   = true
}

output "key_vault_uri" {
  description = "Key Vault URI"
  value       = azurerm_key_vault.main.vault_uri
}

output "ai_foundry_endpoint" {
  description = "Azure AI Foundry endpoint"
  value       = azurerm_cognitive_account.ai_foundry.endpoint
  sensitive   = true
}

