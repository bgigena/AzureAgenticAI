# 📘 Documentación Técnica: Ecosistema de Ingesta de IA Automatizada

Esta solución implementa una arquitectura **Event-Driven** para la gestión de conocimiento en Agentes de IA, utilizando un enfoque de **Infraestructura como Código (IaC)** y servicios **Serverless**.

## 🏗️ Arquitectura del Sistema

El sistema se divide en tres capas principales:

1.  **Capa de Infraestructura (Azure Resource Manager via Terraform):**
    - Despliegue de servicios de IA (Azure OpenAI + AI Search).
    - Configuración de redes y almacenamiento seguro.
2.  **Capa de Ingesta (Azure Functions - Python):**
    - Trigger automático ante la subida de blobs.
    - Lógica de procesamiento: Chunking, Embedding e Indexación Vectorial.
3.  **Capa de Automatización (GitHub Actions):**
    - Pipeline de CI/CD que valida y aplica cambios en la infraestructura y despliega el código de la función.



## 🛠️ Flujo de Trabajo (Workflow)

1. **Despliegue Inicial:** Se ejecuta la pipeline de GitHub Actions para crear los recursos.
2. **Carga de Datos:** El usuario final sube documentos (PDF, TXT, DOCX) al container `documents` en Azure Blob Storage.
3. **Procesamiento Automático:** - La **Azure Function** detecta el evento `BlobCreated`.
   - El script fragmenta el texto y genera vectores de alta dimensionalidad usando el modelo `text-embedding-ada-002`.
   - Los vectores se almacenan en el índice de **Azure AI Search**.
4. **Consulta:** El Agente de IA (Web App o Bot) ya tiene acceso inmediato a la nueva información para responder consultas basadas en RAG (*Retrieval-Augmented Generation*).

## 🔒 Seguridad y Gobernanza

- **Identidades Gestionadas:** Los servicios se comunican entre sí sin necesidad de almacenar Connection Strings en el código (vía Azure RBAC).
- **Aislamiento Serverless:** La lógica de procesamiento de documentos corre en un sandbox aislado (Azure Functions), protegiendo la infraestructura principal.
- **Monitoreo:** Cada ejecución de la función y cada llamada a la API de IA es registrada en **Application Insights** para auditoría y control de costos.

---

## 🚀 Guía de Operación para el Cliente

### ¿Cómo actualizar el conocimiento del Agente?
Simplemente suba los nuevos archivos a la carpeta `documents` del Storage Account. El sistema los procesará en un tiempo promedio de <10 segundos por documento.

### ¿Cómo monitorear costos?
Acceda al Dashboard de **Log Analytics** creado por la pipeline para visualizar el consumo de tokens y ejecuciones de la función.