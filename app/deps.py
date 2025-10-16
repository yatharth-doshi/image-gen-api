
from fastapi import Depends, HTTPException, status,Request
from fastapi.security import HTTPBearer
from app.database import SessionLocal
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext    
from app.models.models import User, RoleEnum
from typing import List
from jose import jwt, JWTError

SECRET_KEY = "your_secret_key_here"  # Change to a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") 

bearer_scheme =  HTTPBearer()


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------
# JWT token functions
# ---------------------------
def create_access_token(user_id: int, email: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "role": role, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def create_refresh_token(user_id: int) -> str:
    """
    Create a refresh token valid for longer (e.g., 7 days).
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "type": "refresh", "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")



def get_current_payload(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing or invalid format"
        )

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def get_current_user(request: Request) -> User:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user

def require_roles(*allowed_roles: RoleEnum):
    """
    Dependency to allow access only to users with specific roles.
    Usage:
        @router.get("/admin")
        def admin_route(user=Depends(require_roles(RoleEnum.ADMIN))):
            ...
    """
    def role_dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return current_user
    return role_dependency  