import google.generativeai as genai

from app.config import get_settings
from app.core.retriever import retrieve
from app.core.prompt_builder import build_prompt

_settings = get_settings()
genai.configure(api_key=_settings.GOOGLE_API_KEY)
_model = genai.GenerativeModel(model_name=_settings.CHAT_MODEL)


def run(
    question: str,
    user_id: str,
    top_k: int | None = None,
    chat_history: list[dict] | None = None,
) -> dict:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    chunks = retrieve(question, user_id=user_id, top_k=top_k)
    prompt = build_prompt(question=question, chunks=chunks, chat_history=chat_history)

    response = _model.generate_content(prompt)
    answer   = response.text.strip()

    sources = [
        {
            "file_name":   chunk["metadata"].get("file_name", "unknown"),
            "page_number": chunk["metadata"].get("page_number", "?"),
            "score":       chunk["score"],
        }
        for chunk in chunks
    ]

    return {"answer": answer, "sources": sources}
