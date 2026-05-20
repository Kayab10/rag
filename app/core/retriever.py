from app.config import get_settings
from app.core.vector_store import search

_settings = get_settings()


def retrieve(query: str, user_id: str, top_k: int | None = None) -> list[dict]:
    top_k   = top_k or _settings.TOP_K_RESULTS
    results = search(query=query, user_id=user_id, top_k=top_k)
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def retrieve_texts(query: str, user_id: str, top_k: int | None = None) -> list[str]:
    return [r["text"] for r in retrieve(query, user_id, top_k)]
