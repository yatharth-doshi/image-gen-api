from fastapi import APIRouter, Depends,HTTPException, Body
from sqlalchemy.orm import Session , joinedload
from app.schemas import UserLogin, Token,ImageResponse,UserResponse
from app.models.models import Image
from app.deps import require_roles,get_db,verify_password,create_access_token
from app.models.models import RoleEnum,User

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/login", response_model=Token)
def admin_login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if db_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Not an Admin")
    token = create_access_token(user_id=db_user.id, email=db_user.email, role=db_user.role.value)
  
    return {"access_token": token, "token_type": "bearer",   "expires_in": 3600, "refresh_token": None}

@router.get("/dashboard",response_model=list[UserResponse])
def admin_dashboard(current_user: User=Depends(require_roles(RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN)), db: Session = Depends(get_db)):
    
    users = db.query(User)\
        .options(
            joinedload(User.prompts),
            joinedload(User.images),
            joinedload(User.generated_images)
        ).all()
    return users

@router.post("/generate-image", response_model=ImageResponse)
def generate_admin_image(
    prompt_text: str = Body(..., embed=True),
    current_user: User = Depends(require_roles(RoleEnum.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Admin generates an image for themselves using a prompt.
    Only accessible by ADMIN role.
    """
    # Replace with your actual image generation logic
    generated_image_url = f"https://fake-image-service.com/admin/{current_user.id}.png"

    # Save image in DB for Admin
    new_image = Image(
        owner_id=current_user.id,
        file_url=generated_image_url,
        status="ACCEPTED",
        prompt_id=some_prompt_id  # Admin-generated images can be auto-accepted
    )

    db.add(new_image)
    db.commit() 
    db.refresh(new_image)

    return new_image
