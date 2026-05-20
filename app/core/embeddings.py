# embeddings.py - Converts text into vector representations using Google Gemini.
#
# What is an embedding?
#   A list of floats that captures the *meaning* of a piece of text.
#   "RAG combines retrieval and generation"  →  [0.021, -0.193, 0.442, ...]
#   Texts with similar meaning end up with vectors that are close together,
#   which is what makes similarity search possible.
#
# Model used: models/text-embedding-004  (configured in config.py / .env)

import google.generativeai as genai

from app.config import get_settings

# ── Module-level setup ────────────────────────────────────────────────────────
# Configure the SDK once when this module is first imported.
_settings = get_settings()
genai.configure(api_key=_settings.GOOGLE_API_KEY)


# ── Public API ────────────────────────────────────────────────────────────────

def embed_text(text: str) -> list[float]:
    """
    Convert a single string into an embedding vector.

    Parameters
    ----------
    text : str
        The text to embed (a chunk, a query, etc.)

    Returns
    -------
    list[float]
        The embedding vector, e.g. [0.021, -0.193, 0.442, ...]
    """
    text = text.strip()
    if not text:
        raise ValueError("Cannot embed empty text.")

    response = genai.embed_content(
        model=_settings.EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_document",   # optimises the vector for document storage
    )

    return response["embedding"]


def embed_query(text: str) -> list[float]:
    """
    Convert a user query into an embedding vector.

    Identical to embed_text but uses task_type="retrieval_query", which tells
    the model this vector will be used to *search* rather than *store*.
    Gemini embedding models produce slightly better results when they know
    the intended use.

    Parameters
    ----------
    text : str
        The user's question or search query.

    Returns
    -------
    list[float]
        The query embedding vector.
    """
    text = text.strip()
    if not text:
        raise ValueError("Cannot embed empty query.")

    response = genai.embed_content(
        model=_settings.EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_query",      # optimises the vector for querying
    )

    return response["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts one by one and return all vectors.

    Google's embed_content API does not support true batch requests in the
    same way as some other providers, so we loop and collect results.
    Each text is embedded as a retrieval_document.

    Parameters
    ----------
    texts : list[str]
        List of text chunks to embed (e.g. output of text_splitter).

    Returns
    -------
    list[list[float]]
        One vector per input text, in the same order.
    """
    if not texts:
        return []

    return [embed_text(t) for t in texts]
