from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.utils.dependencies import get_student
from app.utils.file_upload import FileUploadService

router = APIRouter(prefix="/files", tags=["student-files"])


@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = "submission",  # submission, profile
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """
    Upload a file (Student only).
    
    file_type options:
    - submission: Assignment submission files
    - profile: Profile pictures
    """
    institute_id = request.state.institute_id
    
    # Define allowed types based on file_type
    allowed_types_map = {
        "submission": FileUploadService.ALLOWED_SUBMISSION_TYPES,
        "profile": {'image/jpeg', 'image/png', 'image/gif', 'image/webp'},
    }
    
    allowed_types = allowed_types_map.get(file_type, FileUploadService.ALLOWED_SUBMISSION_TYPES)
    
    # Save file
    base_url = str(request.base_url).rstrip('/')
    directory = f"files/{institute_id}/submissions" if file_type == "submission" else f"files/{institute_id}/profile"
    file_info = await FileUploadService.save_file(
        file,
        directory=directory,
        allowed_types=allowed_types,
        max_size=FileUploadService.MAX_FILE_SIZE,
        base_url=base_url
    )
    
    return {
        "file_url": file_info['file_url'],
        "filename": file_info['filename'],
        "original_filename": file_info['original_filename'],
        "file_size": file_info['file_size'],
        "content_type": file_info['content_type']
    }
