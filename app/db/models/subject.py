from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(String(1000), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute", back_populates="subjects")
    class_subjects = relationship("ClassSubject", back_populates="subject", cascade="all, delete-orphan")
