from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.gradebook import (
    GradebookEntryResponse,
    GradebookEntryCreate,
    GradebookEntryUpdate,
    GradebookCalculateRequest,
    GradebookBulkUpdateRequest,
    GradeDistributionResponse,
    GradebookHistoryResponse,
    ReportCardRequest
)
from app.services.gradebook_service import GradebookService
from app.utils.dependencies import get_institute_admin
from app.utils.permissions import require_permission
from app.db.models.gradebook import TermType

router = APIRouter(prefix="/gradebook", tags=["admin-gradebook"])


@router.post("/calculate", response_model=List[GradebookEntryResponse])
async def calculate_gradebook(
    request: Request,
    data: GradebookCalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gradebook", "create"))
):
    """Calculate gradebook entries for a class/subject/term (Admin only)."""
    institute_id = request.state.institute_id
    
    # Verify weights sum to 1.0
    total_weight = data.quiz_weight + data.assignment_weight + data.exam_weight
    if abs(total_weight - 1.0) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Weights must sum to 1.0. Current sum: {total_weight}"
        )
    
    # Get all students in the class
    from app.db.models.class_model import Class
    from app.db.models.enrollment import Enrollment
    
    class_obj = db.query(Class).filter(
        and_(
            Class.id == data.class_id,
            Class.institute_id == institute_id
        )
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Get enrolled students
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
    
    # If subject_id is not provided, get all subjects for the class
    if not data.subject_id:
        from app.db.models.class_subject import ClassSubject
        class_subjects = db.query(ClassSubject).filter(
            ClassSubject.class_id == data.class_id
        ).all()
        
        if not class_subjects:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No subjects found for this class"
            )
        
        subject_ids = [cs.subject_id for cs in class_subjects]
    else:
        subject_ids = [data.subject_id]
    
    # Calculate gradebook for each student and subject
    entries = []
    for enrollment in enrollments:
        for subject_id in subject_ids:
            try:
                entry = GradebookService.calculate_gradebook_entry(
                    db,
                    enrollment.student_id,
                    data.class_id,
                    subject_id,
                    institute_id,
                    data.academic_year,
                    data.term,
                    data.quiz_weight,
                    data.assignment_weight,
                    data.exam_weight,
                    current_user.id
                )
                entries.append(entry)
            except Exception as e:
                # Log error but continue with other students/subjects
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error calculating gradebook for student {enrollment.student_id}, subject {subject_id}: {e}", exc_info=True)
                continue
    
    if not entries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No gradebook entries were calculated. Please check if students have quiz/assignment results."
        )
    
    # Format responses
    formatted_entries = []
    for entry in entries:
        try:
            student = db.query(User).filter(User.id == entry.student_id).first()
            from app.db.models.class_model import Class
            from app.db.models.subject import Subject
            class_obj = db.query(Class).filter(Class.id == entry.class_id).first()
            subject = db.query(Subject).filter(Subject.id == entry.subject_id).first()
            creator = db.query(User).filter(User.id == entry.created_by).first() if entry.created_by else None
            
            formatted_entries.append(GradebookEntryResponse.model_validate({
                **entry.__dict__,
                "student_name": student.name if student else None,
                "class_name": class_obj.name if class_obj else None,
                "subject_name": subject.name if subject else None,
                "creator_name": creator.name if creator else None
            }))
        except Exception as e:
            logger.error(f"Error formatting entry {entry.id}: {e}", exc_info=True)
            continue
    
    return formatted_entries


