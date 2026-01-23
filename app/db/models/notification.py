from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class NotificationType(str, enum.Enum):
    LEAVE_STATUS_UPDATE = "LEAVE_STATUS_UPDATE"
    TIMETABLE_CHANGE = "TIMETABLE_CHANGE"
    QUIZ_PUBLISHED = "QUIZ_PUBLISHED"
    ASSIGNMENT_DEADLINE = "ASSIGNMENT_DEADLINE"
    RESULT_ANNOUNCED = "RESULT_ANNOUNCED"
    SYSTEM = "SYSTEM"
    GENERAL = "GENERAL"


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # LEAVE_STATUS_UPDATE, QUIZ_PUBLISHED, etc.
    target_role = Column(String(20), nullable=True)  # If null, applies to all roles
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # Specific user
    target_class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=True, index=True)  # All users in class
    notification_metadata = Column(JSON, nullable=True)  # Additional data (quiz_id, assignment_id, etc.)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    institute = relationship("Institute")
    target_user = relationship("User", foreign_keys=[target_user_id])
    target_class = relationship("Class")
    creator = relationship("User", foreign_keys=[created_by])
    read_statuses = relationship("NotificationReadStatus", back_populates="notification", cascade="all, delete-orphan")


class NotificationReadStatus(Base):
    __tablename__ = "notification_read_status"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    notification = relationship("Notification", back_populates="read_statuses")
    user = relationship("User", foreign_keys=[user_id])
    
    # Ensure one read status per user per notification
    __table_args__ = (
        UniqueConstraint('notification_id', 'user_id', name='uq_notification_user'),
    )
