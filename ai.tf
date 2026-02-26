# AI Services Account
resource "azurerm_cognitive_account" "openai" {
  name                  = "oai-${var.project_name}-${var.environment}"
  location              = azurerm_resource_group.ai_rg.location
  resource_group_name   = azurerm_resource_group.ai_rg.name
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = "oai-${var.project_name}-${var.environment}"
}

# Modelo GPT
resource "azurerm_cognitive_deployment" "model" {
  name                 = var.openai_model_name
  cognitive_account_id = azurerm_cognitive_account.openai.id
  model {
    format  = "OpenAI"
    name    = var.openai_model_name
    version = var.openai_model_version
  }
  sku {
    name     = "Standard"
    capacity = var.tokens_capacity
  }
}

# Modelo de Embeddings
resource "azurerm_cognitive_deployment" "embedding_model" {
  name                 = var.embedding_model_name
  cognitive_account_id = azurerm_cognitive_account.openai.id
  model {
    format  = "OpenAI"
    name    = var.embedding_model_name
    version = var.embedding_model_version
  }
  sku {
    name     = "Standard"
    capacity = var.tokens_capacity
  }
}

# Vector Store
resource "azurerm_search_service" "vector_db" {
  name                = "search-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.ai_rg.name
  location            = azurerm_resource_group.ai_rg.location
  sku                 = "standard"
  semantic_search_sku = "standard"
}

# Monitoreo
resource "azurerm_log_analytics_workspace" "logs" {
  name                = "log-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.ai_rg.location
  resource_group_name = azurerm_resource_group.ai_rg.name
}

resource "azurerm_application_insights" "ai_app_insights" {
  name                = "appi-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.ai_rg.location
  resource_group_name = azurerm_resource_group.ai_rg.name
  workspace_id        = azurerm_log_analytics_workspace.logs.id
  application_type    = "web"
}

# ASIGNACIÓN DE ROLES (Tu toque de experto DevOps)
# Te da a ti (que despliegas) permisos para usar el modelo sin Keys
resource "azurerm_role_assignment" "me_openai_user" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = data.azurerm_client_config.current.object_id
}
