"""
Audit logging utility for tracking sensitive actions.
"""
from sqlalchemy.orm import Session
from fastapi import Request
from app.db.models.audit_log import AuditLog
from app.db.models.user import User
from typing import Optional


def log_audit_event(
    db: Session,
    user_id: Optional[int],
    action: str,
    request: Optional[Request] = None,
    details: Optional[str] = None
) -> AuditLog:
    """
    Log an audit event.
    
    Args:
        db: Database session
        user_id: ID of user performing the action (None for system actions)
        action: Description of the action (e.g., "USER_CREATED", "ATTENDANCE_MARKED")
        request: FastAPI request object (optional, for IP address)
        details: Additional details about the action (optional)
    
    Returns:
        Created AuditLog record
    """
    ip_address = None
    if request:
        # Try to get IP from various headers (for proxies/load balancers)
        ip_address = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.headers.get("X-Real-IP") or
            request.client.host if request.client else None
        )
    
    audit_log = AuditLog(
        user_id=user_id,
        action=f"{action}{f': {details}' if details else ''}",
        ip_address=ip_address
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    return audit_log


# Common audit action constants
class AuditAction:
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    ATTENDANCE_MARKED = "ATTENDANCE_MARKED"
    ATTENDANCE_UPDATED = "ATTENDANCE_UPDATED"
    LEAVE_REQUEST_CREATED = "LEAVE_REQUEST_CREATED"
    LEAVE_REQUEST_APPROVED = "LEAVE_REQUEST_APPROVED"
    LEAVE_REQUEST_REJECTED = "LEAVE_REQUEST_REJECTED"
    LEAVE_TYPE_UPDATED = "LEAVE_TYPE_UPDATED"
    LEAVE_TYPE_DELETED = "LEAVE_TYPE_DELETED"
    FEE_STRUCTURE_UPDATED = "FEE_STRUCTURE_UPDATED"
    FEE_STRUCTURE_DELETED = "FEE_STRUCTURE_DELETED"
    FEE_INVOICE_GENERATED = "FEE_INVOICE_GENERATED"
    FEE_PAYMENT_RECORDED = "FEE_PAYMENT_RECORDED"
    FEE_PAYMENT_RECORDED = "FEE_PAYMENT_RECORDED"
    FEE_INVOICE_GENERATED = "FEE_INVOICE_GENERATED"
    CERTIFICATE_ISSUED = "CERTIFICATE_ISSUED"
    CERTIFICATE_TEMPLATE_CREATED = "CERTIFICATE_TEMPLATE_CREATED"
    QUIZ_CREATED = "QUIZ_CREATED"
    QUIZ_PUBLISHED = "QUIZ_PUBLISHED"
    ASSIGNMENT_CREATED = "ASSIGNMENT_CREATED"
    ASSIGNMENT_GRADED = "ASSIGNMENT_GRADED"
    RESULT_PUBLISHED = "RESULT_PUBLISHED"
    CLASS_CREATED = "CLASS_CREATED"
    STUDENT_ENROLLED = "STUDENT_ENROLLED"
    TIMETABLE_CREATED = "TIMETABLE_CREATED"
    CMS_SETTINGS_UPDATED = "CMS_SETTINGS_UPDATED"
