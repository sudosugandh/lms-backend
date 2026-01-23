from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
import logging
from app.db.models.notification import Notification, NotificationReadStatus
from app.db.models.user import User
from app.db.models.class_model import Class
from app.db.models.enrollment import Enrollment

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        institute_id: int,
        title: str,
        message: str,
        notification_type: str,
        target_role: Optional[str] = None,
        target_user_id: Optional[int] = None,
        target_class_id: Optional[int] = None,
        notification_metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None,
        include_parents: bool = False
    ) -> Optional[Notification]:
        """
        Create a notification and distribute to target users.
        Returns None if notification creation fails (non-blocking).
        """
        try:
            notification = Notification(
                institute_id=institute_id,
                title=title,
                message=message,
                notification_type=notification_type,
                target_role=target_role,
                target_user_id=target_user_id,
                target_class_id=target_class_id,
                notification_metadata=notification_metadata,
                created_by=created_by
            )
            
            db.add(notification)
            db.flush()
            
            # Determine target users and create read statuses
            target_user_ids = []
            
            if target_user_id:
                # Specific user
                target_user_ids = [target_user_id]
                # Optionally include linked parents
                if include_parents:
                    from app.db.models.parent import ParentStudentLink
                    parent_links = db.query(ParentStudentLink).filter(
                        ParentStudentLink.student_id == target_user_id
                    ).all()
                    parent_ids = [link.parent_id for link in parent_links]
                    target_user_ids.extend(parent_ids)
            elif target_class_id:
                # All users in class
                # Get students enrolled in class
                enrollments = db.query(Enrollment).filter(
                    Enrollment.class_id == target_class_id
                ).all()
                student_ids = [e.student_id for e in enrollments]
                
                # Optionally include linked parents for all students
                if include_parents:
                    from app.db.models.parent import ParentStudentLink
                    parent_links = db.query(ParentStudentLink).filter(
                        ParentStudentLink.student_id.in_(student_ids)
                    ).all()
                    parent_ids = list(set([link.parent_id for link in parent_links]))
                    student_ids.extend(parent_ids)
                
                # Get teachers assigned to class
                from app.db.models.class_subject import ClassSubject
                assignments = db.query(ClassSubject).join(Class).filter(
                    Class.id == target_class_id
                ).all()
                teacher_ids = list(set([a.teacher_id for a in assignments if a.teacher_id]))
                
                target_user_ids = student_ids + teacher_ids
            elif target_role:
                # All users with specific role in institute
                users = db.query(User).filter(
                    and_(
                        User.institute_id == institute_id,
                        User.role == target_role,
                        User.is_active == True
                    )
                ).all()
                target_user_ids = [u.id for u in users]
            else:
                # All users in institute
                users = db.query(User).filter(
                    and_(
                        User.institute_id == institute_id,
                        User.is_active == True
                    )
                ).all()
                target_user_ids = [u.id for u in users]
            
            # Remove duplicates
            target_user_ids = list(set(target_user_ids))
            
            # Create read statuses for all target users
            for user_id in target_user_ids:
                read_status = NotificationReadStatus(
                    notification_id=notification.id,
                    user_id=user_id,
                    is_read=False
                )
                db.add(read_status)
            
            db.commit()
            db.refresh(notification)
            return notification
        except Exception as e:
            # Log error but don't fail the main operation
            logger.error(
                f"Failed to create notification: {title}",
                exc_info=True,
                extra={
                    "institute_id": institute_id,
                    "notification_type": notification_type,
                    "target_role": target_role,
                    "target_user_id": target_user_id,
                    "target_class_id": target_class_id,
                    "error": str(e)
                }
            )
            db.rollback()
            return None
    
    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        institute_id: int,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for a user."""
        # Verify user belongs to institute
        user = db.query(User).filter(
            and_(
                User.id == user_id,
                User.institute_id == institute_id
            )
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Query notifications with read status
        query = db.query(Notification).join(NotificationReadStatus).filter(
            and_(
                Notification.institute_id == institute_id,
                NotificationReadStatus.user_id == user_id,
                Notification.is_active == True
            )
        )
        
        if is_read is not None:
            query = query.filter(NotificationReadStatus.is_read == is_read)
        
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)
        
        return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def mark_notification_read(
        db: Session,
        notification_id: int,
        user_id: int,
        institute_id: int
    ) -> NotificationReadStatus:
        """Mark a notification as read."""
        # Verify notification belongs to institute
        notification = db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.institute_id == institute_id
            )
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Get or create read status
        read_status = db.query(NotificationReadStatus).filter(
            and_(
                NotificationReadStatus.notification_id == notification_id,
                NotificationReadStatus.user_id == user_id
            )
        ).first()
        
        if not read_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not accessible to user"
            )
        
        if not read_status.is_read:
            from datetime import datetime
            read_status.is_read = True
            read_status.read_at = datetime.utcnow()
            db.commit()
        
        db.refresh(read_status)
        return read_status
    
    @staticmethod
    def mark_all_read(
        db: Session,
        user_id: int,
        institute_id: int
    ) -> int:
        """Mark all notifications as read for a user."""
        # Verify user belongs to institute
        user = db.query(User).filter(
            and_(
                User.id == user_id,
                User.institute_id == institute_id
            )
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update all unread notifications
        from datetime import datetime
        now = datetime.utcnow()
        
        updated = db.query(NotificationReadStatus).join(Notification).filter(
            and_(
                NotificationReadStatus.user_id == user_id,
                Notification.institute_id == institute_id,
                NotificationReadStatus.is_read == False
            )
        ).update(
            {
                NotificationReadStatus.is_read: True,
                NotificationReadStatus.read_at: now
            },
            synchronize_session=False
        )
        
        db.commit()
        return updated
    
    @staticmethod
    def get_unread_count(
        db: Session,
        user_id: int,
        institute_id: int
    ) -> int:
        """Get count of unread notifications for a user."""
        # Verify user belongs to institute
        user = db.query(User).filter(
            and_(
                User.id == user_id,
                User.institute_id == institute_id
            )
        ).first()
        
        if not user:
            return 0
        
        count = db.query(NotificationReadStatus).join(Notification).filter(
            and_(
                NotificationReadStatus.user_id == user_id,
                Notification.institute_id == institute_id,
                Notification.is_active == True,
                NotificationReadStatus.is_read == False
            )
        ).count()
        
        return count
