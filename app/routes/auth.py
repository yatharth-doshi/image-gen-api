from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import UserCreate, UserLogin, Token
from app.models import User
from app.helper.response_helper import success_response, error_response, safe_api
from app.enums.user_type import UserType
from app.deps import get_db, get_password_hash, verify_password, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=dict)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
       return error_response("Email already exists", 400)
    
    new_user = User(
        firstname=user.firstname,
        lastname=user.lastname,
        email=user.email,
        password=get_password_hash(user.password),
        user_type=UserType.USER 
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return success_response(
        "User registered successfully",
        {"user_id": new_user.user_id, "email": new_user.email,"user_type": UserType(new_user.user_type).name},
        201
    )

@router.post("/login", response_model=Token)
@safe_api
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password):
        return error_response("Invalid email or password", 401)
    
    access_token = create_access_token(user.user_id)
    refresh_token = create_refresh_token(user.user_id)
    
    return success_response(
        "User logged in successfully",
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
        },
        200
    )

