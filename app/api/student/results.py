from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.quiz import ResultResponse
from app.services.result_service import ResultService
from app.utils.dependencies import get_student

router = APIRouter(prefix="/results", tags=["student-results"])


@router.get("", response_model=List[ResultResponse])
async def get_my_results(
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    result_type: Optional[str] = None,
    current_user: User = Depends(get_student)
):
    """Get own results (Student only)."""
    institute_id = request.state.institute_id
    results = ResultService.get_student_results(
        db, current_user.id, institute_id, class_id, subject_id, result_type
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


@router.get("/{result_id}", response_model=ResultResponse)
async def get_result(
    result_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Get a specific result (Student only)."""
    institute_id = request.state.institute_id
    result = ResultService.get_result(
        db, result_id, institute_id, current_user.id, current_user.role.value
    )
    
    # Format response
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
    
    return ResultResponse(
        **result.__dict__,
        student_name=student.name if student else None,
        class_name=class_obj.name if class_obj else None,
        subject_name=subject.name if subject else None,
        quiz_title=quiz_title,
        assignment_title=assignment_title
    )