@router.get("", response_model=List[GradebookEntryResponse])
async def get_gradebook_entries(
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    student_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    term: Optional[TermType] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_permission("gradebook", "view"))
):
    """Get all gradebook entries (Admin only)."""
    institute_id = request.state.institute_id
    
    entries = GradebookService.get_gradebook_entries(
        db, institute_id, class_id, subject_id, student_id, academic_year, term, status
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
async def get_gradebook_entry(
    entry_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gradebook", "view"))
):
    """Get a specific gradebook entry (Admin only)."""
    institute_id = request.state.institute_id
    
    entry = GradebookService.get_gradebook_entry(db, entry_id, institute_id)
    
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


@router.put("/{entry_id}", response_model=GradebookEntryResponse)
async def update_gradebook_entry(
    entry_id: int,
    request: Request,
    data: GradebookEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gradebook", "edit"))
):
    """Update a gradebook entry (Admin only)."""
    institute_id = request.state.institute_id
    
    entry = GradebookService.update_gradebook_entry(
        db, entry_id, institute_id, current_user.id,
        data.quiz_weight, data.assignment_weight, data.exam_weight,
        data.status, data.remarks
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


@router.post("/bulk-update", response_model=List[GradebookEntryResponse])
async def bulk_update_gradebook(
    request: Request,
    data: GradebookBulkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gradebook", "edit"))
):
    """Bulk update gradebook entries (Admin only)."""
    institute_id = request.state.institute_id
    
    updated_entries = []
    for entry_id in data.entry_ids:
        try:
            entry = GradebookService.update_gradebook_entry(
                db, entry_id, institute_id, current_user.id,
                None, None, None, data.status, data.remarks
            )
            updated_entries.append(entry)
        except Exception:
            continue
    
    # Format responses
    formatted_entries = []
    for entry in updated_entries:
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


@router.post("/distributions/calculate", response_model=GradeDistributionResponse)
async def calculate_grade_distribution(
    request: Request,
    class_id: int,
    academic_year: str,
    term: TermType,
    subject_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gradebook", "view"))
):
    """Calculate grade distribution for a class/subject/term (Admin only)."""
    institute_id = request.state.institute_id
    
    distribution = GradebookService.calculate_grade_distribution(
        db, institute_id, class_id, subject_id, academic_year, term
    )
    
    from app.db.models.class_model import Class
    from app.db.models.subject import Subject
    class_obj = db.query(Class).filter(Class.id == distribution.class_id).first()
    subject = db.query(Subject).filter(Subject.id == distribution.subject_id).first() if distribution.subject_id else None
    
    return GradeDistributionResponse(
        **distribution.__dict__,
        class_name=class_obj.name if class_obj else None,
        subject_name=subject.name if subject else None
    )


@router.get("/distributions", response_model=List[GradeDistributionResponse])
async def get_grade_distributions(
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    term: Optional[TermType] = None,
    current_user: User = Depends(require_permission("gradebook", "view"))
):
    """Get grade distributions (Admin only)."""
    institute_id = request.state.institute_id
    
    from app.db.models.gradebook import GradeDistribution
    query = db.query(GradeDistribution).filter(
        GradeDistribution.institute_id == institute_id
    )
    
    if class_id:
        query = query.filter(GradeDistribution.class_id == class_id)
    if subject_id:
        query = query.filter(GradeDistribution.subject_id == subject_id)
    if academic_year:
        query = query.filter(GradeDistribution.academic_year == academic_year)
    if term:
        query = query.filter(GradeDistribution.term == term)
    
    distributions = query.all()
    
    # Format responses
    formatted_distributions = []
    for dist in distributions:
        from app.db.models.class_model import Class
        from app.db.models.subject import Subject
        class_obj = db.query(Class).filter(Class.id == dist.class_id).first()
        subject = db.query(Subject).filter(Subject.id == dist.subject_id).first() if dist.subject_id else None
        
        formatted_distributions.append(GradeDistributionResponse(
            **dist.__dict__,
            class_name=class_obj.name if class_obj else None,
            subject_name=subject.name if subject else None
        ))
    
    return formatted_distributions


@router.get("/{entry_id}/history", response_model=List[GradebookHistoryResponse])
async def get_gradebook_history(
    entry_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gradebook", "view"))
):
    """Get history for a gradebook entry (Admin only)."""
    institute_id = request.state.institute_id
    
    # Verify entry exists and belongs to institute
    entry = GradebookService.get_gradebook_entry(db, entry_id, institute_id)
    
    from app.db.models.gradebook import GradebookHistory
    history = db.query(GradebookHistory).filter(
        GradebookHistory.gradebook_entry_id == entry_id
    ).order_by(GradebookHistory.created_at.desc()).all()
    
    # Format responses
    formatted_history = []
    for h in history:
        changed_by_user = db.query(User).filter(User.id == h.changed_by).first() if h.changed_by else None
        
        formatted_history.append(GradebookHistoryResponse(
            **h.__dict__,
            changed_by_name=changed_by_user.name if changed_by_user else None
        ))
    
    return formatted_history


@router.post("/report-card", response_model=dict)
async def generate_report_card(
    request: Request,
    data: ReportCardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("gradebook", "view"))
):
    """Generate PDF report card for a student (Admin only)."""
    from app.services.report_card_service import ReportCardService
    
    institute_id = request.state.institute_id
    
    # Generate report card
    report_card = ReportCardService.generate_report_card(
        db,
        institute_id,
        data.student_id,
        data.academic_year,
        data.term,
        data.include_remarks,
        data.include_attendance,
        data.include_analytics
    )
    
    return report_card
