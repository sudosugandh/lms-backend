from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.schemas.user import TeacherCreate, TeacherUpdate, TeacherResponse
from app.core.security import get_password_hash
from app.utils.dependencies import get_institute_admin
from app.utils.permissions import require_permission
from app.utils.pagination import PaginatedResponse, create_paginated_response

router = APIRouter(prefix="/teachers", tags=["admin-teachers"])


@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_data: TeacherCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users", "create"))
):
    """Create a new teacher (Institute Admin only)."""
    institute_id = request.state.institute_id
    
    # Check if email already exists
    existing = db.query(User).filter(User.email == teacher_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    teacher = User(
        institute_id=institute_id,
        name=teacher_data.name,
        email=teacher_data.email,
        password_hash=get_password_hash(teacher_data.password),
        role=UserRole.TEACHER,
        is_active=True
    )
    
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    
    return teacher


@router.get("", response_model=PaginatedResponse[TeacherResponse])
async def list_teachers(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of items to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_permission("users", "view"))
):
    """List all teachers in the institute with pagination (Institute Admin only)."""
    institute_id = request.state.institute_id
    
    query = db.query(User).filter(
        User.institute_id == institute_id,
        User.role == UserRole.TEACHER
    )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    teachers = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return create_paginated_response(
        items=[TeacherResponse(**t.__dict__) for t in teachers],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get a specific teacher (Institute Admin only)."""
    institute_id = request.state.institute_id
    
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.institute_id == institute_id,
        User.role == UserRole.TEACHER
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    return teacher


@router.put("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users", "edit"))
):
    """Update a teacher (Institute Admin only)."""
    institute_id = request.state.institute_id
    
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.institute_id == institute_id,
        User.role == UserRole.TEACHER
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    # Check if email is being changed and if it already exists
    if teacher_data.email and teacher_data.email != teacher.email:
        existing = db.query(User).filter(
            User.email == teacher_data.email,
            User.id != teacher_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Update fields
    if teacher_data.name is not None:
        teacher.name = teacher_data.name
    if teacher_data.email is not None:
        teacher.email = teacher_data.email
    if teacher_data.password is not None:
        teacher.password_hash = get_password_hash(teacher_data.password)
    if teacher_data.is_active is not None:
        teacher.is_active = teacher_data.is_active
    
    db.commit()
    db.refresh(teacher)
    return teacher
