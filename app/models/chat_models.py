# chat_models.py - Pydantic models for chat request and response validation.

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The user's question")
    top_k: int | None = Field(None, ge=1, le=20, description="Number of chunks to retrieve")

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "What is RAG?",
                "top_k": 4
            }
        }
    }


class SourceDocument(BaseModel):
    file_name:   str
    page_number: int | str
    score:       float


class ChatResponse(BaseModel):
    question: str
    answer:   str
    sources:  list[SourceDocument]
