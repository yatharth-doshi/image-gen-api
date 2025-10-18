from fastapi import FastAPI
from app.database import Base, engine
from app.middleware.auth_middleware import AuthMiddleware
from app.routes import auth, generation
from dotenv import load_dotenv

load_dotenv(override=True)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Image Generation System")

# Add middleware
# app.add_middleware(AuthMiddleware)

# Include routes
app.include_router(auth.router, prefix="/api")
app.add_middleware(AuthMiddleware)
app.include_router(generation.router,prefix="/api")

@app.get("/")
def root():
    return {"message":"API is running"}

