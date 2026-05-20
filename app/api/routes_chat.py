# routes_chat.py - Chat API route.
#
# Endpoint:
#   POST /chat — ask a question, get an answer with sources

from fastapi import APIRouter, HTTPException

from app.services.chat_service import ask
from app.models.chat_models import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Ask a question and get an answer generated from your uploaded documents.

    The pipeline:
    1. Retrieves the most relevant chunks from ChromaDB
    2. Builds a prompt with the context + question
    3. Sends it to Gemini and returns the answer

    Returns the answer and the source documents used to generate it.
    """
    try:
        result = ask(question=request.question, top_k=request.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    return result
