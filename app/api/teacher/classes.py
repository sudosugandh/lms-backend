from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Set
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.enrollment import Enrollment
from app.db.models.class_model import Class
from app.schemas.class_model import ClassSubjectResponse, EnrollmentResponse, ClassResponse, SubjectResponse
from app.services.class_service import ClassSubjectService, ClassService
from app.utils.dependencies import get_teacher

router = APIRouter(prefix="/classes", tags=["teacher-classes"])


@router.get("", response_model=List[ClassResponse])
async def get_teacher_classes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Get all classes assigned to the current teacher."""
    institute_id = request.state.institute_id
    assignments = ClassSubjectService.get_teacher_assignments(
        db, current_user.id, institute_id
    )
    
    # Get unique class IDs
    class_ids: Set[int] = {a.class_id for a in assignments}
    
    if not class_ids:
        return []
    
    # Get class objects
    classes = db.query(Class).filter(
        Class.id.in_(class_ids),
        Class.institute_id == institute_id
    ).all()
    
    # Format response
    result = []
    for class_obj in classes:
        result.append(ClassResponse(
            id=class_obj.id,
            name=class_obj.name,
            code=class_obj.code,
            description=class_obj.description,
            is_active=class_obj.is_active,
            institute_id=class_obj.institute_id,
            created_at=class_obj.created_at
        ))
    
    return result


@router.get("/assignments", response_model=List[ClassSubjectResponse])
async def get_teacher_assignments(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Get all class-subject assignments for the current teacher."""
    institute_id = request.state.institute_id
    assignments = ClassSubjectService.get_teacher_assignments(
        db, current_user.id, institute_id
    )
    
    # Format response with teacher names
    result = []
    for assignment in assignments:
        teacher_name = None
        if assignment.teacher_id:
            teacher = db.query(User).filter(User.id == assignment.teacher_id).first()
            if teacher:
                teacher_name = teacher.name
        
        result.append(ClassSubjectResponse(
            id=assignment.id,
            class_id=assignment.class_id,
            subject_id=assignment.subject_id,
            teacher_id=assignment.teacher_id,
            teacher_name=teacher_name
        ))
    
    return result


@router.get("/{class_id}/subjects", response_model=List[SubjectResponse])
async def get_class_subjects(
    class_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Get all subjects assigned to the teacher for a specific class."""
    institute_id = request.state.institute_id
    
    # Verify class belongs to institute
    ClassService.get_class(db, class_id, institute_id)
    
    # Get teacher's assignments for this class
    assignments = ClassSubjectService.get_teacher_assignments(
        db, current_user.id, institute_id
    )
    
    # Filter assignments for this specific class
    class_assignments = [a for a in assignments if a.class_id == class_id]
    
    if not class_assignments:
        # Teacher is not assigned to this class
        return []
    
    # Get unique subject IDs
    subject_ids = [a.subject_id for a in class_assignments]
    
    # Get subject objects
    from app.db.models.subject import Subject
    subjects = db.query(Subject).filter(
        Subject.id.in_(subject_ids),
        Subject.institute_id == institute_id
    ).all()
    
    # Format response
    result = []
    for subject in subjects:
        result.append(SubjectResponse(
            id=subject.id,
            name=subject.name,
            code=subject.code,
            description=subject.description,
            is_active=subject.is_active,
            institute_id=subject.institute_id,
            created_at=subject.created_at
        ))
    
    return result


@router.get("/{class_id}/students", response_model=List[EnrollmentResponse])
async def get_class_students(
    class_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Get all students enrolled in a class (only for classes assigned to the teacher)."""
    institute_id = request.state.institute_id
    
    # Verify class belongs to institute
    class_obj = ClassService.get_class(db, class_id, institute_id)
    
    # Verify teacher is assigned to this class
    assignments = ClassSubjectService.get_teacher_assignments(
        db, current_user.id, institute_id
    )
    is_assigned = any(a.class_id == class_id for a in assignments)
    
    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class"
        )
    
    # Get all enrollments for this class
    enrollments = db.query(Enrollment).filter(
        Enrollment.class_id == class_id
    ).all()
    
    # Format response with student and class names
    result = []
    for enrollment in enrollments:
        student = db.query(User).filter(User.id == enrollment.student_id).first()
        result.append(EnrollmentResponse(
            id=enrollment.id,
            student_id=enrollment.student_id,
            class_id=enrollment.class_id,
            enrolled_at=enrollment.enrolled_at,
            student_name=student.name if student else "",
            class_name=class_obj.name
        ))
    
    return result
