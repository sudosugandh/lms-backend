"""
Permission checking utilities and decorators.
"""
from functools import wraps
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.services.permission_service import PermissionService
from app.utils.dependencies import get_current_user


def require_permission(module: str, action: str):
    """
    Dependency factory for requiring a specific permission.
    
    Usage:
        @router.get("/users")
        async def list_users(
            current_user: User = Depends(require_permission("users", "view")),
            db: Session = Depends(get_db)
        ):
            ...
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not PermissionService.user_has_permission(db, current_user, module, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {module}.{action}"
            )
        return current_user
    
    return permission_checker


def check_permission(user: User, db: Session, module: str, action: str) -> bool:
    """
    Helper function to check if user has permission.
    Returns True/False instead of raising exception.
    """
    return PermissionService.user_has_permission(db, user, module, action)
