import os
import sys
import urllib.request
import json
from azure.storage.blob import BlobServiceClient

def main():
    if len(sys.argv) < 2:
        print("Uso: python ingestar_local.py <ruta_al_archivo>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: El archivo '{file_path}' no existe.")
        sys.exit(1)

    blob_name = os.path.basename(file_path)
    container_name = "documents"
    
    # 1. Leer el contenido (en modo binario para soportar PDFs)
    with open(file_path, 'rb') as f:
        content = f.read()

    # 2. Subir a Azurite
    conn_str = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://localhost:10000/devstoreaccount1;"
    print("Conectando a Azurite local (API Version: 2023-11-03)...")
    # Forzamos una versión de API compatible con Azurite
    blob_service_client = BlobServiceClient.from_connection_string(conn_str, api_version='2023-11-03')
    
    try:
        blob_service_client.create_container(container_name)
    except Exception:
        pass # Ignorar si ya existe
        
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(content, overwrite=True)
    print(f"✅ Archivo '{blob_name}' subido a Azurite (contenedor: '{container_name}').")

    # 3. Disparar el Trigger Local vía HTTP Bypass
    print("Avisando al contenedor Ingestor para que lo procese (vía /api/ingest)...")
    function_url = "http://localhost:8080/api/ingest"
    
    payload = {
        "url": f"http://azurite:10000/devstoreaccount1/{container_name}/{blob_name}"
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(function_url, data=json.dumps(payload).encode(), headers=headers)
    try:
        urllib.request.urlopen(req)
        print("✅ Ingesta iniciada. El agente lo está fragmentando y enviando a Qdrant en segundo plano.")
        print("   (Podés ver el progreso con: docker logs -f azure-ai-freelance-kit-ingestor-function-1)")
    except Exception as e:
        print(f"❌ Error disparando el trigger. Asegurate de que el contenedor ingestor-function esté corriendo.")
        print(f"Detalle del error: {e}")

if __name__ == "__main__":
    main()
