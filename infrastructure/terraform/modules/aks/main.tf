# AKS Module for Phoenix System

# AKS Cluster
resource "azurerm_kubernetes_cluster" "main" {
  name                = "aks-${var.resource_suffix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = "aks-${var.resource_suffix}"
  kubernetes_version  = var.kubernetes_version
  
  default_node_pool {
    name                = "default"
    node_count          = var.node_count
    vm_size             = var.node_vm_size
    vnet_subnet_id      = var.subnet_id
    enable_auto_scaling = true
    min_count          = var.min_node_count
    max_count          = var.max_node_count
    
    upgrade_settings {
      max_surge = "10%"
    }
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  network_profile {
    network_plugin    = "azure"
    network_policy    = "azure"
    load_balancer_sku = "standard"
    service_cidr      = "172.16.0.0/16"
    dns_service_ip    = "172.16.0.10"
  }
  
  # Enable monitoring
  oms_agent {
    log_analytics_workspace_id = var.log_analytics_workspace_id
  }
  
  # Enable Azure Policy
  azure_policy_enabled = true
  
  # Enable HTTP application routing (for demo purposes)
  http_application_routing_enabled = false
  
  # Enable role-based access control
  role_based_access_control_enabled = true
  
  # Azure Active Directory integration
  azure_active_directory_role_based_access_control {
    managed = true
  }
  
  tags = var.tags
}

# Additional Node Pool for AI workloads
resource "azurerm_kubernetes_cluster_node_pool" "ai_workloads" {
  name                  = "aipool"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = var.ai_node_vm_size
  node_count            = var.ai_node_count
  vnet_subnet_id        = var.subnet_id
  
  enable_auto_scaling = true
  min_count          = 1
  max_count          = 5
  
  node_taints = ["workload=ai:NoSchedule"]
  
  node_labels = {
    "workload" = "ai"
    "gpu"      = "enabled"
  }
  
  tags = var.tags
}

# Container Registry
resource "azurerm_container_registry" "main" {
  name                = "acr${replace(var.resource_suffix, "-", "")}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Premium"
  admin_enabled       = false
  
  identity {
    type = "SystemAssigned"
  }
  
  network_rule_set {
    default_action = "Deny"
    
    virtual_network {
      action    = "Allow"
      subnet_id = var.subnet_id
    }
  }
  
  tags = var.tags
}

# Grant AKS access to ACR
resource "azurerm_role_assignment" "aks_acr_pull" {
  principal_id                     = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                           = azurerm_container_registry.main.id
  skip_service_principal_aad_check = true
}

# Diagnostic Settings for AKS
resource "azurerm_monitor_diagnostic_setting" "aks" {
  count                      = var.log_analytics_workspace_id != null ? 1 : 0
  name                       = "diag-aks-${var.resource_suffix}"
  target_resource_id         = azurerm_kubernetes_cluster.main.id
  log_analytics_workspace_id = var.log_analytics_workspace_id
  
  enabled_log {
    category = "kube-apiserver"
  }
  
  enabled_log {
    category = "kube-audit"
  }
  
  enabled_log {
    category = "kube-audit-admin"
  }
  
  enabled_log {
    category = "kube-controller-manager"
  }
  
  enabled_log {
    category = "kube-scheduler"
  }
  
  enabled_log {
    category = "cluster-autoscaler"
  }
  
  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

# Flux Configuration for GitOps
resource "azurerm_kubernetes_flux_configuration" "main" {
  name       = "phoenix-gitops"
  cluster_id = azurerm_kubernetes_cluster.main.id
  namespace  = "flux-system"
  
  git_repository {
    url                      = var.gitops_repository_url
    reference_type           = "branch"
    reference_value          = "main"
    sync_interval_in_seconds = 600
  }
  
  kustomizations {
    name = "phoenix-apps"
    path = "./kubernetes/apps"
    sync_interval_in_seconds = 600
    retry_interval_in_seconds = 600
  }
  
  depends_on = [azurerm_kubernetes_cluster.main]
}

