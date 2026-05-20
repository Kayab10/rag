# routes_health.py - Health check endpoint.
# Used to verify the API is running and the vector store is reachable.

from fastapi import APIRouter
from app.core.vector_store import get_collection_info

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    """
    Returns API status and current vector store chunk count.
    Use this to confirm the server is running before making other calls.
    """
    info = get_collection_info()
    return {
        "status":       "ok",
        "collection":   info["collection_name"],
        "total_chunks": info["total_chunks"],
    }
