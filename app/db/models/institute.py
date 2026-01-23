from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Institute(Base):
    __tablename__ = "institutes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    domains = relationship("Domain", back_populates="institute", cascade="all, delete-orphan")
    users = relationship("User", back_populates="institute")
    classes = relationship("Class", back_populates="institute", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="institute", cascade="all, delete-orphan")
    website_settings = relationship("WebsiteSettings", back_populates="institute", uselist=False, cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="institute", cascade="all, delete-orphan")