from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.quiz import (
    QuizCreate, QuizUpdate, QuizResponse, QuizQuestionCreate, QuizQuestionUpdate,
    QuizQuestionResponse, QuizAttemptResponse, QuizAttemptWithAnswers,
    QuizOptionCreate
)
from app.services.quiz_service import QuizService, QuizQuestionService, QuizAttemptService
from app.utils.dependencies import get_teacher

router = APIRouter(prefix="/quizzes", tags=["teacher-quizzes"])


@router.post("", response_model=QuizResponse, status_code=201)
async def create_quiz(
    quiz_data: QuizCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Create a new quiz (Teacher only)."""
    institute_id = request.state.institute_id
    quiz = QuizService.create_quiz(db, institute_id, current_user.id, quiz_data)
    
    # Format response with names
    from app.db.models.class_model import Class
    from app.db.models.subject import Subject
    class_obj = db.query(Class).filter(Class.id == quiz.class_id).first()
    subject = db.query(Subject).filter(Subject.id == quiz.subject_id).first()
    
    return QuizResponse(
        **quiz.__dict__,
        class_name=class_obj.name if class_obj else None,
        subject_name=subject.name if subject else None,
        creator_name=current_user.name
    )


@router.put("/{quiz_id}", response_model=QuizResponse)
async def update_quiz(
    quiz_id: int,
    quiz_data: QuizUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Update a quiz (Teacher only)."""
    institute_id = request.state.institute_id
    quiz = QuizService.update_quiz(db, quiz_id, institute_id, current_user.id, quiz_data)
    
    # Format response
    from app.db.models.class_model import Class
    from app.db.models.subject import Subject
    class_obj = db.query(Class).filter(Class.id == quiz.class_id).first()
    subject = db.query(Subject).filter(Subject.id == quiz.subject_id).first()
    
    return QuizResponse(
        **quiz.__dict__,
        class_name=class_obj.name if class_obj else None,
        subject_name=subject.name if subject else None,
        creator_name=current_user.name
    )


@router.get("", response_model=List[QuizResponse])
async def list_quizzes(
    request: Request,
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    current_user: User = Depends(get_teacher)
):
    """List all quizzes created by the teacher."""
    institute_id = request.state.institute_id
    quizzes = QuizService.get_teacher_quizzes(db, current_user.id, institute_id, status)
    
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
            creator_name=current_user.name
        ))
    
    return results


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Get a specific quiz (Teacher only)."""
    institute_id = request.state.institute_id
    quiz = QuizService.get_quiz(db, quiz_id, institute_id, current_user.id)
    
    # Format response
    from app.db.models.class_model import Class
    from app.db.models.subject import Subject
    class_obj = db.query(Class).filter(Class.id == quiz.class_id).first()
    subject = db.query(Subject).filter(Subject.id == quiz.subject_id).first()
    
    return QuizResponse(
        **quiz.__dict__,
        class_name=class_obj.name if class_obj else None,
        subject_name=subject.name if subject else None,
        creator_name=current_user.name
    )


@router.post("/{quiz_id}/publish", response_model=QuizResponse)
async def publish_quiz(
    quiz_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Publish a quiz (Teacher only)."""
    institute_id = request.state.institute_id
    quiz = QuizService.publish_quiz(db, quiz_id, institute_id, current_user.id)
    
    # Format response
    from app.db.models.class_model import Class
    from app.db.models.subject import Subject
    class_obj = db.query(Class).filter(Class.id == quiz.class_id).first()
    subject = db.query(Subject).filter(Subject.id == quiz.subject_id).first()
    
    return QuizResponse(
        **quiz.__dict__,
        class_name=class_obj.name if class_obj else None,
        subject_name=subject.name if subject else None,
        creator_name=current_user.name
    )


@router.post("/{quiz_id}/close", response_model=QuizResponse)
async def close_quiz(
    quiz_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Close a quiz (Teacher only)."""
    institute_id = request.state.institute_id
    quiz = QuizService.close_quiz(db, quiz_id, institute_id, current_user.id)
    
    # Format response
    from app.db.models.class_model import Class
    from app.db.models.subject import Subject
    class_obj = db.query(Class).filter(Class.id == quiz.class_id).first()
    subject = db.query(Subject).filter(Subject.id == quiz.subject_id).first()
    
    return QuizResponse(
        **quiz.__dict__,
        class_name=class_obj.name if class_obj else None,
        subject_name=subject.name if subject else None,
        creator_name=current_user.name
    )


@router.get("/{quiz_id}/questions", response_model=List[QuizQuestionResponse])
async def get_quiz_questions(
    quiz_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Get all questions for a quiz (Teacher only)."""
    institute_id = request.state.institute_id
    quiz = QuizService.get_quiz(db, quiz_id, institute_id, current_user.id)
    
    from app.db.models.quiz import QuizQuestion, QuizOption
    from app.schemas.quiz import QuizOptionResponse
    
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id
    ).order_by(QuizQuestion.order).all()
    
    results = []
    for question in questions:
        options_list = []
        if question.question_type == "MCQ":
            options = db.query(QuizOption).filter(
                QuizOption.question_id == question.id
            ).order_by(QuizOption.order).all()
            options_list = [QuizOptionResponse(**opt.__dict__) for opt in options]
        
        results.append(QuizQuestionResponse(
            id=question.id,
            quiz_id=question.quiz_id,
            question_text=question.question_text,
            question_type=question.question_type,
            marks=question.marks,
            order=question.order,
            is_active=question.is_active,
            created_at=question.created_at,
            options=options_list
        ))
    
    return results


