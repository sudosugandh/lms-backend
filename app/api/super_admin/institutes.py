from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.institute import Institute
from app.db.models.user import User
from app.schemas.institute import InstituteCreate, InstituteResponse
from app.utils.dependencies import get_super_admin

router = APIRouter(prefix="/institutes", tags=["super-admin-institutes"])


@router.post("", response_model=InstituteResponse, status_code=status.HTTP_201_CREATED)
async def create_institute(
    institute_data: InstituteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """Create a new institute (Super Admin only)."""
    # Check if code already exists
    existing = db.query(Institute).filter(Institute.code == institute_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institute code already exists"
        )
    
    institute = Institute(
        name=institute_data.name,
        code=institute_data.code,
        is_active=institute_data.is_active
    )
    
    db.add(institute)
    db.commit()
    db.refresh(institute)
    
    return institute


@router.get("", response_model=List[InstituteResponse])
async def list_institutes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_super_admin)
):
    """List all institutes (Super Admin only)."""
    institutes = db.query(Institute).all()
    return institutes
