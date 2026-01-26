from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.timetable import (
    TimetableCreate, TimetableUpdate, TimetableResponse,
    TimetableSlotCreate, TimetableSlotUpdate, TimetableSlotResponse,
    TimetableAssignmentCreate, TimetableAssignmentUpdate, TimetableAssignmentResponse,
    TimetableWithSlots
)
from app.services.timetable_service import (
    TimetableService, TimetableSlotService, TimetableAssignmentService
)
from app.utils.dependencies import get_institute_admin

router = APIRouter(prefix="/timetables", tags=["admin-timetables"])


@router.post("", response_model=TimetableResponse, status_code=201)
async def create_timetable(
    timetable_data: TimetableCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Create a timetable for a class (Admin only)."""
    institute_id = request.state.institute_id
    timetable = TimetableService.create_timetable(
        db, institute_id, current_user.id, timetable_data
    )
    
    # Format response
    from app.db.models.class_model import Class
    class_obj = db.query(Class).filter(Class.id == timetable.class_id).first()
    
    return TimetableResponse(
        **timetable.__dict__,
        class_name=class_obj.name if class_obj else None
    )


@router.put("/{timetable_id}", response_model=TimetableResponse)
async def update_timetable(
    timetable_id: int,
    timetable_data: TimetableUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Update a timetable (Admin only)."""
    institute_id = request.state.institute_id
    timetable = TimetableService.update_timetable(
        db, timetable_id, institute_id, timetable_data
    )
    
    # Format response
    from app.db.models.class_model import Class
    class_obj = db.query(Class).filter(Class.id == timetable.class_id).first()
    
    return TimetableResponse(
        **timetable.__dict__,
        class_name=class_obj.name if class_obj else None
    )


@router.get("/classes/{class_id}", response_model=TimetableWithSlots)
async def get_class_timetable(
    class_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get timetable for a class with slots (Admin only)."""
    institute_id = request.state.institute_id
    timetable = TimetableService.get_class_timetable(db, class_id, institute_id)
    
    if not timetable:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timetable not found for this class"
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
            
            formatted_assignments.append(TimetableAssignmentResponse(
                **assignment.__dict__,
                subject_name=subject.name if subject else None,
                teacher_name=teacher_name
            ))
        
        formatted_slots.append(TimetableSlotResponse(
            **slot.__dict__,
            assignments=formatted_assignments
        ))
    
    from app.db.models.class_model import Class
    class_obj = db.query(Class).filter(Class.id == timetable.class_id).first()
    
    return TimetableWithSlots(
        **timetable.__dict__,
        class_name=class_obj.name if class_obj else None,
        slots=formatted_slots
    )


@router.post("/slots", response_model=TimetableSlotResponse, status_code=201)
async def create_slot(
    slot_data: TimetableSlotCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Create a timetable slot (Admin only)."""
    institute_id = request.state.institute_id
    return TimetableSlotService.create_slot(db, institute_id, slot_data)


@router.put("/slots/{slot_id}", response_model=TimetableSlotResponse)
async def update_slot(
    slot_id: int,
    slot_data: TimetableSlotUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Update a timetable slot (Admin only)."""
    institute_id = request.state.institute_id
    return TimetableSlotService.update_slot(db, slot_id, institute_id, slot_data)


@router.delete("/slots/{slot_id}", status_code=204)
async def delete_slot(
    slot_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Delete a timetable slot (Admin only)."""
    institute_id = request.state.institute_id
    TimetableSlotService.delete_slot(db, slot_id, institute_id)
    return None


@router.post("/assignments", response_model=TimetableAssignmentResponse, status_code=201)
async def create_assignment(
    assignment_data: TimetableAssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Create a timetable assignment (Admin only)."""
    institute_id = request.state.institute_id
    assignment = TimetableAssignmentService.create_assignment(
        db, institute_id, assignment_data
    )
    
    # Format response
    from app.db.models.subject import Subject
    subject = db.query(Subject).filter(Subject.id == assignment.subject_id).first()
    
    teacher_name = None
    if assignment.teacher_id:
        teacher = db.query(User).filter(User.id == assignment.teacher_id).first()
        teacher_name = teacher.name if teacher else None
    
    return TimetableAssignmentResponse(
        **assignment.__dict__,
        subject_name=subject.name if subject else None,
        teacher_name=teacher_name
    )


@router.put("/assignments/{assignment_id}", response_model=TimetableAssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_data: TimetableAssignmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Update a timetable assignment (Admin only)."""
    institute_id = request.state.institute_id
    assignment = TimetableAssignmentService.update_assignment(
        db, assignment_id, institute_id, assignment_data
    )
    
    # Format response
    from app.db.models.subject import Subject
    subject = db.query(Subject).filter(Subject.id == assignment.subject_id).first()
    
    teacher_name = None
    if assignment.teacher_id:
        teacher = db.query(User).filter(User.id == assignment.teacher_id).first()
        teacher_name = teacher.name if teacher else None
    
    return TimetableAssignmentResponse(
        **assignment.__dict__,
        subject_name=subject.name if subject else None,
        teacher_name=teacher_name
    )


@router.delete("/assignments/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Delete a timetable assignment (Admin only)."""
    institute_id = request.state.institute_id
    TimetableAssignmentService.delete_assignment(db, assignment_id, institute_id)
    return None
