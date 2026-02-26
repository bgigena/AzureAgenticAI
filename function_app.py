import azure.functions as func
import logging
import os
import json
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient
from openai import AzureOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tenacity import retry, wait_random_exponential, stop_after_attempt
from azure.monitor.opentelemetry import configure_azure_monitor

# Configurar OpenTelemetry para Application Insights
configure_azure_monitor(
    connection_string=os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
)

app = func.FunctionApp()

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def get_embeddings_with_retry(client: AzureOpenAI, text: str):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def upload_docs_with_retry(client: SearchClient, docs: list):
    client.upload_documents(documents=docs)

@app.event_grid_trigger(arg_name="event")
def doc_ingestor_trigger(event: func.EventGridEvent):
    event_data = event.get_json()
    blob_url = event_data['url']
    logging.info(f"Procesando evento de Event Grid para archivo: {blob_url}")
    
    # Extraer nombre del contenedor y blob de la URL
    # URL format: https://<account>.blob.core.windows.net/<container>/<blob>
    blob_url_parts = blob_url.split('/')
    container_name = blob_url_parts[-2]
    blob_name = "/".join(blob_url_parts[-1:])
    
    # 0. Descargar contenido del Blob
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    content = blob_client.download_blob().readall().decode('utf-8')
    
    # 1. Chunking avanzado con solapamiento
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.create_documents([content])
    logging.info(f"Documento dividido en {len(chunks)} chunks.")
    
    # 2. Azure OpenAI Client para Embeddings
    openai_client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_KEY"],
        api_version="2024-02-01",
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
    )
    
    search_client = SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        index_name=os.environ["AZURE_SEARCH_INDEX_NAME"],
        credential=AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
    )
    
    docs_to_upload = []
    for i, chunk in enumerate(chunks):
        # 3. Generar Embeddings (con reintentos)
        embedding = get_embeddings_with_retry(openai_client, chunk.page_content)
        
        # 4. Preparar documento para AI Search
        docs_to_upload.append({
            "id": f"{blob_name.replace('.','_')}_{i}", # IDs deben ser seguros para URL
            "content": chunk.page_content,
            "contentVector": embedding,
            "source_file": blob_name,
            "category": "automatic-ingest"
        })
    
    # Subir lote a Azure AI Search (con reintentos)
    if docs_to_upload:
        upload_docs_with_retry(search_client, docs_to_upload)
        logging.info(f"Indexados {len(docs_to_upload)} chunks de {blob_name} correctamente.")