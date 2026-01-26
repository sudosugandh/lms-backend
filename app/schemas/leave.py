from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class LeaveTypeBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    max_days_per_year: Optional[int] = None
    requires_approval: bool = True
    is_active: bool = True


class LeaveTypeCreate(LeaveTypeBase):
    pass


class LeaveTypeUpdate(LeaveTypeBase):
    pass


class LeaveTypeResponse(LeaveTypeBase):
    id: int
    institute_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class LeaveRequestBase(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestResponse(LeaveRequestBase):
    id: int
    institute_id: int
    user_id: int
    number_of_days: int
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None
    leave_type_name: Optional[str] = None
    approver_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class LeaveRequestUpdate(BaseModel):
    """Admin update for leave request"""
    status: str  # APPROVED or REJECTED
    rejection_reason: Optional[str] = None
