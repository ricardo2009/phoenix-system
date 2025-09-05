# App Service Module for Phoenix System

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "asp-${var.resource_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = var.sku_name
  
  tags = var.tags
}

# App Service
resource "azurerm_linux_web_app" "main" {
  name                = "app-${var.resource_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.main.id
  
  virtual_network_subnet_id = var.subnet_id
  
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
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = var.app_insights_connection_string
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE"   = "false"
    "DOCKER_REGISTRY_SERVER_URL"            = "https://index.docker.io"
    "PHOENIX_ENVIRONMENT"                   = "production"
    "KEY_VAULT_URI"                        = var.key_vault_uri
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  logs {
    detailed_error_messages = true
    failed_request_tracing  = true
    
    application_logs {
      file_system_level = "Information"
    }
    
    http_logs {
      file_system {
        retention_in_days = 7
        retention_in_mb   = 35
      }
    }
  }
  
  tags = var.tags
}

# Key Vault Access Policy for App Service
resource "azurerm_key_vault_access_policy" "app_service" {
  key_vault_id = var.key_vault_id
  tenant_id    = azurerm_linux_web_app.main.identity[0].tenant_id
  object_id    = azurerm_linux_web_app.main.identity[0].principal_id
  
  secret_permissions = [
    "Get",
    "List"
  ]
  
  certificate_permissions = [
    "Get",
    "List"
  ]
}

# App Service Slot for Blue-Green Deployment
resource "azurerm_linux_web_app_slot" "staging" {
  name           = "staging"
  app_service_id = azurerm_linux_web_app.main.id
  
  site_config {
    always_on = true
    
    application_stack {
      python_version = "3.11"
    }
  }
  
  app_settings = {
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = var.app_insights_connection_string
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE"   = "false"
    "DOCKER_REGISTRY_SERVER_URL"            = "https://index.docker.io"
    "PHOENIX_ENVIRONMENT"                   = "staging"
    "KEY_VAULT_URI"                        = var.key_vault_uri
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

# Diagnostic Settings
resource "azurerm_monitor_diagnostic_setting" "app_service" {
  name                       = "diag-app-${var.resource_suffix}"
  target_resource_id         = azurerm_linux_web_app.main.id
  log_analytics_workspace_id = var.log_analytics_workspace_id
  
  enabled_log {
    category = "AppServiceHTTPLogs"
  }
  
  enabled_log {
    category = "AppServiceConsoleLogs"
  }
  
  enabled_log {
    category = "AppServiceAppLogs"
  }
  
  enabled_log {
    category = "AppServiceAuditLogs"
  }
  
  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

