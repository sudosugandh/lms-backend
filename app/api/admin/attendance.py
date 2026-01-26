from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.class_model import AttendanceResponse
from app.services.attendance_service import AttendanceService
from app.utils.dependencies import get_institute_admin

router = APIRouter(prefix="/attendance", tags=["admin-attendance"])


@router.get("/overview", response_model=List[AttendanceResponse])
async def get_attendance_overview(
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    start_date: Optional[date] = Query(None, description="Start date for attendance records"),
    end_date: Optional[date] = Query(None, description="End date for attendance records"),
    current_user: User = Depends(get_institute_admin)
):
    """Get attendance overview for the institute (Admin only)."""
    institute_id = request.state.institute_id
    
    # Get all attendance records for the institute
    attendance_records = AttendanceService.get_institute_attendance(
        db=db,
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
