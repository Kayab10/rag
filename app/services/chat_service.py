from app.core.rag_pipeline import run
from app.core.vector_store import get_collection_info
from app.db.chat_history import get_history, save_message


def ask(question: str, user_id: str, top_k: int | None = None) -> dict:
    question = question.strip()
    if not question:
        raise ValueError("Question cannot be empty.")

    info = get_collection_info(user_id=user_id)
    if info["total_chunks"] == 0:
        raise RuntimeError(
            "No documents found. Please upload documents before asking questions."
        )

    history = get_history(user_id)
    result  = run(question=question, user_id=user_id, top_k=top_k, chat_history=history)

    save_message(user_id, "user",      question)
    save_message(user_id, "assistant", result["answer"])

    return {
        "question": question,
        "answer":   result["answer"],
        "sources":  result["sources"],
    }
