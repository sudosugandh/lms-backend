from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class CertificateTemplateBase(BaseModel):
    name: str
    certificate_type: str  # BONAFIDE, TRANSFER_CERTIFICATE, etc.
    template_content: str  # HTML/Text with placeholders
    placeholders: Optional[str] = None  # JSON array of available placeholders
    is_active: bool = True


class CertificateTemplateCreate(CertificateTemplateBase):
    pass


class CertificateTemplateUpdate(BaseModel):
    name: Optional[str] = None
    template_content: Optional[str] = None
    placeholders: Optional[str] = None
    is_active: Optional[bool] = None


class CertificateTemplateResponse(CertificateTemplateBase):
    id: int
    institute_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CertificateIssuanceBase(BaseModel):
    student_id: int
    template_id: int
    certificate_metadata: Optional[Dict[str, Any]] = None  # Additional data for placeholders


class CertificateIssuanceCreate(CertificateIssuanceBase):
    pass


class CertificateIssuanceResponse(CertificateIssuanceBase):
    id: int
    institute_id: int
    certificate_number: str
    certificate_content: str
    certificate_url: Optional[str] = None
    issued_date: datetime
    issued_by: Optional[int] = None
    is_active: bool
    created_at: datetime
    student_name: Optional[str] = None
    template_name: Optional[str] = None
    issuer_name: Optional[str] = None
    
    class Config:
        from_attributes = True
