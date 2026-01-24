from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
from app.db.models.quiz import Quiz, QuizQuestion, QuizOption, QuizAttempt, QuizAttemptAnswer, QuizStatus, QuestionType
from app.db.models.class_model import Class
from app.db.models.subject import Subject
from app.db.models.class_subject import ClassSubject
from app.db.models.enrollment import Enrollment
from app.db.models.user import User
from app.db.models.result import Result
from app.schemas.quiz import (
    QuizCreate, QuizUpdate, QuizQuestionCreate, QuizQuestionUpdate,
    QuizQuestionBase, QuizOptionCreate, QuizOptionBase, QuizAttemptAnswerBase
)
from app.services.class_service import ClassService, SubjectService, ClassSubjectService


class QuizService:
    @staticmethod
    def create_quiz(
        db: Session,
        institute_id: int,
        teacher_id: int,
        quiz_data: QuizCreate
    ) -> Quiz:
        """Create a new quiz."""
        # Verify class belongs to institute
        ClassService.get_class(db, quiz_data.class_id, institute_id)
        
        # Verify subject belongs to institute
        SubjectService.get_subject(db, quiz_data.subject_id, institute_id)
        
        # Verify teacher is assigned to this class-subject combination
        assignments = ClassSubjectService.get_teacher_assignments(
            db, teacher_id, institute_id
        )
        is_assigned = any(
            a.class_id == quiz_data.class_id and 
            a.subject_id == quiz_data.subject_id 
            for a in assignments
        )
        
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to teach this subject in this class"
            )
        
        # Validate that end_time is after start_time if both are provided
        if quiz_data.start_time and quiz_data.end_time:
            # Ensure both are timezone-aware for comparison
            start_time = quiz_data.start_time
            end_time = quiz_data.end_time
            
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            else:
                start_time = start_time.astimezone(timezone.utc)
            
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            else:
                end_time = end_time.astimezone(timezone.utc)
            
            if end_time <= start_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="End time must be after start time"
                )
        
        quiz = Quiz(
            institute_id=institute_id,
            class_id=quiz_data.class_id,
            subject_id=quiz_data.subject_id,
            created_by=teacher_id,
            title=quiz_data.title,
            description=quiz_data.description,
            instructions=quiz_data.instructions,
            total_marks=quiz_data.total_marks,
            duration_minutes=quiz_data.duration_minutes,
            start_time=quiz_data.start_time,
            end_time=quiz_data.end_time,
            allow_multiple_attempts=quiz_data.allow_multiple_attempts,
            status="DRAFT"
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        return quiz
    
    @staticmethod
    def update_quiz(
        db: Session,
        quiz_id: int,
        institute_id: int,
        teacher_id: int,
        quiz_data: QuizUpdate
    ) -> Quiz:
        """Update a quiz."""
        quiz = QuizService.get_quiz(db, quiz_id, institute_id, teacher_id)
        
        # Validate that end_time is after start_time if both are provided
        start_time = quiz_data.start_time if quiz_data.start_time is not None else quiz.start_time
        end_time = quiz_data.end_time if quiz_data.end_time is not None else quiz.end_time
        
        if start_time and end_time:
            # Ensure both are timezone-aware for comparison
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            else:
                start_time = start_time.astimezone(timezone.utc)
            
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            else:
                end_time = end_time.astimezone(timezone.utc)
            
            if end_time <= start_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="End time must be after start time"
                )
        
        update_data = quiz_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(quiz, field, value)
        
        db.commit()
        db.refresh(quiz)
        return quiz
    
    @staticmethod
    def get_quiz(
        db: Session,
        quiz_id: int,
        institute_id: int,
        teacher_id: Optional[int] = None
    ) -> Quiz:
        """Get a quiz by ID, ensuring it belongs to the institute and teacher."""
        quiz = db.query(Quiz).filter(
            and_(
                Quiz.id == quiz_id,
                Quiz.institute_id == institute_id
            )
        ).first()
        
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        if teacher_id and quiz.created_by != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access quizzes you created"
            )
        
        return quiz
    
    @staticmethod
    def get_teacher_quizzes(
        db: Session,
        teacher_id: int,
        institute_id: int,
        status: Optional[str] = None
    ) -> List[Quiz]:
        """Get all quizzes created by a teacher."""
        query = db.query(Quiz).filter(
            and_(
                Quiz.institute_id == institute_id,
                Quiz.created_by == teacher_id
            )
        )
        
        if status:
            query = query.filter(Quiz.status == status)
        
        return query.order_by(Quiz.created_at.desc()).all()
    
    @staticmethod
    def get_student_quizzes(
        db: Session,
        student_id: int,
        institute_id: int
    ) -> List[Quiz]:
        """Get all published quizzes for a student's enrolled classes."""
        # Get student's enrolled classes
        enrollments = db.query(Enrollment).filter(
            Enrollment.student_id == student_id
        ).all()
        
        class_ids = [e.class_id for e in enrollments]
        
        if not class_ids:
            return []
        
        # Get published quizzes for enrolled classes
        # Show quizzes that are PUBLISHED and active
        # Don't filter by start_time/end_time here - let frontend handle availability
        now = datetime.utcnow()
        quizzes = db.query(Quiz).filter(
            and_(
                Quiz.institute_id == institute_id,
                Quiz.class_id.in_(class_ids),
                Quiz.status == "PUBLISHED",
                Quiz.is_active == True
            )
        ).order_by(Quiz.created_at.desc()).all()
        
        return quizzes
    
    @staticmethod
    def publish_quiz(
        db: Session,
        quiz_id: int,
        institute_id: int,
        teacher_id: int
    ) -> Quiz:
        """Publish a quiz."""
        quiz = QuizService.get_quiz(db, quiz_id, institute_id, teacher_id)
        
        if quiz.status == "PUBLISHED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quiz is already published"
            )
        
        if quiz.status == "CLOSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish a closed quiz"
            )
        
        # Verify quiz has questions
        questions_count = db.query(QuizQuestion).filter(
            and_(
                QuizQuestion.quiz_id == quiz_id,
                QuizQuestion.is_active == True
            )
        ).count()
        
        if questions_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish quiz without questions"
            )
        
        quiz.status = "PUBLISHED"
        db.commit()
        db.refresh(quiz)
        
        # Create notification for students in the class (and their parents)
        from app.services.notification_service import NotificationService
        from app.db.models.enrollment import Enrollment
        
        enrollments = db.query(Enrollment).filter(
            Enrollment.class_id == quiz.class_id
        ).all()
        
        if enrollments:
            NotificationService.create_notification(
                db=db,
                institute_id=institute_id,
                title="New Quiz Published",
                message=f"A new quiz '{quiz.title}' has been published",
                notification_type="QUIZ_PUBLISHED",
                target_class_id=quiz.class_id,
                notification_metadata={"quiz_id": quiz.id, "class_id": quiz.class_id},
                include_parents=True
            )
        
        return quiz
    
    @staticmethod
    def close_quiz(
        db: Session,
        quiz_id: int,
        institute_id: int,
        teacher_id: int
    ) -> Quiz:
        """Close a quiz."""
        quiz = QuizService.get_quiz(db, quiz_id, institute_id, teacher_id)
        
        quiz.status = "CLOSED"
        db.commit()
        db.refresh(quiz)
        return quiz


