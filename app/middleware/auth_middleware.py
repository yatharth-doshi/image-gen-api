from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from app.deps import SECRET_KEY, ALGORITHM
from app.database import SessionLocal
from app.models import User
from app.enums.user_type import UserType


EXCLUDED_PATHS = ["/api/auth/login", "/api/auth/register", "/docs", "/openapi.json"]

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(path) for path in EXCLUDED_PATHS):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail":"Missing or invalid token"})
        
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            db = SessionLocal()
            user = db.query(User).filter(User.user_id == user_id).first()
            db.close()
            if not user:
                return JSONResponse(status_code=401, content={"detail":"User not found"})
            request.state.user = user
        except JWTError:
            return JSONResponse(status_code=401, content={"detail":"Invalid or expired token"})
        
        return await call_next(request)
