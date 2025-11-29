from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.schemas import RefreshRequest
from jose import jwt, JWTError
from app.deps import REFRESH_SECRET_KEY ,verify_token
from app.schemas import UserCreate, UserLogin, Token
from app.models import User, GenerationSession
from app.helper.response_helper import success_response, error_response, safe_api
from app.enums.user_type import UserType
from app.deps import get_db, get_password_hash, verify_password, create_access_token, create_refresh_token, require_role

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
        user_type=user.user_type.value
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
    if not user or not verify_password(payload.password, user.password):
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
        status_code=200
    )

@router.post("/refresh", response_model=dict)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_data = verify_token(payload.refresh_token, REFRESH_SECRET_KEY)
    if not token_data:
        return error_response("Invalid or expired refresh token", 401)

    user_id = token_data.get("sub")
    if not user_id:
        return error_response("Invalid token payload", 400)

    # Generate new tokens
    new_access_token = create_access_token(int(user_id))
    new_refresh_token = create_refresh_token(int(user_id))

    return success_response(
        "New tokens generated successfully",
        {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer"
        },
        status_code=200
    )

@router.get("/all-activities")
def get_all_activities(
    current_user: User = Depends(require_role(UserType.ADMIN, UserType.SUPERADMIN)),
    db: Session = Depends(get_db)
):
    # Admin can see all generation sessions from all users
    sessions = db.query(GenerationSession).join(User).all()
    
    session_data = []
    for session in sessions:
        session_data.append({
            "session_id": session.session_id,
            "user_id": session.user_id,
            "user_email": current_user.email,
            "user_name": f"{current_user.firstname} {current_user.lastname}",
            "reference_image": session.reference_image,
            "input_prompt": session.input_prompt,
            "output_path": session.output_path,
            "approved": session.approved,
            "attempts": session.attempts,
            "created_at": session.created_at.isoformat() if session.created_at else None
        })
    
    return success_response(
        "All user activities retrieved",
        {"sessions": session_data, "total_sessions": len(session_data)}
    )

@router.get("/my-activity", response_model=dict)
def get_my_activity(
    current_user: User = Depends(require_role(UserType.USER)),
    db: Session = Depends(get_db)
):
    
    sessions = db.query(GenerationSession).filter(
        GenerationSession.user_id == current_user.user_id
    ).all()
    
    session_data = []
    for session in sessions:
        session_data.append({
            "session_id": session.session_id,
            "user_id": session.user_id,
            "user_email": current_user.email,
            "user_name": f"{current_user.firstname} {current_user.lastname}",
            "reference_image": session.reference_image,
            "input_prompt": session.input_prompt,
            "output_path": session.output_path,
            "approved": session.approved,
            "attempts": session.attempts,
            "created_at": session.created_at.isoformat() if session.created_at else None
        })
    
    return success_response(
        "User activities retrieved",
        {"sessions": session_data, "total_sessions": len(session_data)}
    )