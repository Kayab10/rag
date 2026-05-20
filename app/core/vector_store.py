from functools import lru_cache
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams,
    PointStruct,
)

from app.config import get_settings
from app.core.document_loader import Document
from app.core.embeddings import embed_batch, embed_query

_settings = get_settings()
VECTOR_SIZE = 3072  # gemini-embedding-001 output dimension


@lru_cache
def _get_client() -> QdrantClient:
    return QdrantClient(
        url=_settings.QDRANT_URL,
        api_key=_settings.QDRANT_API_KEY,
    )


def _collection_name(user_id: str) -> str:
    return f"user_{user_id.replace('-', '_')}"


def _ensure_collection(user_id: str) -> str:
    client = _get_client()
    name = _collection_name(user_id)
    existing = [c.name for c in client.get_collections().collections]
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    return name


def add_documents(documents: list[Document], user_id: str) -> int:
    if not documents:
        return 0

    client = _get_client()
    name = _ensure_collection(user_id)

    texts      = [doc["text"]     for doc in documents]
    metadatas  = [doc["metadata"] for doc in documents]
    embeddings = embed_batch(texts)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"text": text, **metadata},
        )
        for text, metadata, embedding in zip(texts, metadatas, embeddings)
    ]

    client.upsert(collection_name=name, points=points)
    return len(points)


def search(query: str, user_id: str, top_k: int | None = None) -> list[dict]:
    top_k  = top_k or _settings.TOP_K_RESULTS
    client = _get_client()
    name   = _ensure_collection(user_id)

    count = client.count(collection_name=name).count
    if count == 0:
        return []

    query_vector = embed_query(query)
    results = client.query_points(
        collection_name=name,
        query=query_vector,
        limit=min(top_k, count),
        with_payload=True,
    ).points

    output = []
    for hit in results:
        payload = dict(hit.payload or {})
        text = payload.pop("text", "")
        output.append({
            "text":     text,
            "metadata": payload,
            "score":    round(hit.score, 4),
        })

    return output


def get_collection_info(user_id: str) -> dict:
    client = _get_client()
    name   = _ensure_collection(user_id)
    count  = client.count(collection_name=name).count
    return {"collection_name": name, "total_chunks": count}


def reset_collection(user_id: str) -> None:
    client = _get_client()
    name   = _collection_name(user_id)
    existing = [c.name for c in client.get_collections().collections]
    if name in existing:
        client.delete_collection(collection_name=name)
    _ensure_collection(user_id)
