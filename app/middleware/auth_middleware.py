from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from jose import jwt, JWTError, ExpiredSignatureError
from app.deps import SECRET_KEY, ALGORITHM
from app.database import SessionLocal
from app.models import User
from app.enums.user_type import UserType
import os

EXCLUDED_PATHS = ["/api/auth/login", "/api/auth/register","/api/auth/refresh", "/docs", "/openapi.json"]

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth check for public routes
        if any(request.url.path.startswith(path) for path in EXCLUDED_PATHS):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or malformed Authorization header"}
            )

        token = auth_header.split(" ")[1]
        environment = os.getenv("ENVIRONMENT", "production")

        db = SessionLocal()
        try:
            # Decode token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")

            if not user_id:
                raise JWTError("Token payload missing 'sub' (user id)")

            # Fetch user from DB
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return JSONResponse(status_code=401, content={"detail": "User not found"})

            # Attach user to request
            request.state.user = user

        except ExpiredSignatureError as e:
            detail = "Token has expired"
            if environment == "development":
                detail += f" ({str(e)})"
            return JSONResponse(status_code=401, content={"detail": detail})

        except JWTError as e:
            detail = "Invalid or expired token"
            if environment == "development":
                detail += f" ({str(e)})"
            return JSONResponse(status_code=401, content={"detail": detail})

        finally:
            db.close()

        return await call_next(request)
