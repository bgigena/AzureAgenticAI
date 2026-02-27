import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# Detección de entorno
# ─────────────────────────────────────────────
RUNNING_ENV = os.getenv("RUNNING_ENV", "cloud").lower()
IS_LOCAL = RUNNING_ENV == "local"

# ─────────────────────────────────────────────
# Configuración de clientes (lazy, sólo al usar)
# ─────────────────────────────────────────────

def get_openai_client():
    """Devuelve el cliente OpenAI correcto según entorno."""
    from openai import AzureOpenAI, OpenAI

    if IS_LOCAL:
        # Apunta a un endpoint local compatible con OpenAI (Ollama, LiteLLM, etc.)
        # Si no está definido, usa la API pública de OpenAI con la key que haya.
        base_url = os.getenv("LOCAL_OPENAI_BASE_URL", "http://host.docker.internal:11434/v1")
        api_key  = os.getenv("LOCAL_OPENAI_API_KEY", "ollama")
        return OpenAI(base_url=base_url, api_key=api_key)
    else:
        return AzureOpenAI(
            api_key      = os.environ["AZURE_OPENAI_KEY"],
            api_version  = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"],
        )


def get_embedding(client, text: str, model: str) -> list[float]:
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding


def search_qdrant(query_vector: list[float], collection: str, top_k: int):
    from qdrant_client import QdrantClient

    host = os.getenv("QDRANT_HOST", "vector-db")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant = QdrantClient(host=host, port=port)

    # In newer qdrant-client versions, use query_points instead of search
    try:
        results = qdrant.query_points(
            collection_name=collection,
            query=query_vector,
            limit=top_k,
        ).points
    except Exception as e:
        print(f"Warning: Qdrant search failed (Collection might not exist): {e}")
        return []
        
    return [
        {"content": r.payload.get("content", ""), "source": r.payload.get("source", "—"), "score": r.score}
        for r in results
    ]


def search_azure(query_vector: list[float], top_k: int):
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential

    client = SearchClient(
        endpoint   = os.environ["AZURE_SEARCH_ENDPOINT"],
        index_name = os.environ["AZURE_SEARCH_INDEX_NAME"],
        credential = AzureKeyCredential(os.environ["AZURE_SEARCH_KEY"]),
    )
    results = client.search(
        search_text=None,
        vector_queries=[{
            "kind": "vector",
            "vector": query_vector,
            "fields": "contentVector",
            "k": top_k,
        }],
    )
    return [
        {"content": r.get("content", ""), "source": r.get("source_file", "—"), "score": r.get("@search.score", 0)}
        for r in results
    ]


def do_search(query_vector: list[float], vector_store: str, top_k: int, collection: str):
    if vector_store == "Qdrant (local)":
        return search_qdrant(query_vector, collection, top_k)
    else:
        return search_azure(query_vector, top_k)


def build_prompt(question: str, context_chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[Fuente: {c['source']}]\n{c['content']}" for c in context_chunks
    )
    return (
        "Sos un asistente experto. Respondé en el mismo idioma que la pregunta.\n"
        "Usá únicamente la información del contexto para responder. "
        "Si la respuesta no está en el contexto, decilo claramente.\n\n"
        f"### Contexto:\n{context}\n\n"
        f"### Pregunta:\n{question}"
    )


def stream_answer(client, prompt: str, chat_model: str, temperature: float):
    stream = client.chat.completions.create(
        model=chat_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="RAG Agent",
    page_icon="🤖",
    layout="wide",
)

