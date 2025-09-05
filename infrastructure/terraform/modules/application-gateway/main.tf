# Application Gateway Module for Phoenix System

# Public IP for Application Gateway
resource "azurerm_public_ip" "main" {
  name                = "pip-agw-${var.resource_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  allocation_method   = "Static"
  sku                 = "Standard"
  
  tags = var.tags
}

# Application Gateway
resource "azurerm_application_gateway" "main" {
  name                = "agw-${var.resource_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  
  sku {
    name     = var.sku_name
    tier     = var.sku_tier
    capacity = var.capacity
  }
  
  gateway_ip_configuration {
    name      = "gateway-ip-configuration"
    subnet_id = var.subnet_id
  }
  
  frontend_port {
    name = "frontend-port-80"
    port = 80
  }
  
  frontend_port {
    name = "frontend-port-443"
    port = 443
  }
  
  frontend_ip_configuration {
    name                 = "frontend-ip-configuration"
    public_ip_address_id = azurerm_public_ip.main.id
  }
  
  backend_address_pool {
    name  = "backend-pool"
    fqdns = var.backend_address_pool_fqdns
  }
  
  backend_http_settings {
    name                  = "backend-http-settings"
    cookie_based_affinity = "Disabled"
    path                  = "/"
    port                  = 80
    protocol              = "Http"
    request_timeout       = 60
    
    probe_name = "health-probe"
  }
  
  backend_http_settings {
    name                  = "backend-https-settings"
    cookie_based_affinity = "Disabled"
    path                  = "/"
    port                  = 443
    protocol              = "Https"
    request_timeout       = 60
    
    probe_name = "health-probe-https"
  }
  
  http_listener {
    name                           = "http-listener"
    frontend_ip_configuration_name = "frontend-ip-configuration"
    frontend_port_name             = "frontend-port-80"
    protocol                       = "Http"
  }
  
  request_routing_rule {
    name                       = "routing-rule-http"
    rule_type                  = "Basic"
    http_listener_name         = "http-listener"
    backend_address_pool_name  = "backend-pool"
    backend_http_settings_name = "backend-http-settings"
    priority                   = 100
  }
  
  probe {
    name                = "health-probe"
    protocol            = "Http"
    path                = "/health"
    host                = "127.0.0.1"
    interval            = 30
    timeout             = 30
    unhealthy_threshold = 3
    
    match {
      status_code = ["200-399"]
    }
  }
  
  probe {
    name                = "health-probe-https"
    protocol            = "Https"
    path                = "/health"
    host                = "127.0.0.1"
    interval            = 30
    timeout             = 30
    unhealthy_threshold = 3
    
    match {
      status_code = ["200-399"]
    }
  }
  
  # WAF Configuration
  waf_configuration {
    enabled          = true
    firewall_mode    = "Prevention"
    rule_set_type    = "OWASP"
    rule_set_version = "3.2"
    
    disabled_rule_group {
      rule_group_name = "REQUEST-920-PROTOCOL-ENFORCEMENT"
      rules           = ["920300", "920440"]
    }
  }
  
  # Enable HTTP/2
  enable_http2 = true
  
  tags = var.tags
}

# Diagnostic Settings
resource "azurerm_monitor_diagnostic_setting" "application_gateway" {
  count                      = var.log_analytics_workspace_id != null ? 1 : 0
  name                       = "diag-agw-${var.resource_suffix}"
  target_resource_id         = azurerm_application_gateway.main.id
  log_analytics_workspace_id = var.log_analytics_workspace_id
  
  enabled_log {
    category = "ApplicationGatewayAccessLog"
  }
  
  enabled_log {
    category = "ApplicationGatewayPerformanceLog"
  }
  
  enabled_log {
    category = "ApplicationGatewayFirewallLog"
  }
  
  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

