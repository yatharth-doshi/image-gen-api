from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from fastapi import HTTPException
import shutil
from app.helper.response_helper import success_response, error_response
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.image_model import generate_3d, login_hf

from app.models import GenerationSession, User
import os
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/generate", tags=["generation"])

UPLOAD_DIR = "app/uploads"
OUTPUT_DIR = "app/outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)



HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("Missing HF_TOKEN in environment variables")
login_hf(HF_TOKEN)


@router.post("/")
async def generate(
    input_prompt: str = Form(...),
    reference_image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user = current_user  # extracted by middleware

        # Ensure upload folder exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Save the uploaded file
        file_ext = reference_image.filename.split(".")[-1]
        filename = f"{uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await reference_image.read())
    
        relative_path = f"uploads/{filename}"
        output_filename = f"{uuid4()}.png"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # Generate the image
        relative_output_path = generate_3d(file_path, output_path)
        # Save path to DB (not file itself)
        session = GenerationSession(
            user_id=user.user_id,
            reference_image=relative_path,
            input_prompt=input_prompt,
            output_path=relative_output_path
         )

        db.add(session)
        db.commit()
        db.refresh(session)

        return success_response(
            "Generation session created successfully",
            data={
                "session_id": session.session_id,
                "reference_image": relative_path,
                "temp_output_dir":relative_output_path
            },
            status_code=200
        )
    except Exception as e:
        # Capture any unexpected error and return detailed message in development
        return error_response(
            message="Failed to create generation session",
            dev_message=str(e), 
            status_code=500
        )

@router.post("/approve/{session_id}")
def approve_generated_image(session_id: int, db: Session = Depends(get_db)):
    """
    Approves the generated image: move the single file from temp_output to outputs and update DB.
    """
    try:
        session = db.query(GenerationSession).filter(GenerationSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        session.approved = True
        db.commit()

        return success_response(
            "Image approved successfully",
            data={
                "session_id": session.session_id,
                "final_output_image": session.output_path
            }
        )
    except Exception as e:
        return error_response("Failed to approve image", dev_message=str(e), status_code=500)
    


@router.post("/change/{session_id}")
async def regenerate_image_with_new_prompt(
    session_id: int,
    new_prompt: str = Form(...),
    reference_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Allows user to request a new generation using a modified prompt.
    """
    try:
        session = db.query(GenerationSession).filter(GenerationSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Determine reference image (new or existing)
        if reference_image:
            file_ext = reference_image.filename.split(".")[-1]
            filename = f"{uuid4()}.{file_ext}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, "wb") as buffer:
                buffer.write(await reference_image.read())
            relative_path = f"uploads/{filename}"
        else:
            relative_path = session.reference_image  # use previous image

        # Generate again
        full_output_path = os.path.join("app", session.output_path)
        new_output_path = generate_3d(os.path.join("app", relative_path),  full_output_path)


        # Update DB
        session.input_prompt = new_prompt
        session.reference_image = relative_path
        session.output_path = new_output_path
        session.attempts += 1
        session.approved = False
        db.commit()

        return success_response(
            "New image generated successfully",
            data={
                "session_id": session.session_id,
                "reference_image": relative_path,
                "new_output_dir": new_output_path,
                "attempts": session.attempts
            }
        )
    except Exception as e:
        return error_response("Failed to regenerate image", dev_message=str(e), status_code=500)

    
@router.get("/list")
def get_all_generations(current_user: User = Depends(get_current_user),  db: Session = Depends(get_db)):
    """
    Fetch all generation sessions.
    - Normal users: only their own sessions
    - Admin/SuperAdmin: all sessions
    """
    try:
       
        if current_user.user_type in [1, 2]:  # 1=SuperAdmin, 2=Admin
            sessions = db.query(GenerationSession).all()
        else:
            # Normal user sees only their own
            sessions = db.query(GenerationSession).filter(
                GenerationSession.user_id == current_user.user_id
            ).all()

        if not sessions:
            return success_response("No generation sessions found", data=[])

        results = []
        for s in sessions:
            results.append({
                "session_id": s.session_id,
                "user_id": s.user_id,
                "input_prompt": s.input_prompt,
                "reference_image": s.reference_image,
                "output_path": s.output_path,
                "approved": s.approved,
                "attempts": s.attempts,
                "created_at": s.created_at.isoformat() if s.created_at else None
            })

        return success_response("Generation sessions fetched successfully", results)

    except Exception as e:
        return error_response("Failed to fetch generation sessions", dev_message=str(e))
