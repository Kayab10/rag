# prompt_builder.py - Assembles retrieved chunks + user question into a final prompt.
#
# Why a dedicated file for this?
#   The prompt is the single biggest lever for LLM quality.
#   Keeping it here means you can iterate on wording, structure, and tone
#   without touching any other part of the pipeline.
#
# Anti-hallucination strategy:
#   We explicitly tell the model to answer ONLY from the provided context
#   and to admit when it doesn't know. This is the most important instruction
#   in a RAG system.

# ── Prompt template ───────────────────────────────────────────────────────────
# {context}  and  {question}  are filled in at runtime by build_prompt().

RAG_PROMPT_TEMPLATE = """You are a helpful assistant. Answer the question using only the context below.
If the answer is not in the context, say "I don't have enough information to answer that."
Do not make up information that is not in the context.

Context:
{context}

Question:
{question}

Answer:"""


# ── Public API ────────────────────────────────────────────────────────────────

def build_prompt(question: str, chunks: list[str] | list[dict]) -> str:
    """
    Assemble retrieved chunks and the user question into a single prompt string.

    Parameters
    ----------
    question : str
        The user's question, e.g. "What is RAG?"

    chunks : list[str] | list[dict]
        Either:
        - A list of plain text strings  (from retriever.retrieve_texts)
        - A list of result dicts        (from retriever.retrieve)
        Both formats are accepted for flexibility.

    Returns
    -------
    str
        The complete prompt ready to be sent to the Gemini chat model.
    """
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if not chunks:
        # No context found — tell the model explicitly so it doesn't hallucinate
        context_str = "No relevant context was found in the documents."
    else:
        context_str = _format_context(chunks)

    return RAG_PROMPT_TEMPLATE.format(
        context=context_str,
        question=question.strip(),
    )


def _format_context(chunks: list[str] | list[dict]) -> str:
    """
    Format a list of chunks into a numbered context block.

    Example output:
        [1] RAG stands for Retrieval-Augmented Generation...
            Source: rag_notes.pdf | Page: 1

        [2] The retrieval step fetches relevant documents...
            Source: rag_notes.pdf | Page: 2

    Numbering helps the model reference specific pieces of context
    and makes debugging easier when you inspect prompts.
    """
    lines = []

    for i, chunk in enumerate(chunks, start=1):
        # Accept both plain strings and full result dicts
        if isinstance(chunk, dict):
            text     = chunk.get("text", "")
            metadata = chunk.get("metadata", {})
            source   = metadata.get("file_name", "unknown")
            page     = metadata.get("page_number", "?")
            lines.append(f"[{i}] {text.strip()}\n    Source: {source} | Page: {page}")
        else:
            lines.append(f"[{i}] {chunk.strip()}")

    return "\n\n".join(lines)
