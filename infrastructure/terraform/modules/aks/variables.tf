# AKS Module Variables

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
  description = "ID of the subnet for AKS"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "node_count" {
  description = "Number of nodes in the default node pool"
  type        = number
  default     = 3
}

variable "min_node_count" {
  description = "Minimum number of nodes in the default node pool"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum number of nodes in the default node pool"
  type        = number
  default     = 10
}

variable "node_vm_size" {
  description = "VM size for nodes"
  type        = string
  default     = "Standard_D2s_v3"
}

variable "ai_node_count" {
  description = "Number of nodes in the AI node pool"
  type        = number
  default     = 2
}

variable "ai_node_vm_size" {
  description = "VM size for AI nodes"
  type        = string
  default     = "Standard_NC6s_v3"
}

variable "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace"
  type        = string
}

variable "gitops_repository_url" {
  description = "URL of the GitOps repository"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

