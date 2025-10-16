from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.middleware.auth_middleware import AuthMiddleware
from app.routes import auth , user , admin , superadmin

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Image Management System", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(superadmin.router)
app.include_router(admin.router)
app.include_router(user.router)



@app.get("/")
def root():
    return {"message": "Welcome to Image Management System"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
