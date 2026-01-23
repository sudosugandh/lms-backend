from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    class_ = relationship("Class", back_populates="enrollments")
    
    # Ensure unique combination of student and class
    __table_args__ = (
        UniqueConstraint('student_id', 'class_id', name='uq_student_class'),
    )
