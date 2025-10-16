from fastapi import APIRouter, Depends,HTTPException,Header,Body
from sqlalchemy.orm import Session,joinedload
from app.schemas import PromptCreate, ImageCreate,UserLogin,Token,ImageResponse,UserResponse
from app.deps import get_current_user, require_roles,verify_password, create_access_token
from app.models.models import RoleEnum, Prompt, Image,User
from app.database import get_db
router = APIRouter(prefix="/user", tags=["User"])

@router.post("/login", response_model=Token)
def user_login(user: UserLogin, db: Session = Depends(get_db)):
    """
    User login route.
    Returns JWT token if credentials are valid.
    """
    # Check if user exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Only allow normal users
    if db_user.role != RoleEnum.USER:
        raise HTTPException(status_code=403, detail="Not a regular User")

    # Create access token
    token = create_access_token(user_id=db_user.id, email=db_user.email, role=db_user.role.value)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 3600,
        "refresh_token": None
    }

@router.get("/dashboard", response_model=UserResponse)
def user_dashboard(
    current_user: User = Depends(require_roles(RoleEnum.USER)),
    db: Session = Depends(get_db)
):
    """
    Fetch the current user's own prompts, images, and generated images.
    Only accessible by USER role.
    """
    user = db.query(User)\
        .options(
            joinedload(User.prompts),
            joinedload(User.images),
            joinedload(User.generated_images)
        )\
        .filter(User.id == current_user.id)\
        .first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

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
