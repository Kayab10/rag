RAG_PROMPT_TEMPLATE = """You are a knowledgeable tutor and assistant. Your job is to have a helpful, detailed conversation with the user.

You have access to the user's documents (provided as context below). Use them as your primary reference when they are relevant. When the documents don't fully cover the topic, use your own knowledge to give a complete, helpful answer — just like a teacher would.

Guidelines:
- If the user asks to summarize or explain something from their documents, do it thoroughly.
- If the user asks about a concept (e.g. "what is supervised learning"), explain it in detail using your knowledge, referencing the documents where relevant.
- If the user asks a follow-up question, use the conversation history to give a coherent response.
- Never say "I don't have enough information" if you actually know the answer from your training.
- Only say you don't know if you genuinely cannot answer.

{history}
Relevant context from user's documents:
{context}

User: {question}
Assistant:"""


def build_prompt(
    question: str,
    chunks: list[str] | list[dict],
    chat_history: list[dict] | None = None,
) -> str:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    context_str = _format_context(chunks) if chunks else "No relevant documents found."
    history_str = _format_history(chat_history) if chat_history else ""

    return RAG_PROMPT_TEMPLATE.format(
        history=history_str,
        context=context_str,
        question=question.strip(),
    )


def _format_context(chunks: list[str] | list[dict]) -> str:
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        if isinstance(chunk, dict):
            text   = chunk.get("text", "")
            meta   = chunk.get("metadata", {})
            source = meta.get("file_name", "unknown")
            page   = meta.get("page_number", "?")
            lines.append(f"[{i}] {text.strip()}\n    Source: {source} | Page: {page}")
        else:
            lines.append(f"[{i}] {chunk.strip()}")
    return "\n\n".join(lines)


def _format_history(chat_history: list[dict]) -> str:
    if not chat_history:
        return ""
    lines = ["Previous conversation:"]
    for msg in chat_history:
        role    = "User" if msg["role"] == "user" else "Assistant"
        message = msg.get("message", "")
        lines.append(f"{role}: {message}")
    return "\n".join(lines) + "\n\n"
