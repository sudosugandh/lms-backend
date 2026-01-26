from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.utils.dependencies import get_teacher
from app.utils.file_upload import FileUploadService

router = APIRouter(prefix="/files", tags=["teacher-files"])


@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = "assignment",  # assignment, quiz, profile
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """
    Upload a file (Teacher only).
    
    file_type options:
    - assignment: Assignment attachments
    - quiz: Quiz attachments
    - profile: Profile pictures
    """
    institute_id = request.state.institute_id
    
    # Define allowed types based on file_type
    allowed_types_map = {
        "assignment": FileUploadService.ALLOWED_ASSIGNMENT_TYPES,
        "quiz": FileUploadService.ALLOWED_SUBMISSION_TYPES,
        "profile": {'image/jpeg', 'image/png', 'image/gif', 'image/webp'},
    }
    
    allowed_types = allowed_types_map.get(file_type, FileUploadService.ALLOWED_ASSIGNMENT_TYPES)
    
    # Save file
    base_url = str(request.base_url).rstrip('/')
    directory = f"files/{institute_id}/{file_type}" if file_type != "profile" else f"files/{institute_id}/profile"
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


@router.post("/upload-multiple", response_model=List[dict])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    file_type: str = "assignment",
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """
    Upload multiple files at once (Teacher only).
    """
    institute_id = request.state.institute_id
    
    allowed_types_map = {
        "assignment": FileUploadService.ALLOWED_ASSIGNMENT_TYPES,
        "quiz": FileUploadService.ALLOWED_SUBMISSION_TYPES,
        "profile": {'image/jpeg', 'image/png', 'image/gif', 'image/webp'},
    }
    
    allowed_types = allowed_types_map.get(file_type, FileUploadService.ALLOWED_ASSIGNMENT_TYPES)
    base_url = str(request.base_url).rstrip('/')
    
    uploaded_files = []
    errors = []
    
    for file in files:
        try:
            file_info = await FileUploadService.save_file(
                file,
                directory=f"files/{institute_id}/{file_type}",
                allowed_types=allowed_types,
                max_size=FileUploadService.MAX_FILE_SIZE,
                base_url=base_url
            )
            uploaded_files.append({
                "file_url": file_info['file_url'],
                "filename": file_info['filename'],
                "original_filename": file_info['original_filename'],
                "file_size": file_info['file_size'],
                "content_type": file_info['content_type']
            })
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    if errors and not uploaded_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload files: {errors}"
        )
    
    return uploaded_files
