from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from datetime import datetime
from typing import List, Optional
from app.db.models.assignment import Assignment, AssignmentSubmission
from app.db.models.class_model import Class
from app.db.models.subject import Subject
from app.db.models.class_subject import ClassSubject
from app.db.models.enrollment import Enrollment
from app.db.models.user import User
from app.db.models.result import Result
from app.schemas.quiz import AssignmentCreate, AssignmentUpdate, AssignmentSubmissionCreate
from app.services.class_service import ClassService, SubjectService, ClassSubjectService


class AssignmentService:
    @staticmethod
    def create_assignment(
        db: Session,
        institute_id: int,
        teacher_id: int,
        assignment_data: AssignmentCreate
    ) -> Assignment:
        """Create a new assignment."""
        # Verify class belongs to institute
        ClassService.get_class(db, assignment_data.class_id, institute_id)
        
        # Verify subject belongs to institute
        SubjectService.get_subject(db, assignment_data.subject_id, institute_id)
        
        # Verify teacher is assigned to this class-subject combination
        assignments = ClassSubjectService.get_teacher_assignments(
            db, teacher_id, institute_id
        )
        is_assigned = any(
            a.class_id == assignment_data.class_id and 
            a.subject_id == assignment_data.subject_id 
            for a in assignments
        )
        
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to teach this subject in this class"
            )
        
        assignment = Assignment(
            institute_id=institute_id,
            class_id=assignment_data.class_id,
            subject_id=assignment_data.subject_id,
            created_by=teacher_id,
            title=assignment_data.title,
            description=assignment_data.description,
            instructions=assignment_data.instructions,
            total_marks=assignment_data.total_marks,
            deadline=assignment_data.deadline,
            allow_late_submission=assignment_data.allow_late_submission,
            attachment_url=assignment_data.attachment_url
        )
        
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        
        # Create notification for students in the class (and their parents)
        from app.services.notification_service import NotificationService
        from app.db.models.enrollment import Enrollment
        
        enrollments = db.query(Enrollment).filter(
            Enrollment.class_id == assignment_data.class_id
        ).all()
        
        if enrollments:
            NotificationService.create_notification(
                db=db,
                institute_id=institute_id,
                title="New Assignment",
                message=f"A new assignment '{assignment.title}' has been created. Deadline: {assignment.deadline}",
                notification_type="ASSIGNMENT_DEADLINE",
                target_class_id=assignment_data.class_id,
                notification_metadata={"assignment_id": assignment.id, "deadline": assignment.deadline.isoformat()},
                include_parents=True
            )
        
        return assignment
    
    @staticmethod
    def update_assignment(
        db: Session,
        assignment_id: int,
        institute_id: int,
        teacher_id: int,
        assignment_data: AssignmentUpdate
    ) -> Assignment:
        """Update an assignment."""
        assignment = AssignmentService.get_assignment(
            db, assignment_id, institute_id, teacher_id
        )
        
        update_data = assignment_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(assignment, field, value)
        
        db.commit()
        db.refresh(assignment)
        return assignment
    
    @staticmethod
    def get_assignment(
        db: Session,
        assignment_id: int,
        institute_id: int,
        teacher_id: Optional[int] = None
    ) -> Assignment:
        """Get an assignment by ID."""
        assignment = db.query(Assignment).filter(
            and_(
                Assignment.id == assignment_id,
                Assignment.institute_id == institute_id
            )
        ).first()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        if teacher_id and assignment.created_by != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access assignments you created"
            )
        
        return assignment
    
    @staticmethod
    def get_teacher_assignments(
        db: Session,
        teacher_id: int,
        institute_id: int
    ) -> List[Assignment]:
        """Get all assignments created by a teacher (including inactive ones)."""
        return db.query(Assignment).filter(
            and_(
                Assignment.institute_id == institute_id,
                Assignment.created_by == teacher_id
            )
        ).order_by(Assignment.created_at.desc()).all()
    
    @staticmethod
    def get_student_assignments(
        db: Session,
        student_id: int,
        institute_id: int
    ) -> List[Assignment]:
        """Get all assignments for a student's enrolled classes."""
        # Get student's enrolled classes
        enrollments = db.query(Enrollment).filter(
            Enrollment.student_id == student_id
        ).all()
        
        class_ids = [e.class_id for e in enrollments]
        
        if not class_ids:
            return []
        
        # Get active assignments for enrolled classes
        now = datetime.utcnow()
        assignments = db.query(Assignment).filter(
            and_(
                Assignment.institute_id == institute_id,
                Assignment.class_id.in_(class_ids),
                Assignment.is_active == True,
                Assignment.deadline >= now  # Only show assignments not yet past deadline
            )
        ).order_by(Assignment.deadline.asc()).all()
        
        return assignments
    
    @staticmethod
    def delete_assignment(
        db: Session,
        assignment_id: int,
        institute_id: int,
        teacher_id: int
    ) -> None:
        """Delete an assignment (only if no submissions exist)."""
        assignment = AssignmentService.get_assignment(
            db, assignment_id, institute_id, teacher_id
        )
        
        # Check if there are any submissions
        submission_count = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == assignment_id
        ).count()
        
        if submission_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete assignment with existing submissions. Deactivate it instead."
            )
        
        # Delete related results first (cascade should handle this, but being explicit)
        db.query(Result).filter(
            Result.assignment_id == assignment_id
        ).delete()
        
        # Delete the assignment
        db.delete(assignment)
        db.commit()


