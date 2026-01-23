from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.certificate import CertificateIssuanceResponse
from app.services.certificate_service import CertificateIssuanceService
from app.utils.dependencies import get_student

router = APIRouter(prefix="/certificates", tags=["student-certificates"])


@router.get("", response_model=List[CertificateIssuanceResponse])
async def get_my_certificates(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Get own certificates (Student only)."""
    institute_id = request.state.institute_id
    certificates = CertificateIssuanceService.get_student_certificates(
        db, current_user.id, institute_id
    )
    
    # Format response
    results = []
    for cert in certificates:
        from app.db.models.certificate import CertificateTemplate
        template = db.query(CertificateTemplate).filter(CertificateTemplate.id == cert.template_id).first()
        
        issuer_name = None
        if cert.issued_by:
            issuer = db.query(User).filter(User.id == cert.issued_by).first()
            issuer_name = issuer.name if issuer else None
        
        results.append(CertificateIssuanceResponse(
            **cert.__dict__,
            student_name=current_user.name,
            template_name=template.name if template else None,
            issuer_name=issuer_name
        ))
    
    return results


@router.get("/{certificate_id}", response_model=CertificateIssuanceResponse)
async def get_certificate(
    certificate_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Get a specific certificate (Student only - must own it)."""
    institute_id = request.state.institute_id
    certificate = CertificateIssuanceService.get_certificate(db, certificate_id, institute_id)
    
    # Verify student owns this certificate
    if certificate.student_id != current_user.id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This certificate does not belong to you."
        )
    
    # Format response
    from app.db.models.certificate import CertificateTemplate
    template = db.query(CertificateTemplate).filter(CertificateTemplate.id == certificate.template_id).first()
    
    issuer_name = None
    if certificate.issued_by:
        issuer = db.query(User).filter(User.id == certificate.issued_by).first()
        issuer_name = issuer.name if issuer else None
    
    return CertificateIssuanceResponse(
        **certificate.__dict__,
        student_name=current_user.name,
        template_name=template.name if template else None,
        issuer_name=issuer_name
    )
