from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.class_subject import ClassSubject
from app.db.models.enrollment import Enrollment
from app.db.models.user import User
from app.db.models.class_model import Class
from app.services.class_service import ClassService


class AttendanceService:
    @staticmethod
    def mark_attendance(
        db: Session,
        institute_id: int,
        class_id: int,
        subject_id: Optional[int],
        attendance_date: date,
        student_id: int,
        status: str,
        marked_by: int,
        remarks: Optional[str] = None
    ) -> Attendance:
        """Mark attendance for a single student."""
        # Validate status
        if status not in [s.value for s in AttendanceStatus]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in AttendanceStatus]}"
            )
        
        # Verify class belongs to institute
        ClassService.get_class(db, class_id, institute_id)
        
        # Verify student belongs to institute and is enrolled in the class
        student = db.query(User).filter(
            and_(
                User.id == student_id,
                User.institute_id == institute_id,
                User.role == "STUDENT",
                User.is_active == True
            )
        ).first()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found or inactive"
            )
        
        # Check enrollment
        enrollment = db.query(Enrollment).filter(
            and_(
                Enrollment.student_id == student_id,
                Enrollment.class_id == class_id
            )
        ).first()
        
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student is not enrolled in this class"
            )
        
        # If subject_id provided, verify it's assigned to the class
        if subject_id:
            class_subject = db.query(ClassSubject).filter(
                and_(
                    ClassSubject.class_id == class_id,
                    ClassSubject.subject_id == subject_id
                )
            ).first()
            
            if not class_subject:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subject is not assigned to this class"
                )
        
        # Check if attendance already exists (unique constraint)
        existing = db.query(Attendance).filter(
            and_(
                Attendance.student_id == student_id,
                Attendance.class_id == class_id,
                Attendance.subject_id == subject_id,
                Attendance.attendance_date == attendance_date
            )
        ).first()
        
        if existing:
            # Update existing record
            existing.status = status
            existing.remarks = remarks
            existing.marked_by = marked_by
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new attendance record
        new_attendance = Attendance(
            student_id=student_id,
            class_id=class_id,
            subject_id=subject_id,
            attendance_date=attendance_date,
            status=status,
            marked_by=marked_by,
            remarks=remarks
        )
        
        db.add(new_attendance)
        db.commit()
        db.refresh(new_attendance)
        return new_attendance
    
    @staticmethod
    def mark_bulk_attendance(
        db: Session,
        institute_id: int,
        class_id: int,
        subject_id: Optional[int],
        attendance_date: date,
        attendance_records: List[dict],
        marked_by: int
    ) -> List[Attendance]:
        """Mark attendance for multiple students at once."""
        results = []
        
        for record in attendance_records:
            student_id = record.get("student_id")
            status = record.get("status")
            remarks = record.get("remarks")
            
            if not student_id or not status:
                continue
            
            try:
                attendance = AttendanceService.mark_attendance(
                    db=db,
                    institute_id=institute_id,
                    class_id=class_id,
                    subject_id=subject_id,
                    attendance_date=attendance_date,
                    student_id=student_id,
                    status=status,
                    marked_by=marked_by,
                    remarks=remarks
                )
                results.append(attendance)
            except HTTPException:
                # Skip records that fail validation
                continue
        
        return results
    
    @staticmethod
    def get_class_attendance(
        db: Session,
        class_id: int,
        institute_id: int,
        attendance_date: Optional[date] = None,
        subject_id: Optional[int] = None
    ) -> List[Attendance]:
        """Get attendance records for a class."""
        # Verify class belongs to institute
        ClassService.get_class(db, class_id, institute_id)
        
        query = db.query(Attendance).filter(
            Attendance.class_id == class_id
        )
        
        if attendance_date:
            query = query.filter(Attendance.attendance_date == attendance_date)
        
        if subject_id:
            query = query.filter(Attendance.subject_id == subject_id)
        
        return query.order_by(Attendance.attendance_date.desc()).all()
    
    @staticmethod
    def get_student_attendance(
        db: Session,
        student_id: int,
        institute_id: int,
        class_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Attendance]:
        """Get attendance records for a student."""
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
        
        query = db.query(Attendance).filter(
            Attendance.student_id == student_id
        )
        
        if class_id:
            query = query.filter(Attendance.class_id == class_id)
        
        if start_date:
            query = query.filter(Attendance.attendance_date >= start_date)
        
        if end_date:
            query = query.filter(Attendance.attendance_date <= end_date)
        
        return query.order_by(Attendance.attendance_date.desc()).all()
    
    @staticmethod
    def get_teacher_class_attendance(
        db: Session,
        teacher_id: int,
        institute_id: int,
        class_id: Optional[int] = None,
        subject_id: Optional[int] = None
    ) -> List[Attendance]:
        """Get attendance records for classes/subjects assigned to a teacher."""
        # Get teacher's assigned classes and subjects
        assignments = db.query(ClassSubject).filter(
            ClassSubject.teacher_id == teacher_id
        ).all()
        
        if not assignments:
            return []
        
        # Build query for attendance in assigned classes/subjects
        class_ids = [a.class_id for a in assignments]
        subject_ids = [a.subject_id for a in assignments]
        
        query = db.query(Attendance).filter(
            and_(
                Attendance.class_id.in_(class_ids),
                or_(
                    Attendance.subject_id.in_(subject_ids),
                    Attendance.subject_id.is_(None)
                )
            )
        )
        
        if class_id:
            # Verify teacher is assigned to this class
            if class_id not in class_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to this class"
                )
            query = query.filter(Attendance.class_id == class_id)
        
        if subject_id:
            # Verify teacher is assigned to this subject
            if subject_id not in subject_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to this subject"
                )
            query = query.filter(Attendance.subject_id == subject_id)
        
        return query.order_by(Attendance.attendance_date.desc()).all()
    
    @staticmethod
    def get_institute_attendance(
        db: Session,
        institute_id: int,
        class_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Attendance]:
        """Get attendance records for an entire institute (Admin only)."""
        # Get all classes in the institute
        classes = db.query(Class).filter(
            and_(
                Class.institute_id == institute_id,
                Class.is_active == True
            )
        ).all()
        
        if not classes:
            return []
        
        class_ids = [c.id for c in classes]
        
        # Build query
        query = db.query(Attendance).filter(
            Attendance.class_id.in_(class_ids)
        )
        
        if class_id:
            # Verify class belongs to institute
            if class_id not in class_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Class not found in this institute"
                )
            query = query.filter(Attendance.class_id == class_id)
        
        if start_date:
            query = query.filter(Attendance.attendance_date >= start_date)
        
        if end_date:
            query = query.filter(Attendance.attendance_date <= end_date)
        
        return query.order_by(Attendance.attendance_date.desc()).all()