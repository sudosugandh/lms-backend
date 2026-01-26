from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from typing import List, Optional
from app.db.models.timetable import Timetable, TimetableSlot, TimetableAssignment
from app.db.models.class_model import Class
from app.db.models.subject import Subject
from app.db.models.user import User
from app.db.models.class_subject import ClassSubject
from app.db.models.enrollment import Enrollment
from app.schemas.timetable import (
    TimetableCreate, TimetableUpdate, TimetableSlotCreate, TimetableSlotUpdate,
    TimetableAssignmentCreate, TimetableAssignmentUpdate
)
from app.services.class_service import ClassService, SubjectService, ClassSubjectService


class TimetableService:
    @staticmethod
    def create_timetable(
        db: Session,
        institute_id: int,
        admin_id: int,
        timetable_data: TimetableCreate
    ) -> Timetable:
        """Create a new timetable for a class."""
        # Verify class belongs to institute
        ClassService.get_class(db, timetable_data.class_id, institute_id)
        
        timetable = Timetable(
            institute_id=institute_id,
            class_id=timetable_data.class_id,
            name=timetable_data.name,
            description=timetable_data.description,
            academic_year=timetable_data.academic_year,
            start_date=timetable_data.start_date,
            end_date=timetable_data.end_date,
            is_active=timetable_data.is_active,
            created_by=admin_id
        )
        
        db.add(timetable)
        db.commit()
        db.refresh(timetable)
        return timetable
    
    @staticmethod
    def update_timetable(
        db: Session,
        timetable_id: int,
        institute_id: int,
        timetable_data: TimetableUpdate
    ) -> Timetable:
        """Update a timetable."""
        timetable = TimetableService.get_timetable(db, timetable_id, institute_id)
        
        update_data = timetable_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(timetable, field, value)
        
        db.commit()
        db.refresh(timetable)
        return timetable
    
    @staticmethod
    def get_timetable(
        db: Session,
        timetable_id: int,
        institute_id: int
    ) -> Timetable:
        """Get a timetable by ID."""
        timetable = db.query(Timetable).filter(
            and_(
                Timetable.id == timetable_id,
                Timetable.institute_id == institute_id
            )
        ).first()
        
        if not timetable:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Timetable not found"
            )
        
        return timetable
    
    @staticmethod
    def get_class_timetable(
        db: Session,
        class_id: int,
        institute_id: int
    ) -> Optional[Timetable]:
        """Get active timetable for a class."""
        return db.query(Timetable).filter(
            and_(
                Timetable.class_id == class_id,
                Timetable.institute_id == institute_id,
                Timetable.is_active == True
            )
        ).first()
    
    @staticmethod
    def get_user_timetable(
        db: Session,
        user_id: int,
        institute_id: int
    ) -> Optional[Timetable]:
        """Get timetable for a user (teacher or student)."""
        user = db.query(User).filter(
            and_(
                User.id == user_id,
                User.institute_id == institute_id
            )
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.role == "TEACHER":
            # Get timetable from any class where teacher is assigned
            assignments = ClassSubjectService.get_teacher_assignments(
                db, user_id, institute_id
            )
            if not assignments:
                return None
            
            class_ids = [a.class_id for a in assignments]
            return db.query(Timetable).filter(
                and_(
                    Timetable.class_id.in_(class_ids),
                    Timetable.institute_id == institute_id,
                    Timetable.is_active == True
                )
            ).first()
        
        elif user.role == "STUDENT":
            # Get timetable from enrolled class
            enrollment = db.query(Enrollment).filter(
                Enrollment.student_id == user_id
            ).first()
            
            if not enrollment:
                return None
            
            return db.query(Timetable).filter(
                and_(
                    Timetable.class_id == enrollment.class_id,
                    Timetable.institute_id == institute_id,
                    Timetable.is_active == True
                )
            ).first()
        
        return None


class TimetableSlotService:
    @staticmethod
    def create_slot(
        db: Session,
        institute_id: int,
        slot_data: TimetableSlotCreate
    ) -> TimetableSlot:
        """Create a timetable slot."""
        # Verify timetable belongs to institute
        TimetableService.get_timetable(db, slot_data.timetable_id, institute_id)
        
        # Check for duplicate slot (same timetable, day, period)
        existing = db.query(TimetableSlot).filter(
            and_(
                TimetableSlot.timetable_id == slot_data.timetable_id,
                TimetableSlot.day_of_week == slot_data.day_of_week,
                TimetableSlot.period_number == slot_data.period_number
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slot already exists for this timetable, day, and period"
            )
        
        slot = TimetableSlot(
            timetable_id=slot_data.timetable_id,
            day_of_week=slot_data.day_of_week,
            period_number=slot_data.period_number,
            start_time=slot_data.start_time,
            end_time=slot_data.end_time,
            is_active=slot_data.is_active
        )
        
        db.add(slot)
        db.commit()
        db.refresh(slot)
        return slot
    
    @staticmethod
    def get_timetable_slots(
        db: Session,
        timetable_id: int,
        institute_id: int
    ) -> List[TimetableSlot]:
        """Get all slots for a timetable."""
        TimetableService.get_timetable(db, timetable_id, institute_id)
        
        return db.query(TimetableSlot).filter(
            and_(
                TimetableSlot.timetable_id == timetable_id,
                TimetableSlot.is_active == True
            )
        ).order_by(TimetableSlot.day_of_week, TimetableSlot.period_number).all()
    
    @staticmethod
    def update_slot(
        db: Session,
        slot_id: int,
        institute_id: int,
        slot_data: TimetableSlotUpdate
    ) -> TimetableSlot:
        """Update a timetable slot."""
        slot = db.query(TimetableSlot).join(Timetable).filter(
            and_(
                TimetableSlot.id == slot_id,
                Timetable.institute_id == institute_id
            )
        ).first()
        
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot not found"
            )
        
        update_data = slot_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(slot, field, value)
        
        db.commit()
        db.refresh(slot)
        return slot
    
    @staticmethod
    def delete_slot(
        db: Session,
        slot_id: int,
        institute_id: int
    ) -> bool:
        """Delete a timetable slot (soft delete by setting is_active=False)."""
        slot = db.query(TimetableSlot).join(Timetable).filter(
            and_(
                TimetableSlot.id == slot_id,
                Timetable.institute_id == institute_id
            )
        ).first()
        
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot not found"
            )
        
        # Soft delete: set is_active to False
        slot.is_active = False
        db.commit()
        return True


