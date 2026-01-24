from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.quiz import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    AssignmentSubmissionResponse, AssignmentSubmissionGrade
)
from app.services.assignment_service import AssignmentService, AssignmentSubmissionService
from app.utils.dependencies import get_teacher

router = APIRouter(prefix="/assignments", tags=["teacher-assignments"])


@router.post("", response_model=AssignmentResponse, status_code=201)
async def create_assignment(
    assignment_data: AssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Create a new assignment (Teacher only)."""
    institute_id = request.state.institute_id
    assignment = AssignmentService.create_assignment(
        db, institute_id, current_user.id, assignment_data
    )
    
    # Format response
    from app.db.models.class_model import Class
    from app.db.models.subject import Subject
    class_obj = db.query(Class).filter(Class.id == assignment.class_id).first()
    subject = db.query(Subject).filter(Subject.id == assignment.subject_id).first()
    
    return AssignmentResponse(
        **assignment.__dict__,
        class_name=class_obj.name if class_obj else None,
        subject_name=subject.name if subject else None,
        creator_name=current_user.name
    )


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Update an assignment (Teacher only)."""
    institute_id = request.state.institute_id
    assignment = AssignmentService.update_assignment(
        db, assignment_id, institute_id, current_user.id, assignment_data
    )
    
    # Format response
    from app.db.models.class_model import Class
    from app.db.models.subject import Subject
    class_obj = db.query(Class).filter(Class.id == assignment.class_id).first()
    subject = db.query(Subject).filter(Subject.id == assignment.subject_id).first()
    
    return AssignmentResponse(
        **assignment.__dict__,
        class_name=class_obj.name if class_obj else None,
        subject_name=subject.name if subject else None,
        creator_name=current_user.name
    )


@router.get("", response_model=List[AssignmentResponse])
async def list_assignments(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """List all assignments created by the teacher."""
    institute_id = request.state.institute_id
    assignments = AssignmentService.get_teacher_assignments(
        db, current_user.id, institute_id
    )
    
    # Format responses
    results = []
    for assignment in assignments:
        from app.db.models.class_model import Class
        from app.db.models.subject import Subject
        class_obj = db.query(Class).filter(Class.id == assignment.class_id).first()
        subject = db.query(Subject).filter(Subject.id == assignment.subject_id).first()
        
        results.append(AssignmentResponse(
            **assignment.__dict__,
            class_name=class_obj.name if class_obj else None,
            subject_name=subject.name if subject else None,
            creator_name=current_user.name
        ))
    
    return results


@router.get("/{assignment_id}/submissions", response_model=List[AssignmentSubmissionResponse])
async def get_assignment_submissions(
    assignment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Get all submissions for an assignment (Teacher only)."""
    institute_id = request.state.institute_id
    submissions = AssignmentSubmissionService.get_assignment_submissions(
        db, assignment_id, institute_id, current_user.id
    )
    
    # Format responses
    results = []
    for submission in submissions:
        student = db.query(User).filter(User.id == submission.student_id).first()
        from app.db.models.assignment import Assignment
        assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
        
        results.append(AssignmentSubmissionResponse(
            **submission.__dict__,
            student_name=student.name if student else None,
            assignment_title=assignment.title if assignment else None
        ))
    
    return results


@router.post("/submissions/{submission_id}/grade", response_model=AssignmentSubmissionResponse)
async def grade_submission(
    submission_id: int,
    grade_data: AssignmentSubmissionGrade,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Grade an assignment submission (Teacher only)."""
    institute_id = request.state.institute_id
    submission = AssignmentSubmissionService.grade_submission(
        db, submission_id, institute_id, current_user.id,
        grade_data.marks_obtained, grade_data.feedback
    )
    
    # Format response
    student = db.query(User).filter(User.id == submission.student_id).first()
    from app.db.models.assignment import Assignment
    assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
    
    return AssignmentSubmissionResponse(
        **submission.__dict__,
        student_name=student.name if student else None,
        assignment_title=assignment.title if assignment else None
    )


@router.post("/quizzes/answers/{answer_id}/grade")
async def grade_quiz_answer(
    answer_id: int,
    marks_obtained: int,
    feedback: str = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Grade a descriptive quiz answer (Teacher only)."""
    institute_id = request.state.institute_id
    
    from app.services.result_service import GradingService
    answer = GradingService.grade_descriptive_answer(
        db, answer_id, institute_id, current_user.id,
        marks_obtained, feedback
    )
    
    from app.schemas.quiz import QuizAttemptAnswerResponse
    # Explicitly construct response to avoid serialization issues
    return QuizAttemptAnswerResponse(
        id=answer.id,
        attempt_id=answer.attempt_id,
        question_id=answer.question_id,
        selected_option_id=answer.selected_option_id,
        descriptive_answer=answer.descriptive_answer,
        marks_obtained=answer.marks_obtained,
        is_correct=answer.is_correct,
        graded_by=answer.graded_by,
        graded_at=answer.graded_at,
        feedback=answer.feedback,
        created_at=answer.created_at
    )
