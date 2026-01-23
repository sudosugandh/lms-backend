from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.class_model import AttendanceMarkRequest, AttendanceResponse
from app.services.attendance_service import AttendanceService
from app.services.attendance_analytics import AttendanceAnalyticsService
from app.services.class_service import ClassSubjectService
from app.utils.dependencies import get_teacher
from app.utils.audit import log_audit_event, AuditAction

router = APIRouter(prefix="/attendance", tags=["teacher-attendance"])


@router.post("/mark", response_model=List[AttendanceResponse], status_code=201)
async def mark_attendance(
    attendance_data: AttendanceMarkRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Mark attendance for multiple students (Teacher only)."""
    institute_id = request.state.institute_id
    
    # Verify teacher is assigned to this class-subject combination
    if attendance_data.subject_id:
        assignments = ClassSubjectService.get_teacher_assignments(
            db, current_user.id, institute_id
        )
        is_assigned = any(
            a.class_id == attendance_data.class_id and 
            a.subject_id == attendance_data.subject_id 
            for a in assignments
        )
        
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to teach this subject in this class"
            )
    
    # Mark attendance for all students
    results = AttendanceService.mark_bulk_attendance(
        db=db,
        institute_id=institute_id,
        class_id=attendance_data.class_id,
        subject_id=attendance_data.subject_id,
        attendance_date=attendance_data.attendance_date,
        attendance_records=attendance_data.attendance_records,
        marked_by=current_user.id
    )
    
    # Log audit event
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action=AuditAction.ATTENDANCE_MARKED,
        request=request,
        details=f"Marked attendance for {len(results)} students in class {attendance_data.class_id} on {attendance_data.attendance_date}"
    )
    
    # Format response with names
    formatted_results = []
    for attendance in results:
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


@router.get("/history", response_model=List[AttendanceResponse])
async def get_attendance_history(
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    current_user: User = Depends(get_teacher)
):
    """Get attendance history for classes/subjects assigned to the teacher."""
    institute_id = request.state.institute_id
    
    attendance_records = AttendanceService.get_teacher_class_attendance(
        db=db,
        teacher_id=current_user.id,
        institute_id=institute_id,
        class_id=class_id,
        subject_id=subject_id
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
