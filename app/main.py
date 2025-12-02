from fastapi import FastAPI
from app.database import Base, engine
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
# from app.middleware.auth_middleware import AuthMiddleware
from app.routes import auth, generation
from dotenv import load_dotenv
from app.image_model import login_hf  
import os

load_dotenv(override=True)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Image Generation System")

# Add middleware
# app.add_middleware(AuthMiddleware)
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("Missing HF_TOKEN in environment variables")

# Login once globally
login_hf(HF_TOKEN)
print("✅ Logged in to Hugging Face successfully")

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


UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

OUTPUT_DIR = "app/outputs"
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

@app.get("/")
def root():
    return {"message":"API is running"}

