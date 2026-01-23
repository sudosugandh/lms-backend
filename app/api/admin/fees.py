from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.fee import (
    FeeStructureCreate, FeeStructureUpdate, FeeStructureResponse,
    FeeInvoiceCreate, FeeInvoiceResponse,
    FeePaymentCreate, FeePaymentResponse
)
from app.services.fee_service import (
    FeeStructureService, FeeInvoiceService, FeePaymentService
)
from app.utils.dependencies import get_institute_admin
from app.utils.audit import log_audit_event, AuditAction

router = APIRouter(prefix="/fees", tags=["admin-fees"])


# Fee Structure endpoints
@router.post("/structures", response_model=FeeStructureResponse, status_code=201)
async def create_fee_structure(
    fee_structure_data: FeeStructureCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Create a fee structure (Admin only)."""
    institute_id = request.state.institute_id
    fee_structure = FeeStructureService.create_fee_structure(
        db, institute_id, current_user.id, fee_structure_data
    )
    
    # Format response
    from app.db.models.class_model import Class
    class_obj = db.query(Class).filter(Class.id == fee_structure.class_id).first() if fee_structure.class_id else None
    
    return FeeStructureResponse(
        **fee_structure.__dict__,
        class_name=class_obj.name if class_obj else None
    )


@router.get("/structures", response_model=List[FeeStructureResponse])
async def list_fee_structures(
    request: Request,
    db: Session = Depends(get_db),
    class_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_institute_admin)
):
    """List fee structures (Admin only)."""
    institute_id = request.state.institute_id
    fee_structures = FeeStructureService.get_fee_structures(
        db, institute_id, class_id, is_active
    )
    
    # Format response
    results = []
    for fs in fee_structures:
        from app.db.models.class_model import Class
        class_obj = db.query(Class).filter(Class.id == fs.class_id).first() if fs.class_id else None
        
        results.append(FeeStructureResponse(
            **fs.__dict__,
            class_name=class_obj.name if class_obj else None
        ))
    
    return results


# Fee Invoice endpoints
@router.post("/invoices", response_model=FeeInvoiceResponse, status_code=201)
async def generate_invoice(
    invoice_data: FeeInvoiceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Generate a fee invoice (Admin only)."""
    institute_id = request.state.institute_id
    invoice = FeeInvoiceService.generate_invoice(
        db, institute_id, current_user.id, invoice_data
    )
    
    # Format response
    student = db.query(User).filter(User.id == invoice.student_id).first()
    from app.db.models.fee import FeeStructure
    fee_structure = db.query(FeeStructure).filter(FeeStructure.id == invoice.fee_structure_id).first()
    
    return FeeInvoiceResponse(
        **invoice.__dict__,
        student_name=student.name if student else None,
        fee_structure_name=fee_structure.name if fee_structure else None,
        payments=[]
    )


@router.get("/invoices", response_model=List[FeeInvoiceResponse])
async def list_invoices(
    request: Request,
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    student_id: Optional[int] = None,
    current_user: User = Depends(get_institute_admin)
):
    """List fee invoices (Admin only)."""
    institute_id = request.state.institute_id
    invoices = FeeInvoiceService.get_institute_invoices(
        db, institute_id, status, student_id
    )
    
    # Format response
    results = []
    for invoice in invoices:
        student = db.query(User).filter(User.id == invoice.student_id).first()
        from app.db.models.fee import FeeStructure
        fee_structure = db.query(FeeStructure).filter(FeeStructure.id == invoice.fee_structure_id).first()
        
        # Get payments
        payments = FeePaymentService.get_invoice_payments(db, invoice.id, institute_id)
        formatted_payments = []
        for payment in payments:
            recorder_name = None
            if payment.recorded_by:
                recorder = db.query(User).filter(User.id == payment.recorded_by).first()
                recorder_name = recorder.name if recorder else None
            
            formatted_payments.append(FeePaymentResponse(
                **payment.__dict__,
                recorder_name=recorder_name
            ))
        
        results.append(FeeInvoiceResponse(
            **invoice.__dict__,
            student_name=student.name if student else None,
            fee_structure_name=fee_structure.name if fee_structure else None,
            payments=formatted_payments
        ))
    
    return results


# Fee Payment endpoints
@router.post("/payments", response_model=FeePaymentResponse, status_code=201)
async def record_payment(
    payment_data: FeePaymentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Record a fee payment (Admin only)."""
    institute_id = request.state.institute_id
    payment = FeePaymentService.record_payment(
        db, institute_id, current_user.id, payment_data
    )
    
    # Format response
    recorder_name = current_user.name
    
    return FeePaymentResponse(
        **payment.__dict__,
        recorder_name=recorder_name
    )


@router.get("/invoices/{invoice_id}/payments", response_model=List[FeePaymentResponse])
async def get_invoice_payments(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get payments for an invoice (Admin only)."""
    institute_id = request.state.institute_id
    payments = FeePaymentService.get_invoice_payments(db, invoice_id, institute_id)
    
    # Format response
    results = []
    for payment in payments:
        recorder_name = None
        if payment.recorded_by:
            recorder = db.query(User).filter(User.id == payment.recorded_by).first()
            recorder_name = recorder.name if recorder else None
        
        results.append(FeePaymentResponse(
            **payment.__dict__,
            recorder_name=recorder_name
        ))
    
    return results