class TimetableAssignmentService:
    @staticmethod
    def create_assignment(
        db: Session,
        institute_id: int,
        assignment_data: TimetableAssignmentCreate
    ) -> TimetableAssignment:
        """Create a timetable assignment."""
        # Verify slot exists and belongs to institute
        slot = db.query(TimetableSlot).join(Timetable).filter(
            and_(
                TimetableSlot.id == assignment_data.slot_id,
                Timetable.institute_id == institute_id
            )
        ).first()
        
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot not found"
            )
        
        # Verify subject belongs to institute
        SubjectService.get_subject(db, assignment_data.subject_id, institute_id)
        
        # If teacher assigned, verify teacher belongs to institute and is assigned to class
        if assignment_data.teacher_id:
            # Get class from timetable
            timetable = db.query(Timetable).filter(
                Timetable.id == slot.timetable_id
            ).first()
            
            teacher = db.query(User).filter(
                and_(
                    User.id == assignment_data.teacher_id,
                    User.institute_id == institute_id,
                    User.role == "TEACHER",
                    User.is_active == True
                )
            ).first()
            
            if not teacher:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Teacher not found or inactive"
                )
            
            # Verify teacher is assigned to this class-subject
            assignment = db.query(ClassSubject).filter(
                and_(
                    ClassSubject.class_id == timetable.class_id,
                    ClassSubject.subject_id == assignment_data.subject_id,
                    ClassSubject.teacher_id == assignment_data.teacher_id
                )
            ).first()
            
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Teacher is not assigned to this subject in this class"
                )
        
        # Check if slot already has an assignment
        existing = db.query(TimetableAssignment).filter(
            and_(
                TimetableAssignment.slot_id == assignment_data.slot_id,
                TimetableAssignment.is_active == True
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slot already has an assignment"
            )
        
        assignment = TimetableAssignment(
            slot_id=assignment_data.slot_id,
            subject_id=assignment_data.subject_id,
            teacher_id=assignment_data.teacher_id,
            room=assignment_data.room,
            is_active=assignment_data.is_active
        )
        
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
    
    @staticmethod
    def update_assignment(
        db: Session,
        assignment_id: int,
        institute_id: int,
        assignment_data: TimetableAssignmentUpdate
    ) -> TimetableAssignment:
        """Update a timetable assignment."""
        assignment = db.query(TimetableAssignment).join(
            TimetableSlot
        ).join(Timetable).filter(
            and_(
                TimetableAssignment.id == assignment_id,
                Timetable.institute_id == institute_id
            )
        ).first()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        update_data = assignment_data.dict(exclude_unset=True)
        
        # If subject_id is being updated, verify it belongs to institute
        if 'subject_id' in update_data:
            SubjectService.get_subject(db, update_data['subject_id'], institute_id)
        
        # If teacher_id is being updated, verify teacher
        if 'teacher_id' in update_data and update_data['teacher_id']:
            slot = db.query(TimetableSlot).filter(
                TimetableSlot.id == assignment.slot_id
            ).first()
            timetable = db.query(Timetable).filter(
                Timetable.id == slot.timetable_id
            ).first()
            
            teacher = db.query(User).filter(
                and_(
                    User.id == update_data['teacher_id'],
                    User.institute_id == institute_id,
                    User.role == "TEACHER",
                    User.is_active == True
                )
            ).first()
            
            if not teacher:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Teacher not found or inactive"
                )
            
            # Verify teacher is assigned to this class-subject
            subject_id = update_data.get('subject_id', assignment.subject_id)
            class_subject = db.query(ClassSubject).filter(
                and_(
                    ClassSubject.class_id == timetable.class_id,
                    ClassSubject.subject_id == subject_id,
                    ClassSubject.teacher_id == update_data['teacher_id']
                )
            ).first()
            
            if not class_subject:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Teacher is not assigned to this subject in this class"
                )
        
        for field, value in update_data.items():
            setattr(assignment, field, value)
        
        db.commit()
        db.refresh(assignment)
        return assignment
    
    @staticmethod
    def delete_assignment(
        db: Session,
        assignment_id: int,
        institute_id: int
    ) -> bool:
        """Delete a timetable assignment (soft delete by setting is_active=False)."""
        assignment = db.query(TimetableAssignment).join(
            TimetableSlot
        ).join(Timetable).filter(
            and_(
                TimetableAssignment.id == assignment_id,
                Timetable.institute_id == institute_id
            )
        ).first()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        # Soft delete: set is_active to False
        assignment.is_active = False
        db.commit()
        return True