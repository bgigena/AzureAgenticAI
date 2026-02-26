output "openai_endpoint" {
  value = azurerm_cognitive_account.openai.endpoint
}

output "search_service_name" {
  value = azurerm_search_service.vector_db.name
}

output "app_insights_key" {
  value     = azurerm_application_insights.ai_app_insights.instrumentation_key
  sensitive = true
}

output "resource_group_name" {
  value = azurerm_resource_group.ai_rg.name
}