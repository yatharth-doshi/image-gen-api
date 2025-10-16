from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session 
from app.schemas  import UserLogin, Token,UserCreate 
from app.models.models import User,RoleEnum 
from app.database import get_db 
from app.deps import get_password_hash, verify_password, create_access_token,create_refresh_token ,ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Auth"])

ROLE_KEYS = {
    "SUPERADMIN123": RoleEnum.SUPER_ADMIN,
    "ADMIN123": RoleEnum.ADMIN,
}

@router.post("/signup", response_model=Token)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    if user.role_key and user.role_key in ROLE_KEYS:
        assigned_role = ROLE_KEYS[user.role_key]
    else:
        assigned_role = RoleEnum.USER 
    hashed = get_password_hash(user.password)
    new_user = User(
    email=user.email,
    username=user.username,
    password_hash=hashed,
    role=assigned_role
)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = create_access_token(user_id=new_user.id, email=new_user.email, role=new_user.role.value)
    refresh_token = create_refresh_token(user_id=new_user.id)
    return { 
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  
        "refresh_token": refresh_token, 
    }

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(user_id=db_user.id, email=db_user.email, role=db_user.role.value)
    refresh_token = create_refresh_token(user_id=db_user.id)
    
    return {    
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token
        
}

@router.post("/refresh", response_model=Token)
def refresh_token_endpoint(refresh_token: str = Body(...), db: Session = Depends(get_db)):
    try:
        payload = decode_token(refresh_token)
        user_id = int(payload.get("sub"))
    except:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Generate new access token
    access_token = create_access_token(user_id=user.id, email=user.email, role=user.role.value)
    refresh_token = create_refresh_token(user_id=user.id)  # Optional: issue new refresh token

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token
    }