@router.post("/{quiz_id}/questions", response_model=QuizQuestionResponse, status_code=201)
async def create_question(
    quiz_id: int,
    question_data: QuizQuestionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Create a quiz question (Teacher only)."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        institute_id = request.state.institute_id
        logger.info(f"Received request to create question for quiz {quiz_id}, user: {current_user.id}, institute: {institute_id}")
        
        # Validate MCQ questions have options
        if question_data.question_type == "MCQ":
            if not question_data.options or len(question_data.options) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="MCQ questions must have at least 2 options"
                )
            # Check at least one option is correct
            if not any(opt.is_correct for opt in question_data.options):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one option must be marked as correct"
                )
        
        # Extract options if provided (already in QuizOptionBase format)
        options = question_data.options if question_data.options else None
        
        logger.info(f"Creating question for quiz {quiz_id}, type: {question_data.question_type}, options: {len(options) if options else 0}")
        
        # Create a QuizQuestionBase manually with only the base fields
        # This avoids any issues with passing extra fields like quiz_id or options
        from app.schemas.quiz import QuizQuestionBase
        question_base = QuizQuestionBase(
            question_text=question_data.question_text,
            question_type=question_data.question_type,
            marks=question_data.marks,
            order=question_data.order
        )
        
        logger.info(f"Question base created: text={question_base.question_text[:50]}..., type={question_base.question_type}, marks={question_base.marks}")
        
        question = QuizQuestionService.create_question(
            db, quiz_id, institute_id, current_user.id, question_base, options
        )
        
        logger.info(f"Question created successfully with ID: {question.id}")
        
        # Load options if MCQ
        from app.db.models.quiz import QuizOption
        from app.schemas.quiz import QuizOptionResponse
        loaded_options = []
        if question.question_type == "MCQ":
            options_list = db.query(QuizOption).filter(
                QuizOption.question_id == question.id
            ).order_by(QuizOption.order).all()
            loaded_options = [QuizOptionResponse(**opt.__dict__) for opt in options_list]
        
        return QuizQuestionResponse(
            id=question.id,
            quiz_id=question.quiz_id,
            question_text=question.question_text,
            question_type=question.question_type,
            marks=question.marks,
            order=question.order,
            is_active=question.is_active,
            created_at=question.created_at,
            options=loaded_options
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error creating question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create question: {str(e)}"
        )


@router.put("/questions/{question_id}", response_model=QuizQuestionResponse)
async def update_question(
    question_id: int,
    question_data: QuizQuestionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Update a quiz question (Teacher only)."""
    institute_id = request.state.institute_id
    question = QuizQuestionService.update_question(
        db, question_id, institute_id, current_user.id, question_data
    )
    
    # Load options if MCQ
    if question.question_type == "MCQ":
        from app.db.models.quiz import QuizOption
        question.options = db.query(QuizOption).filter(
            QuizOption.question_id == question.id
        ).all()
    
    return QuizQuestionResponse(
        **question.__dict__,
        options=[opt.__dict__ for opt in question.options] if hasattr(question, 'options') and question.options else []
    )


@router.get("/{quiz_id}/attempts", response_model=List[QuizAttemptResponse])
async def get_quiz_attempts(
    quiz_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Get all attempts for a quiz (Teacher only)."""
    institute_id = request.state.institute_id
    attempts = QuizAttemptService.get_quiz_attempts(db, quiz_id, institute_id, current_user.id)
    
    # Format responses
    results = []
    for attempt in attempts:
        student = db.query(User).filter(User.id == attempt.student_id).first()
        from app.db.models.quiz import Quiz
        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        
        results.append(QuizAttemptResponse(
            **attempt.__dict__,
            student_name=student.name if student else None,
            quiz_title=quiz.title if quiz else None
        ))
    
    return results


@router.get("/attempts/{attempt_id}", response_model=QuizAttemptWithAnswers)
async def get_attempt_details(
    attempt_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Get detailed attempt with answers (Teacher only)."""
    institute_id = request.state.institute_id
    
    from app.db.models.quiz import QuizAttempt, QuizAttemptAnswer
    attempt = db.query(QuizAttempt).join(Quiz).filter(
        and_(
            QuizAttempt.id == attempt_id,
            Quiz.institute_id == institute_id,
            Quiz.created_by == current_user.id
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
    
    student = db.query(User).filter(User.id == attempt.student_id).first()
    from app.db.models.quiz import Quiz
    quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
    
    return QuizAttemptWithAnswers(
        **attempt.__dict__,
        student_name=student.name if student else None,
        quiz_title=quiz.title if quiz else None,
        answers=[ans.__dict__ for ans in answers]
    )
