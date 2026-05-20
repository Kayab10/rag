from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from app.dependencies import get_current_user
from app.services.document_service import ingest_upload, list_uploaded_files, delete_file
from app.models.document_models import IngestResponse, FileListResponse, DeleteResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    file_bytes = await file.read()
    try:
        result = ingest_upload(file_name=file.filename, file_bytes=file_bytes, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
    return result


@router.get("", response_model=FileListResponse)
def list_documents(user_id: str = Depends(get_current_user)):
    files = list_uploaded_files(user_id=user_id)
    return {"files": files, "total": len(files)}


@router.delete("/{file_name}", response_model=DeleteResponse)
def remove_document(file_name: str, user_id: str = Depends(get_current_user)):
    try:
        return delete_file(file_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
