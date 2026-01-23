from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.timetable import TimetableWithSlots
from app.services.timetable_service import TimetableService, TimetableSlotService
from app.utils.dependencies import get_teacher

router = APIRouter(prefix="/timetable", tags=["teacher-timetable"])


@router.get("", response_model=TimetableWithSlots)
async def get_my_timetable(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Get own timetable (Teacher only)."""
    institute_id = request.state.institute_id
    timetable = TimetableService.get_user_timetable(db, current_user.id, institute_id)
    
    if not timetable:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timetable not found"
        )
    
    # Get slots with assignments
    slots = TimetableSlotService.get_timetable_slots(db, timetable.id, institute_id)
    
    # Format slots with assignments
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
                "id": assignment.id,
                "slot_id": assignment.slot_id,
                "subject_id": assignment.subject_id,
                "teacher_id": assignment.teacher_id,
                "room": assignment.room,
                "is_active": assignment.is_active,
                "created_at": assignment.created_at,
                "subject_name": subject.name if subject else None,
                "teacher_name": teacher_name
            })
        
        formatted_slots.append({
            "id": slot.id,
            "timetable_id": slot.timetable_id,
            "day_of_week": slot.day_of_week,
            "period_number": slot.period_number,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "is_active": slot.is_active,
            "created_at": slot.created_at,
            "assignments": formatted_assignments
        })
    
    from app.db.models.class_model import Class
    class_obj = db.query(Class).filter(Class.id == timetable.class_id).first()
    
    return TimetableWithSlots(
        **timetable.__dict__,
        class_name=class_obj.name if class_obj else None,
        slots=formatted_slots
    )
