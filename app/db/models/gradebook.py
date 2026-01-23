from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class TermType(str, enum.Enum):
    FIRST_TERM = "FIRST_TERM"
    SECOND_TERM = "SECOND_TERM"
    THIRD_TERM = "THIRD_TERM"
    MID_TERM = "MID_TERM"
    FINAL = "FINAL"
    SEMESTER_1 = "SEMESTER_1"
    SEMESTER_2 = "SEMESTER_2"
    ANNUAL = "ANNUAL"


class GradebookEntry(Base):
    __tablename__ = "gradebook_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Academic period
    academic_year = Column(String(20), nullable=False)  # e.g., "2024-2025"
    term = Column(Enum(TermType), nullable=False)  # FIRST_TERM, SECOND_TERM, etc.
    
    # Weighted scores
    quiz_weight = Column(Float, default=0.30, nullable=False)  # Default 30%
    assignment_weight = Column(Float, default=0.40, nullable=False)  # Default 40%
    exam_weight = Column(Float, default=0.30, nullable=False)  # Default 30%
    
    # Calculated scores
    quiz_total_marks = Column(Float, default=0.0, nullable=False)
    quiz_obtained_marks = Column(Float, default=0.0, nullable=False)
    quiz_weighted_score = Column(Float, default=0.0, nullable=False)
    
    assignment_total_marks = Column(Float, default=0.0, nullable=False)
    assignment_obtained_marks = Column(Float, default=0.0, nullable=False)
    assignment_weighted_score = Column(Float, default=0.0, nullable=False)
    
    exam_total_marks = Column(Float, default=0.0, nullable=False)
    exam_obtained_marks = Column(Float, default=0.0, nullable=False)
    exam_weighted_score = Column(Float, default=0.0, nullable=False)
    
    # Final calculated grade
    total_marks = Column(Float, default=0.0, nullable=False)
    obtained_marks = Column(Float, default=0.0, nullable=False)
    percentage = Column(Float, default=0.0, nullable=False)
    letter_grade = Column(String(5), nullable=True)  # A+, A, B+, B, etc.
    grade_point = Column(Float, nullable=True)  # 4.0, 3.5, etc.
    
    # Status and metadata
    status = Column(String(20), default="DRAFT", nullable=False)  # DRAFT, PUBLISHED, LOCKED
    remarks = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    student = relationship("User", foreign_keys=[student_id])
    class_ = relationship("Class")
    subject = relationship("Subject")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Ensure one gradebook entry per student per subject per term
    __table_args__ = (
        UniqueConstraint('student_id', 'class_id', 'subject_id', 'academic_year', 'term', name='uq_gradebook_entry'),
    )


class GradebookHistory(Base):
    __tablename__ = "gradebook_history"
    
    id = Column(Integer, primary_key=True, index=True)
    gradebook_entry_id = Column(Integer, ForeignKey("gradebook_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    change_type = Column(String(20), nullable=False)  # CREATED, UPDATED, PUBLISHED, LOCKED
    old_value = Column(Text, nullable=True)  # JSON string of old values
    new_value = Column(Text, nullable=True)  # JSON string of new values
    change_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    gradebook_entry = relationship("GradebookEntry")
    changed_by_user = relationship("User", foreign_keys=[changed_by])


class GradeDistribution(Base):
    __tablename__ = "grade_distributions"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True, index=True)
    academic_year = Column(String(20), nullable=False)
    term = Column(Enum(TermType), nullable=False)
    
    # Distribution statistics
    total_students = Column(Integer, default=0, nullable=False)
    a_plus_count = Column(Integer, default=0, nullable=False)
    a_count = Column(Integer, default=0, nullable=False)
    b_plus_count = Column(Integer, default=0, nullable=False)
    b_count = Column(Integer, default=0, nullable=False)
    c_plus_count = Column(Integer, default=0, nullable=False)
    c_count = Column(Integer, default=0, nullable=False)
    d_count = Column(Integer, default=0, nullable=False)
    f_count = Column(Integer, default=0, nullable=False)
    
    average_percentage = Column(Float, default=0.0, nullable=False)
    highest_percentage = Column(Float, default=0.0, nullable=False)
    lowest_percentage = Column(Float, default=0.0, nullable=False)
    
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    class_ = relationship("Class")
    subject = relationship("Subject")
    
    # Ensure one distribution per class/subject/term
    __table_args__ = (
        UniqueConstraint('class_id', 'subject_id', 'academic_year', 'term', name='uq_grade_distribution'),
    )
