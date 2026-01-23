from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.permission import (
    PermissionResponse,
    RolePermissionResponse,
    RolePermissionsUpdate,
    UserPermissionsResponse,
    PermissionModule
)
from app.services.permission_service import PermissionService
from app.utils.dependencies import get_institute_admin
from app.utils.pagination import PaginatedResponse, create_paginated_response

router = APIRouter(prefix="/permissions", tags=["admin-permissions"])


@router.post("/seed", response_model=List[PermissionResponse])
async def seed_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Seed all permissions into the database (Admin only)."""
    permissions = PermissionService.seed_permissions(db)
    return [PermissionResponse(**p.__dict__) for p in permissions]


@router.get("", response_model=List[PermissionResponse])
async def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """List all available permissions (Admin only)."""
    permissions = PermissionService.get_all_permissions(db)
    # If no permissions exist, seed them automatically
    if not permissions:
        permissions = PermissionService.seed_permissions(db)
    return [PermissionResponse(**p.__dict__) for p in permissions]


@router.get("/modules", response_model=List[PermissionModule])
async def get_permissions_by_module(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get permissions grouped by module (Admin only)."""
    # Ensure permissions are seeded
    permissions = PermissionService.get_all_permissions(db)
    if not permissions:
        PermissionService.seed_permissions(db)
    
    permissions_by_module = PermissionService.get_permissions_by_module(db)
    
    result = []
    for module, permissions in permissions_by_module.items():
        actions = [p.action for p in permissions]
        result.append(PermissionModule(
            module=module,
            name=module.title(),
            actions=actions,
            permissions=[PermissionResponse(**p.__dict__) for p in permissions]
        ))
    
    return result


@router.get("/roles/{role}", response_model=List[PermissionResponse])
async def get_role_permissions(
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get all permissions for a specific role (Admin only)."""
    return PermissionService.get_role_permissions(db, role)


@router.put("/roles/{role}", response_model=List[RolePermissionResponse])
async def update_role_permissions(
    role: str,
    data: RolePermissionsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Update permissions for a role (Admin only)."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Ensure permissions are seeded
        permissions = PermissionService.get_all_permissions(db)
        if not permissions:
            logger.info("No permissions found, seeding permissions...")
            PermissionService.seed_permissions(db)
        
        logger.info(f"Updating permissions for role {role} with {len(data.permission_ids)} permissions")
        role_permissions = PermissionService.set_role_permissions(
            db, role, data.permission_ids
        )
        
        # Fetch with permission details
        from app.db.models.permission import Permission
        result = []
        for rp in role_permissions:
            perm = db.query(Permission).filter(Permission.id == rp.permission_id).first()
            
            result.append(RolePermissionResponse(
                id=rp.id,
                role=rp.role,
                permission_id=rp.permission_id,
                permission=PermissionResponse(**perm.__dict__) if perm else None,
                created_at=rp.created_at
            ))
        
        logger.info(f"Successfully updated {len(result)} permissions for role {role}")
        return result
    except Exception as e:
        logger.error(f"Error updating role permissions: {str(e)}", exc_info=True)
        raise


@router.get("/me", response_model=UserPermissionsResponse)
async def get_my_permissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get current user's permissions (Admin only)."""
    permissions = PermissionService.get_user_permissions(db, current_user)
    permissions_by_module = PermissionService.get_user_permissions_by_module(db, current_user)
    
    return UserPermissionsResponse(
        role=current_user.role.value,
        permissions=list(permissions),
        permissions_by_module=permissions_by_module
    )
