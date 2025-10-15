# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List,Dict
from app.models.models import RoleEnum, ImageStatus

class Token(BaseModel):
        access_token: str
        token_type: str = "bearer"
        expires_in: Optional[int]= None
        refresh_token: Optional[str]=None

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
    


class UserLogin(BaseModel):
    email: str
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
class PromptResponse(BaseModel):
    id: int
    text: str
    meta_data: Optional[Dict] = None

    class Config:
        orm_mode = True

class ImageResponse(BaseModel):
    id: int
    file_url: str
    status: str
    prompt_id: Optional[int] = None

    class Config:
        orm_mode = True

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    prompts: List[PromptResponse] = []
    images: List[ImageResponse] = []

    class Config:
        orm_mode = True
