from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.certificate import CertificateIssuanceResponse
from app.services.parent_service import ParentService
from app.services.certificate_service import CertificateIssuanceService
from app.utils.dependencies import get_parent

router = APIRouter(prefix="/certificates", tags=["parent-certificates"])


@router.get("/students/{student_id}", response_model=List[CertificateIssuanceResponse])
async def get_student_certificates(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_parent)
):
    """Get certificates for a linked student (Parent only)."""
    institute_id = request.state.institute_id
    
    # Verify parent has access to this student
    if not ParentService.verify_parent_student_link(db, current_user.id, student_id, institute_id):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student is not linked to this parent."
        )
    
    certificates = CertificateIssuanceService.get_student_certificates(db, student_id, institute_id)
    
    # Format response
    results = []
    for cert in certificates:
        student = db.query(User).filter(User.id == cert.student_id).first()
        from app.db.models.certificate import CertificateTemplate
        template = db.query(CertificateTemplate).filter(CertificateTemplate.id == cert.template_id).first()
        
        issuer_name = None
        if cert.issued_by:
            issuer = db.query(User).filter(User.id == cert.issued_by).first()
            issuer_name = issuer.name if issuer else None
        
        results.append(CertificateIssuanceResponse(
            **cert.__dict__,
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
    current_user: User = Depends(get_parent)
):
    """Get a specific certificate (Parent only - must be linked to student)."""
    institute_id = request.state.institute_id
    
    certificate = CertificateIssuanceService.get_certificate(db, certificate_id, institute_id)
    
    # Verify parent has access to this student
    if not ParentService.verify_parent_student_link(db, current_user.id, certificate.student_id, institute_id):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Certificate belongs to a student not linked to this parent."
        )
    
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
