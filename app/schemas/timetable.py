from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, time


class TimetableBase(BaseModel):
    name: str
    description: Optional[str] = None
    academic_year: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True


class TimetableCreate(TimetableBase):
    class_id: int


class TimetableUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    academic_year: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class TimetableResponse(TimetableBase):
    id: int
    institute_id: int
    class_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    class_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class TimetableSlotBase(BaseModel):
    day_of_week: int  # 0=Monday, 6=Sunday
    period_number: int
    start_time: time
    end_time: time
    is_active: bool = True


class TimetableSlotCreate(TimetableSlotBase):
    timetable_id: int


class TimetableSlotUpdate(BaseModel):
    day_of_week: Optional[int] = None
    period_number: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_active: Optional[bool] = None


class TimetableSlotResponse(TimetableSlotBase):
    id: int
    timetable_id: int
    created_at: datetime
    assignments: Optional[List['TimetableAssignmentResponse']] = []
    
    class Config:
        from_attributes = True


class TimetableAssignmentBase(BaseModel):
    subject_id: int
    teacher_id: Optional[int] = None
    room: Optional[str] = None
    is_active: bool = True


class TimetableAssignmentCreate(TimetableAssignmentBase):
    slot_id: int


class TimetableAssignmentUpdate(BaseModel):
    subject_id: Optional[int] = None
    teacher_id: Optional[int] = None
    room: Optional[str] = None
    is_active: Optional[bool] = None


class TimetableAssignmentResponse(TimetableAssignmentBase):
    id: int
    slot_id: int
    created_at: datetime
    subject_name: Optional[str] = None
    teacher_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class TimetableWithSlots(TimetableResponse):
    slots: List[TimetableSlotResponse] = []
