from pydantic import BaseModel, EmailStr
from typing import Optional

# ---------------- Registration & Login ----------------
class UserCreate(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ---------------- Token ----------------
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

# ---------------- Generation ----------------
class GenerationCreate(BaseModel):
    input_prompt: str
    reference_image: Optional[str] = None  # relative path
