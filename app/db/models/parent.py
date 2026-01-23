from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class ParentStudentLink(Base):
    __tablename__ = "parent_student_links"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False)  # Father, Mother, Guardian, etc.
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    parent = relationship("User", foreign_keys=[parent_id])
    student = relationship("User", foreign_keys=[student_id])
    
    # Ensure one link per parent-student combination
    __table_args__ = (
        UniqueConstraint('parent_id', 'student_id', name='uq_parent_student'),
    )
