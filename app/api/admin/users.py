from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse
from app.core.security import get_password_hash
from app.utils.dependencies import get_institute_admin
from app.utils.audit import log_audit_event, AuditAction
from app.utils.pagination import PaginatedResponse, create_paginated_response

router = APIRouter(prefix="/users", tags=["admin-users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Create a new user in the institute (Institute Admin only)."""
    # Get institute_id from request state (resolved by middleware)
    institute_id = request.state.institute_id
    
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Institute admin can only create ADMIN users in their own institute
    if user_data.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Institute admin can only create ADMIN users"
        )
    
    user = User(
        institute_id=institute_id,
        name=user_data.name,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Log audit event
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action=AuditAction.USER_CREATED,
        request=request,
        details=f"Created {user_data.role.value} user: {user_data.email}"
    )
    
    return user


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of items to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_institute_admin)
):
    """List all admin users in the institute with pagination (Institute Admin only)."""
    institute_id = request.state.institute_id
    
    query = db.query(User).filter(
        User.institute_id == institute_id,
        User.role == UserRole.ADMIN
    )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return create_paginated_response(
        items=[UserResponse(**u.__dict__) for u in users],
        total=total,
        skip=skip,
        limit=limit
    )
