from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.quiz import ResultResponse
from app.services.result_service import ResultService
from app.utils.dependencies import get_institute_admin

router = APIRouter(prefix="/results", tags=["admin-results"])


@router.get("", response_model=List[ResultResponse])
async def get_institute_results(
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    result_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_institute_admin)
):
    """Get all results for the institute (Admin only - read-only)."""
    institute_id = request.state.institute_id
    results = ResultService.get_institute_results(
        db, institute_id, class_id, subject_id, result_type, status
    )
    
    # Format responses
    formatted_results = []
    for result in results:
        student = db.query(User).filter(User.id == result.student_id).first()
        from app.db.models.class_model import Class
        from app.db.models.subject import Subject
        class_obj = db.query(Class).filter(Class.id == result.class_id).first()
        subject = db.query(Subject).filter(Subject.id == result.subject_id).first()
        
        quiz_title = None
        if result.quiz_id:
            from app.db.models.quiz import Quiz
            quiz = db.query(Quiz).filter(Quiz.id == result.quiz_id).first()
            if quiz:
                quiz_title = quiz.title
        
        assignment_title = None
        if result.assignment_id:
            from app.db.models.assignment import Assignment
            assignment = db.query(Assignment).filter(Assignment.id == result.assignment_id).first()
            if assignment:
                assignment_title = assignment.title
        
        formatted_results.append(ResultResponse(
            **result.__dict__,
            student_name=student.name if student else None,
            class_name=class_obj.name if class_obj else None,
            subject_name=subject.name if subject else None,
            quiz_title=quiz_title,
            assignment_title=assignment_title
        ))
    
    return formatted_results


@router.get("/classes/{class_id}", response_model=List[ResultResponse])
async def get_class_results(
    class_id: int,
    request: Request,
    db: Session = Depends(get_db),
    subject_id: Optional[int] = None,
    result_type: Optional[str] = None,
    current_user: User = Depends(get_institute_admin)
):
    """Get all results for a class (Admin only - read-only)."""
    institute_id = request.state.institute_id
    results = ResultService.get_class_results(
        db, class_id, institute_id, subject_id, result_type
    )
    
    # Format responses
    formatted_results = []
    for result in results:
        student = db.query(User).filter(User.id == result.student_id).first()
        from app.db.models.class_model import Class
        from app.db.models.subject import Subject
        class_obj = db.query(Class).filter(Class.id == result.class_id).first()
        subject = db.query(Subject).filter(Subject.id == result.subject_id).first()
        
        quiz_title = None
        if result.quiz_id:
            from app.db.models.quiz import Quiz
            quiz = db.query(Quiz).filter(Quiz.id == result.quiz_id).first()
            if quiz:
                quiz_title = quiz.title
        
        assignment_title = None
        if result.assignment_id:
            from app.db.models.assignment import Assignment
            assignment = db.query(Assignment).filter(Assignment.id == result.assignment_id).first()
            if assignment:
                assignment_title = assignment.title
        
        formatted_results.append(ResultResponse(
            **result.__dict__,
            student_name=student.name if student else None,
            class_name=class_obj.name if class_obj else None,
            subject_name=subject.name if subject else None,
            quiz_title=quiz_title,
            assignment_title=assignment_title
        ))
    
    return formatted_results
