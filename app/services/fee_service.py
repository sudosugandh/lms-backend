from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import date
from app.db.models.fee import FeeStructure, FeeInvoice, FeePayment, PaymentStatus
from app.db.models.user import User, UserRole
from app.db.models.class_model import Class
from app.schemas.fee import FeeStructureCreate, FeeInvoiceCreate, FeePaymentCreate


class FeeStructureService:
    @staticmethod
    def create_fee_structure(
        db: Session,
        institute_id: int,
        admin_id: int,
        fee_structure_data: FeeStructureCreate
    ) -> FeeStructure:
        """Create a fee structure."""
        # If class_id specified, verify it belongs to institute
        if fee_structure_data.class_id:
            from app.services.class_service import ClassService
            ClassService.get_class(db, fee_structure_data.class_id, institute_id)
        
        fee_structure = FeeStructure(
            institute_id=institute_id,
            class_id=fee_structure_data.class_id,
            name=fee_structure_data.name,
            description=fee_structure_data.description,
            academic_year=fee_structure_data.academic_year,
            total_amount=fee_structure_data.total_amount,
            is_active=fee_structure_data.is_active,
            created_by=admin_id
        )
        
        db.add(fee_structure)
        db.commit()
        db.refresh(fee_structure)
        return fee_structure
    
    @staticmethod
    def get_fee_structures(
        db: Session,
        institute_id: int,
        class_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[FeeStructure]:
        """Get fee structures for an institute."""
        query = db.query(FeeStructure).filter(
            FeeStructure.institute_id == institute_id
        )
        
        if class_id:
            query = query.filter(
                (FeeStructure.class_id == class_id) | (FeeStructure.class_id.is_(None))
            )
        
        if is_active is not None:
            query = query.filter(FeeStructure.is_active == is_active)
        
        return query.all()


class FeeInvoiceService:
    @staticmethod
    def generate_invoice(
        db: Session,
        institute_id: int,
        admin_id: int,
        invoice_data: FeeInvoiceCreate
    ) -> FeeInvoice:
        """Generate a fee invoice for a student."""
        # Verify student exists and belongs to institute
        student = db.query(User).filter(
            and_(
                User.id == invoice_data.student_id,
                User.institute_id == institute_id,
                User.role == UserRole.STUDENT,
                User.is_active == True
            )
        ).first()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found or inactive"
            )
        
        # Verify fee structure exists and belongs to institute
        fee_structure = db.query(FeeStructure).filter(
            and_(
                FeeStructure.id == invoice_data.fee_structure_id,
                FeeStructure.institute_id == institute_id,
                FeeStructure.is_active == True
            )
        ).first()
        
        if not fee_structure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fee structure not found"
            )
        
        # Generate unique invoice number
        invoice_number = FeeInvoiceService._generate_invoice_number(db, institute_id)
        
        invoice = FeeInvoice(
            institute_id=institute_id,
            student_id=invoice_data.student_id,
            fee_structure_id=invoice_data.fee_structure_id,
            invoice_number=invoice_number,
            total_amount=fee_structure.total_amount,
            paid_amount=0.0,
            due_amount=fee_structure.total_amount,
            status="UNPAID",
            due_date=invoice_data.due_date,
            created_by=admin_id
        )
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice
    
    @staticmethod
    def _generate_invoice_number(db: Session, institute_id: int) -> str:
        """Generate a unique invoice number."""
        from app.db.models.institute import Institute
        institute = db.query(Institute).filter(Institute.id == institute_id).first()
        prefix = institute.code if institute else "INV"
        
        # Get last invoice number for this institute
        last_invoice = db.query(FeeInvoice).filter(
            FeeInvoice.institute_id == institute_id
        ).order_by(FeeInvoice.id.desc()).first()
        
        if last_invoice and last_invoice.invoice_number:
            # Extract number from last invoice
            try:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}-INV-{new_num:06d}"
    
    @staticmethod
    def get_student_invoices(
        db: Session,
        student_id: int,
        institute_id: int,
        status: Optional[str] = None
    ) -> List[FeeInvoice]:
        """Get all invoices for a student."""
        # Verify student belongs to institute
        student = db.query(User).filter(
            and_(
                User.id == student_id,
                User.institute_id == institute_id
            )
        ).first()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        query = db.query(FeeInvoice).filter(
            and_(
                FeeInvoice.student_id == student_id,
                FeeInvoice.institute_id == institute_id
            )
        )
        
        if status:
            query = query.filter(FeeInvoice.status == status)
        
        return query.order_by(FeeInvoice.created_at.desc()).all()
    
    @staticmethod
    def get_institute_invoices(
        db: Session,
        institute_id: int,
        status: Optional[str] = None,
        student_id: Optional[int] = None
    ) -> List[FeeInvoice]:
        """Get all invoices for an institute (admin only)."""
        query = db.query(FeeInvoice).filter(
            FeeInvoice.institute_id == institute_id
        )
        
        if status:
            query = query.filter(FeeInvoice.status == status)
        
        if student_id:
            query = query.filter(FeeInvoice.student_id == student_id)
        
        return query.order_by(FeeInvoice.created_at.desc()).all()


class FeePaymentService:
    @staticmethod
    def record_payment(
        db: Session,
        institute_id: int,
        admin_id: int,
        payment_data: FeePaymentCreate
    ) -> FeePayment:
        """Record a fee payment."""
        # Verify invoice exists and belongs to institute
        invoice = db.query(FeeInvoice).filter(
            and_(
                FeeInvoice.id == payment_data.invoice_id,
                FeeInvoice.institute_id == institute_id
            )
        ).first()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        # Verify payment amount doesn't exceed due amount
        if payment_data.amount > invoice.due_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount exceeds due amount. Due: {invoice.due_amount}"
            )
        
        payment = FeePayment(
            invoice_id=payment_data.invoice_id,
            amount=payment_data.amount,
            payment_method=payment_data.payment_method,
            payment_date=payment_data.payment_date,
            receipt_number=payment_data.receipt_number,
            transaction_reference=payment_data.transaction_reference,
            notes=payment_data.notes,
            recorded_by=admin_id
        )
        
        db.add(payment)
        
        # Update invoice payment status
        invoice.paid_amount += payment_data.amount
        invoice.due_amount = invoice.total_amount - invoice.paid_amount
        
        if invoice.due_amount == 0:
            invoice.status = "PAID"
        elif invoice.paid_amount > 0:
            invoice.status = "PARTIAL"
        else:
            invoice.status = "UNPAID"
        
        db.commit()
        db.refresh(payment)
        return payment
    
    @staticmethod
    def get_invoice_payments(
        db: Session,
        invoice_id: int,
        institute_id: int
    ) -> List[FeePayment]:
        """Get all payments for an invoice."""
        # Verify invoice belongs to institute
        invoice = db.query(FeeInvoice).filter(
            and_(
                FeeInvoice.id == invoice_id,
                FeeInvoice.institute_id == institute_id
            )
        ).first()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        return db.query(FeePayment).filter(
            FeePayment.invoice_id == invoice_id
        ).order_by(FeePayment.payment_date.desc()).all()
