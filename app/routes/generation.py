from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.deps import get_db
from app.schemas import GenerationCreate
from app.models import GenerationSession

router = APIRouter(prefix="/generate", tags=["generation"])

@router.post("/")
def generate(data: GenerationCreate, request: Request, db: Session = Depends(get_db)):
    user = request.state.user  # extracted by middleware
    session = GenerationSession(
        user_id=user.user_id,
        reference_image=data.reference_image,
        input_prompt=data.input_prompt
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"message": "Generation session created", "session_id": session.session_id}
