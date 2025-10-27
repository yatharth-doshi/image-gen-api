from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from app.helper.response_helper import success_response, error_response
from sqlalchemy.orm import Session
from app.deps import get_db
from app.image_model import generate_3d, login_hf

from app.models import GenerationSession
import os
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/generate", tags=["generation"])

UPLOAD_DIR = "app/uploads"

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("Missing HF_TOKEN in environment variables")
login_hf(HF_TOKEN)


@router.post("/")
async def generate(
    input_prompt: str = Form(...),
    reference_image: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    try:
        user = request.state.user  # extracted by middleware

        # Ensure upload folder exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save the uploaded file
        file_ext = reference_image.filename.split(".")[-1]
        filename = f"{uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await reference_image.read())
    
        relative_path = f"uploads/{filename}"
        
        output_dir = generate_3d(file_path)
    # Save path to DB (not file itself)
        session = GenerationSession(
            user_id=user.user_id,
            reference_image=relative_path,
            input_prompt=input_prompt,
            output_directory=output_dir
         )

        db.add(session)
        db.commit()
        db.refresh(session)

        return success_response(
        "Generation session created successfully",
        data={
            "session_id": session.session_id,
            "reference_image": relative_path,
             "output_dir": output_dir
        },
        status_code=201
  
         )
    except Exception as e:
        # Capture any unexpected error and return detailed message in development
     return error_response(
            message="Failed to create generation session",
            dev_message=str(e),   # 🔥 this shows detailed reason if ENVIRONMENT=development
            status_code=500
        )