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
### 2. Ingestar Documentos (RAG)

#### En Cloud

Subí un PDF a tu Blob Storage (`documents`). El Event Grid disparará automáticamente tu Azure Function (`doc_ingestor_trigger`) y extraerá texto, generará embeddings, y los mandará a Azure AI Search.

#### En el entorno Local (Docker + Azurite + Qdrant)

Azurite no dispara eventos automáticamente. Por eso incluimos un script para facilitar la carga.
Abrí tu terminal y ejecutá:

```powershell
# Ejemplo: Subir un documento txt o pdf al entorno local
pip install azure-storage-blob
python ingestar_local.py ruta/a/tu/archivo.txt
```

Esto va a:
1. Subir el archivo al Storage local (Azurite).
2. Mandar el aviso a tu contenedor (por Puerto 8080) simulando el evento de la nube.
3. El contenedor fragmentará el texto y usará Ollama para generar los vectores.

**¿Dónde veo mis documentos guardados?**
- **Archivo Original:** Descargá Microsoft Azure Storage Explorer, conectate a "Emulator" y buscá el contenedor `documents`.
- **Vectores y Chunks:** Entrá a [http://localhost:6333/dashboard](http://localhost:6333/dashboard) en tu navegador para ver la base de datos vectorial Qdrant gráficamente.

## 💻 Desarrollo Local Completo (Docker + Ollama)

Para reducir costos de desarrollo, facilitar el testing o desplegar la solución en una computadora nueva de forma 100% local, el sistema soporta un entorno offline contenedorizado.

**Componentes locales:**
- **Almacenamiento:** Azurite (Emulador de Azure Blob Storage).
- **Vector DB:** Qdrant (Base de datos vectorial Open Source).
- **LLM y Embeddings:** Ollama (Modelos ejecutándose en CPU/GPU local).

### Pasos para Desplegar en una Computadora Nueva

#### 1. Instalar Pre-Requisitos
1. Instalá **Docker Desktop** (Asegurate de que esté corriendo).
2. Instalá **Ollama** desde [ollama.com](https://ollama.com/)
3. Instalá **Python 3.11+**

#### 2. Descargar Modelos de IA
Abrí una terminal (PowerShell o CMD) y ejecutá estos comandos para descargar los modelos que usa el agente localmente:
```powershell
ollama pull llama3
ollama pull nomic-embed-text
```
*(Nota: El comando `ollama serve` no suele ser necesario en Windows ya que Ollama correo como un servicio en segundo plano automáticamente).*

#### 3. Iniciar la Infraestructura
En la raíz del proyecto (donde está el archivo `docker-compose.yml`), ejecutá:
```powershell
docker-compose up -d --build
```
Esto levantará 4 contenedores: la UI, la función de ingesta, la base de datos Qdrant y el emulador Azurite. Podés verificar que todos estén verdes en Docker Desktop.

#### 4. Probar la UI
Ingresá a [http://localhost:8501](http://localhost:8501). Vas a ver la interfaz del agente. Asegurate de que en el panel lateral esté seleccionado "Local" y "Qdrant". 

#### 5. Ingestar tu Primer Documento
Por defecto la base de datos está vacía. Para que el agente pueda responder preguntas, necesitás cargarle conocimiento.

1. Abrí tu terminal en la carpeta del proyecto.
2. Instalá el SDK de Azure (solo la primera vez):
   ```powershell
   pip install azure-storage-blob
   ```
3. Ejecutá el script de ingesta apuntando a cualquier archivo `.txt` que tengas:
   ```powershell
   python ingestar_local.py ruta/a/tu/archivo.txt
   ```
   *El script subirá el archivo a tu storage local y simulará el evento en la nube para despertar al contenedor ingestor, el cual calculará los vectores vía Ollama usando tu CPU y los guardará en Qdrant.*

#### 6. Observar los Datos
- **Los vectores:** Podés ver tu base de datos y cómo se partió el texto entrando a [http://localhost:6333/dashboard](http://localhost:6333/dashboard) en tu navegador e ingresando a la colección `documents`.
- **Los archivos originales:** Descargá *Microsoft Azure Storage Explorer*, conectate al "Local Emulator" y vas a ver un contenedor `documents` con tus `.txt` originales.