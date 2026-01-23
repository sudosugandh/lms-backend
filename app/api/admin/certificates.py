from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.certificate import (
    CertificateTemplateCreate, CertificateTemplateUpdate, CertificateTemplateResponse,
    CertificateIssuanceCreate, CertificateIssuanceResponse
)
from app.services.certificate_service import (
    CertificateTemplateService, CertificateIssuanceService
)
from app.utils.dependencies import get_institute_admin

router = APIRouter(prefix="/certificates", tags=["admin-certificates"])


# Certificate Template endpoints
@router.post("/templates", response_model=CertificateTemplateResponse, status_code=201)
async def create_template(
    template_data: CertificateTemplateCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Create a certificate template (Admin only)."""
    institute_id = request.state.institute_id
    template = CertificateTemplateService.create_template(
        db, institute_id, current_user.id, template_data
    )
    
    return CertificateTemplateResponse(**template.__dict__)


@router.get("/templates", response_model=List[CertificateTemplateResponse])
async def list_templates(
    request: Request,
    db: Session = Depends(get_db),
    certificate_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_institute_admin)
):
    """List certificate templates (Admin only)."""
    institute_id = request.state.institute_id
    templates = CertificateTemplateService.get_templates(
        db, institute_id, certificate_type, is_active
    )
    
    return [CertificateTemplateResponse(**t.__dict__) for t in templates]


# Certificate Issuance endpoints
@router.post("/generate", response_model=CertificateIssuanceResponse, status_code=201)
async def generate_certificate(
    issuance_data: CertificateIssuanceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Generate a certificate for a student (Admin only)."""
    institute_id = request.state.institute_id
    issuance = CertificateIssuanceService.generate_certificate(
        db, institute_id, current_user.id, issuance_data
    )
    
    # Format response
    student = db.query(User).filter(User.id == issuance.student_id).first()
    from app.db.models.certificate import CertificateTemplate
    template = db.query(CertificateTemplate).filter(CertificateTemplate.id == issuance.template_id).first()
    
    issuer_name = current_user.name
    
    # Log audit event
    from app.utils.audit import log_audit_event, AuditAction
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action=AuditAction.CERTIFICATE_ISSUED,
        request=request,
        details=f"Issued certificate #{issuance.id} to student {student.name if student else issuance.student_id}"
    )
    
    return CertificateIssuanceResponse(
        **issuance.__dict__,
        student_name=student.name if student else None,
        template_name=template.name if template else None,
        issuer_name=issuer_name
    )


@router.get("/issuances", response_model=List[CertificateIssuanceResponse])
async def list_issuances(
    request: Request,
    db: Session = Depends(get_db),
    student_id: Optional[int] = None,
    current_user: User = Depends(get_institute_admin)
):
    """List certificate issuances (Admin only)."""
    institute_id = request.state.institute_id
    
    if student_id:
        issuances = CertificateIssuanceService.get_student_certificates(
            db, student_id, institute_id
        )
    else:
        # Get all issuances for institute
        from app.db.models.certificate import CertificateIssuance
        issuances = db.query(CertificateIssuance).filter(
            CertificateIssuance.institute_id == institute_id,
            CertificateIssuance.is_active == True
        ).order_by(CertificateIssuance.issued_date.desc()).all()
    
    # Format response
    results = []
    for issuance in issuances:
        student = db.query(User).filter(User.id == issuance.student_id).first()
        from app.db.models.certificate import CertificateTemplate
        template = db.query(CertificateTemplate).filter(CertificateTemplate.id == issuance.template_id).first()
        
        issuer_name = None
        if issuance.issued_by:
            issuer = db.query(User).filter(User.id == issuance.issued_by).first()
            issuer_name = issuer.name if issuer else None
        
        results.append(CertificateIssuanceResponse(
            **issuance.__dict__,
            student_name=student.name if student else None,
            template_name=template.name if template else None,
            issuer_name=issuer_name
        ))
    
    return results


@router.get("/{certificate_id}", response_model=CertificateIssuanceResponse)
async def get_certificate(
    certificate_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get a specific certificate (Admin only)."""
    institute_id = request.state.institute_id
    certificate = CertificateIssuanceService.get_certificate(db, certificate_id, institute_id)
    
    # Format response
    student = db.query(User).filter(User.id == certificate.student_id).first()
    from app.db.models.certificate import CertificateTemplate
    template = db.query(CertificateTemplate).filter(CertificateTemplate.id == certificate.template_id).first()
    
    issuer_name = None
    if certificate.issued_by:
        issuer = db.query(User).filter(User.id == certificate.issued_by).first()
        issuer_name = issuer.name if issuer else None
    
    return CertificateIssuanceResponse(
        **certificate.__dict__,
        student_name=student.name if student else None,
        template_name=template.name if template else None,
        issuer_name=issuer_name
    )
