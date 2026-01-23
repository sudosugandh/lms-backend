from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.core.security import decode_access_token


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    authorization = request.headers.get("authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


def get_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user is a super admin."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user


def get_institute_admin(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user is an institute admin and validate institute match."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # For admin, institute_id must match resolved institute
    resolved_institute_id = getattr(request.state, "institute_id", None)
    
    if not resolved_institute_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institute not resolved"
        )
    
    if current_user.institute_id != resolved_institute_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Institute mismatch"
        )
    
    return current_user


def get_institute_user(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user belongs to an institute (ADMIN, TEACHER, STUDENT, or PARENT)."""
    if current_user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin cannot access institute resources"
        )
    
    resolved_institute_id = getattr(request.state, "institute_id", None)
    
    if not resolved_institute_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institute not resolved"
        )
    
    if current_user.institute_id != resolved_institute_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Institute mismatch"
        )
    
    return current_user


def get_teacher(
    request: Request,
    current_user: User = Depends(get_institute_user)
) -> User:
    """Ensure current user is a teacher."""
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )
    
    return current_user


def get_student(
    request: Request,
    current_user: User = Depends(get_institute_user)
) -> User:
    """Ensure current user is a student."""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )
    
    return current_user


def get_parent(
    request: Request,
    current_user: User = Depends(get_institute_user)
) -> User:
    """Ensure current user is a parent."""
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent access required"
        )
    
    return current_user
