from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LEAVE = "LEAVE"


class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True, index=True)
    attendance_date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # PRESENT, ABSENT, LEAVE
    marked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    remarks = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    class_ = relationship("Class", back_populates="attendance_records")
    subject = relationship("Subject")
    marked_by_user = relationship("User", foreign_keys=[marked_by])
    
    # Prevent duplicate attendance records for same student, class, date, and subject
    __table_args__ = (
        UniqueConstraint('student_id', 'class_id', 'subject_id', 'attendance_date', name='uq_attendance'),
    )
