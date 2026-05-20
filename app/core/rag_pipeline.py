# rag_pipeline.py - Orchestrates the full RAG flow end to end.
#
# Steps:
#   1. Receive user question
#   2. Retrieve relevant chunks      (retriever.py)
#   3. Build prompt                  (prompt_builder.py)
#   4. Send prompt to Gemini LLM     (google-generativeai)
#   5. Return answer + sources
#
# This file is the single entry point the API and CLI will call.
# It connects every core module together.

import google.generativeai as genai

from app.config import get_settings
from app.core.retriever import retrieve
from app.core.prompt_builder import build_prompt

# ── Setup ─────────────────────────────────────────────────────────────────────
_settings = get_settings()
genai.configure(api_key=_settings.GOOGLE_API_KEY)

_model = genai.GenerativeModel(model_name=_settings.CHAT_MODEL)


# ── Response type ─────────────────────────────────────────────────────────────
# A plain dict so it's easy to serialize to JSON in the API later.
#
# {
#     "answer":  "RAG stands for Retrieval-Augmented Generation...",
#     "sources": [
#         {"file_name": "rag_notes.pdf", "page_number": 1, "score": 0.91},
#         {"file_name": "rag_notes.pdf", "page_number": 2, "score": 0.87},
#     ]
# }


def run(question: str, top_k: int | None = None) -> dict:
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
            "answer":  str,          # Gemini's response
            "sources": list[dict]    # which chunks were used, with metadata + score
        }
    """
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    # ── Step 1: Retrieve relevant chunks ──────────────────────────────────────
    chunks = retrieve(question, top_k=top_k)
    # chunks → [{"text": "...", "metadata": {...}, "score": 0.91}, ...]

    # ── Step 2: Build the prompt ───────────────────────────────────────────────
    prompt = build_prompt(question=question, chunks=chunks)

    # ── Step 3: Call Gemini ────────────────────────────────────────────────────
    response = _model.generate_content(prompt)
    answer = response.text.strip()

    # ── Step 4: Build sources list ─────────────────────────────────────────────
    # Extract just the metadata + score from each chunk so the caller knows
    # exactly which documents were used to generate the answer.
    sources = [
        {
            "file_name":   chunk["metadata"].get("file_name", "unknown"),
            "page_number": chunk["metadata"].get("page_number", "?"),
            "score":       chunk["score"],
        }
        for chunk in chunks
    ]

    return {
        "answer":  answer,
        "sources": sources,
    }
