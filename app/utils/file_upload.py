import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings


class FileUploadService:
    """Service for handling file uploads."""
    
    # Allowed file types for assignments
    ALLOWED_ASSIGNMENT_TYPES = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain',
        'image/jpeg',
        'image/png',
        'image/gif',
    }
    
    # Allowed file types for submissions
    ALLOWED_SUBMISSION_TYPES = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain',
        'image/jpeg',
        'image/png',
        'image/gif',
        'application/zip',
        'application/x-zip-compressed',
    }
    
    # Max file size: 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    
    @staticmethod
    def get_upload_directory() -> Path:
        """Get the base upload directory."""
        upload_dir = Path(settings.UPLOAD_DIR if hasattr(settings, 'UPLOAD_DIR') else 'uploads')
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir
    
    @staticmethod
    def validate_file(
        file: UploadFile,
        allowed_types: Optional[set] = None,
        max_size: Optional[int] = None
    ) -> None:
        """Validate uploaded file."""
        if allowed_types is None:
            allowed_types = FileUploadService.ALLOWED_SUBMISSION_TYPES
        
        if max_size is None:
            max_size = FileUploadService.MAX_FILE_SIZE
        
        # Check file type
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Note: file.size might not be available until we read the file
        # We'll check size after reading
    
    @staticmethod
    async def save_file(
        file: UploadFile,
        directory: str,
        allowed_types: Optional[set] = None,
        max_size: Optional[int] = None,
        base_url: Optional[str] = None
    ) -> dict:
        """
        Save uploaded file and return file info.
        
        Returns:
            dict with keys: filename, file_path, file_url, file_size, content_type
        """
        if allowed_types is None:
            allowed_types = FileUploadService.ALLOWED_SUBMISSION_TYPES
        
        if max_size is None:
            max_size = FileUploadService.MAX_FILE_SIZE
        
        # Validate file type
        FileUploadService.validate_file(file, allowed_types, max_size)
        
        # Read file content to check size
        content = await file.read()
        file_size = len(content)
        
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {max_size / (1024 * 1024):.1f}MB"
            )
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix if file.filename else '.bin'
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Create directory if it doesn't exist
        upload_dir = FileUploadService.get_upload_directory()
        target_dir = upload_dir / directory
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = target_dir / unique_filename
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Generate URL - use absolute URL if base_url provided, otherwise relative
        if base_url:
            # Remove trailing slash from base_url if present
            base_url = base_url.rstrip('/')
            file_url = f"{base_url}/uploads/{directory}/{unique_filename}"
        else:
            file_url = f"/uploads/{directory}/{unique_filename}"
        
        return {
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": str(file_path),
            "file_url": file_url,
            "file_size": file_size,
            "content_type": file.content_type
        }
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete a file from the filesystem."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception:
            return False
