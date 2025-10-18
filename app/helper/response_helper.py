from fastapi.responses import JSONResponse
from functools import wraps
import os

def success_response(message: str, data: dict = None):
    response_content = {
        "status": "success",
        "message": message,
        "data": data
    }

    return JSONResponse(status_code=200, content=response_content)

def error_response(message: str, dev_message: str = None, status_code: int = 400):
    environment = os.getenv("ENVIRONMENT", "production")
    print(os.getenv("ENVIRONMENT"), "NOW")
    response_content = {
        "status": "error",
        "message": message,
        "data": None
    }
    if environment == "development" and dev_message:
        response_content["dev_message"] = dev_message

    return JSONResponse(status_code=status_code, content=response_content)

def safe_api(handler):
    """
    Decorator to wrap any FastAPI route with try/except and return standard error format.
    """
    @wraps(handler)
    async def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except Exception as e:
            return error_response("Internal Server Error", dev_message=str(e), status_code=500)
    return wrapper