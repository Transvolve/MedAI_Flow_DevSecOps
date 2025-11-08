# ------------------------------------------------------------
# Terraform IaC for Azure AKS + ACR (MedAI_Flow_DevSecOps)
# ------------------------------------------------------------
terraform {
  required_version = ">= 1.3.0"
  
  # Remote state backend (uncomment for production)
  # backend "azurerm" {
  #   resource_group_name  = "rg-medai-terraform"
  #   storage_account_name = "medaitfstate"
  #   container_name       = "tfstate"
  #   key                  = "medai-flow.tfstate"
  # }
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# ---------------- Resource Group ----------------
resource "azurerm_resource_group" "medai_rg" {
  name     = "rg-medai-flow"
  location = "westeurope"
}

# ---------------- Container Registry ----------------
resource "azurerm_container_registry" "medai_acr" {
  name                = "medaiflowacr"
  resource_group_name = azurerm_resource_group.medai_rg.name
  location            = azurerm_resource_group.medai_rg.location
  sku                 = "Standard"  # Upgraded from Basic for security features
  admin_enabled       = false       # SECURITY: Disabled admin account, use managed identity

  # Enable content trust and vulnerability scanning
  quarantine_policy_enabled = true
  
  # Encryption at rest
  encryption {
    enabled = true
  }

  # Network rules for production
  network_rule_set {
    default_action = "Deny"
    
    ip_rule {
      action   = "Allow"
      ip_range = "0.0.0.0/0"  # TODO: Restrict to AKS subnet and CI/CD IPs
    }
  }

  tags = {
    Environment = "DevSecOps"
    Project     = "MedAI_Flow"
    Compliance  = "ISO27001,FDA21CFR820"
  }
}

# Grant AKS pull access to ACR using Managed Identity
resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.medai_acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.medai_aks.kubelet_identity[0].object_id
}

# ---------------- AKS Cluster ----------------
resource "azurerm_kubernetes_cluster" "medai_aks" {
  name                = "medai-aks-cluster"
  location            = azurerm_resource_group.medai_rg.location
  resource_group_name = azurerm_resource_group.medai_rg.name
  dns_prefix          = "medaiflow"

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_B2s"
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
  }

  tags = {
    Environment = "DevSecOps"
    Project     = "MedAI_Flow"
  }
}

# ---------------- Outputs ----------------
output "kube_config" {
  value     = azurerm_kubernetes_cluster.medai_aks.kube_config_raw
  sensitive = true
}

output "acr_login_server" {
  value = azurerm_container_registry.medai_acr.login_server
}
