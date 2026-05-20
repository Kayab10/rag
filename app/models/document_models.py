# document_models.py - Pydantic models for document operation responses.

from pydantic import BaseModel


class IngestResponse(BaseModel):
    file_name:     str
    pages_loaded:  int
    chunks_stored: int
    total_chunks:  int


class FileInfo(BaseModel):
    file_name: str
    size_kb:   float


class FileListResponse(BaseModel):
    files: list[FileInfo]
    total: int


class DeleteResponse(BaseModel):
    deleted: str
