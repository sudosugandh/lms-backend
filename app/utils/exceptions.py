"""
Custom exceptions and error handling utilities.
"""
from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class BaseAPIException(HTTPException):
    """Base API exception with consistent error format."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        error_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize API exception.
        
        Args:
            status_code: HTTP status code
            detail: Error message
            error_code: Machine-readable error code (optional)
            error_data: Additional error data (optional)
        """
        self.error_code = error_code
        self.error_data = error_data
        
        # Format error response
        error_response = {
            "detail": detail,
        }
        
        if error_code:
            error_response["error_code"] = error_code
        
        if error_data:
            error_response["error_data"] = error_data
        
        super().__init__(status_code=status_code, detail=error_response)


class NotFoundException(BaseAPIException):
    """Resource not found exception."""
    
    def __init__(self, resource: str, resource_id: Optional[int] = None):
        """
        Initialize not found exception.
        
        Args:
            resource: Resource name (e.g., "User", "Class")
            resource_id: Resource ID (optional)
        """
        detail = f"{resource} not found"
        if resource_id is not None:
            detail += f" (ID: {resource_id})"
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND"
        )


class UnauthorizedException(BaseAPIException):
    """Unauthorized access exception."""
    
    def __init__(self, detail: str = "Unauthorized access"):
        """
        Initialize unauthorized exception.
        
        Args:
            detail: Error message
        """
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )


class ForbiddenException(BaseAPIException):
    """Forbidden access exception."""
    
    def __init__(self, detail: str = "Access forbidden"):
        """
        Initialize forbidden exception.
        
        Args:
            detail: Error message
        """
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )


class ValidationException(BaseAPIException):
    """Validation error exception."""
    
    def __init__(self, detail: str, errors: Optional[Dict[str, Any]] = None):
        """
        Initialize validation exception.
        
        Args:
            detail: Error message
            errors: Field-specific validation errors (optional)
        """
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_ERROR",
            error_data={"errors": errors} if errors else None
        )


class ConflictException(BaseAPIException):
    """Resource conflict exception."""
    
    def __init__(self, detail: str):
        """
        Initialize conflict exception.
        
        Args:
            detail: Error message
        """
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT"
        )


class InternalServerException(BaseAPIException):
    """Internal server error exception."""
    
    def __init__(self, detail: str = "An internal error occurred"):
        """
        Initialize internal server exception.
        
        Args:
            detail: Error message
        """
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="INTERNAL_ERROR"
        )
