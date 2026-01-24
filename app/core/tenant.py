from typing import Optional
from sqlalchemy.orm import Session
from app.db.models.domain import Domain
from app.db.models.institute import Institute


def normalize_host(host: str) -> str:
    """
    Normalize host by removing protocol only.
    Returns host exactly as received (with port if present).
    This matches eureka SaaS pattern: exact matching, no port stripping.
    
    Examples:
    - "localhost:3000" -> "localhost:3000" (exact match required in DB)
    - "example.com" -> "example.com" (exact match required in DB)
    - "http://localhost:3000" -> "localhost:3000" (protocol removed)
    """
    host = host.strip()
    # Remove protocol if present (Host header never includes protocol, but might come from DB)
    if host.startswith('http://'):
        host = host.replace('http://', '', 1)
    if host.startswith('https://'):
        host = host.replace('https://', '', 1)
    return host.strip()


def resolve_institute_by_host(db: Session, host: str) -> Optional[Institute]:
    """
    Resolve institute by hostname from domains table.
    Matches Host header EXACTLY against domains.host_name field (eureka SaaS pattern).
    
    This means:
    - If DB has "localhost:3000", only "localhost:3000" will match
    - If DB has "localhost:3001", only "localhost:3001" will match
    - If DB has "example.com", only "example.com" will match (no port)
    - Exact case-sensitive matching, no normalization
    """
    # Normalize only to remove protocol (if present)
    normalized_host = normalize_host(host)
    
    # Exact match lookup (case-sensitive, includes port if present in DB)
    domain = db.query(Domain).filter(
        Domain.host_name == normalized_host,
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
