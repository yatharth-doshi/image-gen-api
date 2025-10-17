from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from app.database import SessionLocal
from app.models.models import User
from app.deps import SECRET_KEY, ALGORITHM

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
       
        if request.url.path.startswith("/auth") or request.url.path.startswith("/docs") or request.url.path.startswith("/openapi.json") or request.url.path.startswith("/superadmin/login") or request.url.path.startswith("/admin/login")or request.url.path.startswith("/user/login")or request.url.path.startswith("/user/dashboard"):
            
            
            
            return await call_next(request)

        authorization = request.headers.get("authorization") 
        print("👉 Received Authorization Header:", authorization)
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Missing or invalid token"}
    )

        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")

            db = SessionLocal()
            user = db.query(User).filter(User.id == user_id).first()
            db.close()

            if not user:
                raise HTTPException(status_code=401, detail="User not found")

            # Attach current user to request.state for access in routes
            request.state.user = user

        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        return await call_next(request)
