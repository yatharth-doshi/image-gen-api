from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums.user_type import UserType

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    user_type = Column(Integer, nullable=False,default=UserType.USER)  # 1=superadmin, 2=admin, 3=user
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    sessions = relationship("GenerationSession", back_populates="user")

class GenerationSession(Base):
    __tablename__ = "generation_sessions"
    
    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    reference_image = Column(String, nullable=True)  
    input_prompt = Column(Text, nullable=False)
    output_path = Column(String, nullable=True)
    approved = Column(Boolean, default=False)
    attempts = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())
    
    user = relationship("User", back_populates="sessions")
