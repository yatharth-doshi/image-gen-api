from fastapi import FastAPI
from app.database import Base, engine
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
# from app.middleware.auth_middleware import AuthMiddleware
from app.routes import auth, generation
from dotenv import load_dotenv
import os

load_dotenv(override=True)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Image Generation System")

# Include routes
app.include_router(auth.router, prefix="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "*" 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(generation.router,prefix="/api")

@app.get("/")
def root():
    return {"message":"API is running"}

