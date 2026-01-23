from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.services.notification_service import NotificationService
from app.utils.dependencies import get_institute_admin

router = APIRouter(prefix="/notifications", tags=["admin-notifications"])


@router.post("", response_model=NotificationResponse, status_code=201)
async def create_notification(
    notification_data: NotificationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Create a notification (Admin only)."""
    institute_id = request.state.institute_id
    notification = NotificationService.create_notification(
        db=db,
        institute_id=institute_id,
        title=notification_data.title,
        message=notification_data.message,
        notification_type=notification_data.notification_type,
        target_role=notification_data.target_role,
        target_user_id=notification_data.target_user_id,
        target_class_id=notification_data.target_class_id,
        notification_metadata=notification_data.notification_metadata,
        created_by=current_user.id
    )
    
    if not notification:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )
    
    return NotificationResponse(
        **notification.__dict__,
        is_read=None,
        read_at=None
    )


@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    request: Request,
    db: Session = Depends(get_db),
    is_read: Optional[bool] = None,
    notification_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_institute_admin)
):
    """Get notifications for the admin."""
    institute_id = request.state.institute_id
    notifications = NotificationService.get_user_notifications(
        db, current_user.id, institute_id, is_read, notification_type, limit, offset
    )
    
    # Format with read status
    formatted = []
    for notif in notifications:
        from app.db.models.notification import NotificationReadStatus
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
    current_user: User = Depends(get_institute_admin)
):
    """Get count of unread notifications (Admin only)."""
    institute_id = request.state.institute_id
    count = NotificationService.get_unread_count(db, current_user.id, institute_id)
    return {"count": count}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Mark a notification as read (Admin only)."""
    institute_id = request.state.institute_id
    read_status = NotificationService.mark_notification_read(
        db, notification_id, current_user.id, institute_id
    )
    
    from app.db.models.notification import Notification
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
    current_user: User = Depends(get_institute_admin)
):
    """Mark all notifications as read (Admin only)."""
    institute_id = request.state.institute_id
    count = NotificationService.mark_all_read(db, current_user.id, institute_id)
    return {"message": f"Marked {count} notifications as read"}
