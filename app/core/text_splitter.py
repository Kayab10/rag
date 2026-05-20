# text_splitter.py - Splits large document text into overlapping chunks.
#
# Phase 1.2 — replaced character sliding window with recursive splitter.
#
# Why recursive?
#   The old splitter cut blindly every 800 chars, often mid-sentence.
#   The recursive splitter tries natural boundaries first:
#     1. \n\n  — paragraph breaks  (best split point)
#     2. \n    — line breaks
#     3. ". "  — sentence endings
#     4. " "   — word boundaries
#     5. ""    — characters        (last resort fallback)
#   This produces cleaner chunks that preserve meaning better.

from app.config import get_settings
from app.core.document_loader import Document

# Split priority — try each separator in order, fall back to the next
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def split_documents(
    documents: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """
    Split a list of documents into smaller overlapping chunks.

    Each output chunk inherits the metadata of its source document and gains:
        chunk_index  : position within its source document (0-based)
        total_chunks : total chunks produced from that source

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
    chunk_size    = chunk_size    or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be smaller than chunk_size ({chunk_size})."
        )

    all_chunks: list[Document] = []

    for doc in documents:
        chunks = _recursive_split(doc["text"], chunk_size, chunk_overlap, _SEPARATORS)

        total = len(chunks)
        for idx, chunk_text in enumerate(chunks):
            all_chunks.append(
                {
                    "text": chunk_text,
                    "metadata": {
                        **doc["metadata"],
                        "chunk_index":  idx,
                        "total_chunks": total,
                    },
                }
            )

    return all_chunks


# ── Internal helpers ──────────────────────────────────────────────────────────

def _recursive_split(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    separators: list[str],
) -> list[str]:
    """
    Recursively split *text* using the first separator that produces
    pieces small enough to fit in *chunk_size*.

    If a piece is still too large after splitting, recurse with the
    next separator in the list.
    """
    if not text.strip():
        return []

    # If text already fits, return as-is
    if len(text) <= chunk_size:
        return [text.strip()]

    # Try each separator in priority order
    for sep in separators:
        parts = text.split(sep) if sep else list(text)

        # Only use this separator if it actually splits the text
        if len(parts) > 1:
            return _merge_splits(parts, sep, chunk_size, chunk_overlap, separators)

    # Absolute fallback — hard cut at chunk_size
    return [text[i:i + chunk_size].strip() for i in range(0, len(text), chunk_size - chunk_overlap)]


def _merge_splits(
    parts: list[str],
    separator: str,
    chunk_size: int,
    chunk_overlap: int,
    separators: list[str],
) -> list[str]:
    """
    Merge split parts back into chunks that respect chunk_size,
    with chunk_overlap characters carried over between chunks.

    Parts that are individually too large are recursively split further.
    """
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for part in parts:
        part = part.strip()
        if not part:
            continue

        part_len = len(part) + len(separator)

        # Part alone exceeds chunk_size — recurse with next separator
        if len(part) > chunk_size:
            # Flush current buffer first
            if current:
                chunks.append(separator.join(current).strip())
                current, current_len = _apply_overlap(current, separator, chunk_overlap)

            # Recursively split the oversized part
            next_seps = separators[separators.index(separator) + 1:] if separator in separators else [""]
            sub_chunks = _recursive_split(part, chunk_size, chunk_overlap, next_seps or [""])
            chunks.extend(sub_chunks)
            continue

        # Adding this part would exceed chunk_size — flush and start new chunk
        if current_len + part_len > chunk_size and current:
            chunks.append(separator.join(current).strip())
            current, current_len = _apply_overlap(current, separator, chunk_overlap)

        current.append(part)
        current_len += part_len

    # Flush remaining parts
    if current:
        chunks.append(separator.join(current).strip())

    return [c for c in chunks if c]


def _apply_overlap(
    current: list[str],
    separator: str,
    chunk_overlap: int,
) -> tuple[list[str], int]:
    """
    Carry over the tail of the current chunk as overlap for the next chunk.
    Returns the new current list and its character length.
    """
    overlap_parts: list[str] = []
    overlap_len = 0

    for part in reversed(current):
        part_len = len(part) + len(separator)
        if overlap_len + part_len > chunk_overlap:
            break
        overlap_parts.insert(0, part)
        overlap_len += part_len

    return overlap_parts, overlap_len
