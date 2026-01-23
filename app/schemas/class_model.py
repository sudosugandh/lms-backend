from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class ClassBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool = True


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ClassResponse(ClassBase):
    id: int
    institute_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ClassWithSubjects(ClassResponse):
    subjects: List['SubjectResponse'] = []
    
    class Config:
        from_attributes = True


class SubjectBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool = True


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SubjectResponse(SubjectBase):
    id: int
    institute_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ClassSubjectBase(BaseModel):
    class_id: int
    subject_id: int
    teacher_id: Optional[int] = None


class ClassSubjectCreate(ClassSubjectBase):
    pass


class ClassSubjectResponse(ClassSubjectBase):
    id: int
    teacher_name: Optional[str] = None
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class EnrollmentBase(BaseModel):
    student_id: int
    class_id: int


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentResponse(EnrollmentBase):
    id: int
    enrolled_at: datetime
    student_name: str
    class_name: str
    
    class Config:
        from_attributes = True


class AttendanceBase(BaseModel):
    student_id: int
    class_id: int
    subject_id: Optional[int] = None
    attendance_date: date
    status: str  # PRESENT, ABSENT, LEAVE
    remarks: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceMarkRequest(BaseModel):
    """Request model for marking attendance for multiple students at once"""
    class_id: int
    subject_id: Optional[int] = None
    attendance_date: date
    attendance_records: List[dict]  # [{"student_id": 1, "status": "PRESENT", "remarks": ""}]


class AttendanceResponse(AttendanceBase):
    id: int
    marked_by: Optional[int] = None
    created_at: datetime
    student_name: str
    class_name: str
    subject_name: Optional[str] = None
    
    class Config:
        from_attributes = True
