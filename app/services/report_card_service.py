"""
Service for generating report cards in PDF format.
"""
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import HTTPException, status
from app.db.models.gradebook import GradebookEntry, TermType
from app.db.models.user import User
from app.db.models.class_model import Class
from app.db.models.institute import Institute
import json
import os
from datetime import datetime


class ReportCardService:
    """Service for generating student report cards."""
    
    @staticmethod
    def generate_report_card(
        db: Session,
        institute_id: int,
        student_id: int,
        academic_year: str,
        term: Optional[TermType] = None,
        include_remarks: bool = True,
        include_attendance: bool = True,
        include_analytics: bool = True
    ) -> dict:
        """
        Generate a report card for a student.
        
        Returns:
            dict with report_card_data and download_url (to be implemented with PDF generation)
        """
        # Get student
        from app.db.models.user import UserRole
        student = db.query(User).filter(
            User.id == student_id,
            User.institute_id == institute_id,
            User.role == UserRole.STUDENT
        ).first()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Get institute
        institute = db.query(Institute).filter(Institute.id == institute_id).first()
        
        # Get gradebook entries
        query = db.query(GradebookEntry).filter(
            GradebookEntry.student_id == student_id,
            GradebookEntry.institute_id == institute_id,
            GradebookEntry.academic_year == academic_year
        )
        
        if term:
            query = query.filter(GradebookEntry.term == term)
        
        entries = query.all()
        
        if not entries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No gradebook entries found for this student"
            )
        
        # Get class information from first entry
        class_obj = db.query(Class).filter(Class.id == entries[0].class_id).first()
        
        # Calculate overall statistics
        total_percentage = sum(e.percentage for e in entries)
        average_percentage = total_percentage / len(entries) if entries else 0.0
        
        # Get letter grade for average
        from app.services.gradebook_service import GradebookService
        avg_letter_grade, avg_grade_point = GradebookService.calculate_letter_grade(average_percentage)
        
        # Prepare report card data
        report_card_data = {
            "student": {
                "id": student.id,
                "name": student.name,
                "email": student.email,
            },
            "institute": {
                "name": institute.name if institute else "Unknown Institute",
                "address": getattr(institute, 'address', ''),
            },
            "class": {
                "id": class_obj.id if class_obj else None,
                "name": class_obj.name if class_obj else "Unknown Class",
            },
            "academic_year": academic_year,
            "term": term.value if term else "All Terms",
            "generated_at": datetime.now().isoformat(),
            "subjects": [],
            "summary": {
                "total_subjects": len(entries),
                "average_percentage": round(average_percentage, 2),
                "average_grade": avg_letter_grade,
                "average_grade_point": round(avg_grade_point, 2),
            }
        }
        
        # Add subject details
        for entry in entries:
            subject = db.query(Class).join("subjects").filter(
                Class.id == entry.class_id
            ).first()
            
            # Get subject name
            from app.db.models.subject import Subject
            subject_obj = db.query(Subject).filter(Subject.id == entry.subject_id).first()
            
            subject_data = {
                "subject_id": entry.subject_id,
                "subject_name": subject_obj.name if subject_obj else f"Subject {entry.subject_id}",
                "term": entry.term.value,
                "quiz_score": {
                    "obtained": entry.quiz_obtained_marks,
                    "total": entry.quiz_total_marks,
                    "weighted": entry.quiz_weighted_score,
                },
                "assignment_score": {
                    "obtained": entry.assignment_obtained_marks,
                    "total": entry.assignment_total_marks,
                    "weighted": entry.assignment_weighted_score,
                },
                "exam_score": {
                    "obtained": entry.exam_obtained_marks,
                    "total": entry.exam_total_marks,
                    "weighted": entry.exam_weighted_score,
                },
                "total_marks": entry.total_marks,
                "obtained_marks": entry.obtained_marks,
                "percentage": round(entry.percentage, 2),
                "letter_grade": entry.letter_grade,
                "grade_point": entry.grade_point,
            }
            
            if include_remarks and entry.remarks:
                subject_data["remarks"] = entry.remarks
            
            report_card_data["subjects"].append(subject_data)
        
        # TODO: Generate PDF file
        # For now, return JSON data
        # In production, use a PDF library like reportlab or weasyprint
        
        return {
            "report_card_data": report_card_data,
            "download_url": None,  # Will be implemented with PDF generation
            "message": "Report card data generated. PDF generation will be implemented next."
        }
