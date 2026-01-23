from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InstituteBase(BaseModel):
    name: str
    code: str
    is_active: bool = True


class InstituteCreate(InstituteBase):
    pass


class InstituteResponse(InstituteBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DomainBase(BaseModel):
    host_name: str
    is_active: bool = True


class DomainCreate(DomainBase):
    institute_id: int


class DomainResponse(DomainBase):
    id: int
    institute_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