# ── Estilos ──────────────────────────────────
st.markdown("""
<style>
  [data-testid="stSidebar"] { background: #0f1117; }
  .source-chip {
    display: inline-block;
    background: #1e2130;
    border: 1px solid #2e3250;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.75rem;
    color: #a0aec0;
    margin: 2px;
  }
  .env-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 8px;
  }
  .local  { background:#1a3a2a; color:#4caf50; border:1px solid #4caf50; }
  .cloud  { background:#1a2a3a; color:#2196f3; border:1px solid #2196f3; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuración")

    env_label = "local" if IS_LOCAL else "cloud"
    env_class = "local" if IS_LOCAL else "cloud"
    st.markdown(
        f'<span class="env-badge {env_class}">{"🟢 Local" if IS_LOCAL else "☁️ Cloud (Azure)"}</span>',
        unsafe_allow_html=True,
    )

    st.divider()

    # Vector Store
    vector_store_options = ["Qdrant (local)", "Azure AI Search"]
    default_vs = 0 if IS_LOCAL else 1
    vector_store = st.selectbox("🗄️ Vector Store", vector_store_options, index=default_vs)

    qdrant_collection = ""
    if vector_store == "Qdrant (local)":
        qdrant_collection = st.text_input("Colección Qdrant", value=os.getenv("QDRANT_COLLECTION", "documents"))

    top_k = st.slider("📄 Chunks a recuperar (top-k)", 1, 10, 4)

    st.divider()

    # Modelos
    default_embed = (
        os.getenv("LOCAL_EMBEDDING_MODEL", "nomic-embed-text")
        if IS_LOCAL
        else os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-3-small")
    )
    default_chat = (
        os.getenv("LOCAL_CHAT_MODEL", "llama3")
        if IS_LOCAL
        else os.getenv("AZURE_CHAT_MODEL", "gpt-4o")
    )

    embed_model = st.text_input("🔢 Modelo de embeddings", value=default_embed)
    chat_model  = st.text_input("💬 Modelo de chat", value=default_chat)
    temperature = st.slider("🌡️ Temperatura", 0.0, 1.0, 0.3, 0.05)

    st.divider()
    if st.button("🗑️ Limpiar historial"):
        st.session_state.messages = []
        st.rerun()

# ── Header ───────────────────────────────────
st.markdown("# 🤖 RAG Agent")
st.caption(
    f"**Entorno:** `{RUNNING_ENV}` · "
    f"**Vector store:** `{vector_store}` · "
    f"**Chat model:** `{chat_model}`"
)
st.divider()

# ── Estado ───────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Historial ────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            st.markdown(
                " ".join(f'<span class="source-chip">📄 {s}</span>' for s in msg["sources"]),
                unsafe_allow_html=True,
            )

# ── Input ────────────────────────────────────
if question := st.chat_input("Hacé tu pregunta…"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        status = st.status("Pensando…", expanded=False)

        try:
            oai_client = get_openai_client()

            # 1. Embedding de la pregunta
            status.update(label="🔢 Generando embedding…")
            query_vector = get_embedding(oai_client, question, embed_model)

            # 2. Búsqueda en vector store
            status.update(label=f"🔍 Buscando en {vector_store}…")
            chunks = do_search(query_vector, vector_store, top_k, qdrant_collection)

            if not chunks:
                st.warning("No encontré contexto relevante para tu pregunta.")
                st.stop()

            # 3. Construir prompt
            prompt = build_prompt(question, chunks)

            # 4. Completions en stream
            status.update(label="✍️ Generando respuesta…")
            answer_placeholder = st.empty()
            full_answer = ""
            for token in stream_answer(oai_client, prompt, chat_model, temperature):
                full_answer += token
                answer_placeholder.markdown(full_answer + "▌")
            answer_placeholder.markdown(full_answer)

            # 5. Fuentes
            sources = list({c["source"] for c in chunks})
            st.markdown(
                " ".join(f'<span class="source-chip">📄 {s}</span>' for s in sources),
                unsafe_allow_html=True,
            )
            status.update(label="✅ Listo", state="complete", expanded=False)

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_answer,
                "sources": sources,
            })

        except Exception as e:
            status.update(label="❌ Error", state="error")
            st.error(f"**Error:** {e}")
