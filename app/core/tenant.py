from typing import Optional
from sqlalchemy.orm import Session
from app.db.models.domain import Domain
from app.db.models.institute import Institute


def extract_hostname(host: str) -> str:
    """
    Extract hostname from host header exactly as received.
    For development: No normalization, no port stripping, exact match only.
    Removes protocol if present (http:// or https://).
    """
    # Remove protocol if present (Host header never includes protocol, but DB might)
    host = host.strip()
    if host.startswith('http://'):
        host = host.replace('http://', '', 1)
    if host.startswith('https://'):
        host = host.replace('https://', '', 1)
    # Return host exactly as received (after protocol removal)
    return host.strip()


def resolve_institute_by_host(db: Session, host: str) -> Optional[Institute]:
    """
    Resolve institute by hostname from domains table.
    Matches Host header exactly against domains.host_name field.
    """
    # Get hostname exactly as received (no normalization)
    hostname = extract_hostname(host)
    
    # Exact match lookup (case-sensitive, includes port if present)
    domain = db.query(Domain).filter(
        Domain.host_name == hostname,
        Domain.is_active == True
    ).first()
    
    if not domain:
        return None
    
    # Check if institute is active
    institute = db.query(Institute).filter(
        Institute.id == domain.institute_id,
        Institute.is_active == True
    ).first()
    
    return institute
