from fastapi import APIRouter, Depends, HTTPException, Body,Header
from sqlalchemy.orm import Session, joinedload
from app.deps import create_access_token, require_roles, get_db, verify_password
from app.models.models import User,RoleEnum, Image, Prompt
from app.schemas import UserResponse, ImageResponse, PromptResponse ,Token,UserLogin

router = APIRouter(prefix="/superadmin", tags=["SuperAdmin"])


@router.post("/login", response_model=Token)
def superadmin_login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if db_user.role != RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Not a SuperAdmin")
    token = create_access_token(user_id=db_user.id, email=db_user.email, role=db_user.role.value)
    print("Generated token:", token)

    return {"access_token": token, "token_type": "bearer","expires_in": 3600, "refresh_token": None}

@router.get("/dashboard",response_model=list[UserResponse])
def superadmin_dashboard(authorization: str = Header(None),user=Depends(require_roles(RoleEnum.SUPER_ADMIN)),db: Session = Depends(get_db)):
    """
    Fetch all users along with their prompts, uploaded images,
    and generated images. Only accessible by SUPER_ADMIN.   
    """
    users = db.query(User)\
        .options(
            joinedload(User.prompts),
            joinedload(User.images),
            joinedload(User.generated_images)
        ).all()

    return users
   
@router.post("/generate-image", response_model=ImageResponse)
def generate_superadmin_image(
    prompt_text: str = Body(..., embed=True),
    current_user: User = Depends(require_roles(RoleEnum.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    SuperAdmin generates an image for themselves using a prompt.
    """
    new_prompt = Prompt(text=prompt_text, user_id=current_user.id)
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    # Replace with your actual image generation logic
    generated_image_url = f"https://fake-image-service.com/superadmin/{current_user.id}.png"

    # Save image in DB for SuperAdmin
    new_image = Image(
        owner_id=current_user.id,
        file_url=generated_image_url,
        status="ACCEPTED" ,
        prompt_id=new_prompt.id )    # SuperAdmin-generated images can be auto-accepte)

    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return new_image