class QuizQuestionService:
    @staticmethod
    def create_question(
        db: Session,
        quiz_id: int,
        institute_id: int,
        teacher_id: int,
        question_data: QuizQuestionBase,
        options: Optional[List[QuizOptionBase]] = None
    ) -> QuizQuestion:
        """Create a quiz question with optional options."""
        # Verify quiz belongs to teacher
        QuizService.get_quiz(db, quiz_id, institute_id, teacher_id)
        
        question = QuizQuestion(
            quiz_id=quiz_id,
            question_text=question_data.question_text,
            question_type=question_data.question_type,
            marks=question_data.marks,
            order=question_data.order
        )
        
        db.add(question)
        db.flush()
        
        # Add options if MCQ
        if question.question_type == "MCQ" and options:
            for option_data in options:
                option = QuizOption(
                    question_id=question.id,
                    option_text=option_data.option_text,
                    is_correct=option_data.is_correct,
                    order=option_data.order
                )
                db.add(option)
        
        # Update quiz total marks
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        quiz.total_marks += question_data.marks
        db.commit()
        db.refresh(question)
        return question
    
    @staticmethod
    def update_question(
        db: Session,
        question_id: int,
        institute_id: int,
        teacher_id: int,
        question_data: QuizQuestionUpdate
    ) -> QuizQuestion:
        """Update a quiz question."""
        question = QuizQuestionService.get_question(db, question_id, institute_id, teacher_id)
        
        old_marks = question.marks
        update_data = question_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)
        
        # Update quiz total marks if marks changed
        if 'marks' in update_data:
            quiz = db.query(Quiz).filter(Quiz.id == question.quiz_id).first()
            quiz.total_marks = quiz.total_marks - old_marks + question.marks
        
        db.commit()
        db.refresh(question)
        return question
    
    @staticmethod
    def get_question(
        db: Session,
        question_id: int,
        institute_id: int,
        teacher_id: int
    ) -> QuizQuestion:
        """Get a question by ID."""
        question = db.query(QuizQuestion).join(Quiz).filter(
            and_(
                QuizQuestion.id == question_id,
                Quiz.institute_id == institute_id,
                Quiz.created_by == teacher_id
            )
        ).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        return question


