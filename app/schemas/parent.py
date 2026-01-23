from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ParentStudentLinkBase(BaseModel):
    student_id: int
    relationship_type: str  # Father, Mother, Guardian, etc.
    is_active: bool = True


class ParentStudentLinkCreate(ParentStudentLinkBase):
    pass


class ParentStudentLinkResponse(ParentStudentLinkBase):
    id: int
    parent_id: int
    created_at: datetime
    student_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class StudentInfo(BaseModel):
    """Minimal student info for parent view"""
    id: int
    name: str
    email: str
    class_name: Optional[str] = None
    class_id: Optional[int] = None
    
    class Config:
        from_attributes = True
