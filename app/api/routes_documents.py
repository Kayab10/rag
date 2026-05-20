# routes_documents.py - Document management API routes.
#
# Endpoints:
#   POST   /documents/upload          — upload and ingest a file
#   GET    /documents                 — list all uploaded files
#   DELETE /documents/{file_name}     — delete a file from disk

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.document_service import ingest_upload, list_uploaded_files, delete_file
from app.models.document_models import IngestResponse, FileListResponse, DeleteResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=IngestResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (.pdf, .txt, .md) and ingest it into the vector store.

    The file is saved to data/raw/, chunked, embedded, and stored in ChromaDB.
    Returns a summary of what was ingested.
    """
    file_bytes = await file.read()

    try:
        result = ingest_upload(
            file_name=file.filename,
            file_bytes=file_bytes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    return result


@router.get("", response_model=FileListResponse)
def list_documents():
    """
    List all files currently stored in data/raw/.
    """
    files = list_uploaded_files()
    return {"files": files, "total": len(files)}


@router.delete("/{file_name}", response_model=DeleteResponse)
def remove_document(file_name: str):
    """
    Delete a file from disk by name.

    Note: this does not remove its chunks from ChromaDB.
    Use POST /documents/reset to wipe the vector store.
    """
    try:
        result = delete_file(file_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return result
