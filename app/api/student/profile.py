from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import UserMe
from app.utils.dependencies import get_student
from app.core.security import get_password_hash

router = APIRouter(prefix="/profile", tags=["student-profile"])


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    profile_picture: Optional[str] = None


@router.get("", response_model=UserMe)
async def get_profile(
    current_user: User = Depends(get_student)
):
    """Get current student profile."""
    return UserMe(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.value,
        institute_id=current_user.institute_id,
        is_active=current_user.is_active,
        profile_picture=current_user.profile_picture
    )


@router.put("", response_model=UserMe)
async def update_profile(
    profile_data: ProfileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Update current student profile."""
    # Check if email is being changed and if it's already taken
    if profile_data.email and profile_data.email != current_user.email:
        existing = db.query(User).filter(User.email == profile_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        current_user.email = profile_data.email
    
    if profile_data.name:
        current_user.name = profile_data.name
    
    if profile_data.password:
        current_user.password_hash = get_password_hash(profile_data.password)
    
    if profile_data.profile_picture is not None:
        current_user.profile_picture = profile_data.profile_picture
    
    db.commit()
    db.refresh(current_user)
    
    return UserMe(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.value,
        institute_id=current_user.institute_id,
        is_active=current_user.is_active,
        profile_picture=current_user.profile_picture
    )
