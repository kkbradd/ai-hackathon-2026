from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import verify_token
from database import get_db
from models import User
from schemas import ChatRequest, ChatResponse
from agent import agent

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db), _: User = Depends(verify_token)):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")
    try:
        result = agent.chat(
            message=request.message,
            session_id=request.session_id,
            db=db,
        )
        return ChatResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
def clear_session(session_id: str):
    agent.clear_session(session_id)
    return {"detail": f"Oturum '{session_id}' temizlendi."}
