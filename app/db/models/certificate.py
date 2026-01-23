from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class CertificateType(str, enum.Enum):
    BONAFIDE = "BONAFIDE"
    TRANSFER_CERTIFICATE = "TRANSFER_CERTIFICATE"
    COURSE_COMPLETION = "COURSE_COMPLETION"
    ACHIEVEMENT = "ACHIEVEMENT"
    CHARACTER = "CHARACTER"
    OTHER = "OTHER"


class CertificateTemplate(Base):
    __tablename__ = "certificate_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    certificate_type = Column(String(50), nullable=False)  # BONAFIDE, TRANSFER_CERTIFICATE, etc.
    template_content = Column(Text, nullable=False)  # HTML/Text template with placeholders like {{student_name}}, {{class}}, etc.
    placeholders = Column(Text, nullable=True)  # JSON array of available placeholders
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    creator = relationship("User", foreign_keys=[created_by])
    issuances = relationship("CertificateIssuance", back_populates="template", cascade="all, delete-orphan")


class CertificateIssuance(Base):
    __tablename__ = "certificate_issuance"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("certificate_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    certificate_number = Column(String(100), nullable=False, index=True)
    certificate_content = Column(Text, nullable=False)  # Final rendered certificate content
    certificate_url = Column(String(500), nullable=True)  # URL/path to stored certificate file (PDF/image)
    issued_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    certificate_metadata = Column(Text, nullable=True)  # JSON with additional data used in certificate
    issued_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    student = relationship("User", foreign_keys=[student_id])
    template = relationship("CertificateTemplate", back_populates="issuances")
    issuer = relationship("User", foreign_keys=[issued_by])
    
    # Ensure unique certificate number per institute
    __table_args__ = (
        UniqueConstraint('certificate_number', 'institute_id', name='uq_certificate_number'),
    )
