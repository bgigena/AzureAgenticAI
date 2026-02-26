# --- RED VIRTUAL Y PRIVATE ENDPOINTS ---

resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-${var.project_name}-${var.environment}"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.ai_rg.location
  resource_group_name = azurerm_resource_group.ai_rg.name
}

resource "azurerm_subnet" "endpoints_subnet" {
  name                 = "snet-endpoints"
  resource_group_name  = azurerm_resource_group.ai_rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_subnet" "function_subnet" {
  name                 = "snet-function"
  resource_group_name  = azurerm_resource_group.ai_rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.2.0/24"]
  delegation {
    name = "delegation"
    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

# 1. Private Endpoint para OpenAI
resource "azurerm_private_endpoint" "pe_openai" {
  name                = "pe-openai-${var.project_name}"
  location            = azurerm_resource_group.ai_rg.location
  resource_group_name = azurerm_resource_group.ai_rg.name
  subnet_id           = azurerm_subnet.endpoints_subnet.id

  private_service_connection {
    name                           = "psc-openai"
    private_connection_resource_id = azurerm_cognitive_account.openai.id
    is_manual_connection           = false
    subresource_names              = ["account"]
  }
}

resource "azurerm_private_dns_zone" "dns_openai" {
  name                = "privatelink.openai.azure.com"
  resource_group_name = azurerm_resource_group.ai_rg.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "link_openai" {
  name                  = "link-openai"
  resource_group_name   = azurerm_resource_group.ai_rg.name
  private_dns_zone_name = azurerm_private_dns_zone.dns_openai.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
}

# 2. Private Endpoint para AI Search
resource "azurerm_private_endpoint" "pe_search" {
  name                = "pe-search-${var.project_name}"
  location            = azurerm_resource_group.ai_rg.location
  resource_group_name = azurerm_resource_group.ai_rg.name
  subnet_id           = azurerm_subnet.endpoints_subnet.id

  private_service_connection {
    name                           = "psc-search"
    private_connection_resource_id = azurerm_search_service.vector_db.id
    is_manual_connection           = false
    subresource_names              = ["searchService"]
  }
}

resource "azurerm_private_dns_zone" "dns_search" {
  name                = "privatelink.search.windows.net"
  resource_group_name = azurerm_resource_group.ai_rg.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "link_search" {
  name                  = "link-search"
  resource_group_name   = azurerm_resource_group.ai_rg.name
  private_dns_zone_name = azurerm_private_dns_zone.dns_search.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
}

# 3. Private Endpoint para Storage (Blob)
resource "azurerm_private_endpoint" "pe_storage" {
  name                = "pe-storage-${var.project_name}"
  location            = azurerm_resource_group.ai_rg.location
  resource_group_name = azurerm_resource_group.ai_rg.name
  subnet_id           = azurerm_subnet.endpoints_subnet.id

  private_service_connection {
    name                           = "psc-storage"
    private_connection_resource_id = azurerm_storage_account.ai_storage.id
    is_manual_connection           = false
    subresource_names              = ["blob"]
  }
}

resource "azurerm_private_dns_zone" "dns_storage" {
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = azurerm_resource_group.ai_rg.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "link_storage" {
  name                  = "link-storage"
  resource_group_name   = azurerm_resource_group.ai_rg.name
  private_dns_zone_name = azurerm_private_dns_zone.dns_storage.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
}