class QuizAttemptService:
    @staticmethod
    def start_attempt(
        db: Session,
        quiz_id: int,
        student_id: int,
        institute_id: int
    ) -> QuizAttempt:
        """Start a quiz attempt."""
        # Verify quiz is available
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
        
        # Check time constraints
        # Use timezone-aware UTC datetime to match database timezone-aware datetimes
        now = datetime.now(timezone.utc)
        
        if quiz.start_time:
            # Ensure start_time is timezone-aware for comparison
            if quiz.start_time.tzinfo is None:
                start_time_utc = quiz.start_time.replace(tzinfo=timezone.utc)
            else:
                start_time_utc = quiz.start_time.astimezone(timezone.utc)
            if start_time_utc > now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quiz has not started yet"
                )
        
        if quiz.end_time:
            # Ensure end_time is timezone-aware for comparison
            if quiz.end_time.tzinfo is None:
                end_time_utc = quiz.end_time.replace(tzinfo=timezone.utc)
            else:
                end_time_utc = quiz.end_time.astimezone(timezone.utc)
            if end_time_utc < now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quiz has ended"
                )
        
        # Verify student is enrolled in class
        enrollment = db.query(Enrollment).filter(
            and_(
                Enrollment.student_id == student_id,
                Enrollment.class_id == quiz.class_id
            )
        ).first()
        
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this class"
            )
        
        # Check for existing attempts
        # First check for IN_PROGRESS attempts (can resume)
        in_progress_attempt = db.query(QuizAttempt).filter(
            and_(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.student_id == student_id,
                QuizAttempt.status == "IN_PROGRESS"
            )
        ).first()
        
        if in_progress_attempt:
            return in_progress_attempt  # Return existing in-progress attempt
        
        # Check for any completed attempts (SUBMITTED or GRADED)
        if not quiz.allow_multiple_attempts:
            completed_attempt = db.query(QuizAttempt).filter(
                and_(
                    QuizAttempt.quiz_id == quiz_id,
                    QuizAttempt.student_id == student_id,
                    QuizAttempt.status.in_(["SUBMITTED", "GRADED"])
                )
            ).first()
            
            if completed_attempt:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Multiple attempts not allowed for this quiz"
                )
        
        # Create new attempt
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            student_id=student_id,
            status="IN_PROGRESS"
        )
        
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt
    
    @staticmethod
    def submit_attempt(
        db: Session,
        attempt_id: int,
        student_id: int,
        institute_id: int,
        answers: List[QuizAttemptAnswerBase]
    ) -> QuizAttempt:
        """Submit a quiz attempt with answers."""
        attempt = db.query(QuizAttempt).join(Quiz).filter(
            and_(
                QuizAttempt.id == attempt_id,
                QuizAttempt.student_id == student_id,
                Quiz.institute_id == institute_id,
                QuizAttempt.status == "IN_PROGRESS"
            )
        ).first()
        
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attempt not found or already submitted"
            )
        
        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        
        # Check time constraints - use timezone-aware UTC datetime
        now = datetime.now(timezone.utc)
        
        # Ensure quiz.end_time is timezone-aware for comparison
        if quiz.end_time:
            if quiz.end_time.tzinfo is None:
                end_time_utc = quiz.end_time.replace(tzinfo=timezone.utc)
            else:
                end_time_utc = quiz.end_time.astimezone(timezone.utc)
            if end_time_utc < now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quiz has ended"
                )
        
        # Check duration if set
        if quiz.duration_minutes:
            # Ensure started_at is timezone-aware for calculation
            if attempt.started_at.tzinfo is None:
                started_at_utc = attempt.started_at.replace(tzinfo=timezone.utc)
            else:
                started_at_utc = attempt.started_at.astimezone(timezone.utc)
            
            elapsed_seconds = (now - started_at_utc).total_seconds()
            elapsed_minutes = elapsed_seconds / 60
            if elapsed_minutes > quiz.duration_minutes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quiz time limit exceeded"
                )
        
        # Save answers and auto-evaluate MCQ
        total_marks = 0
        for answer_data in answers:
            question = db.query(QuizQuestion).filter(
                QuizQuestion.id == answer_data.question_id
            ).first()
            
            if not question:
                continue
            
            answer = QuizAttemptAnswer(
                attempt_id=attempt_id,
                question_id=answer_data.question_id,
                selected_option_id=answer_data.selected_option_id,
                descriptive_answer=answer_data.descriptive_answer
            )
            
            # Auto-evaluate MCQ
            if question.question_type == "MCQ" and answer_data.selected_option_id:
                option = db.query(QuizOption).filter(
                    QuizOption.id == answer_data.selected_option_id
                ).first()
                
                if option and option.is_correct:
                    answer.is_correct = True
                    answer.marks_obtained = question.marks
                    total_marks += question.marks
                else:
                    answer.is_correct = False
                    answer.marks_obtained = 0
            else:
                # Descriptive - needs manual grading
                answer.marks_obtained = None
                answer.is_correct = None
            
            db.add(answer)
        
        # Update attempt - ensure timezone-aware calculation
        attempt.submitted_at = now
        
        # Ensure started_at is timezone-aware for calculation
        if attempt.started_at.tzinfo is None:
            started_at_utc = attempt.started_at.replace(tzinfo=timezone.utc)
        else:
            started_at_utc = attempt.started_at.astimezone(timezone.utc)
        
        # Calculate time taken in minutes (ensure positive)
        time_taken_seconds = (now - started_at_utc).total_seconds()
        attempt.time_taken_minutes = max(0, int(time_taken_seconds / 60))
        attempt.status = "SUBMITTED"
        attempt.total_marks_obtained = total_marks
        
        # Check if any descriptive questions need manual grading
        has_descriptive = db.query(QuizQuestion).filter(
            and_(
                QuizQuestion.quiz_id == quiz.id,
                QuizQuestion.question_type == "DESCRIPTIVE",
                QuizQuestion.is_active == True
            )
        ).count() > 0
        
        # Create or update result
        result = db.query(Result).filter(
            and_(
                Result.student_id == student_id,
                Result.quiz_id == quiz.id
            )
        ).first()
        
        if not result:
            result = Result(
                institute_id=institute_id,
                student_id=student_id,
                class_id=quiz.class_id,
                subject_id=quiz.subject_id,
                quiz_id=quiz.id,
                quiz_attempt_id=attempt.id,
                result_type="QUIZ",
                total_marks=quiz.total_marks,
                marks_obtained=total_marks,
                percentage=(total_marks / quiz.total_marks * 100) if quiz.total_marks > 0 else 0,
                status="PENDING" if has_descriptive else "GRADED"
            )
            db.add(result)
        else:
            result.marks_obtained = total_marks
            result.percentage = (total_marks / quiz.total_marks * 100) if quiz.total_marks > 0 else 0
            result.quiz_attempt_id = attempt.id
            result.status = "PENDING" if has_descriptive else "GRADED"
        
        # Create notification for teacher when student submits quiz
        try:
            from app.services.notification_service import NotificationService
            from app.db.models.user import User
            import logging
            logger = logging.getLogger(__name__)
            
            student = db.query(User).filter(User.id == student_id).first()
            student_name = student.name if student else "A student"
            
            # Notify the teacher who created the quiz
            if quiz.created_by:
                NotificationService.create_notification(
                    db=db,
                    institute_id=institute_id,
                    title="New Quiz Submission",
                    message=f"{student_name} has submitted the quiz '{quiz.title}'. "
                           f"{'Manual grading required for descriptive questions.' if has_descriptive else 'Quiz is fully graded.'}",
                    notification_type="QUIZ_SUBMITTED",
                    target_user_id=quiz.created_by,
                    notification_metadata={
                        "quiz_id": quiz.id,
                        "quiz_title": quiz.title,
                        "attempt_id": attempt.id,
                        "student_id": student_id,
                        "student_name": student_name,
                        "needs_grading": has_descriptive
                    }
                )
        except Exception as e:
            # Don't fail quiz submission if notification fails
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create notification for quiz submission: {str(e)}")
        
        db.commit()
        db.refresh(attempt)
        return attempt
    
    @staticmethod
    def get_student_attempts(
        db: Session,
        student_id: int,
        institute_id: int,
        quiz_id: Optional[int] = None
    ) -> List[QuizAttempt]:
        """Get all quiz attempts by a student."""
        query = db.query(QuizAttempt).join(Quiz).filter(
            and_(
                QuizAttempt.student_id == student_id,
                Quiz.institute_id == institute_id
            )
        )
        
        if quiz_id:
            query = query.filter(QuizAttempt.quiz_id == quiz_id)
        
        return query.order_by(QuizAttempt.started_at.desc()).all()
    
    @staticmethod
    def get_quiz_attempts(
        db: Session,
        quiz_id: int,
        institute_id: int,
        teacher_id: int
    ) -> List[QuizAttempt]:
        """Get all attempts for a quiz (teacher only)."""
        # Verify quiz belongs to teacher
        QuizService.get_quiz(db, quiz_id, institute_id, teacher_id)
        
        return db.query(QuizAttempt).filter(
            QuizAttempt.quiz_id == quiz_id
        ).order_by(QuizAttempt.started_at.desc()).all()
