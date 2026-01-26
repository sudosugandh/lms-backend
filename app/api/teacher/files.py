from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.utils.dependencies import get_teacher
from app.utils.file_upload import FileUploadService

router = APIRouter(prefix="/files", tags=["teacher-files"])


@router.post("/assignments/upload")
async def upload_assignment_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Upload a file for an assignment (Teacher only)."""
    try:
        # Get base URL from request
        base_url = str(request.base_url).rstrip('/')
        file_info = await FileUploadService.save_file(
            file=file,
            directory="assignments",
            allowed_types=FileUploadService.ALLOWED_ASSIGNMENT_TYPES,
            base_url=base_url
        )
        return {
            "success": True,
            "file_url": file_info["file_url"],
            "filename": file_info["filename"],
            "original_filename": file_info["original_filename"],
            "file_size": file_info["file_size"],
            "content_type": file_info["content_type"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
