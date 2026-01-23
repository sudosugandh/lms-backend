from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.notification import Notification, NotificationReadStatus
from app.schemas.notification import NotificationResponse
from app.services.notification_service import NotificationService
from app.utils.dependencies import get_teacher

router = APIRouter(prefix="/notifications", tags=["teacher-notifications"])


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    request: Request,
    db: Session = Depends(get_db),
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_teacher)
):
    """Get notifications for the teacher."""
    institute_id = request.state.institute_id
    notifications = NotificationService.get_user_notifications(
        db, current_user.id, institute_id, is_read, notification_type, limit, offset
    )
    
    # Format with read status
    formatted = []
    for notif in notifications:
        read_status = db.query(NotificationReadStatus).filter(
            and_(
                NotificationReadStatus.notification_id == notif.id,
                NotificationReadStatus.user_id == current_user.id
            )
        ).first()
        
        formatted.append(NotificationResponse(
            **notif.__dict__,
            is_read=read_status.is_read if read_status else False,
            read_at=read_status.read_at if read_status else None
        ))
    
    return formatted


@router.get("/unread-count")
async def get_unread_count(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Get count of unread notifications (Teacher only)."""
    institute_id = request.state.institute_id
    count = NotificationService.get_unread_count(db, current_user.id, institute_id)
    return {"count": count}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Mark a notification as read (Teacher only)."""
    institute_id = request.state.institute_id
    read_status = NotificationService.mark_notification_read(
        db, notification_id, current_user.id, institute_id
    )
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    return NotificationResponse(
        **notification.__dict__,
        is_read=True,
        read_at=read_status.read_at
    )


@router.post("/mark-all-read")
async def mark_all_read(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher)
):
    """Mark all notifications as read (Teacher only)."""
    institute_id = request.state.institute_id
    count = NotificationService.mark_all_read(db, current_user.id, institute_id)
    return {"message": f"Marked {count} notifications as read"}
