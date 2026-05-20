import google.generativeai as genai
from app.config import get_settings

_settings = get_settings()
genai.configure(api_key=_settings.GOOGLE_API_KEY)

BATCH_SIZE = 100  # Gemini supports up to 100 texts per batch call


def embed_text(text: str) -> list[float]:
    text = text.strip()
    if not text:
        raise ValueError("Cannot embed empty text.")
    response = genai.embed_content(
        model=_settings.EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_document",
    )
    return response["embedding"]


def embed_query(text: str) -> list[float]:
    text = text.strip()
    if not text:
        raise ValueError("Cannot embed empty query.")
    response = genai.embed_content(
        model=_settings.EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_query",
    )
    return response["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed texts in batches of up to 100 using Gemini's batch_embed_contents.
    Much faster than one API call per chunk.
    """
    if not texts:
        return []

    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        result = genai.embed_content(
            model=_settings.EMBEDDING_MODEL,
            content=batch,
            task_type="retrieval_document",
        )
        # When content is a list, response["embedding"] is a list of vectors
        embeddings = result["embedding"]
        all_embeddings.extend(embeddings)

    return all_embeddings
