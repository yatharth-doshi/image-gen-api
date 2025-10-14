# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.models.models import RoleEnum, ImageStatus

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str]

class TokenPayload(BaseModel):
    sub: int
    email: EmailStr
    role: RoleEnum
    iat: int
    exp: int

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: RoleEnum

    class Config:
        orm_mode = True

class PromptCreate(BaseModel):
    text: str
    metadata: Optional[dict] = None

class PromptOut(BaseModel):
    id: int
    owner_id: int
    text: str
    metadata: Optional[dict]
    class Config:
        orm_mode = True

class ImageCreate(BaseModel):
    prompt_id: Optional[int] = None
    file_url: Optional[str] = None
    metadata: Optional[dict] = None

class ImageOut(BaseModel):
    id: int
    owner_id: int
    prompt_id: Optional[int]
    file_url: Optional[str]
    status: ImageStatus
    metadata: Optional[dict]
    class Config:
        orm_mode = True
