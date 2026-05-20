# text_splitter.py - Splits large document text into overlapping chunks.
#
# Why chunking?
#   LLMs have a limited context window, and retrieval works better on focused,
#   smaller pieces of text rather than entire documents.
#
# How overlap works:
#   CHUNK_SIZE=800, CHUNK_OVERLAP=150
#   Chunk 1 → chars    0 – 800
#   Chunk 2 → chars  650 – 1450   (starts 150 chars before chunk 1 ended)
#   Chunk 3 → chars 1300 – 2100
#   The repeated 150 chars ensure a sentence cut at a boundary isn't lost.

from app.config import get_settings
from app.core.document_loader import Document


def split_documents(
    documents: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """
    Split a list of documents into smaller overlapping chunks.

    Each output chunk inherits the metadata of its source document and gains
    two extra metadata fields:
        chunk_index  : position of this chunk within its source document (0-based)
        total_chunks : total number of chunks produced from that source document

    Parameters
    ----------
    documents    : output of document_loader.load_document()
    chunk_size   : max characters per chunk  (defaults to config CHUNK_SIZE)
    chunk_overlap: overlap between chunks    (defaults to config CHUNK_OVERLAP)

    Returns
    -------
    list[Document]
        Flat list of chunk documents ready for embedding.
    """
    settings = get_settings()
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be smaller than chunk_size ({chunk_size})."
        )

    all_chunks: list[Document] = []

    for doc in documents:
        chunks = _split_text(doc["text"], chunk_size, chunk_overlap)

        total = len(chunks)
        for idx, chunk_text in enumerate(chunks):
            all_chunks.append(
                {
                    "text": chunk_text,
                    "metadata": {
                        **doc["metadata"],          # inherit file_name, page_number, etc.
                        "chunk_index": idx,
                        "total_chunks": total,
                    },
                }
            )

    return all_chunks


# ── Internal helper ───────────────────────────────────────────────────────────

def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Slide a window of *chunk_size* characters over *text* with *chunk_overlap*
    characters of overlap between consecutive windows.

    Empty or whitespace-only chunks are discarded.
    """
    if not text.strip():
        return []

    step = chunk_size - chunk_overlap   # how far to advance each time
    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks
