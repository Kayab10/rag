# chat_service.py - Business logic for chat operations.
#
# Flow:
#   receive question
#       ↓
#   run RAG pipeline        (rag_pipeline.run)
#       ↓
#   return answer + sources
#
# This keeps the API route thin — it just calls ask() and returns the result.

from app.core.rag_pipeline import run
from app.core.vector_store import get_collection_info


def ask(question: str, top_k: int | None = None) -> dict:
    """
    Run the full RAG pipeline for a user question.

    Parameters
    ----------
    question : str
        The user's question, e.g. "What is RAG?"
    top_k : int | None
        Number of chunks to retrieve. Defaults to config TOP_K_RESULTS.

    Returns
    -------
    dict
        {
            "question": "What is RAG?",
            "answer":   "RAG stands for Retrieval-Augmented Generation...",
            "sources": [
                {"file_name": "rag_notes.pdf", "page_number": 1, "score": 0.91},
                ...
            ]
        }

    Raises
    ------
    ValueError
        If the question is empty.
    RuntimeError
        If the vector store is empty (no documents ingested yet).
    """
    question = question.strip()
    if not question:
        raise ValueError("Question cannot be empty.")

    # Guard: give a clear error if no documents have been ingested yet
    info = get_collection_info()
    if info["total_chunks"] == 0:
        raise RuntimeError(
            "No documents found in the vector store. "
            "Please upload documents before asking questions."
        )

    result = run(question=question, top_k=top_k)

    return {
        "question": question,
        "answer":   result["answer"],
        "sources":  result["sources"],
    }
