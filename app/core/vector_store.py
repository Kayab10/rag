# vector_store.py - Stores and searches vector embeddings using ChromaDB.
#
# ChromaDB is a local, file-based vector database — no server needed.
# All data is persisted to VECTOR_DB_PATH (configured in config.py / .env).
#
# Stored item shape:
#   {
#       "id":        "chunk_001",
#       "text":      "RAG stands for Retrieval-Augmented Generation...",
#       "embedding": [0.12, 0.44, -0.21, ...],
#       "metadata":  {"file_name": "rag_notes.pdf", "page_number": 1, ...}
#   }

import uuid
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from app.core.document_loader import Document
from app.core.embeddings import embed_batch, embed_query

# ── Constants ─────────────────────────────────────────────────────────────────
COLLECTION_NAME = "rag_documents"

# ── ChromaDB client (module-level singleton) ──────────────────────────────────
_settings = get_settings()

_client = chromadb.PersistentClient(
    path=_settings.VECTOR_DB_PATH,
    settings=ChromaSettings(anonymized_telemetry=False),
)


# ── Internal helper ───────────────────────────────────────────────────────────

def _get_collection() -> chromadb.Collection:
    """Return the collection, creating it if it doesn't exist yet."""
    return _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine similarity for text search
    )


# ── Public API ────────────────────────────────────────────────────────────────

def add_documents(documents: list[Document]) -> int:
    """
    Embed and store a list of document chunks in ChromaDB.

    Each chunk gets a unique ID (UUID4). If a chunk with the same ID already
    exists it will be skipped — use reset_collection() first for a full reload.

    Parameters
    ----------
    documents : list[Document]
        Output of text_splitter.split_documents().

    Returns
    -------
    int
        Number of chunks successfully added.
    """
    if not documents:
        return 0

    collection = _get_collection()

    texts     = [doc["text"]     for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]
    ids       = [str(uuid.uuid4()) for _ in documents]

    # Embed all chunks in one pass
    embeddings = embed_batch(texts)

    collection.add(
        ids=ids,
        documents=texts,       # ChromaDB stores the raw text alongside the vector
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(ids)


def search(query: str, top_k: int | None = None) -> list[dict]:
    """
    Find the most similar chunks to *query* using cosine similarity.

    Parameters
    ----------
    query : str
        The user's question or search string.
    top_k : int | None
        Number of results to return. Defaults to config TOP_K_RESULTS.

    Returns
    -------
    list[dict]
        Ranked list of results, each containing:
        {
            "text":     "...",
            "metadata": {"file_name": "...", "page_number": N, ...},
            "score":    0.87        # cosine similarity, higher = more relevant
        }
    """
    top_k = top_k or _settings.TOP_K_RESULTS
    collection = _get_collection()

    # Guard: can't query an empty collection
    if collection.count() == 0:
        return []

    query_vector = embed_query(query)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection.count()),  # can't ask for more than exists
        include=["documents", "metadatas", "distances"],
    )

    # Unpack ChromaDB's nested response format into a clean flat list
    output = []
    for text, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append(
            {
                "text":     text,
                "metadata": metadata,
                "score":    round(1 - distance, 4),  # convert distance → similarity
            }
        )

    return output


def get_collection_info() -> dict:
    """
    Return basic stats about the current collection.

    Returns
    -------
    dict
        {"collection_name": "...", "total_chunks": N}
    """
    collection = _get_collection()
    return {
        "collection_name": collection.name,
        "total_chunks":    collection.count(),
    }


def reset_collection() -> None:
    """
    Delete and recreate the collection, removing all stored chunks.

    Use this when re-ingesting documents from scratch.
    Safe to call even if the collection doesn't exist yet.
    """
    existing = [c.name for c in _client.list_collections()]
    if COLLECTION_NAME in existing:
        _client.delete_collection(name=COLLECTION_NAME)
    _get_collection()   # recreates it immediately
