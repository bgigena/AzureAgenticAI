provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "ai_rg" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location
}