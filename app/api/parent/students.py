from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.parent import StudentInfo
from app.schemas.class_model import AttendanceResponse
from app.services.parent_service import ParentService
from app.services.attendance_service import AttendanceService
from app.services.attendance_analytics import AttendanceAnalyticsService
from app.utils.dependencies import get_parent

router = APIRouter(prefix="/students", tags=["parent-students"])


@router.get("", response_model=List[StudentInfo])
async def get_my_students(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_parent)
):
    """Get all students linked to the parent."""
    institute_id = request.state.institute_id
    students = ParentService.get_parent_students(db, current_user.id, institute_id)
    
    # Format response
    results = []
    for student in students:
        # Get student's class
        from app.db.models.enrollment import Enrollment
        enrollment = db.query(Enrollment).filter(
            Enrollment.student_id == student.id
        ).first()
        
        class_name = None
        if enrollment:
            from app.db.models.class_model import Class
            class_obj = db.query(Class).filter(Class.id == enrollment.class_id).first()
            class_name = class_obj.name if class_obj else None
        
        results.append(StudentInfo(
            id=student.id,
            name=student.name,
            email=student.email,
            class_name=class_name,
            class_id=enrollment.class_id if enrollment else None
        ))
    
    return results


@router.get("/{student_id}/attendance", response_model=List[AttendanceResponse])
async def get_student_attendance(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_parent)
):
    """Get attendance records for a linked student (Parent only)."""
    institute_id = request.state.institute_id
    
    # Verify parent has access to this student
    if not ParentService.verify_parent_student_link(db, current_user.id, student_id, institute_id):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student is not linked to this parent."
        )
    
    attendance_records = AttendanceService.get_student_attendance(
        db, student_id, institute_id, start_date=start_date, end_date=end_date
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


@router.get("/{student_id}/attendance/analytics/statistics")
async def get_student_attendance_statistics(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_parent)
):
    """Get attendance statistics for a linked student (Parent only)."""
    institute_id = request.state.institute_id
    
    # Verify parent has access to this student
    if not ParentService.verify_parent_student_link(db, current_user.id, student_id, institute_id):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student is not linked to this parent."
        )
    
    stats = AttendanceAnalyticsService.get_attendance_statistics(
        db=db,
        institute_id=institute_id,
        student_id=student_id,
        class_id=class_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return stats


@router.get("/{student_id}/attendance/analytics/trends")
async def get_student_attendance_trends(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = Query(None),
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_parent)
):
    """Get attendance trends over time for a linked student (Parent only)."""
    institute_id = request.state.institute_id
    
    # Verify parent has access to this student
    if not ParentService.verify_parent_student_link(db, current_user.id, student_id, institute_id):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student is not linked to this parent."
        )
    
    trends = AttendanceAnalyticsService.get_attendance_trends(
        db=db,
        institute_id=institute_id,
        student_id=student_id,
        class_id=class_id,
        days=days
    )
    
    return trends


@router.get("/{student_id}/results")
async def get_student_results(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_parent)
):
    """Get results for a linked student (Parent only)."""
    institute_id = request.state.institute_id
    
    # Verify parent has access to this student
    if not ParentService.verify_parent_student_link(db, current_user.id, student_id, institute_id):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student is not linked to this parent."
        )
    
    from app.services.result_service import ResultService
    results = ResultService.get_results_for_student(db, student_id, institute_id)
    
    # Format response
    formatted_results = []
    for result in results:
        formatted_results.append({
            "id": result.id,
            "score": result.marks_obtained,
            "max_score": result.total_marks,
            "percentage": result.percentage,
            "status": result.status,
            "subject_name": result.subject.name if result.subject else None,
            "class_name": result.class_.name if result.class_ else None,
            "quiz_title": result.quiz.title if result.quiz else None,
            "assignment_title": result.assignment.title if result.assignment else None,
            "feedback": result.feedback,
            "created_at": result.created_at
        })
    
    return formatted_results


@router.get("/{student_id}/assignments")
async def get_student_assignments(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_parent)
):
    """Get assignments for a linked student (Parent only)."""
    institute_id = request.state.institute_id
    
    # Verify parent has access to this student
    if not ParentService.verify_parent_student_link(db, current_user.id, student_id, institute_id):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student is not linked to this parent."
        )
    
    from app.services.assignment_service import AssignmentService
    assignments = AssignmentService.get_student_assignments(db, student_id, institute_id)
    
    # Format response
    formatted = []
    for assignment in assignments:
        formatted.append({
            "id": assignment.id,
            "title": assignment.title,
            "description": assignment.description,
            "deadline": assignment.deadline,
            "total_marks": assignment.total_marks,
            "status": assignment.status,
            "class_name": assignment.class_.name if assignment.class_ else None,
            "subject_name": assignment.subject.name if assignment.subject else None,
            "created_at": assignment.created_at
        })
    
    return formatted


@router.get("/{student_id}/timetable")
async def get_student_timetable(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_parent)
):
    """Get timetable for a linked student (Parent only)."""
    institute_id = request.state.institute_id
    
    # Verify parent has access to this student
    if not ParentService.verify_parent_student_link(db, current_user.id, student_id, institute_id):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student is not linked to this parent."
        )
    
    from app.services.timetable_service import TimetableService, TimetableSlotService
    timetable = TimetableService.get_user_timetable(db, student_id, institute_id)
    
    if not timetable:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timetable not found"
        )
    
    # Get slots with assignments
    slots = TimetableSlotService.get_timetable_slots(db, timetable.id, institute_id)
    
    # Format slots
    formatted_slots = []
    for slot in slots:
        from app.db.models.timetable import TimetableAssignment
        slot_assignments = db.query(TimetableAssignment).filter(
            TimetableAssignment.slot_id == slot.id,
            TimetableAssignment.is_active == True
        ).all()
        
        formatted_assignments = []
        for assignment in slot_assignments:
            from app.db.models.subject import Subject
            subject = db.query(Subject).filter(Subject.id == assignment.subject_id).first()
            
            teacher_name = None
            if assignment.teacher_id:
                teacher = db.query(User).filter(User.id == assignment.teacher_id).first()
                teacher_name = teacher.name if teacher else None
            
            formatted_assignments.append({
                "subject_name": subject.name if subject else None,
                "teacher_name": teacher_name,
                "room": assignment.room
            })
        
        formatted_slots.append({
            "day_of_week": slot.day_of_week,
            "period_number": slot.period_number,
            "start_time": slot.start_time.isoformat(),
            "end_time": slot.end_time.isoformat(),
            "assignments": formatted_assignments
        })
    
    return {
        "timetable_name": timetable.name,
        "class_name": timetable.class_.name if timetable.class_ else None,
        "slots": formatted_slots
    }
