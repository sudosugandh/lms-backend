from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.permission import UserPermissionsResponse
from app.services.permission_service import PermissionService
from app.utils.dependencies import get_parent

router = APIRouter(prefix="/permissions", tags=["parent-permissions"])


@router.get("/me", response_model=UserPermissionsResponse)
async def get_my_permissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_parent)
):
    """Get current parent's permissions."""
    permissions = PermissionService.get_user_permissions(db, current_user)
    permissions_by_module = PermissionService.get_user_permissions_by_module(db, current_user)
    
    return UserPermissionsResponse(
        role=current_user.role.value,
        permissions=list(permissions),
        permissions_by_module=permissions_by_module
    )
