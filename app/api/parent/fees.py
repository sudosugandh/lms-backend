from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.fee import FeeInvoiceResponse, FeePaymentResponse
from app.services.parent_service import ParentService
from app.services.fee_service import FeeInvoiceService, FeePaymentService
from app.utils.dependencies import get_parent

router = APIRouter(prefix="/fees", tags=["parent-fees"])


@router.get("/students/{student_id}/invoices", response_model=List[FeeInvoiceResponse])
async def get_student_invoices(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_parent)
):
    """Get fee invoices for a linked student (Parent only)."""
    institute_id = request.state.institute_id
    
    # Verify parent has access to this student
    if not ParentService.verify_parent_student_link(db, current_user.id, student_id, institute_id):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student is not linked to this parent."
        )
    
    invoices = FeeInvoiceService.get_student_invoices(db, student_id, institute_id)
    
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
