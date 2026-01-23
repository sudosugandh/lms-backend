from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
import re
import uuid
from datetime import datetime
from app.db.models.certificate import CertificateTemplate, CertificateIssuance
from app.db.models.user import User, UserRole
from app.db.models.class_model import Class
from app.db.models.enrollment import Enrollment
from app.schemas.certificate import CertificateTemplateCreate, CertificateIssuanceCreate


class CertificateTemplateService:
    @staticmethod
    def create_template(
        db: Session,
        institute_id: int,
        admin_id: int,
        template_data: CertificateTemplateCreate
    ) -> CertificateTemplate:
        """Create a certificate template."""
        template = CertificateTemplate(
            institute_id=institute_id,
            name=template_data.name,
            certificate_type=template_data.certificate_type,
            template_content=template_data.template_content,
            placeholders=template_data.placeholders,
            is_active=template_data.is_active,
            created_by=admin_id
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        return template
    
    @staticmethod
    def get_templates(
        db: Session,
        institute_id: int,
        certificate_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[CertificateTemplate]:
        """Get certificate templates for an institute."""
        query = db.query(CertificateTemplate).filter(
            CertificateTemplate.institute_id == institute_id
        )
        
        if certificate_type:
            query = query.filter(CertificateTemplate.certificate_type == certificate_type)
        
        if is_active is not None:
            query = query.filter(CertificateTemplate.is_active == is_active)
        
        return query.all()


class CertificateIssuanceService:
    @staticmethod
    def generate_certificate(
        db: Session,
        institute_id: int,
        admin_id: int,
        issuance_data: CertificateIssuanceCreate
    ) -> CertificateIssuance:
        """Generate a certificate for a student."""
        # Verify student exists and belongs to institute
        student = db.query(User).filter(
            and_(
                User.id == issuance_data.student_id,
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
        
        # Verify template exists and belongs to institute
        template = db.query(CertificateTemplate).filter(
            and_(
                CertificateTemplate.id == issuance_data.template_id,
                CertificateTemplate.institute_id == institute_id,
                CertificateTemplate.is_active == True
            )
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate template not found"
            )
        
        # Check for duplicate issuance (prevent same certificate type for same student)
        existing = db.query(CertificateIssuance).filter(
            and_(
                CertificateIssuance.student_id == issuance_data.student_id,
                CertificateIssuance.template_id == issuance_data.template_id,
                CertificateIssuance.is_active == True
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Certificate already issued for this student with this template"
            )
        
        # Generate certificate content by replacing placeholders
        certificate_content = CertificateIssuanceService._render_template(
            db, template.template_content, student, issuance_data.certificate_metadata or {}
        )
        
        # Generate unique certificate number
        certificate_number = CertificateIssuanceService._generate_certificate_number(db, institute_id)
        
        issuance = CertificateIssuance(
            institute_id=institute_id,
            student_id=issuance_data.student_id,
            template_id=issuance_data.template_id,
            certificate_number=certificate_number,
            certificate_content=certificate_content,
            issued_by=admin_id,
            certificate_metadata=str(issuance_data.certificate_metadata) if issuance_data.certificate_metadata else None
        )
        
        db.add(issuance)
        db.commit()
        db.refresh(issuance)
        return issuance
    
    @staticmethod
    def _render_template(
        db: Session,
        template_content: str,
        student: User,
        metadata: Dict[str, Any]
    ) -> str:
        """Render certificate template with placeholders."""
        content = template_content
        
        # Get student's class
        enrollment = db.query(Enrollment).filter(
            Enrollment.student_id == student.id
        ).first()
        
        class_name = None
        if enrollment:
            class_obj = db.query(Class).filter(Class.id == enrollment.class_id).first()
            class_name = class_obj.name if class_obj else None
        
        # Get institute info
        from app.db.models.institute import Institute
        institute = db.query(Institute).filter(Institute.id == student.institute_id).first()
        
        # Common placeholders
        replacements = {
            '{{student_name}}': student.name,
            '{{student_email}}': student.email,
            '{{class}}': class_name or 'N/A',
            '{{institute_name}}': institute.name if institute else 'N/A',
            '{{institute_code}}': institute.code if institute else 'N/A',
            '{{issue_date}}': datetime.now().strftime('%B %d, %Y'),
            '{{current_date}}': datetime.now().strftime('%B %d, %Y'),
            '{{current_year}}': str(datetime.now().year),
        }
        
        # Add metadata replacements
        for key, value in metadata.items():
            placeholder = '{{{' + key + '}}}'
            replacements[placeholder] = str(value)
        
        # Replace placeholders
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        
        return content
    
    @staticmethod
    def _generate_certificate_number(db: Session, institute_id: int) -> str:
        """Generate a unique certificate number."""
        from app.db.models.institute import Institute
        institute = db.query(Institute).filter(Institute.id == institute_id).first()
        prefix = institute.code if institute else "CERT"
        
        # Get last certificate number for this institute
        last_cert = db.query(CertificateIssuance).filter(
            CertificateIssuance.institute_id == institute_id
        ).order_by(CertificateIssuance.id.desc()).first()
        
        if last_cert and last_cert.certificate_number:
            try:
                last_num = int(last_cert.certificate_number.split('-')[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}-CERT-{new_num:06d}"
    
    @staticmethod
    def get_student_certificates(
        db: Session,
        student_id: int,
        institute_id: int
    ) -> List[CertificateIssuance]:
        """Get all certificates for a student."""
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
        
        return db.query(CertificateIssuance).filter(
            and_(
                CertificateIssuance.student_id == student_id,
                CertificateIssuance.institute_id == institute_id,
                CertificateIssuance.is_active == True
            )
        ).order_by(CertificateIssuance.issued_date.desc()).all()
    
    @staticmethod
    def get_certificate(
        db: Session,
        certificate_id: int,
        institute_id: int
    ) -> CertificateIssuance:
        """Get a specific certificate."""
        certificate = db.query(CertificateIssuance).filter(
            and_(
                CertificateIssuance.id == certificate_id,
                CertificateIssuance.institute_id == institute_id,
                CertificateIssuance.is_active == True
            )
        ).first()
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        return certificate
