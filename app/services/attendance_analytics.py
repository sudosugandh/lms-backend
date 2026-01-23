from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from fastapi import HTTPException, status
from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict
from app.db.models.attendance import Attendance
from app.db.models.class_subject import ClassSubject
from app.db.models.class_model import Class
from app.services.class_service import ClassService


class AttendanceAnalyticsService:
    @staticmethod
    def get_attendance_statistics(
        db: Session,
        institute_id: int,
        student_id: Optional[int] = None,
        class_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Calculate attendance statistics."""
        query = db.query(Attendance)
        
        # Build filter conditions
        conditions = []
        
        if student_id:
            conditions.append(Attendance.student_id == student_id)
        
        if class_id:
            conditions.append(Attendance.class_id == class_id)
            # Verify class belongs to institute
            ClassService.get_class(db, class_id, institute_id)
        
        if subject_id:
            conditions.append(Attendance.subject_id == subject_id)
        
        if start_date:
            conditions.append(Attendance.attendance_date >= start_date)
        
        if end_date:
            conditions.append(Attendance.attendance_date <= end_date)
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        # Get all records
        records = query.all()
        
        if not records:
            return {
                "total": 0,
                "present": 0,
                "absent": 0,
                "leave": 0,
                "attendance_percentage": 0.0,
                "present_percentage": 0.0,
                "absent_percentage": 0.0,
                "leave_percentage": 0.0
            }
        
        total = len(records)
        present = sum(1 for r in records if r.status == "PRESENT")
        absent = sum(1 for r in records if r.status == "ABSENT")
        leave = sum(1 for r in records if r.status == "LEAVE")
        
        attendance_percentage = (present / total * 100) if total > 0 else 0.0
        
        return {
            "total": total,
            "present": present,
            "absent": absent,
            "leave": leave,
            "attendance_percentage": round(attendance_percentage, 2),
            "present_percentage": round((present / total * 100) if total > 0 else 0.0, 2),
            "absent_percentage": round((absent / total * 100) if total > 0 else 0.0, 2),
            "leave_percentage": round((leave / total * 100) if total > 0 else 0.0, 2)
        }
    
    @staticmethod
    def get_attendance_trends(
        db: Session,
        institute_id: int,
        student_id: Optional[int] = None,
        class_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get attendance trends over time (daily)."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = db.query(Attendance).filter(
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date
        )
        
        if student_id:
            query = query.filter(Attendance.student_id == student_id)
        
        if class_id:
            query = query.filter(Attendance.class_id == class_id)
            ClassService.get_class(db, class_id, institute_id)
        
        if subject_id:
            query = query.filter(Attendance.subject_id == subject_id)
        
        records = query.all()
        
        # Group by date
        daily_stats = defaultdict(lambda: {"present": 0, "absent": 0, "leave": 0, "total": 0})
        
        for record in records:
            date_str = record.attendance_date.isoformat()
            daily_stats[date_str]["total"] += 1
            if record.status == "PRESENT":
                daily_stats[date_str]["present"] += 1
            elif record.status == "ABSENT":
                daily_stats[date_str]["absent"] += 1
            elif record.status == "LEAVE":
                daily_stats[date_str]["leave"] += 1
        
        # Convert to list and calculate percentages
        trends = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            stats = daily_stats[date_str]
            
            attendance_pct = (stats["present"] / stats["total"] * 100) if stats["total"] > 0 else 0
            
            trends.append({
                "date": date_str,
                "present": stats["present"],
                "absent": stats["absent"],
                "leave": stats["leave"],
                "total": stats["total"],
                "attendance_percentage": round(attendance_pct, 2)
            })
            
            current_date += timedelta(days=1)
        
        return trends
    
    @staticmethod
    def get_class_wise_attendance(
        db: Session,
        institute_id: int,
        teacher_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get attendance statistics grouped by class."""
        query = db.query(
            Attendance.class_id,
            func.count(Attendance.id).label('total'),
            func.sum(func.case((Attendance.status == "PRESENT", 1), else_=0)).label('present'),
            func.sum(func.case((Attendance.status == "ABSENT", 1), else_=0)).label('absent'),
            func.sum(func.case((Attendance.status == "LEAVE", 1), else_=0)).label('leave')
        )
        
        if teacher_id:
            # Get teacher's assigned classes
            assignments = db.query(ClassSubject).filter(
                ClassSubject.teacher_id == teacher_id
            ).all()
            class_ids = [a.class_id for a in assignments]
            if class_ids:
                query = query.filter(Attendance.class_id.in_(class_ids))
            else:
                return []
        
        if start_date:
            query = query.filter(Attendance.attendance_date >= start_date)
        
        if end_date:
            query = query.filter(Attendance.attendance_date <= end_date)
        
        results = query.group_by(Attendance.class_id).all()
        
        class_stats = []
        for result in results:
            class_obj = db.query(Class).filter(Class.id == result.class_id).first()
            if not class_obj or class_obj.institute_id != institute_id:
                continue
            
            total = result.total or 0
            present = result.present or 0
            attendance_pct = (present / total * 100) if total > 0 else 0.0
            
            class_stats.append({
                "class_id": result.class_id,
                "class_name": class_obj.name,
                "total": total,
                "present": present,
                "absent": result.absent or 0,
                "leave": result.leave or 0,
                "attendance_percentage": round(attendance_pct, 2)
            })
        
        return sorted(class_stats, key=lambda x: x["attendance_percentage"], reverse=True)
