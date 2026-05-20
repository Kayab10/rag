import hashlib
from pathlib import Path

from app.core.document_loader import load_document, SUPPORTED_EXTENSIONS
from app.core.text_splitter import split_documents
from app.core.vector_store import add_documents, get_collection_info
from app.db.documents import save_document, get_document_by_hash, list_documents

UPLOAD_DIR = Path("data/raw")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ingest_file(file_path: str | Path, user_id: str) -> dict:
    path   = Path(file_path)
    docs   = load_document(path)
    chunks = split_documents(docs)
    added  = add_documents(chunks, user_id=user_id)
    info   = get_collection_info(user_id=user_id)

    return {
        "file_name":     path.name,
        "pages_loaded":  len(docs),
        "chunks_stored": added,
        "total_chunks":  info["total_chunks"],
    }


def ingest_upload(file_name: str, file_bytes: bytes, user_id: str) -> dict:
    safe_name = Path(file_name).name
    suffix    = Path(safe_name).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    file_hash = _hash_bytes(file_bytes)
    existing  = get_document_by_hash(user_id, file_hash)

    if existing:
        info = get_collection_info(user_id=user_id)
        return {
            "file_name":     safe_name,
            "pages_loaded":  0,
            "chunks_stored": 0,
            "total_chunks":  info["total_chunks"],
            "skipped":       True,
            "reason":        "File already ingested (duplicate content detected)",
        }

    save_path = UPLOAD_DIR / safe_name
    save_path.write_bytes(file_bytes)

    result = ingest_file(save_path, user_id=user_id)

    save_document(
        user_id=user_id,
        file_name=safe_name,
        file_hash=file_hash,
        chunks_stored=result["chunks_stored"],
    )

    return result


def list_uploaded_files(user_id: str) -> list[dict]:
    db_docs = list_documents(user_id)
    return [
        {"file_name": d["file_name"], "size_kb": 0.0}
        for d in db_docs
    ]


def delete_file(file_name: str) -> dict:
    safe_name = Path(file_name).name
    target    = UPLOAD_DIR / safe_name
    if not target.exists():
        raise FileNotFoundError(f"File not found: {safe_name}")
    target.unlink()
    return {"deleted": safe_name}
