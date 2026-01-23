from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.class_model import AttendanceResponse
from app.services.attendance_service import AttendanceService
from app.services.attendance_analytics import AttendanceAnalyticsService
from app.utils.dependencies import get_student

router = APIRouter(prefix="/attendance", tags=["student-attendance"])


@router.get("", response_model=List[AttendanceResponse])
async def get_my_attendance(
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_student)
):
    """Get own attendance records (Student only)."""
    institute_id = request.state.institute_id
    
    attendance_records = AttendanceService.get_student_attendance(
        db=db,
        student_id=current_user.id,
        institute_id=institute_id,
        class_id=class_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Format response with names
    formatted_results = []
    for attendance in attendance_records:
        student = db.query(User).filter(User.id == attendance.student_id).first()
        from app.db.models.class_model import Class
        class_obj = db.query(Class).filter(Class.id == attendance.class_id).first()
        
        subject_name = None
        if attendance.subject_id:
            from app.db.models.subject import Subject
            subject = db.query(Subject).filter(Subject.id == attendance.subject_id).first()
            if subject:
                subject_name = subject.name
        
        formatted_results.append(AttendanceResponse(
            id=attendance.id,
            student_id=attendance.student_id,
            class_id=attendance.class_id,
            subject_id=attendance.subject_id,
            attendance_date=attendance.attendance_date,
            status=attendance.status,
            remarks=attendance.remarks,
            marked_by=attendance.marked_by,
            created_at=attendance.created_at,
            student_name=student.name if student else "",
            class_name=class_obj.name if class_obj else "",
            subject_name=subject_name
        ))
    
    return formatted_results


@router.get("/analytics/statistics")
async def get_my_attendance_statistics(
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_student)
):
    """Get attendance statistics for the student (Student only)."""
    institute_id = request.state.institute_id
    
    stats = AttendanceAnalyticsService.get_attendance_statistics(
        db=db,
        institute_id=institute_id,
        student_id=current_user.id,
        class_id=class_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return stats


@router.get("/analytics/trends")
async def get_my_attendance_trends(
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = Query(None),
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_student)
):
    """Get attendance trends over time for the student (Student only)."""
    institute_id = request.state.institute_id
    
    trends = AttendanceAnalyticsService.get_attendance_trends(
        db=db,
        institute_id=institute_id,
        student_id=current_user.id,
        class_id=class_id,
        days=days
    )
    
    return trends
