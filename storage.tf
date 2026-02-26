# --- RECURSOS PARA LA INGESTA AUTOMÁTICA ---

# 1. Storage Account para Documentos y Function
resource "azurerm_storage_account" "ai_storage" {
  name                     = "st${var.project_name}${var.environment}"
  resource_group_name      = azurerm_resource_group.ai_rg.name
  location                 = azurerm_resource_group.ai_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# Container donde se subirán los PDFs/Docs
resource "azurerm_storage_container" "docs_container" {
  name                  = "documents"
  storage_account_name  = azurerm_storage_account.ai_storage.name
  container_access_type = "private"
}
