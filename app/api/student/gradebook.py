from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.gradebook import GradebookEntryResponse
from app.services.gradebook_service import GradebookService
from app.utils.dependencies import get_student
from app.db.models.gradebook import TermType

router = APIRouter(prefix="/gradebook", tags=["student-gradebook"])


@router.get("", response_model=List[GradebookEntryResponse])
async def get_my_gradebook(
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    term: Optional[TermType] = None,
    current_user: User = Depends(get_student)
):
    """Get own gradebook entries (Student only)."""
    institute_id = request.state.institute_id
    
    # Students can only view published entries
    entries = GradebookService.get_gradebook_entries(
        db, institute_id, class_id, subject_id, current_user.id, academic_year, term, "PUBLISHED"
    )
    
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


@router.get("/{entry_id}", response_model=GradebookEntryResponse)
async def get_my_gradebook_entry(
    entry_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Get a specific gradebook entry (Student only - own entries, published only)."""
    institute_id = request.state.institute_id
    
    entry = GradebookService.get_gradebook_entry(db, entry_id, institute_id)
    
    # Verify it's the student's own entry
    if entry.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own gradebook entries"
        )
    
    # Verify it's published
    if entry.status != "PUBLISHED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This gradebook entry is not yet published"
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
