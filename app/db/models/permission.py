from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Permission(Base):
    """Permission definitions - static list of all available permissions."""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    module = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('module', 'action', name='uq_permission_module_action'),
    )


class RolePermission(Base):
    """Many-to-many relationship between roles and permissions."""
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False, index=True)  # UserRole enum value
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    permission = relationship("Permission", back_populates="role_permissions")
    
    __table_args__ = (
        UniqueConstraint('role', 'permission_id', name='uq_role_permission'),
    )
