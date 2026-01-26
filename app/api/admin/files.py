from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.utils.dependencies import get_institute_admin
from app.utils.file_upload import FileUploadService

router = APIRouter(prefix="/files", tags=["admin-files"])


@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = "general",  # general, assignment, quiz, profile, certificate
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """
    Upload a file (Admin only).
    
    file_type options:
    - general: General purpose files
    - assignment: Assignment attachments
    - quiz: Quiz attachments
    - profile: Profile pictures
    - certificate: Certificate templates
    """
    institute_id = request.state.institute_id
    
    # Define allowed types based on file_type
    allowed_types_map = {
        "general": FileUploadService.ALLOWED_SUBMISSION_TYPES,
        "assignment": FileUploadService.ALLOWED_ASSIGNMENT_TYPES,
        "quiz": FileUploadService.ALLOWED_SUBMISSION_TYPES,
        "profile": {'image/jpeg', 'image/png', 'image/gif', 'image/webp'},
        "certificate": {'image/jpeg', 'image/png', 'application/pdf'},
    }
    
    allowed_types = allowed_types_map.get(file_type, FileUploadService.ALLOWED_SUBMISSION_TYPES)
    
    # Save file
    base_url = str(request.base_url).rstrip('/')
    file_info = await FileUploadService.save_file(
        file,
        directory=f"files/{institute_id}/{file_type}",
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
    file_type: str = "general",
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """
    Upload multiple files at once (Admin only).
    """
    institute_id = request.state.institute_id
    
    # Define allowed types based on file_type
    allowed_types_map = {
        "general": FileUploadService.ALLOWED_SUBMISSION_TYPES,
        "assignment": FileUploadService.ALLOWED_ASSIGNMENT_TYPES,
        "quiz": FileUploadService.ALLOWED_SUBMISSION_TYPES,
        "profile": {'image/jpeg', 'image/png', 'image/gif', 'image/webp'},
        "certificate": {'image/jpeg', 'image/png', 'application/pdf'},
    }
    
    allowed_types = allowed_types_map.get(file_type, FileUploadService.ALLOWED_SUBMISSION_TYPES)
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
