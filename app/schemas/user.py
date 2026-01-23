from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.db.models.user import UserRole


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    password: str
    institute_id: Optional[int] = None


class UserResponse(UserBase):
    id: int
    institute_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TeacherCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class TeacherResponse(UserResponse):
    pass


class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(UserResponse):
    class_name: Optional[str] = None
    class_id: Optional[int] = None
