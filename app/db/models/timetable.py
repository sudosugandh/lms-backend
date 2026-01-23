from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Time, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Timetable(Base):
    __tablename__ = "timetables"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    academic_year = Column(String(50), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    class_ = relationship("Class")
    creator = relationship("User", foreign_keys=[created_by])
    slots = relationship("TimetableSlot", back_populates="timetable", cascade="all, delete-orphan")


class TimetableSlot(Base):
    __tablename__ = "timetable_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    timetable_id = Column(Integer, ForeignKey("timetables.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    period_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    timetable = relationship("Timetable", back_populates="slots")
    assignments = relationship("TimetableAssignment", back_populates="slot", cascade="all, delete-orphan")
    
    # Ensure unique combination of timetable, day, and period
    __table_args__ = (
        UniqueConstraint('timetable_id', 'day_of_week', 'period_number', name='uq_timetable_day_period'),
    )


class TimetableAssignment(Base):
    __tablename__ = "timetable_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("timetable_slots.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    room = Column(String(100), nullable=True)  # Optional room number
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    slot = relationship("TimetableSlot", back_populates="assignments")
    subject = relationship("Subject")
    teacher = relationship("User", foreign_keys=[teacher_id])
    
    # Ensure unique subject assignment per slot (one subject per slot)
    __table_args__ = (
        UniqueConstraint('slot_id', 'subject_id', name='uq_slot_subject'),
    )
