from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.fee import FeeInvoiceResponse, FeePaymentResponse
from app.services.fee_service import FeeInvoiceService, FeePaymentService
from app.utils.dependencies import get_student

router = APIRouter(prefix="/fees", tags=["student-fees"])


@router.get("/invoices", response_model=List[FeeInvoiceResponse])
async def get_my_invoices(
    request: Request,
    db: Session = Depends(get_db),
    status: str = None,
    current_user: User = Depends(get_student)
):
    """Get own fee invoices (Student only)."""
    institute_id = request.state.institute_id
    invoices = FeeInvoiceService.get_student_invoices(
        db, current_user.id, institute_id, status
    )
    
    # Format response
    results = []
    for invoice in invoices:
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
            student_name=current_user.name,
            fee_structure_name=fee_structure.name if fee_structure else None,
            payments=formatted_payments
        ))
    
    return results
