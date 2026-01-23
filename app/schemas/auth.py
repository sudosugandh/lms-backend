from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserMe(BaseModel):
    id: int
    name: str
    email: str
    role: str
    institute_id: Optional[int] = None
    is_active: bool
    
    class Config:
        from_attributes = True
