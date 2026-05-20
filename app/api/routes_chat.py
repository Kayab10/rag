from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.services.chat_service import ask
from app.db.chat_history import get_history
from app.models.chat_models import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, user_id: str = Depends(get_current_user)):
    try:
        return ask(question=request.question, user_id=user_id, top_k=request.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")


@router.get("/history")
def chat_history(user_id: str = Depends(get_current_user)):
    return {"history": get_history(user_id)}
