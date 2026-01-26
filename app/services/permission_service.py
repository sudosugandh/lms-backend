from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Dict, Set, Optional
from app.db.models.permission import Permission, RolePermission
from app.db.models.user import UserRole
from fastapi import HTTPException, status


class PermissionService:
    """Service for managing permissions and role-based access control."""
    
    # Define all available modules and actions
    MODULES = {
        'dashboard': {'view'},
        'users': {'view', 'create', 'edit', 'delete', 'export'},
        'classes': {'view', 'create', 'edit', 'delete', 'export'},
        'subjects': {'view', 'create', 'edit', 'delete', 'export'},
        'attendance': {'view', 'create', 'edit', 'delete', 'export'},
        'gradebook': {'view', 'create', 'edit', 'delete', 'export'},
        'quizzes': {'view', 'create', 'edit', 'delete', 'export', 'take'},
        'assignments': {'view', 'create', 'edit', 'delete', 'export', 'submit'},
        'exams': {'view', 'create', 'edit', 'delete', 'export'},
        'timetable': {'view', 'create', 'edit', 'delete', 'export'},
        'leave': {'view', 'create', 'edit', 'delete', 'approve', 'export'},
        'notifications': {'view', 'create', 'edit', 'delete', 'export'},
        'fees': {'view', 'create', 'edit', 'delete', 'export'},
        'certificates': {'view', 'create', 'edit', 'delete', 'export'},
        'cms': {'view', 'create', 'edit', 'delete', 'export'},
        'reports': {'view', 'export'},
        'settings': {'view', 'edit'},
    }
    
    @staticmethod
    def get_permission_string(module: str, action: str) -> str:
        """Get permission string in format 'module.action'."""
        return f"{module}.{action}"
    
    @staticmethod
    def parse_permission_string(permission_str: str) -> tuple:
        """Parse permission string 'module.action' into (module, action)."""
        parts = permission_str.split('.', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid permission format: {permission_str}")
        return parts[0], parts[1]
    
    @staticmethod
    def seed_permissions(db: Session) -> List[Permission]:
        """Seed all available permissions into the database."""
        permissions = []
        
        for module, actions in PermissionService.MODULES.items():
            for action in actions:
                # Check if permission already exists
                existing = db.query(Permission).filter(
                    and_(
                        Permission.module == module,
                        Permission.action == action
                    )
                ).first()
                
                if not existing:
                    permission = Permission(
                        module=module,
                        action=action,
                        name=f"{module.title()} {action.title()}",
                        description=f"Permission to {action} {module}"
                    )
                    db.add(permission)
                    permissions.append(permission)
        
        db.commit()
        return permissions
    
    @staticmethod
    def get_all_permissions(db: Session) -> List[Permission]:
        """Get all permissions."""
        return db.query(Permission).order_by(Permission.module, Permission.action).all()
    
    @staticmethod
    def get_permissions_by_module(db: Session) -> Dict[str, List[Permission]]:
        """Get permissions grouped by module."""
        permissions = PermissionService.get_all_permissions(db)
        result = {}
        for perm in permissions:
            if perm.module not in result:
                result[perm.module] = []
            result[perm.module].append(perm)
        return result
    
    @staticmethod
    def get_role_permissions(db: Session, role: str) -> List[Permission]:
        """Get all permissions for a specific role."""
        role_perms = db.query(RolePermission).filter(
            RolePermission.role == role
        ).all()
        
        permission_ids = [rp.permission_id for rp in role_perms]
        if not permission_ids:
            return []
        
        return db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    
    @staticmethod
    def get_user_permissions(db: Session, user: 'User') -> Set[str]:
        """Get all permission strings for a user (e.g., ['dashboard.view', 'users.create'])."""
        # SUPER_ADMIN has all permissions
        if user.role == UserRole.SUPER_ADMIN:
            all_perms = PermissionService.get_all_permissions(db)
            return {PermissionService.get_permission_string(p.module, p.action) for p in all_perms}
        
        # ADMIN has all permissions at institute level (full access)
        if user.role == UserRole.ADMIN:
            all_perms = PermissionService.get_all_permissions(db)
            return {PermissionService.get_permission_string(p.module, p.action) for p in all_perms}
        
        # Get role permissions
        role_perms = PermissionService.get_role_permissions(db, user.role.value)
        return {PermissionService.get_permission_string(p.module, p.action) for p in role_perms}
    
    @staticmethod
    def user_has_permission(db: Session, user: 'User', module: str, action: str) -> bool:
        """Check if user has a specific permission."""
        # SUPER_ADMIN bypasses all checks (system-wide)
        if user.role == UserRole.SUPER_ADMIN:
            return True
        
        # ADMIN bypasses all checks at institute level (full access)
        if user.role == UserRole.ADMIN:
            return True
        
        permission_str = PermissionService.get_permission_string(module, action)
        user_perms = PermissionService.get_user_permissions(db, user)
        return permission_str in user_perms
    
    @staticmethod
    def set_role_permissions(db: Session, role: str, permission_ids: List[int]) -> List[RolePermission]:
        """Set permissions for a role (replaces existing)."""
        # Validate role
        if role not in [r.value for r in UserRole]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}"
            )
        
        # Validate permission IDs exist
        permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        if len(permissions) != len(permission_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some permission IDs are invalid"
            )
        
        # Delete existing role permissions
        db.query(RolePermission).filter(RolePermission.role == role).delete()
        
        # Create new role permissions
        role_permissions = []
        for permission_id in permission_ids:
            role_perm = RolePermission(
                role=role,
                permission_id=permission_id
            )
            db.add(role_perm)
            role_permissions.append(role_perm)
        
        db.commit()
        return role_permissions
    
    @staticmethod
    def get_user_permissions_by_module(db: Session, user: 'User') -> Dict[str, List[str]]:
        """Get user permissions grouped by module."""
        user_perms = PermissionService.get_user_permissions(db, user)
        result = {}
        
        for perm_str in user_perms:
            module, action = PermissionService.parse_permission_string(perm_str)
            if module not in result:
                result[module] = []
            result[module].append(action)
        
        return result
