
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.quiz import (
    QuizResponse, QuizAttemptResponse, QuizAttemptWithAnswers,
    QuizAttemptSubmit, QuizAttemptAnswerBase, QuizQuestionResponse
)
from app.services.quiz_service import QuizService, QuizAttemptService
from app.utils.dependencies import get_student

router = APIRouter(prefix="/quizzes", tags=["student-quizzes"])


@router.get("", response_model=List[QuizResponse])
async def list_quizzes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """List all available quizzes for the student."""
    institute_id = request.state.institute_id
    quizzes = QuizService.get_student_quizzes(db, current_user.id, institute_id)
    
    # Format responses
    results = []
    for quiz in quizzes:
        from app.db.models.class_model import Class
        from app.db.models.subject import Subject
        class_obj = db.query(Class).filter(Class.id == quiz.class_id).first()
        subject = db.query(Subject).filter(Subject.id == quiz.subject_id).first()
        
        results.append(QuizResponse(
            **quiz.__dict__,
            class_name=class_obj.name if class_obj else None,
            subject_name=subject.name if subject else None,
            creator_name=None  # Not shown to students
        ))
    
    return results


# Attempts routes must come before /{quiz_id} route to avoid route conflicts
@router.get("/attempts", response_model=List[QuizAttemptResponse])
async def list_attempts(
    request: Request,
    db: Session = Depends(get_db),
    quiz_id: Optional[int] = Query(None, description="Filter by quiz ID"),
    current_user: User = Depends(get_student)
):
    """List all quiz attempts by the student."""
    institute_id = request.state.institute_id
    attempts = QuizAttemptService.get_student_attempts(
        db, current_user.id, institute_id, quiz_id
    )
    
    # Format responses
    results = []
    for attempt in attempts:
        from app.db.models.quiz import Quiz
        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        
        results.append(QuizAttemptResponse(
            id=attempt.id,
            quiz_id=int(attempt.quiz_id),  # Ensure it's an integer
            student_id=attempt.student_id,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            time_taken_minutes=attempt.time_taken_minutes,
            status=attempt.status,
            total_marks_obtained=attempt.total_marks_obtained,
            feedback=attempt.feedback,
            created_at=attempt.created_at,
            student_name=current_user.name,
            quiz_title=quiz.title if quiz else None
        ))
    
    return results


