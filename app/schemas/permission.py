from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PermissionBase(BaseModel):
    module: str
    action: str
    name: str
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RolePermissionBase(BaseModel):
    role: str
    permission_id: int


class RolePermissionCreate(RolePermissionBase):
    pass


class RolePermissionResponse(RolePermissionBase):
    id: int
    permission: Optional[PermissionResponse] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class RolePermissionsUpdate(BaseModel):
    """Update permissions for a role."""
    permission_ids: List[int]


class UserPermissionsResponse(BaseModel):
    """User's permissions grouped by module."""
    role: str
    permissions: List[str]  # List of "module.action" strings
    permissions_by_module: dict  # {module: [actions]}


class PermissionModule(BaseModel):
    """Module with its available actions."""
    module: str
    name: str
    actions: List[str]
    permissions: List[PermissionResponse]