class AssignmentSubmissionService:
    @staticmethod
    def submit_assignment(
        db: Session,
        assignment_id: int,
        student_id: int,
        institute_id: int,
        submission_data: AssignmentSubmissionCreate
    ) -> AssignmentSubmission:
        """Submit an assignment."""
        # Verify assignment exists and belongs to institute
        assignment = db.query(Assignment).filter(
            and_(
                Assignment.id == assignment_id,
                Assignment.institute_id == institute_id,
                Assignment.is_active == True
            )
        ).first()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        # Verify student is enrolled in class
        enrollment = db.query(Enrollment).filter(
            and_(
                Enrollment.student_id == student_id,
                Enrollment.class_id == assignment.class_id
            )
        ).first()
        
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this class"
            )
        
        # Check if already submitted
        existing = db.query(AssignmentSubmission).filter(
            and_(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.student_id == student_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment already submitted"
            )
        
        # Check deadline
        now = datetime.utcnow()
        is_late = now > assignment.deadline
        
        if is_late and not assignment.allow_late_submission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment deadline has passed and late submissions are not allowed"
            )
        
        # Create submission
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=student_id,
            submission_text=submission_data.submission_text,
            attachment_url=submission_data.attachment_url,
            is_late=is_late,
            status="SUBMITTED"
        )
        
        db.add(submission)
        
        # Create pending result
        result = Result(
            institute_id=institute_id,
            student_id=student_id,
            class_id=assignment.class_id,
            subject_id=assignment.subject_id,
            assignment_id=assignment.id,
            assignment_submission_id=submission.id,
            result_type="ASSIGNMENT",
            total_marks=assignment.total_marks,
            marks_obtained=0,
            percentage=0.0,
            status="PENDING"
        )
        
        db.add(result)
        db.commit()
        db.refresh(submission)
        
        # Notify teacher about submission
        from app.services.notification_service import NotificationService
        from app.db.models.user import User
        student = db.query(User).filter(User.id == student_id).first()
        student_name = student.name if student else "A student"
        
        NotificationService.create_notification(
            db=db,
            institute_id=institute_id,
            title="New Assignment Submission",
            message=f"{student_name} has submitted the assignment '{assignment.title}'",
            notification_type="ASSIGNMENT_SUBMITTED",
            target_role="TEACHER",
            target_user_id=assignment.created_by
        )
        
        return submission
    
    @staticmethod
    def grade_submission(
        db: Session,
        submission_id: int,
        institute_id: int,
        teacher_id: int,
        marks_obtained: int,
        feedback: Optional[str] = None
    ) -> AssignmentSubmission:
        """Grade an assignment submission."""
        submission = db.query(AssignmentSubmission).join(Assignment).filter(
            and_(
                AssignmentSubmission.id == submission_id,
                Assignment.institute_id == institute_id
            )
        ).first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        assignment = submission.assignment
        
        # Verify teacher created this assignment
        if assignment.created_by != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only grade assignments you created"
            )
        
        # Validate marks
        if marks_obtained < 0 or marks_obtained > assignment.total_marks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Marks must be between 0 and {assignment.total_marks}"
            )
        
        # Update submission
        now = datetime.utcnow()
        submission.marks_obtained = marks_obtained
        submission.feedback = feedback
        submission.graded_by = teacher_id
        submission.graded_at = now
        submission.status = "GRADED"
        
        # Update result
        result = db.query(Result).filter(
            Result.assignment_submission_id == submission_id
        ).first()
        
        if result:
            result.marks_obtained = marks_obtained
            result.percentage = (marks_obtained / assignment.total_marks * 100) if assignment.total_marks > 0 else 0
            result.status = "GRADED"
            result.updated_at = now
        
        db.commit()
        db.refresh(submission)
        
        # Notify student about grading
        from app.services.notification_service import NotificationService
        percentage = (marks_obtained / assignment.total_marks * 100) if assignment.total_marks > 0 else 0
        
        NotificationService.create_notification(
            db=db,
            institute_id=institute_id,
            title="Assignment Graded",
            message=f"Your assignment '{assignment.title}' has been graded. Score: {marks_obtained}/{assignment.total_marks} ({percentage:.1f}%)",
            notification_type="ASSIGNMENT_GRADED",
            target_user_id=submission.student_id
        )
        
        return submission
    
    @staticmethod
    def get_student_submissions(
        db: Session,
        student_id: int,
        institute_id: int,
        assignment_id: Optional[int] = None
    ) -> List[AssignmentSubmission]:
        """Get all assignment submissions by a student."""
        query = db.query(AssignmentSubmission).join(Assignment).filter(
            and_(
                AssignmentSubmission.student_id == student_id,
                Assignment.institute_id == institute_id
            )
        )
        
        if assignment_id:
            query = query.filter(AssignmentSubmission.assignment_id == assignment_id)
        
        return query.order_by(AssignmentSubmission.submitted_at.desc()).all()
    
    @staticmethod
    def get_assignment_submissions(
        db: Session,
        assignment_id: int,
        institute_id: int,
        teacher_id: int
    ) -> List[AssignmentSubmission]:
        """Get all submissions for an assignment (teacher only)."""
        # Verify assignment belongs to teacher
        AssignmentService.get_assignment(db, assignment_id, institute_id, teacher_id)
        
        return db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == assignment_id
        ).order_by(AssignmentSubmission.submitted_at.desc()).all()
