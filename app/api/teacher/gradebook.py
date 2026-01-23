from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.gradebook import (
    GradebookEntryResponse,
    GradebookCalculateRequest
)
from app.services.gradebook_service import GradebookService
from app.utils.dependencies import get_teacher
from app.db.models.gradebook import TermType

router = APIRouter(prefix="/gradebook", tags=["teacher-gradebook"])


@router.post("/calculate", response_model=List[GradebookEntryResponse])
async def calculate_gradebook(
    request: Request,
    data: GradebookCalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Calculate gradebook entries for assigned classes (Teacher only)."""
    institute_id = request.state.institute_id
    
    # Verify teacher is assigned to this class/subject
    from app.db.models.class_subject import ClassSubject
    class_subject = db.query(ClassSubject).filter(
        and_(
            ClassSubject.class_id == data.class_id,
            ClassSubject.teacher_id == current_user.id
        )
    ).first()
    
    if not class_subject:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class/subject"
        )
    
    if data.subject_id and class_subject.subject_id != data.subject_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this subject"
        )
    
    # Verify weights sum to 1.0
    total_weight = data.quiz_weight + data.assignment_weight + data.exam_weight
    if abs(total_weight - 1.0) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Weights must sum to 1.0. Current sum: {total_weight}"
        )
    
    # Get all students in the class
    from app.db.models.enrollment import Enrollment
    
    enrollments = db.query(Enrollment).filter(
        and_(
            Enrollment.class_id == data.class_id,
            Enrollment.institute_id == institute_id
        )
    ).all()
    
    if not enrollments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No students enrolled in this class"
        )
    
    # Calculate gradebook for each student
    entries = []
    for enrollment in enrollments:
        try:
            entry = GradebookService.calculate_gradebook_entry(
                db,
                enrollment.student_id,
                data.class_id,
                data.subject_id or class_subject.subject_id,
                institute_id,
                data.academic_year,
                data.term,
                data.quiz_weight,
                data.assignment_weight,
                data.exam_weight,
                current_user.id
            )
            entries.append(entry)
        except Exception:
            continue
    
    # Format responses
    formatted_entries = []
    for entry in entries:
        student = db.query(User).filter(User.id == entry.student_id).first()
        from app.db.models.class_model import Class
        from app.db.models.subject import Subject
        class_obj = db.query(Class).filter(Class.id == entry.class_id).first()
        subject = db.query(Subject).filter(Subject.id == entry.subject_id).first()
        creator = db.query(User).filter(User.id == entry.created_by).first() if entry.created_by else None
        
        formatted_entries.append(GradebookEntryResponse(
            **entry.__dict__,
            student_name=student.name if student else None,
            class_name=class_obj.name if class_obj else None,
            subject_name=subject.name if subject else None,
            creator_name=creator.name if creator else None
        ))
    
    return formatted_entries


@router.get("", response_model=List[GradebookEntryResponse])
async def get_gradebook_entries(
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    term: Optional[TermType] = None,
    current_user: User = Depends(get_teacher)
):
    """Get gradebook entries for assigned classes (Teacher only)."""
    institute_id = request.state.institute_id
    
    # Get classes assigned to teacher
    from app.db.models.class_subject import ClassSubject
    assigned_classes = db.query(ClassSubject).filter(
        and_(
            ClassSubject.teacher_id == current_user.id,
            ClassSubject.institute_id == institute_id
        )
    ).all()
    
    if not assigned_classes:
        return []
    
    # Filter by assigned classes
    assigned_class_ids = [ac.class_id for ac in assigned_classes]
    if class_id and class_id not in assigned_class_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class"
        )
    
    # Get entries for assigned classes
    entries = GradebookService.get_gradebook_entries(
        db, institute_id, class_id, subject_id, None, academic_year, term, None
    )
    
    # Filter to only assigned classes
    filtered_entries = [
        e for e in entries
        if e.class_id in assigned_class_ids
    ]
    
    # Format responses
    formatted_entries = []
    for entry in filtered_entries:
        student = db.query(User).filter(User.id == entry.student_id).first()
        from app.db.models.class_model import Class
        from app.db.models.subject import Subject
        class_obj = db.query(Class).filter(Class.id == entry.class_id).first()
        subject = db.query(Subject).filter(Subject.id == entry.subject_id).first()
        creator = db.query(User).filter(User.id == entry.created_by).first() if entry.created_by else None
        
        formatted_entries.append(GradebookEntryResponse(
            **entry.__dict__,
            student_name=student.name if student else None,
            class_name=class_obj.name if class_obj else None,
            subject_name=subject.name if subject else None,
            creator_name=creator.name if creator else None
        ))
    
    return formatted_entries


@router.get("/{entry_id}", response_model=GradebookEntryResponse)
async def get_gradebook_entry(
    entry_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Get a specific gradebook entry (Teacher only - must be assigned to class)."""
    institute_id = request.state.institute_id
    
    entry = GradebookService.get_gradebook_entry(db, entry_id, institute_id)
    
    # Verify teacher is assigned to this class
    from app.db.models.class_subject import ClassSubject
    class_subject = db.query(ClassSubject).filter(
        and_(
            ClassSubject.class_id == entry.class_id,
            ClassSubject.subject_id == entry.subject_id,
            ClassSubject.teacher_id == current_user.id
        )
    ).first()
    
    if not class_subject:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this class/subject"
        )
    
    student = db.query(User).filter(User.id == entry.student_id).first()
    from app.db.models.class_model import Class
    from app.db.models.subject import Subject
    class_obj = db.query(Class).filter(Class.id == entry.class_id).first()
    subject = db.query(Subject).filter(Subject.id == entry.subject_id).first()
    creator = db.query(User).filter(User.id == entry.created_by).first() if entry.created_by else None
    
    return GradebookEntryResponse(
        **entry.__dict__,
        student_name=student.name if student else None,
        class_name=class_obj.name if class_obj else None,
        subject_name=subject.name if subject else None,
        creator_name=creator.name if creator else None
    )
