from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    total_marks = Column(Integer, nullable=False, default=0)
    deadline = Column(DateTime(timezone=True), nullable=False)  # Submission deadline
    allow_late_submission = Column(Boolean, default=False, nullable=False)
    attachment_url = Column(String(500), nullable=True)  # File URL for assignment document
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    class_ = relationship("Class")
    subject = relationship("Subject")
    creator = relationship("User", foreign_keys=[created_by])
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="assignment", cascade="all, delete-orphan")


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_text = Column(Text, nullable=True)  # Text submission
    attachment_url = Column(String(500), nullable=True)  # File URL for submission
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_late = Column(Boolean, default=False, nullable=False)  # Whether submitted after deadline
    status = Column(String(20), nullable=False, default="SUBMITTED")  # SUBMITTED, GRADED
    marks_obtained = Column(Integer, nullable=True)  # Marks given
    graded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)
    feedback = Column(Text, nullable=True)  # Teacher feedback
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", foreign_keys=[student_id])
    grader = relationship("User", foreign_keys=[graded_by])
    result = relationship("Result", back_populates="assignment_submission", uselist=False)
