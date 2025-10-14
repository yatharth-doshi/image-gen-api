from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas  import UserCreate, Token
from app.models.models import User
from app.database import get_db
from app.deps import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", response_model=Token)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    hashed = get_password_hash(user.password)
    new_user = User(email=user.email, username=user.username, password_hash=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = create_access_token(user_id=new_user.id, email=new_user.email, role=new_user.role.value)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user_id=db_user.id, email=db_user.email, role=db_user.role.value)
    return {"access_token": token, "token_type": "bearer"}
