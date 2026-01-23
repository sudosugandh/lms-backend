from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class LeaveStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class LeaveType(Base):
    __tablename__ = "leave_types"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    max_days_per_year = Column(Integer, nullable=True)  # Optional limit
    requires_approval = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    leave_requests = relationship("LeaveRequest", back_populates="leave_type", cascade="all, delete-orphan")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    number_of_days = Column(Integer, nullable=False)  # Calculated
    reason = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING, APPROVED, REJECTED
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    user = relationship("User", foreign_keys=[user_id])
    leave_type = relationship("LeaveType", back_populates="leave_requests")
    approver = relationship("User", foreign_keys=[approved_by])
