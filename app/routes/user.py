from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import PromptCreate, ImageCreate
from app.deps import get_current_user, require_roles
from app.models.models import RoleEnum, Prompt, Image
from app.database import get_db

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/prompts")
def create_prompt(data: PromptCreate, user=Depends(require_roles(RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN)), db: Session = Depends(get_db)):
    prompt = Prompt(owner_id=user.id, text=data.text)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt

@router.get("/prompts")
def get_prompts(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == RoleEnum.SUPER_ADMIN:
        return db.query(Prompt).all()
    return db.query(Prompt).filter(Prompt.owner_id == user.id).all()

@router.post("/images")
def create_image(data: ImageCreate, user=Depends(require_roles(RoleEnum.USER, RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN)), db: Session = Depends(get_db)):
    image = Image(owner_id=user.id, prompt_id=data.prompt_id, file_url=data.file_url)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image

@router.get("/images")
def get_images(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role in [RoleEnum.SUPER_ADMIN, RoleEnum.ADMIN]:
        return db.query(Image).all()
    return db.query(Image).filter(Image.owner_id == user.id).all()
