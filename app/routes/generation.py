from fastapi import APIRouter, Depends, File, Form, UploadFile
from typing import Optional
from fastapi import HTTPException
from app.helper.response_helper import success_response, error_response
from app.helper.runpod_helper import submit_job, wait_for_output
from app.helper.s3_helper import s3_helper
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user

from app.models import GenerationSession, User
import os
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/generate", tags=["generation"])

@router.post("/")
async def generate(
    input_prompt: str = Form(...),
    reference_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        reference_s3_key = None

        if reference_image:

            reference_s3_key = s3_helper.upload_file(
                    reference_image, 
                    folder = "image-generation"
            )
    
        referenece_image_url = reference_s3_key["s3_key"]
    
        job_id = await submit_job(input_prompt, referenece_image_url)  
        runpod_result = await wait_for_output(job_id)
        

        generated_image_url = runpod_result.get("image_key", "")   
        
        session = GenerationSession(
            user_id= current_user.user_id,
            reference_image= referenece_image_url,
            input_prompt=input_prompt,
            output_path= generated_image_url,
            approved=False,
            attempts=1
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return success_response(
            "Generation session created successfully",
            data= {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "reference_image" : referenece_image_url,
                "input_prompt": session.input_prompt,
                "output_path": session.output_path,
                "approved": session.approved,
                "attempts": session.attempts,
                "created_at": str(session.created_at),
                "updated_at": str(session.updated_at)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows user to request a new generation using a modified prompt.
    """
    try:
        session = db.query(GenerationSession).filter(GenerationSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        previous_image = session.output_path
        if not previous_image:
            return error_response(
                "No previous image exists for this session",
                status_code=400
            )
        
        if previous_image:

            previous_image_s3_key = s3_helper.upload_file(
                    previous_image, 
                    folder = "image-generation"
            )

        new_image_url = previous_image_s3_key["s3_key"]

        job_id = await submit_job(new_prompt,new_image_url)
        runpod_result = await wait_for_output(job_id)
       

        new_image_url = runpod_result.get("image_url", "")


        # Update DB
        session.input_prompt = new_prompt
        session.reference_image = previous_image
        session.output_path = runpod_result.get("image_url", "")
        session.attempts += 1
        session.approved = False
        db.commit()

        return success_response(
            "New image generated successfully",
            data={
                "session_id": session.session_id,
                "reference_image": previous_image,
                "new_output_dir": new_image_url,
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
        
        session_data = []

        for s in sessions:

            user = db.query(User).filter(User.user_id == s.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            user_details = {
                "user_id": user.user_id,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "email": user.email,
                "user_type": user.user_type
            }

            session_data.append({
                "session_id": s.session_id,
                "user_id": s.user_id,
                "input_prompt": s.input_prompt,
                "reference_image": s.reference_image,
                "output_path": s.output_path,
                "approved": s.approved,
                "attempts": s.attempts,
                "created_at": str(s.created_at),
                "updated_at": str(s.updated_at),
                "user_details" : user_details
            })

        return success_response(
            "Generation sessions fetched successfully",
            data= session_data
        )

    except Exception as e:
        return error_response("Failed to fetch generation sessions", dev_message=str(e))


@router.get("/user/details/{session_id}")
def get_user_with_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetch user details along with a specific session's details.
    """
    try:
        
        session = db.query(GenerationSession).filter(
            GenerationSession.session_id == session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Fetch the user who created the session
        user = db.query(User).filter(User.user_id == session.user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # User details object
        user_details = {
            "user_id": user.user_id,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "email": user.email,
            "user_type": user.user_type
        }

        # Session details for this specific session
        session_details = {
            "session_id": session.session_id,
            "input_prompt": session.input_prompt,
            "reference_image": session.reference_image,
            "output_path": session.output_path,
            "approved": session.approved,
            "attempts": session.attempts,
            "created_at": str(session.created_at),
            "updated_at": str(session.updated_at),
            "user_details" : user_details
        }

        return success_response(
            "User details with session fetched successfully",
            data= session_details
        )

    except Exception as e:
        return error_response(
            "Failed to fetch user/session details",
            dev_message=str(e),
            status_code=500
        )
