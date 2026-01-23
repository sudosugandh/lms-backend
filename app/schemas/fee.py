from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class FeeStructureBase(BaseModel):
    name: str
    description: Optional[str] = None
    academic_year: Optional[str] = None
    total_amount: float
    is_active: bool = True


class FeeStructureCreate(FeeStructureBase):
    class_id: Optional[int] = None


class FeeStructureUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    academic_year: Optional[str] = None
    total_amount: Optional[float] = None
    is_active: Optional[bool] = None


class FeeStructureResponse(FeeStructureBase):
    id: int
    institute_id: int
    class_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    class_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class FeeInvoiceBase(BaseModel):
    student_id: int
    fee_structure_id: int
    due_date: date


class FeeInvoiceCreate(FeeInvoiceBase):
    pass


class FeeInvoiceResponse(FeeInvoiceBase):
    id: int
    institute_id: int
    invoice_number: str
    total_amount: float
    paid_amount: float
    due_amount: float
    status: str
    issued_at: datetime
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    student_name: Optional[str] = None
    fee_structure_name: Optional[str] = None
    payments: Optional[List['FeePaymentResponse']] = []
    
    class Config:
        from_attributes = True


class FeePaymentBase(BaseModel):
    invoice_id: int
    amount: float
    payment_method: str  # CASH, BANK_TRANSFER, etc.
    payment_date: date
    receipt_number: Optional[str] = None
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None


class FeePaymentCreate(FeePaymentBase):
    pass


class FeePaymentResponse(FeePaymentBase):
    id: int
    recorded_by: Optional[int] = None
    created_at: datetime
    recorder_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class FeeInvoiceWithPayments(FeeInvoiceResponse):
    payments: List['FeePaymentResponse'] = []


# Rebuild models to resolve forward references
FeeInvoiceResponse.model_rebuild()
FeeInvoiceWithPayments.model_rebuild()
