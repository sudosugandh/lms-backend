from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class PaymentStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PARTIAL = "PARTIAL"
    PAID = "PAID"


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHEQUE = "CHEQUE"
    OFFLINE_RECEIPT = "OFFLINE_RECEIPT"
    OTHER = "OTHER"


class FeeStructure(Base):
    __tablename__ = "fee_structures"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=True, index=True)  # If null, applies to all classes
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    academic_year = Column(String(50), nullable=True)
    total_amount = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    class_ = relationship("Class")
    creator = relationship("User", foreign_keys=[created_by])
    invoices = relationship("FeeInvoice", back_populates="fee_structure", cascade="all, delete-orphan")


class FeeInvoice(Base):
    __tablename__ = "fee_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    fee_structure_id = Column(Integer, ForeignKey("fee_structures.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0, nullable=False)
    due_amount = Column(Float, nullable=False)  # Calculated: total_amount - paid_amount
    status = Column(String(20), nullable=False, default="UNPAID")  # UNPAID, PARTIAL, PAID
    due_date = Column(Date, nullable=False, index=True)
    issued_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    student = relationship("User", foreign_keys=[student_id])
    fee_structure = relationship("FeeStructure", back_populates="invoices")
    creator = relationship("User", foreign_keys=[created_by])
    payments = relationship("FeePayment", back_populates="invoice", cascade="all, delete-orphan")


class FeePayment(Base):
    __tablename__ = "fee_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("fee_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)  # CASH, BANK_TRANSFER, CHEQUE, etc.
    payment_date = Column(Date, nullable=False, index=True)
    receipt_number = Column(String(100), nullable=True)  # Manual receipt number
    transaction_reference = Column(String(200), nullable=True)  # Bank reference, cheque number, etc.
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    invoice = relationship("FeeInvoice", back_populates="payments")
    recorder = relationship("User", foreign_keys=[recorded_by])
