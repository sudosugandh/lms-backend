from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.quiz import (
    AssignmentResponse, AssignmentSubmissionCreate,
    AssignmentSubmissionResponse
)
from app.services.assignment_service import AssignmentService, AssignmentSubmissionService
from app.utils.dependencies import get_student

router = APIRouter(prefix="/assignments", tags=["student-assignments"])


@router.get("", response_model=List[AssignmentResponse])
async def list_assignments(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """List all available assignments for the student."""
    institute_id = request.state.institute_id
    assignments = AssignmentService.get_student_assignments(
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
            creator_name=None  # Not shown to students
        ))
    
    return results


@router.post("/{assignment_id}/submit", response_model=AssignmentSubmissionResponse, status_code=201)
async def submit_assignment(
    assignment_id: int,
    submission_data: AssignmentSubmissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Submit an assignment (Student only)."""
    institute_id = request.state.institute_id
    
    if submission_data.assignment_id != assignment_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment ID mismatch"
        )
    
    submission = AssignmentSubmissionService.submit_assignment(
        db, assignment_id, current_user.id, institute_id, submission_data
    )
    
    # Format response
    from app.db.models.assignment import Assignment
    assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
    
    return AssignmentSubmissionResponse(
        **submission.__dict__,
        student_name=current_user.name,
        assignment_title=assignment.title if assignment else None
    )


@router.get("/submissions", response_model=List[AssignmentSubmissionResponse])
async def list_submissions(
    request: Request,
    db: Session = Depends(get_db),
    assignment_id: int = None,
    current_user: User = Depends(get_student)
):
    """List all assignment submissions by the student."""
    institute_id = request.state.institute_id
    submissions = AssignmentSubmissionService.get_student_submissions(
        db, current_user.id, institute_id, assignment_id
    )
    
    # Format responses
    results = []
    for submission in submissions:
        from app.db.models.assignment import Assignment
        assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
        
        results.append(AssignmentSubmissionResponse(
            **submission.__dict__,
            student_name=current_user.name,
            assignment_title=assignment.title if assignment else None
        ))
    
    return results
