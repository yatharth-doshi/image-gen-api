from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, Request
from passlib.context import CryptContext
from app.enums.user_type import UserType
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.database import SessionLocal
from app.models import User
import bcrypt


SECRET_KEY = "abcd"
REFRESH_SECRET_KEY = "abcd"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------- Database Dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def safe_password_truncate(password: str) -> str:
    """
    Safely truncate password to 72 bytes for bcrypt compatibility.
    Handles UTF-8 multi-byte characters properly.
    """
    if not password:
        return password
    
    password_bytes = password.encode('utf-8')
    
    if len(password_bytes) <= 72:
        return password
    
    truncated_bytes = password_bytes[:72]
    
    try:
        return truncated_bytes.decode('utf-8')
    except UnicodeDecodeError:
        for i in range(1, 4):  # UTF-8 chars 1-4 bytes
            try:
                return truncated_bytes[:-i].decode('utf-8')
            except UnicodeDecodeError:
                continue
        return ""

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password and return (is_valid, error_message)"""
    if not password:
        return False, "Password cannot be empty"
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, ""

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly"""
    is_valid, error_message = validate_password(password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    password_to_hash = safe_password_truncate(password).encode('utf-8')
    hashed = bcrypt.hashpw(password_to_hash, bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash"""
    password_bytes = safe_password_truncate(plain_password).encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

# ---------- JWT ----------
def create_access_token(user_id: int) -> str:
    
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "type": "access","exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: int) -> str:
   
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "type": "refresh", "exp": expire}
    return jwt.encode(payload, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token, SECRET_KEY)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def verify_token(token: str, secret_key: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    
def require_role(*allowed_roles: UserType):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.user_type not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to access this resource"    
            )
        return current_user
    return role_checker