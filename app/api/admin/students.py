from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.schemas.user import StudentCreate, StudentUpdate, StudentResponse
from app.core.security import get_password_hash
from app.utils.dependencies import get_institute_admin
from app.utils.permissions import require_permission
from app.utils.pagination import PaginatedResponse, create_paginated_response

router = APIRouter(prefix="/students", tags=["admin-students"])


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users", "create"))
):
    """Create a new student (Institute Admin only)."""
    institute_id = request.state.institute_id
    
    # Check if email already exists
    existing = db.query(User).filter(User.email == student_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    student = User(
        institute_id=institute_id,
        name=student_data.name,
        email=student_data.email,
        password_hash=get_password_hash(student_data.password),
        role=UserRole.STUDENT,
        is_active=True
    )
    
    db.add(student)
    db.commit()
    db.refresh(student)
    
    # Return with empty class info (not enrolled yet)
    student_dict = student.__dict__.copy()
    student_dict['class_name'] = None
    student_dict['class_id'] = None
    return StudentResponse(**student_dict)


@router.get("", response_model=PaginatedResponse[StudentResponse])
async def list_students(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of items to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_permission("users", "view"))
):
    """List all students in the institute with pagination (Institute Admin only)."""
    institute_id = request.state.institute_id
    
    query = db.query(User).filter(
        User.institute_id == institute_id,
        User.role == UserRole.STUDENT
    )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    students = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    # Get enrollment information for each student
    from app.db.models.enrollment import Enrollment
    from app.db.models.class_model import Class
    
    student_responses = []
    for student in students:
        # Get student's enrollment (most recent if multiple)
        enrollment = db.query(Enrollment).filter(
            Enrollment.student_id == student.id
        ).order_by(Enrollment.enrolled_at.desc()).first()
        
        class_name = None
        class_id = None
        if enrollment:
            class_obj = db.query(Class).filter(Class.id == enrollment.class_id).first()
            if class_obj:
                class_name = class_obj.name
                class_id = class_obj.id
        
        student_dict = student.__dict__.copy()
        student_dict['class_name'] = class_name
        student_dict['class_id'] = class_id
        student_responses.append(StudentResponse(**student_dict))
    
    return create_paginated_response(
        items=student_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get a specific student (Institute Admin only)."""
    institute_id = request.state.institute_id
    
    student = db.query(User).filter(
        User.id == student_id,
        User.institute_id == institute_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get enrollment information
    from app.db.models.enrollment import Enrollment
    from app.db.models.class_model import Class
    
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student.id
    ).order_by(Enrollment.enrolled_at.desc()).first()
    
    class_name = None
    class_id = None
    if enrollment:
        class_obj = db.query(Class).filter(Class.id == enrollment.class_id).first()
        if class_obj:
            class_name = class_obj.name
            class_id = class_obj.id
    
    student_dict = student.__dict__.copy()
    student_dict['class_name'] = class_name
    student_dict['class_id'] = class_id
    return StudentResponse(**student_dict)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student_data: StudentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users", "edit"))
):
    """Update a student (Institute Admin only)."""
    institute_id = request.state.institute_id
    
    student = db.query(User).filter(
        User.id == student_id,
        User.institute_id == institute_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if email is being changed and if it already exists
    if student_data.email and student_data.email != student.email:
        existing = db.query(User).filter(
            User.email == student_data.email,
            User.id != student_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Update fields
    if student_data.name is not None:
        student.name = student_data.name
    if student_data.email is not None:
        student.email = student_data.email
    if student_data.password is not None:
        student.password_hash = get_password_hash(student_data.password)
    if student_data.is_active is not None:
        student.is_active = student_data.is_active
    
    db.commit()
    db.refresh(student)
    
    # Get enrollment information
    from app.db.models.enrollment import Enrollment
    from app.db.models.class_model import Class
    
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student.id
    ).order_by(Enrollment.enrolled_at.desc()).first()
    
    class_name = None
    class_id = None
    if enrollment:
        class_obj = db.query(Class).filter(Class.id == enrollment.class_id).first()
        if class_obj:
            class_name = class_obj.name
            class_id = class_obj.id
    
    student_dict = student.__dict__.copy()
    student_dict['class_name'] = class_name
    student_dict['class_id'] = class_id
    return StudentResponse(**student_dict)
