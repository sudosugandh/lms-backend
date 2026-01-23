from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class WebsiteSettings(Base):
    __tablename__ = "website_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    logo_url = Column(String(500), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    primary_color = Column(String(20), nullable=True, default="#3B82F6")
    secondary_color = Column(String(20), nullable=True, default="#1E40AF")
    site_name = Column(String(255), nullable=True)
    site_tagline = Column(String(500), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_address = Column(Text, nullable=True)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(String(500), nullable=True)
    footer_text = Column(Text, nullable=True)
    social_links = Column(JSON, nullable=True)  # {"facebook": "...", "twitter": "...", "linkedin": "...", "youtube": "..."}
    is_active = Column(Boolean, default=True, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute", back_populates="website_settings")
    updater = relationship("User", foreign_keys=[updated_by])


class NavigationItem(Base):
    __tablename__ = "navigation_items"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(100), nullable=False)
    url = Column(String(255), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")


class PageContent(Base):
    __tablename__ = "page_contents"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    page_slug = Column(String(100), nullable=False, index=True)  # home, about, careers, contact
    title = Column(String(255), nullable=False)
    content = Column(JSON, nullable=False)  # Structured content: sections, banners, text blocks, etc.
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    updater = relationship("User", foreign_keys=[updated_by])
    
    # Ensure unique page per institute
    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('institute_id', 'page_slug', name='uq_institute_page'),
    )
