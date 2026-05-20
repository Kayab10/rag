# documents.py - Document CRUD operations against Supabase documents table.
# Phase 3.3
#
# Table schema:
#   id            UUID  PRIMARY KEY DEFAULT gen_random_uuid()
#   user_id       UUID  REFERENCES users(id) ON DELETE CASCADE
#   file_name     TEXT  NOT NULL
#   file_hash     TEXT  NOT NULL
#   chunks_stored INT   NOT NULL
#   uploaded_at   TIMESTAMPTZ DEFAULT now()

from app.db.database import get_client


def save_document(
    user_id: str,
    file_name: str,
    file_hash: str,
    chunks_stored: int,
) -> dict:
    """
    Insert a new document record for a user.

    Parameters
    ----------
    user_id       : str  UUID of the owning user.
    file_name     : str  Original filename e.g. "notes.pdf"
    file_hash     : str  sha256 hex digest of the file bytes.
    chunks_stored : int  Number of chunks stored in the vector DB.

    Returns
    -------
    dict  The created document row.
    """
    client = get_client()

    response = (
        client.table("documents")
        .insert({
            "user_id":       user_id,
            "file_name":     file_name,
            "file_hash":     file_hash,
            "chunks_stored": chunks_stored,
        })
        .execute()
    )

    return response.data[0]


def get_document_by_hash(user_id: str, file_hash: str) -> dict | None:
    """
    Check if a document with this hash already exists for the user.
    Used for duplicate prevention.

    Parameters
    ----------
    user_id   : str  Only check within this user's documents.
    file_hash : str  sha256 hex digest to look up.

    Returns
    -------
    dict | None  The existing document row, or None if not found.
    """
    client = get_client()

    response = (
        client.table("documents")
        .select("*")
        .eq("user_id", user_id)
        .eq("file_hash", file_hash)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def list_documents(user_id: str) -> list[dict]:
    """
    Return all documents uploaded by a user, newest first.

    Parameters
    ----------
    user_id : str

    Returns
    -------
    list[dict]  List of document rows for this user.
    """
    client = get_client()

    response = (
        client.table("documents")
        .select("*")
        .eq("user_id", user_id)
        .order("uploaded_at", desc=True)
        .execute()
    )

    return response.data or []
