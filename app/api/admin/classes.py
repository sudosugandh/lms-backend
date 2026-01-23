from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.class_model import ClassCreate, ClassUpdate, ClassResponse, SubjectCreate, SubjectUpdate, SubjectResponse, ClassSubjectCreate, ClassSubjectResponse, EnrollmentCreate, EnrollmentResponse
from app.services.class_service import ClassService, SubjectService, ClassSubjectService, EnrollmentService
from app.utils.dependencies import get_institute_admin
from app.utils.permissions import require_permission
from app.utils.pagination import PaginatedResponse, PaginationParams, create_paginated_response

router = APIRouter(prefix="/classes", tags=["admin-classes"])


@router.post("", response_model=ClassResponse, status_code=201)
async def create_class(
    class_data: ClassCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("classes", "create"))
):
    """Create a new class (Institute Admin only)."""
    institute_id = request.state.institute_id
    return ClassService.create_class(db, institute_id, class_data)


@router.get("", response_model=PaginatedResponse[ClassResponse])
async def list_classes(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of items to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_permission("classes", "view"))
):
    """List all classes in the institute with pagination (Institute Admin only)."""
    institute_id = request.state.institute_id
    classes, total = ClassService.get_classes(db, institute_id, skip, limit, is_active)
    
    return create_paginated_response(
        items=[ClassResponse(**c.__dict__) for c in classes],
        total=total,
        skip=skip,
        limit=limit
    )


# IMPORTANT: Subject routes must be defined BEFORE /{class_id} route
# to avoid route matching conflicts (FastAPI matches routes in order)
@router.post("/subjects", response_model=SubjectResponse, status_code=201)
async def create_subject(
    subject_data: SubjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("subjects", "create"))
):
    """Create a new subject (Institute Admin only)."""
    institute_id = request.state.institute_id
    return SubjectService.create_subject(db, institute_id, subject_data)


@router.get("/subjects", response_model=PaginatedResponse[SubjectResponse])
async def list_subjects(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin),  # Move before query params
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = Query(None)
):
    """List all subjects in the institute with pagination (Institute Admin only)."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get institute_id from request state (set by tenant middleware)
        institute_id = getattr(request.state, 'institute_id', None)
        if not institute_id:
            logger.error("institute_id not found in request.state")
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Institute not resolved"
            )
        
        logger.info(f"Listing subjects for institute_id={institute_id}, skip={skip}, limit={limit}, is_active={is_active}, user_id={current_user.id}, user_role={current_user.role}")
        
        subjects, total = SubjectService.get_subjects(db, institute_id, skip, limit, is_active)
        logger.info(f"Found {len(subjects)} subjects, total={total}")
        
        # Convert subjects to response format using from_attributes
        subject_responses = [SubjectResponse.model_validate(s) for s in subjects]
        
        response = create_paginated_response(
            items=subject_responses,
            total=total,
            skip=skip,
            limit=limit
        )
        logger.info(f"Returning response with {len(response.items)} items")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing subjects: {type(e).__name__}: {e}", exc_info=True)
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching subjects: {str(e)}"
        )


# IMPORTANT: Subject-specific routes with sub-paths must be defined BEFORE /subjects/{subject_id} route
# to avoid route matching conflicts (FastAPI matches routes in order)
@router.get("/subjects/{subject_id}/classes", response_model=List[ClassSubjectResponse])
async def get_subject_classes(
    subject_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get all classes assigned to a subject with their teachers (Institute Admin only)."""
    institute_id = request.state.institute_id
    
    # Verify subject belongs to institute
    SubjectService.get_subject(db, subject_id, institute_id)
    
    # Get all class-subject assignments for this subject
    from app.db.models.class_subject import ClassSubject
    class_subjects = db.query(ClassSubject).filter(
        ClassSubject.subject_id == subject_id
    ).all()
    
    # Verify all classes belong to the institute
    class_ids = [cs.class_id for cs in class_subjects]
    if class_ids:
        classes = db.query(Class).filter(
            Class.id.in_(class_ids),
            Class.institute_id == institute_id
        ).all()
        valid_class_ids = {c.id for c in classes}
        class_subjects = [cs for cs in class_subjects if cs.class_id in valid_class_ids]
    
    # Format response with teacher and class names
    from app.db.models.subject import Subject
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    subject_name = subject.name if subject else None
    
    result = []
    for cs in class_subjects:
        teacher_name = None
        if cs.teacher_id:
            teacher = db.query(User).filter(User.id == cs.teacher_id).first()
            if teacher:
                teacher_name = teacher.name
        
        class_obj = db.query(Class).filter(Class.id == cs.class_id).first()
        class_name = class_obj.name if class_obj else None
        
        result.append(ClassSubjectResponse(
            id=cs.id,
            class_id=cs.class_id,
            subject_id=cs.subject_id,
            teacher_id=cs.teacher_id,
            teacher_name=teacher_name,
            class_name=class_name,
            subject_name=subject_name
        ))
    
    return result


