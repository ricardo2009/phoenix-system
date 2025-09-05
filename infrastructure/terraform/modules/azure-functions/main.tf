# Azure Functions Module for Phoenix System

# Function App Service Plan
resource "azurerm_service_plan" "functions" {
  name                = "asp-func-${var.resource_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = var.sku_name
  
  tags = var.tags
}

# Function App for Orchestrator Agent
resource "azurerm_linux_function_app" "orchestrator" {
  name                = "func-orch-${var.resource_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.functions.id
  
  storage_account_name       = var.storage_account_name
  storage_account_access_key = var.storage_account_access_key
  
  site_config {
    always_on = true
    
    application_stack {
      python_version = "3.11"
    }
    
    cors {
      allowed_origins = ["*"]
    }
  }
  
  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"              = "python"
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = var.app_insights_connection_string
    "COSMOS_DB_ENDPOINT"                   = var.cosmos_db_endpoint
    "COSMOS_DB_KEY"                        = var.cosmos_db_key
    "EVENTHUB_CONNECTION_STRING"           = var.eventhub_connection_string
    "PHOENIX_AGENT_TYPE"                   = "orchestrator"
    "PHOENIX_ENVIRONMENT"                  = "production"
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

# Function App for Diagnostic Agent
resource "azurerm_linux_function_app" "diagnostic" {
  name                = "func-diag-${var.resource_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.functions.id
  
  storage_account_name       = var.storage_account_name
  storage_account_access_key = var.storage_account_access_key
  
  site_config {
    always_on = true
    
    application_stack {
      python_version = "3.11"
    }
  }
  
  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"              = "python"
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = var.app_insights_connection_string
    "COSMOS_DB_ENDPOINT"                   = var.cosmos_db_endpoint
    "COSMOS_DB_KEY"                        = var.cosmos_db_key
    "EVENTHUB_CONNECTION_STRING"           = var.eventhub_connection_string
    "PHOENIX_AGENT_TYPE"                   = "diagnostic"
    "PHOENIX_ENVIRONMENT"                  = "production"
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

# Function App for Resolution Agent
resource "azurerm_linux_function_app" "resolution" {
  name                = "func-res-${var.resource_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.functions.id
  
  storage_account_name       = var.storage_account_name
  storage_account_access_key = var.storage_account_access_key
  
  site_config {
    always_on = true
    
    application_stack {
      python_version = "3.11"
    }
  }
  
  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"              = "python"
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = var.app_insights_connection_string
    "COSMOS_DB_ENDPOINT"                   = var.cosmos_db_endpoint
    "COSMOS_DB_KEY"                        = var.cosmos_db_key
    "EVENTHUB_CONNECTION_STRING"           = var.eventhub_connection_string
    "PHOENIX_AGENT_TYPE"                   = "resolution"
    "PHOENIX_ENVIRONMENT"                  = "production"
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

# Function App for Communication Agent
resource "azurerm_linux_function_app" "communication" {
  name                = "func-comm-${var.resource_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.functions.id
  
  storage_account_name       = var.storage_account_name
  storage_account_access_key = var.storage_account_access_key
  
  site_config {
    always_on = true
    
    application_stack {
      python_version = "3.11"
    }
  }
  
  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"              = "python"
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = var.app_insights_connection_string
    "COSMOS_DB_ENDPOINT"                   = var.cosmos_db_endpoint
    "COSMOS_DB_KEY"                        = var.cosmos_db_key
    "EVENTHUB_CONNECTION_STRING"           = var.eventhub_connection_string
    "PHOENIX_AGENT_TYPE"                   = "communication"
    "PHOENIX_ENVIRONMENT"                  = "production"
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

# Diagnostic Settings for Function Apps
resource "azurerm_monitor_diagnostic_setting" "orchestrator" {
  count                      = var.log_analytics_workspace_id != null ? 1 : 0
  name                       = "diag-func-orch-${var.resource_suffix}"
  target_resource_id         = azurerm_linux_function_app.orchestrator.id
  log_analytics_workspace_id = var.log_analytics_workspace_id
  
  enabled_log {
    category = "FunctionAppLogs"
  }
  
  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

resource "azurerm_monitor_diagnostic_setting" "diagnostic" {
  count                      = var.log_analytics_workspace_id != null ? 1 : 0
  name                       = "diag-func-diag-${var.resource_suffix}"
  target_resource_id         = azurerm_linux_function_app.diagnostic.id
  log_analytics_workspace_id = var.log_analytics_workspace_id
  
  enabled_log {
    category = "FunctionAppLogs"
  }
  
  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

resource "azurerm_monitor_diagnostic_setting" "resolution" {
  count                      = var.log_analytics_workspace_id != null ? 1 : 0
  name                       = "diag-func-res-${var.resource_suffix}"
  target_resource_id         = azurerm_linux_function_app.resolution.id
  log_analytics_workspace_id = var.log_analytics_workspace_id
  
  enabled_log {
    category = "FunctionAppLogs"
  }
  
  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

resource "azurerm_monitor_diagnostic_setting" "communication" {
  count                      = var.log_analytics_workspace_id != null ? 1 : 0
  name                       = "diag-func-comm-${var.resource_suffix}"
  target_resource_id         = azurerm_linux_function_app.communication.id
  log_analytics_workspace_id = var.log_analytics_workspace_id
  
  enabled_log {
    category = "FunctionAppLogs"
  }
  
  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

