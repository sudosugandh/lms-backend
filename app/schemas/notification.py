from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: str  # LEAVE_STATUS_UPDATE, QUIZ_PUBLISHED, etc.
    target_role: Optional[str] = None
    target_user_id: Optional[int] = None
    target_class_id: Optional[int] = None
    notification_metadata: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id: int
    institute_id: int
    is_active: bool
    created_by: Optional[int] = None
    created_at: datetime
    is_read: Optional[bool] = None  # For user's read status
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationReadStatusUpdate(BaseModel):
    is_read: bool = True
