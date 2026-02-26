# 2. Plan Serverless (Consumption)
resource "azurerm_service_plan" "fn_plan" {
  name                = "asp-${var.project_name}-serverless"
  resource_group_name = azurerm_resource_group.ai_rg.name
  location            = azurerm_resource_group.ai_rg.location
  os_type             = "Linux"
  sku_name            = "B1" # Requerido Basic/Standard/Premium para VNet Integration
}

# 3. La Function App (El Cerebro de la Ingesta)
resource "azurerm_linux_function_app" "ingestor_fn" {
  name                = "fn-${var.project_name}-ingestor"
  resource_group_name = azurerm_resource_group.ai_rg.name
  location            = azurerm_resource_group.ai_rg.location

  storage_account_name       = azurerm_storage_account.ai_storage.name
  storage_account_access_key = azurerm_storage_account.ai_storage.primary_access_key
  service_plan_id            = azurerm_service_plan.fn_plan.id
  virtual_network_subnet_id  = azurerm_subnet.function_subnet.id # Integración con VNet

  site_config {
    application_stack {
      python_version = "3.11"
    }
    vnet_route_all_enabled = true # Enrutar todo el tráfico hacia la VNet
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"              = "python"
    "AzureWebJobsStorage"                   = azurerm_storage_account.ai_storage.primary_connection_string
    "AZURE_OPENAI_ENDPOINT"                 = azurerm_cognitive_account.openai.endpoint
    "AZURE_OPENAI_KEY"                      = azurerm_cognitive_account.openai.primary_access_key
    "AZURE_SEARCH_ENDPOINT"                 = "https://${azurerm_search_service.vector_db.name}.search.windows.net"
    "AZURE_SEARCH_KEY"                      = azurerm_search_service.vector_db.primary_key
    "AZURE_SEARCH_INDEX_NAME"               = "vector-index"
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.ai_app_insights.connection_string
  }
}

# 4. Event Grid para Ingesta Escalable
resource "azurerm_eventgrid_system_topic" "storage_topic" {
  name                   = "egst-${var.project_name}-${var.environment}"
  resource_group_name    = azurerm_resource_group.ai_rg.name
  location               = azurerm_resource_group.ai_rg.location
  source_arm_resource_id = azurerm_storage_account.ai_storage.id
  topic_type             = "Microsoft.Storage.StorageAccounts"
}

resource "azurerm_eventgrid_system_topic_event_subscription" "fn_subscription" {
  name                = "egsub-${var.project_name}-${var.environment}"
  system_topic        = azurerm_eventgrid_system_topic.storage_topic.name
  resource_group_name = azurerm_resource_group.ai_rg.name

  webhook_endpoint {
    url = "https://${azurerm_linux_function_app.ingestor_fn.default_hostname}/runtime/webhooks/EventGrid?functionName=doc_ingestor_trigger&code=${azurerm_linux_function_app.ingestor_fn.site_credential[0].password}"
  }

  included_event_types = ["Microsoft.Storage.BlobCreated"]
  
  advanced_filter {
    string_begins_with {
      key    = "subject"
      values = ["/blobServices/default/containers/documents/"]
    }
  }
}
