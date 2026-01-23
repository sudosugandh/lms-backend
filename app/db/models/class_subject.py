from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class ClassSubject(Base):
    __tablename__ = "class_subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    class_ = relationship("Class", back_populates="class_subjects")
    subject = relationship("Subject", back_populates="class_subjects")
    teacher = relationship("User", foreign_keys=[teacher_id])
    
    # Ensure unique combination of class and subject
    __table_args__ = (
        UniqueConstraint('class_id', 'subject_id', name='uq_class_subject'),
    )
