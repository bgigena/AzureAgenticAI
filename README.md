# 🚀 Azure AI Agent Infrastructure - Production Ready

Este repositorio contiene la **Arquitectura de Referencia (IaC)** para desplegar agentes de Inteligencia Artificial Generativa en Microsoft Azure, priorizando la seguridad de datos corporativos, la observabilidad de costos y el escalamiento empresarial.

## 🌟 Propuesta de Valor

A diferencia de los despliegues estándar, este kit de infraestructura implementa las mejores prácticas de **Cloud Adoption Framework (CAF)** y **Well-Architected Framework** para IA:

-   **Zero-Trust Security:** Eliminación de API Keys mediante el uso de **Managed Identities** y **RBAC** (Role-Based Access Control).
-   **Enterprise RAG Ready:** Despliegue automatizado de **Azure AI Search** para arquitecturas de Recuperación Aumentada por Generación.
-   **Observabilidad Total (LLMOps):** Integración con **Application Insights** y **Log Analytics** para monitorear latencia, consumo de tokens y trazas de ejecución.
-   **Cost Governance:** Configuración de cuotas (TPM - Tokens Per Minute) para evitar sorpresas en la facturación.

---

## 🏗️ Arquitectura Desplegada

El stack técnico incluye:
1.  **Azure OpenAI Service:** Instancia privada de modelos (GPT-4o / GPT-o1).
2.  **Azure AI Search:** Base de datos vectorial de alto rendimiento.
3.  **Azure Monitor & App Insights:** Telemetría avanzada para LLMs.
4.  **Identity:** Asignación automática de roles para el usuario/servicio que realiza el despliegue.

---

## 🛠️ Cómo Utilizar este Kit

### Requisitos Previos
-   [Terraform](https://www.terraform.io/downloads.html) >= 1.5.0
-   [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
-   Una suscripción activa de Azure con acceso a **Azure OpenAI Service**.

### Pasos para el Despliegue
1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/azure-ai-infrastructure.git](https://github.com/tu-usuario/azure-ai-infrastructure.git)
   cd azure-ai-infrastructure