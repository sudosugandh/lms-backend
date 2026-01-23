from fastapi import APIRouter, Depends
from app.db.models.user import User
from app.schemas.auth import UserMe
from app.utils.dependencies import get_institute_admin

router = APIRouter(prefix="/profile", tags=["admin-profile"])


@router.get("", response_model=UserMe)
async def get_profile(
    current_user: User = Depends(get_institute_admin)
):
    """Get current institute admin profile."""
    return UserMe(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.value,
        institute_id=current_user.institute_id,
        is_active=current_user.is_active
    )
