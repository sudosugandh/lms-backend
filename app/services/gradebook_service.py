from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from fastapi import HTTPException, status
from typing import List, Optional, Tuple, Dict
from datetime import datetime
import json

from app.db.models.gradebook import GradebookEntry, GradebookHistory, GradeDistribution, TermType
from app.db.models.result import Result, ResultType
from app.db.models.user import User
from app.db.models.class_model import Class
from app.db.models.subject import Subject
from app.services.class_service import ClassService, SubjectService


class GradebookService:
    # Letter grade mapping based on percentage
    GRADE_SCALE = {
        (90, 100): ("A+", 4.0),
        (85, 89.99): ("A", 3.7),
        (80, 84.99): ("B+", 3.3),
        (75, 79.99): ("B", 3.0),
        (70, 74.99): ("C+", 2.7),
        (65, 69.99): ("C", 2.3),
        (60, 64.99): ("D", 2.0),
        (0, 59.99): ("F", 0.0),
    }
    
    @staticmethod
    def calculate_letter_grade(percentage: float) -> Tuple[str, float]:
        """Calculate letter grade and grade point from percentage."""
        for (min_pct, max_pct), (letter, point) in GradebookService.GRADE_SCALE.items():
            if min_pct <= percentage <= max_pct:
                return (letter, point)
        return ("F", 0.0)
    
    @staticmethod
    def get_student_results_for_term(
        db: Session,
        student_id: int,
        class_id: int,
        subject_id: int,
        institute_id: int,
        academic_year: str,
        term: TermType
    ) -> Dict[str, List[Result]]:
        """Get all results for a student in a specific term, grouped by type."""
        # For now, we'll use all results. In future, we can add term filtering
        # based on quiz/assignment dates matching the term period
        quiz_results = db.query(Result).filter(
            and_(
                Result.student_id == student_id,
                Result.class_id == class_id,
                Result.subject_id == subject_id,
                Result.institute_id == institute_id,
                Result.result_type == ResultType.QUIZ,
                Result.status == "GRADED"
            )
        ).all()
        
        assignment_results = db.query(Result).filter(
            and_(
                Result.student_id == student_id,
                Result.class_id == class_id,
                Result.subject_id == subject_id,
                Result.institute_id == institute_id,
                Result.result_type == ResultType.ASSIGNMENT,
                Result.status == "GRADED"
            )
        ).all()
        
        # Exam results - for now, we'll treat exams as quizzes
        # In future, we can add a separate exam model
        exam_results = []  # Placeholder for future exam system
        
        return {
            "quizzes": quiz_results,
            "assignments": assignment_results,
            "exams": exam_results
        }
    
    @staticmethod
    def calculate_weighted_scores(
        results: List[Result],
        weight: float
    ) -> Tuple[float, float, float]:
        """Calculate total, obtained, and weighted scores from results."""
        if not results:
            return (0.0, 0.0, 0.0)
        
        total_marks = sum(r.total_marks for r in results)
        obtained_marks = sum(r.marks_obtained for r in results)
        
        if total_marks == 0:
            weighted_score = 0.0
        else:
            percentage = (obtained_marks / total_marks) * 100
            # Weighted score is percentage * weight (normalized to 100)
            weighted_score = percentage * weight
        
        return (total_marks, obtained_marks, weighted_score)
    
    @staticmethod
    def calculate_gradebook_entry(
        db: Session,
        student_id: int,
        class_id: int,
        subject_id: int,
        institute_id: int,
        academic_year: str,
        term: TermType,
        quiz_weight: float,
        assignment_weight: float,
        exam_weight: float,
        created_by: Optional[int] = None
    ) -> GradebookEntry:
        """Calculate and create/update a gradebook entry."""
        # Verify weights sum to 1.0
        total_weight = quiz_weight + assignment_weight + exam_weight
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Weights must sum to 1.0. Current sum: {total_weight}"
            )
        
        # Verify student, class, subject belong to institute
        from app.db.models.user import UserRole
        student = db.query(User).filter(
            and_(
                User.id == student_id,
                User.institute_id == institute_id,
                User.role == UserRole.STUDENT
            )
        ).first()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        ClassService.get_class(db, class_id, institute_id)
        SubjectService.get_subject(db, subject_id, institute_id)
        
        # Get existing entry or create new
        entry = db.query(GradebookEntry).filter(
            and_(
                GradebookEntry.student_id == student_id,
                GradebookEntry.class_id == class_id,
                GradebookEntry.subject_id == subject_id,
                GradebookEntry.academic_year == academic_year,
                GradebookEntry.term == term
            )
        ).first()
        
        # Get results for this term
        results = GradebookService.get_student_results_for_term(
            db, student_id, class_id, subject_id, institute_id, academic_year, term
        )
        
        # Calculate weighted scores
        quiz_total, quiz_obtained, quiz_weighted = GradebookService.calculate_weighted_scores(
            results["quizzes"], quiz_weight
        )
        
        assignment_total, assignment_obtained, assignment_weighted = GradebookService.calculate_weighted_scores(
            results["assignments"], assignment_weight
        )
        
        exam_total, exam_obtained, exam_weighted = GradebookService.calculate_weighted_scores(
            results["exams"], exam_weight
        )
        
        # Calculate final scores
        total_marks = quiz_total + assignment_total + exam_total
        obtained_marks = quiz_obtained + assignment_obtained + exam_obtained
        
        # Calculate percentage (sum of weighted scores)
        percentage = quiz_weighted + assignment_weighted + exam_weighted
        
        # Calculate letter grade
        letter_grade, grade_point = GradebookService.calculate_letter_grade(percentage)
        
        if entry:
            # Update existing entry
            old_data = {
                "quiz_weighted_score": entry.quiz_weighted_score,
                "assignment_weighted_score": entry.assignment_weighted_score,
                "exam_weighted_score": entry.exam_weighted_score,
                "percentage": entry.percentage,
                "letter_grade": entry.letter_grade
            }
            
            entry.quiz_weight = quiz_weight
            entry.assignment_weight = assignment_weight
            entry.exam_weight = exam_weight
            entry.quiz_total_marks = quiz_total
            entry.quiz_obtained_marks = quiz_obtained
            entry.quiz_weighted_score = quiz_weighted
            entry.assignment_total_marks = assignment_total
            entry.assignment_obtained_marks = assignment_obtained
            entry.assignment_weighted_score = assignment_weighted
            entry.exam_total_marks = exam_total
            entry.exam_obtained_marks = exam_obtained
            entry.exam_weighted_score = exam_weighted
            entry.total_marks = total_marks
            entry.obtained_marks = obtained_marks
            entry.percentage = percentage
            entry.letter_grade = letter_grade
            entry.grade_point = grade_point
            entry.updated_at = datetime.utcnow()
            
            new_data = {
                "quiz_weighted_score": quiz_weighted,
                "assignment_weighted_score": assignment_weighted,
                "exam_weighted_score": exam_weighted,
                "percentage": percentage,
                "letter_grade": letter_grade
            }
            
            # Log history
            GradebookService.log_history(
                db, entry.id, created_by, "UPDATED",
                json.dumps(old_data), json.dumps(new_data)
            )
        else:
            # Create new entry
            entry = GradebookEntry(
                institute_id=institute_id,
                student_id=student_id,
                class_id=class_id,
                subject_id=subject_id,
                academic_year=academic_year,
                term=term,
                quiz_weight=quiz_weight,
                assignment_weight=assignment_weight,
                exam_weight=exam_weight,
                quiz_total_marks=quiz_total,
                quiz_obtained_marks=quiz_obtained,
                quiz_weighted_score=quiz_weighted,
                assignment_total_marks=assignment_total,
                assignment_obtained_marks=assignment_obtained,
                assignment_weighted_score=assignment_weighted,
                exam_total_marks=exam_total,
                exam_obtained_marks=exam_obtained,
                exam_weighted_score=exam_weighted,
                total_marks=total_marks,
                obtained_marks=obtained_marks,
                percentage=percentage,
                letter_grade=letter_grade,
                grade_point=grade_point,
                created_by=created_by,
                status="DRAFT"
            )
            db.add(entry)
            db.flush()
            
            # Log history
            GradebookService.log_history(
                db, entry.id, created_by, "CREATED",
                None, json.dumps({"percentage": percentage, "letter_grade": letter_grade})
            )
        
        db.commit()
        db.refresh(entry)
        return entry
    
    @staticmethod
    def log_history(
        db: Session,
        entry_id: int,
        changed_by: Optional[int],
        change_type: str,
        old_value: Optional[str],
        new_value: Optional[str],
        change_reason: Optional[str] = None
    ):
        """Log a change to gradebook history."""
        history = GradebookHistory(
            gradebook_entry_id=entry_id,
            changed_by=changed_by,
            change_type=change_type,
            old_value=old_value,
            new_value=new_value,
            change_reason=change_reason
        )
        db.add(history)
    
    @staticmethod
    def get_gradebook_entries(
        db: Session,
        institute_id: int,
        class_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        student_id: Optional[int] = None,
        academic_year: Optional[str] = None,
        term: Optional[TermType] = None,
        status: Optional[str] = None
    ) -> List[GradebookEntry]:
        """Get gradebook entries with filters."""
        query = db.query(GradebookEntry).filter(
            GradebookEntry.institute_id == institute_id
        )
        
        if class_id:
            query = query.filter(GradebookEntry.class_id == class_id)
        
        if subject_id:
            query = query.filter(GradebookEntry.subject_id == subject_id)
        
        if student_id:
            query = query.filter(GradebookEntry.student_id == student_id)
        
        if academic_year:
            query = query.filter(GradebookEntry.academic_year == academic_year)
        
        if term:
            query = query.filter(GradebookEntry.term == term)
        
        if status:
            query = query.filter(GradebookEntry.status == status)
        
        return query.order_by(
            GradebookEntry.academic_year.desc(),
            GradebookEntry.term,
            GradebookEntry.percentage.desc()
        ).all()
    
    @staticmethod
    def get_gradebook_entry(
        db: Session,
        entry_id: int,
        institute_id: int
    ) -> GradebookEntry:
        """Get a specific gradebook entry."""
        entry = db.query(GradebookEntry).filter(
            and_(
                GradebookEntry.id == entry_id,
                GradebookEntry.institute_id == institute_id
            )
        ).first()
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gradebook entry not found"
            )
        
        return entry
    
    @staticmethod
    def update_gradebook_entry(
        db: Session,
        entry_id: int,
        institute_id: int,
        updated_by: int,
        quiz_weight: Optional[float] = None,
        assignment_weight: Optional[float] = None,
        exam_weight: Optional[float] = None,
        status: Optional[str] = None,
        remarks: Optional[str] = None
    ) -> GradebookEntry:
        """Update a gradebook entry."""
        entry = GradebookService.get_gradebook_entry(db, entry_id, institute_id)
        
        old_data = {
            "quiz_weight": entry.quiz_weight,
            "assignment_weight": entry.assignment_weight,
            "exam_weight": entry.exam_weight,
            "status": entry.status,
            "remarks": entry.remarks
        }
        
        if quiz_weight is not None:
            entry.quiz_weight = quiz_weight
        if assignment_weight is not None:
            entry.assignment_weight = assignment_weight
        if exam_weight is not None:
            entry.exam_weight = exam_weight
        if status is not None:
            entry.status = status
        if remarks is not None:
            entry.remarks = remarks
        
        # Recalculate if weights changed
        if any([quiz_weight is not None, assignment_weight is not None, exam_weight is not None]):
            entry = GradebookService.calculate_gradebook_entry(
                db,
                entry.student_id,
                entry.class_id,
                entry.subject_id,
                entry.institute_id,
                entry.academic_year,
                entry.term,
                entry.quiz_weight,
                entry.assignment_weight,
                entry.exam_weight,
                updated_by
            )
        
        new_data = {
            "quiz_weight": entry.quiz_weight,
            "assignment_weight": entry.assignment_weight,
            "exam_weight": entry.exam_weight,
            "status": entry.status,
            "remarks": entry.remarks
        }
        
        # Log history
        GradebookService.log_history(
            db, entry.id, updated_by, "UPDATED",
            json.dumps(old_data), json.dumps(new_data)
        )
        
        db.commit()
        db.refresh(entry)
        return entry
    
    @staticmethod
    def calculate_grade_distribution(
        db: Session,
        institute_id: int,
        class_id: int,
        subject_id: Optional[int],
        academic_year: str,
        term: TermType
    ) -> GradeDistribution:
        """Calculate and store grade distribution for a class/subject/term."""
        entries = db.query(GradebookEntry).filter(
            and_(
                GradebookEntry.institute_id == institute_id,
                GradebookEntry.class_id == class_id,
                GradebookEntry.academic_year == academic_year,
                GradebookEntry.term == term,
                GradebookEntry.status == "PUBLISHED"
            )
        )
        
        if subject_id:
            entries = entries.filter(GradebookEntry.subject_id == subject_id)
        
        entries = entries.all()
        
        if not entries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No published gradebook entries found"
            )
        
        # Calculate statistics
        total_students = len(entries)
        percentages = [e.percentage for e in entries]
        average_percentage = sum(percentages) / total_students if total_students > 0 else 0.0
        highest_percentage = max(percentages) if percentages else 0.0
        lowest_percentage = min(percentages) if percentages else 0.0
        
        # Count grades
        grade_counts = {"A+": 0, "A": 0, "B+": 0, "B": 0, "C+": 0, "C": 0, "D": 0, "F": 0}
        for entry in entries:
            if entry.letter_grade:
                grade_counts[entry.letter_grade] = grade_counts.get(entry.letter_grade, 0) + 1
        
        # Get or create distribution
        distribution = db.query(GradeDistribution).filter(
            and_(
                GradeDistribution.institute_id == institute_id,
                GradeDistribution.class_id == class_id,
                GradeDistribution.subject_id == subject_id,
                GradeDistribution.academic_year == academic_year,
                GradeDistribution.term == term
            )
        ).first()
        
        if distribution:
            distribution.total_students = total_students
            distribution.a_plus_count = grade_counts["A+"]
            distribution.a_count = grade_counts["A"]
            distribution.b_plus_count = grade_counts["B+"]
            distribution.b_count = grade_counts["B"]
            distribution.c_plus_count = grade_counts["C+"]
            distribution.c_count = grade_counts["C"]
            distribution.d_count = grade_counts["D"]
            distribution.f_count = grade_counts["F"]
            distribution.average_percentage = average_percentage
            distribution.highest_percentage = highest_percentage
            distribution.lowest_percentage = lowest_percentage
            distribution.calculated_at = datetime.utcnow()
        else:
            distribution = GradeDistribution(
                institute_id=institute_id,
                class_id=class_id,
                subject_id=subject_id,
                academic_year=academic_year,
                term=term,
                total_students=total_students,
                a_plus_count=grade_counts["A+"],
                a_count=grade_counts["A"],
                b_plus_count=grade_counts["B+"],
                b_count=grade_counts["B"],
                c_plus_count=grade_counts["C+"],
                c_count=grade_counts["C"],
                d_count=grade_counts["D"],
                f_count=grade_counts["F"],
                average_percentage=average_percentage,
                highest_percentage=highest_percentage,
                lowest_percentage=lowest_percentage
            )
            db.add(distribution)
        
        db.commit()
        db.refresh(distribution)
        return distribution