@router.get("/subjects/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get a specific subject (Institute Admin only)."""
    institute_id = request.state.institute_id
    return SubjectService.get_subject(db, subject_id, institute_id)


@router.put("/subjects/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int,
    subject_data: SubjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("subjects", "edit"))
):
    """Update a subject (Institute Admin only)."""
    institute_id = request.state.institute_id
    return SubjectService.update_subject(db, subject_id, institute_id, subject_data)


# Class-specific routes (must be after /subjects routes to avoid conflicts)
@router.post("/assign-subject", response_model=ClassSubjectResponse, status_code=201)
async def assign_subject_to_class(
    assignment_data: ClassSubjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Assign a subject to a class with optional teacher (Institute Admin only)."""
    institute_id = request.state.institute_id
    assignment = ClassSubjectService.assign_subject_to_class(db, institute_id, assignment_data)
    
    # Include teacher name in response
    teacher_name = None
    if assignment.teacher_id:
        teacher = db.query(User).filter(User.id == assignment.teacher_id).first()
        if teacher:
            teacher_name = teacher.name
    
    response_data = ClassSubjectResponse(
        id=assignment.id,
        class_id=assignment.class_id,
        subject_id=assignment.subject_id,
        teacher_id=assignment.teacher_id,
        teacher_name=teacher_name
    )
    return response_data


# IMPORTANT: Class-specific routes with sub-paths must be defined BEFORE /{class_id} route
# to avoid route matching conflicts (FastAPI matches routes in order)
@router.get("/{class_id}/subjects", response_model=List[ClassSubjectResponse])
async def get_class_subjects(
    class_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get all subjects assigned to a class with their teachers (Institute Admin only)."""
    institute_id = request.state.institute_id
    class_subjects = ClassSubjectService.get_class_subjects(db, class_id, institute_id)
    
    # Format response with teacher names
    result = []
    for cs in class_subjects:
        teacher_name = None
        if cs.teacher_id:
            teacher = db.query(User).filter(User.id == cs.teacher_id).first()
            if teacher:
                teacher_name = teacher.name
        
        result.append(ClassSubjectResponse(
            id=cs.id,
            class_id=cs.class_id,
            subject_id=cs.subject_id,
            teacher_id=cs.teacher_id,
            teacher_name=teacher_name
        ))
    
    return result


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get a specific class (Institute Admin only)."""
    institute_id = request.state.institute_id
    return ClassService.get_class(db, class_id, institute_id)


@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: int,
    class_data: ClassUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("classes", "edit"))
):
    """Update a class (Institute Admin only)."""
    institute_id = request.state.institute_id
    return ClassService.update_class(db, class_id, institute_id, class_data)


@router.post("/enrollments", response_model=EnrollmentResponse, status_code=201)
async def enroll_student(
    enrollment_data: EnrollmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Enroll a student in a class (Institute Admin only)."""
    institute_id = request.state.institute_id
    enrollment = EnrollmentService.enroll_student(db, institute_id, enrollment_data)
    
    # Include names in response
    student = db.query(User).filter(User.id == enrollment.student_id).first()
    class_obj = db.query(ClassService.get_class(db, enrollment.class_id, institute_id))
    
    from app.db.models.class_model import Class
    class_obj = db.query(Class).filter(Class.id == enrollment.class_id).first()
    
    return EnrollmentResponse(
        id=enrollment.id,
        student_id=enrollment.student_id,
        class_id=enrollment.class_id,
        enrolled_at=enrollment.enrolled_at,
        student_name=student.name if student else "",
        class_name=class_obj.name if class_obj else ""
    )
