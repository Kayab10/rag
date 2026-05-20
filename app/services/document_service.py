# document_service.py - Business logic for document ingestion.
#
# Flow:
#   upload file
#       ↓
#   save to data/raw/
#       ↓
#   load text + metadata       (document_loader)
#       ↓
#   split into chunks          (text_splitter)
#       ↓
#   embed + store in ChromaDB  (vector_store)
#       ↓
#   return ingestion summary

import shutil
from pathlib import Path

from app.core.document_loader import load_document, SUPPORTED_EXTENSIONS
from app.core.text_splitter import split_documents
from app.core.vector_store import add_documents, get_collection_info

# Where uploaded files are saved before processing
UPLOAD_DIR = Path("data/raw")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def ingest_file(file_path: str | Path) -> dict:
    """
    Run the full ingestion pipeline for a single file that is already on disk.

    Parameters
    ----------
    file_path : str | Path
        Path to the file to ingest (must be a supported type).

    Returns
    -------
    dict
        {
            "file_name"    : "rag_notes.pdf",
            "pages_loaded" : 5,
            "chunks_stored": 34,
            "total_chunks" : 134     # total in collection after this ingestion
        }
    """
    path = Path(file_path)

    # Load text + metadata from file
    docs = load_document(path)

    # Split into overlapping chunks
    chunks = split_documents(docs)

    # Embed and store in ChromaDB
    added = add_documents(chunks)

    info = get_collection_info()

    return {
        "file_name":     path.name,
        "pages_loaded":  len(docs),
        "chunks_stored": added,
        "total_chunks":  info["total_chunks"],
    }


def ingest_upload(file_name: str, file_bytes: bytes) -> dict:
    """
    Save an uploaded file to disk, then run the ingestion pipeline.

    This is the entry point called by the upload API route.
    It handles saving the raw bytes before passing to ingest_file().

    Parameters
    ----------
    file_name  : str   Original filename from the upload (e.g. "notes.pdf")
    file_bytes : bytes Raw file content from the HTTP request

    Returns
    -------
    dict
        Same summary dict as ingest_file().

    Raises
    ------
    ValueError
        If the file extension is not supported.
    """
    suffix = Path(file_name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # Save file to data/raw/
    save_path = UPLOAD_DIR / file_name
    save_path.write_bytes(file_bytes)

    # Run ingestion pipeline
    return ingest_file(save_path)


def list_uploaded_files() -> list[dict]:
    """
    Return a list of all files currently in the upload directory.

    Returns
    -------
    list[dict]
        [{"file_name": "notes.pdf", "size_kb": 142.3}, ...]
    """
    files = []
    for f in sorted(UPLOAD_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append({
                "file_name": f.name,
                "size_kb":   round(f.stat().st_size / 1024, 2),
            })
    return files


def delete_file(file_name: str) -> dict:
    """
    Delete an uploaded file from disk.

    Note: this does NOT remove its chunks from ChromaDB.
    Use vector_store.reset_collection() for a full wipe.

    Parameters
    ----------
    file_name : str  Name of the file to delete (not a full path).

    Returns
    -------
    dict
        {"deleted": "notes.pdf"}

    Raises
    ------
    FileNotFoundError
        If the file does not exist in the upload directory.
    """
    target = UPLOAD_DIR / file_name
    if not target.exists():
        raise FileNotFoundError(f"File not found: {file_name}")

    target.unlink()
    return {"deleted": file_name}
