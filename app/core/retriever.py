# retriever.py - Retrieves the most relevant chunks for a user question.
#
# Pipeline:
#   User question
#       ↓
#   Convert question to embedding   (embeddings.embed_query)
#       ↓
#   Search vector DB                (vector_store.search)
#       ↓
#   Return top K chunks             (ranked by cosine similarity score)

from app.config import get_settings
from app.core.vector_store import search

_settings = get_settings()


def retrieve(query: str, top_k: int | None = None) -> list[dict]:
    """
    Find the most relevant document chunks for a given user question.

    Parameters
    ----------
    query : str
        The user's question, e.g. "What is RAG?"
    top_k : int | None
        How many chunks to return. Defaults to config TOP_K_RESULTS (4).

    Returns
    -------
    list[dict]
        Ranked list of the most relevant chunks:
        [
            {
                "text":     "RAG stands for Retrieval-Augmented Generation...",
                "metadata": {"file_name": "rag_notes.pdf", "page_number": 1},
                "score":    0.91
            },
            ...
        ]
        Sorted by score descending (most relevant first).
    """
    top_k = top_k or _settings.TOP_K_RESULTS

    results = search(query=query, top_k=top_k)

    # search() already returns results sorted by ChromaDB (most similar first),
    # but we sort explicitly here to make the contract clear and safe.
    results.sort(key=lambda r: r["score"], reverse=True)

    return results


def retrieve_texts(query: str, top_k: int | None = None) -> list[str]:
    """
    Convenience wrapper — returns only the text strings, no metadata or scores.

    Useful when you just need the raw context to pass into a prompt.

    Parameters
    ----------
    query : str
        The user's question.
    top_k : int | None
        How many chunks to return.

    Returns
    -------
    list[str]
        The text content of the top K chunks, most relevant first.
    """
    return [r["text"] for r in retrieve(query, top_k)]
