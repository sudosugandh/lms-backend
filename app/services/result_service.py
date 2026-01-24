from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from typing import List, Optional
from app.db.models.result import Result, Grading
from app.db.models.user import User
from app.db.models.quiz import Quiz
from app.db.models.assignment import Assignment
from app.services.class_service import ClassService, SubjectService


class ResultService:
    @staticmethod
    def get_student_results(
        db: Session,
        student_id: int,
        institute_id: int,
        class_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        result_type: Optional[str] = None
    ) -> List[Result]:
        """Get all results for a student."""
        # Verify student belongs to institute
        student = db.query(User).filter(
            and_(
                User.id == student_id,
                User.institute_id == institute_id,
                User.role == "STUDENT"
            )
        ).first()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        query = db.query(Result).filter(
            and_(
                Result.student_id == student_id,
                Result.institute_id == institute_id
            )
        )
        
        if class_id:
            query = query.filter(Result.class_id == class_id)
        
        if subject_id:
            query = query.filter(Result.subject_id == subject_id)
        
        if result_type:
            query = query.filter(Result.result_type == result_type)
        
        return query.order_by(Result.created_at.desc()).all()
    
    @staticmethod
    def get_class_results(
        db: Session,
        class_id: int,
        institute_id: int,
        subject_id: Optional[int] = None,
        result_type: Optional[str] = None
    ) -> List[Result]:
        """Get all results for a class (admin/teacher only)."""
        # Verify class belongs to institute
        ClassService.get_class(db, class_id, institute_id)
        
        query = db.query(Result).filter(
            and_(
                Result.class_id == class_id,
                Result.institute_id == institute_id
            )
        )
        
        if subject_id:
            query = query.filter(Result.subject_id == subject_id)
        
        if result_type:
            query = query.filter(Result.result_type == result_type)
        
        return query.order_by(Result.marks_obtained.desc()).all()
    
    @staticmethod
    def get_institute_results(
        db: Session,
        institute_id: int,
        class_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        result_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Result]:
        """Get all results for an institute (admin only)."""
        query = db.query(Result).filter(
            Result.institute_id == institute_id
        )
        
        if class_id:
            query = query.filter(Result.class_id == class_id)
        
        if subject_id:
            query = query.filter(Result.subject_id == subject_id)
        
        if result_type:
            query = query.filter(Result.result_type == result_type)
        
        if status:
            query = query.filter(Result.status == status)
        
        return query.order_by(Result.created_at.desc()).all()
    
    @staticmethod
    def get_result(
        db: Session,
        result_id: int,
        institute_id: int,
        user_id: int,
        user_role: str
    ) -> Result:
        """Get a specific result by ID with authorization check."""
        result = db.query(Result).filter(
            and_(
                Result.id == result_id,
                Result.institute_id == institute_id
            )
        ).first()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Result not found"
            )
        
        # Authorization: Student can only view their own results
        # Teacher/Admin can view all results in their institute
        if user_role == "STUDENT":
            if result.student_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own results"
                )
        elif user_role not in ["TEACHER", "ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access"
            )
        
        return result


class GradingService:
    @staticmethod
    def grade_descriptive_answer(
        db: Session,
        answer_id: int,
        institute_id: int,
        teacher_id: int,
        marks_obtained: int,
        feedback: Optional[str] = None
    ):
        """Grade a descriptive quiz answer."""
        from app.db.models.quiz import QuizAttemptAnswer, QuizQuestion, QuizAttempt, Quiz
        
        answer = db.query(QuizAttemptAnswer).join(QuizAttempt).join(Quiz).filter(
            and_(
                QuizAttemptAnswer.id == answer_id,
                Quiz.institute_id == institute_id
            )
        ).first()
        
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found"
            )
        
        question = db.query(QuizQuestion).filter(
            QuizQuestion.id == answer.question_id
        ).first()
        
        # Verify question is descriptive
        if question.question_type != "DESCRIPTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This question is not descriptive and is auto-graded"
            )
        
        # Verify teacher created the quiz
        quiz = db.query(Quiz).filter(Quiz.id == question.quiz_id).first()
        if quiz.created_by != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only grade quizzes you created"
            )
        
        # Validate marks
        if marks_obtained < 0 or marks_obtained > question.marks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Marks must be between 0 and {question.marks}"
            )
        
        # Update answer
        from datetime import datetime
        now = datetime.utcnow()
        answer.marks_obtained = marks_obtained
        answer.feedback = feedback
        answer.graded_by = teacher_id
        answer.graded_at = now
        
        # Recalculate attempt total marks
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == answer.attempt_id).first()
        total_marks = db.query(func.sum(QuizAttemptAnswer.marks_obtained)).filter(
            QuizAttemptAnswer.attempt_id == attempt.id
        ).scalar() or 0
        
        attempt.total_marks_obtained = total_marks
        
        # Check if all descriptive answers are graded
        all_graded = db.query(QuizAttemptAnswer).join(QuizQuestion).filter(
            and_(
                QuizAttemptAnswer.attempt_id == attempt.id,
                QuizQuestion.question_type == "DESCRIPTIVE"
            )
        ).filter(QuizAttemptAnswer.marks_obtained.is_(None)).count() == 0
        
        if all_graded:
            attempt.status = "GRADED"
            
            # Update result
            result = db.query(Result).filter(Result.quiz_attempt_id == attempt.id).first()
            if result:
                quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
                result.marks_obtained = total_marks
                result.percentage = (total_marks / quiz.total_marks * 100) if quiz and quiz.total_marks > 0 else 0
                result.status = "GRADED"
                result.updated_at = now
                
                # Create notification for student (and their parents) when quiz is fully graded
                from app.services.notification_service import NotificationService
                quiz_obj = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
                if quiz_obj:
                    percentage = (total_marks / quiz.total_marks * 100) if quiz.total_marks > 0 else 0
                    NotificationService.create_notification(
                        db=db,
                        institute_id=quiz_obj.institute_id,
                        title="Quiz Graded",
                        message=f"Your quiz '{quiz_obj.title}' has been graded. Score: {total_marks}/{quiz.total_marks} ({percentage:.1f}%)",
                        notification_type="QUIZ_GRADED",
                        target_user_id=attempt.student_id,
                        notification_metadata={
                            "result_id": result.id,
                            "quiz_id": quiz.id,
                            "quiz_title": quiz_obj.title,
                            "marks_obtained": total_marks,
                            "total_marks": quiz.total_marks,
                            "percentage": round(percentage, 2)
                        },
                        include_parents=True
                    )
        
        db.commit()
        db.refresh(answer)
        return answer
