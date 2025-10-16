# models.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base

class RoleEnum(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    USER = "USE R"

class ImageStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.USER, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    prompts = relationship("Prompt", back_populates="owner")
    images = relationship("Image", back_populates="owner",foreign_keys="Image.owner_id")
    generated_images = relationship("Image", back_populates="generator", foreign_keys="Image.generated_by") 

class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="prompts")
    images = relationship("Image", back_populates="prompt")

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=True)
    file_url = Column(String, nullable=True)  # could be local path or S3 URL
    status = Column(Enum(ImageStatus), default=ImageStatus.PENDING, nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="images", foreign_keys=[owner_id])
    generator = relationship("User", back_populates="generated_images", foreign_keys=[generated_by])
    
    prompt = relationship("Prompt", back_populates="images")
    actions = relationship("ImageAction", back_populates="image")

class ImageAction(Base):
    __tablename__ = "image_actions"
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    action = Column(String, nullable=False)  # e.g., "ACCEPT", "REJECT", "VIEW", "GENERATE"
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    image = relationship("Image", back_populates="actions")
