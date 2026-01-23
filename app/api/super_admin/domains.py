from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.domain import Domain
from app.db.models.institute import Institute
from app.db.models.user import User
from app.schemas.institute import DomainCreate, DomainResponse
from app.utils.dependencies import get_super_admin

router = APIRouter(prefix="/domains", tags=["super-admin-domains"])


@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def create_domain(
    domain_data: DomainCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """Create a new domain for an institute (Super Admin only)."""
    # Verify institute exists
    institute = db.query(Institute).filter(Institute.id == domain_data.institute_id).first()
    if not institute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institute not found"
        )
    
    # Check if host_name already exists
    existing = db.query(Domain).filter(Domain.host_name == domain_data.host_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain already exists"
        )
    
    domain = Domain(
        institute_id=domain_data.institute_id,
        host_name=domain_data.host_name.lower().strip(),
        is_active=domain_data.is_active
    )
    
    db.add(domain)
    db.commit()
    db.refresh(domain)
    
    return domain


@router.get("", response_model=List[DomainResponse])
async def list_domains(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """List all domains (Super Admin only)."""
    domains = db.query(Domain).all()
    return domains
