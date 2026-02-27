import azure.functions as func
import logging
import os
import uuid
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient
from openai import AzureOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tenacity import retry, wait_random_exponential, stop_after_attempt
from azure.monitor.opentelemetry import configure_azure_monitor

# Configurar monitoreo solo si estamos en Cloud
if os.getenv("RUNNING_ENV") == "cloud":
    configure_azure_monitor(connection_string=os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"))

app = func.FunctionApp()

# --- LÓGICA DE REINTENTOS MANTENIDA ---
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def get_embeddings(text: str):
    env = os.getenv("RUNNING_ENV", "local")
    
    if env == "cloud":
        client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_KEY"],
            api_version="2024-02-01",
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
        )
        response = client.embeddings.create(input=text, model="text-embedding-3-small")
        return response.data[0].embedding
    else:
        from openai import OpenAI
        # Llama al Ollama local usando host.docker.internal
        base_url = os.getenv("LOCAL_OPENAI_BASE_URL", "http://host.docker.internal:11434/v1")
        client = OpenAI(base_url=base_url, api_key="ollama")
        response = client.embeddings.create(input=text, model="nomic-embed-text")
        return response.data[0].embedding

@app.event_grid_trigger(arg_name="event")
def doc_ingestor_trigger(event: func.EventGridEvent):
    logging.info("DEBUG: EventGrid trigger fired")
    _process_event(event.get_json())

@app.function_name(name="manual_ingestor")
@app.route(route="ingest", methods=['POST'], auth_level=func.AuthLevel.ANONYMOUS)
def manual_ingestor(req: func.HttpRequest) -> func.HttpResponse:
    print("DEBUG: HTTP trigger 'manual_ingestor' called", flush=True)
    if os.getenv("RUNNING_ENV") != "local":
        return func.HttpResponse("Manual ingestion only allowed in local mode", status_code=403)
    try:
        body = req.get_json()
        print(f"DEBUG: Received body: {body}", flush=True)
        _process_event(body)
        return func.HttpResponse("Ingestion started", status_code=200)
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        print(f"DEBUG: ERROR in manual_ingestor: {err}", flush=True)
        return func.HttpResponse(f"Error: {e}", status_code=500)

def _process_event(event_data):
    print(f"DEBUG: Entering _process_event with {event_data}", flush=True)
    env = os.getenv("RUNNING_ENV", "local")
    blob_url = event_data['url']
    print(f"DEBUG: Blob URL: {blob_url}", flush=True)
    
    # 0. Descarga agnóstica al entorno
    # Azurite (local) usa el mismo SDK que Azure Storage
    print("DEBUG: Connecting to Storage...", flush=True)
    storage_conn = os.environ["AzureWebJobsStorage"]
    if env == "local":
        blob_service_client = BlobServiceClient.from_connection_string(storage_conn, api_version='2023-11-03')
    else:
        blob_service_client = BlobServiceClient.from_connection_string(storage_conn)
    
    # Parsing de URL simplificado
    blob_name = blob_url.split('/')[-1]
    container_name = blob_url.split('/')[-2]
    
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    raw_content = blob_client.download_blob().readall()
    
    if blob_name.lower().endswith('.pdf'):
        import io
        from PyPDF2 import PdfReader
        pdf_reader = PdfReader(io.BytesIO(raw_content))
        content = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                content += extracted + "\n"
    else:
        content = raw_content.decode('utf-8')

    # 1. Tu lógica de Chunking avanzada (Mantenida)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.create_documents([content])
    
    print(f"DEBUG: Starting ingestion loop for {len(chunks)} chunks", flush=True)
    docs_to_upload = []
    for i, chunk in enumerate(chunks):
        print(f"DEBUG: Processing chunk {i+1}/{len(chunks)}...", flush=True)
        embedding = get_embeddings(chunk.page_content)
        
        docs_to_upload.append({
            "id": f"{str(uuid.uuid4())}", # UUID es más seguro para ambos sistemas
            "content": chunk.page_content,
            "contentVector": embedding,
            "metadata": {"source": blob_name, "chunk": i}
        })

    # 2. Upload condicional según entorno
    if env == "cloud":
        search_client = SearchClient(
            endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
            index_name=os.environ["AZURE_SEARCH_INDEX_NAME"],
            credential=AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"])
        )
        search_client.upload_documents(documents=docs_to_upload)
    else:
        # Lógica para Qdrant (Docker Local)
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct
        
        q_client = QdrantClient(host="vector-db", port=6333)
        points = [
            PointStruct(id=str(uuid.uuid4()), vector=d["contentVector"], payload=d) 
            for d in docs_to_upload
        ]
        collection_name = os.getenv("QDRANT_COLLECTION", "documents")
        q_client.upsert(collection_name=collection_name, points=points)

    logging.info(f"Ingesta completada en {env} para {blob_name}")