@router.get("/attempts/{attempt_id}", response_model=QuizAttemptWithAnswers)
async def get_attempt_details(
    attempt_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Get detailed attempt with answers (Student only)."""
    institute_id = request.state.institute_id
    
    from app.db.models.quiz import QuizAttempt, QuizAttemptAnswer, Quiz
    from app.schemas.quiz import QuizAttemptAnswerResponse
    
    attempt = db.query(QuizAttempt).join(Quiz).filter(
        and_(
            QuizAttempt.id == attempt_id,
            QuizAttempt.student_id == current_user.id,
            Quiz.institute_id == institute_id
        )
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )
    
    # Load answers
    answers = db.query(QuizAttemptAnswer).filter(
        QuizAttemptAnswer.attempt_id == attempt_id
    ).all()
    
    quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
    
    # Explicitly construct answer responses to avoid serialization issues
    answer_responses = [
        QuizAttemptAnswerResponse(
            id=ans.id,
            attempt_id=ans.attempt_id,
            question_id=ans.question_id,
            selected_option_id=ans.selected_option_id,
            descriptive_answer=ans.descriptive_answer,
            marks_obtained=ans.marks_obtained,
            is_correct=ans.is_correct,
            graded_by=ans.graded_by,
            graded_at=ans.graded_at,
            feedback=ans.feedback,
            created_at=ans.created_at
        )
        for ans in answers
    ]
    
    # Explicitly construct QuizAttemptWithAnswers
    return QuizAttemptWithAnswers(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        student_id=attempt.student_id,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        time_taken_minutes=attempt.time_taken_minutes,
        status=attempt.status,
        total_marks_obtained=attempt.total_marks_obtained,
        feedback=attempt.feedback,
        created_at=attempt.created_at,
        student_name=current_user.name,
        quiz_title=quiz.title if quiz else None,
        answers=answer_responses
    )


@router.post("/attempts/{attempt_id}/submit", response_model=QuizAttemptResponse)
async def submit_quiz_attempt(
    attempt_id: int,
    submit_data: QuizAttemptSubmit,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Submit a quiz attempt with answers (Student only)."""
    institute_id = request.state.institute_id
    
    attempt = QuizAttemptService.submit_attempt(
        db, attempt_id, current_user.id, institute_id, submit_data.answers
    )
    
    # Format response
    from app.db.models.quiz import Quiz
    quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
    
    return QuizAttemptResponse(
        id=attempt.id,
        quiz_id=int(attempt.quiz_id),  # Ensure it's an integer
        student_id=attempt.student_id,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        time_taken_minutes=attempt.time_taken_minutes,
        status=attempt.status,
        total_marks_obtained=attempt.total_marks_obtained,
        feedback=attempt.feedback,
        created_at=attempt.created_at,
        student_name=current_user.name,
        quiz_title=quiz.title if quiz else None
    )


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Get a specific quiz (Student only)."""
    institute_id = request.state.institute_id
    
    # Get quiz without teacher check
    from app.db.models.quiz import Quiz
    quiz = db.query(Quiz).filter(
        and_(
            Quiz.id == quiz_id,
            Quiz.institute_id == institute_id,
            Quiz.status == "PUBLISHED",
            Quiz.is_active == True
        )
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or not available"
        )
    
    # Verify student is enrolled
    from app.db.models.enrollment import Enrollment
    enrollment = db.query(Enrollment).filter(
        and_(
            Enrollment.student_id == current_user.id,
            Enrollment.class_id == quiz.class_id
        )
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this class"
        )
    
    # Format response
    from app.db.models.class_model import Class
    from app.db.models.subject import Subject
    class_obj = db.query(Class).filter(Class.id == quiz.class_id).first()
    subject = db.query(Subject).filter(Subject.id == quiz.subject_id).first()
    
    return QuizResponse(
        **quiz.__dict__,
        class_name=class_obj.name if class_obj else None,
        subject_name=subject.name if subject else None,
        creator_name=None
    )


@router.get("/{quiz_id}/questions", response_model=List[QuizQuestionResponse])
async def get_quiz_questions_for_attempt(
    quiz_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Get quiz questions for attempting (Student only)."""
    institute_id = request.state.institute_id
    
    # Verify quiz is available
    from app.db.models.quiz import Quiz
    quiz = db.query(Quiz).filter(
        and_(
            Quiz.id == quiz_id,
            Quiz.institute_id == institute_id,
            Quiz.status == "PUBLISHED",
            Quiz.is_active == True
        )
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or not available"
        )
    
    # Verify student is enrolled
    from app.db.models.enrollment import Enrollment
    enrollment = db.query(Enrollment).filter(
        and_(
            Enrollment.student_id == current_user.id,
            Enrollment.class_id == quiz.class_id
        )
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this class"
        )
    
    # Get questions
    from app.db.models.quiz import QuizQuestion, QuizOption
    from app.schemas.quiz import QuizOptionResponse
    
    questions = db.query(QuizQuestion).filter(
        and_(
            QuizQuestion.quiz_id == quiz_id,
            QuizQuestion.is_active == True
        )
    ).order_by(QuizQuestion.order).all()
    
    results = []
    for question in questions:
        options = []
        if question.question_type == "MCQ":
            option_list = db.query(QuizOption).filter(
                QuizOption.question_id == question.id
            ).order_by(QuizOption.order).all()
            
            # Explicitly construct option responses to avoid serialization issues
            options = [
                QuizOptionResponse(
                    id=opt.id,
                    question_id=opt.question_id,
                    option_text=opt.option_text,
                    is_correct=opt.is_correct,
                    order=opt.order,
                    created_at=opt.created_at
                )
                for opt in option_list
            ]
        
        # Explicitly construct question response to avoid serialization issues
        results.append(QuizQuestionResponse(
            id=question.id,
            quiz_id=question.quiz_id,
            question_text=question.question_text,
            question_type=question.question_type,
            marks=question.marks,
            order=question.order,
            is_active=question.is_active,
            created_at=question.created_at,
            options=options
        ))
    
    return results


@router.post("/{quiz_id}/attempt", response_model=QuizAttemptResponse, status_code=201)
async def start_quiz_attempt(
    quiz_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Start a quiz attempt (Student only)."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        institute_id = request.state.institute_id
        logger.info(f"Student {current_user.id} attempting to start quiz {quiz_id}")
        
        attempt = QuizAttemptService.start_attempt(
            db, quiz_id, current_user.id, institute_id
        )
        
        # Format response
        from app.db.models.quiz import Quiz
        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        
        logger.info(f"Quiz attempt {attempt.id} created successfully for student {current_user.id}")
        
        # Construct response explicitly to avoid serialization issues
        return QuizAttemptResponse(
            id=attempt.id,
            quiz_id=int(attempt.quiz_id),  # Ensure it's an integer
            student_id=attempt.student_id,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            time_taken_minutes=attempt.time_taken_minutes,
            status=attempt.status,
            total_marks_obtained=attempt.total_marks_obtained,
            feedback=attempt.feedback,
            created_at=attempt.created_at,
            student_name=current_user.name,
            quiz_title=quiz.title if quiz else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting quiz attempt: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start quiz attempt: {str(e)}"
        )


