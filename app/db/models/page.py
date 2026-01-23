from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class PageType(str, enum.Enum):
    CUSTOM = "custom"
    HOME = "home"
    ABOUT = "about"
    CONTACT = "contact"
    CAREERS = "careers"


class Page(Base):
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    page_type = Column(Enum(PageType), nullable=False, default=PageType.CUSTOM)
    slug = Column(String(255), nullable=False, index=True)
    sequence = Column(Integer, nullable=False, default=0, index=True)
    
    # Navigation settings
    add_in_header_menu = Column(Boolean, default=False, nullable=False)
    show_menu_on_footer = Column(Boolean, default=False, nullable=False)
    show_after_login = Column(Boolean, default=False, nullable=False)
    show_only_to_logged_in_user = Column(Boolean, default=False, nullable=False)
    
    # Advanced settings
    enable_tab = Column(Boolean, default=False, nullable=False)
    use_web_view_url = Column(Boolean, default=False, nullable=False)
    enable_for_blog = Column(Boolean, default=False, nullable=False)
    widget_color = Column(String(20), nullable=True)
    custom_page_url = Column(String(500), nullable=True)
    
    # Hierarchy
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Status
    is_approved = Column(Boolean, default=True, nullable=False, index=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute", back_populates="pages")
    creator = relationship("User", foreign_keys=[created_by])
    parent = relationship("Page", remote_side=[id], backref="children")
    translations = relationship("PageTranslation", back_populates="page", cascade="all, delete-orphan")
    
    # Ensure unique slug per institute
    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('institute_id', 'slug', name='uq_institute_page_slug'),
    )


class PageTranslation(Base):
    __tablename__ = "page_translations"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    locale = Column(String(10), nullable=False, index=True)  # en, es, fr, etc.
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    embedded_code = Column(Text, nullable=True)  # HTML content from TinyMCE
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    page = relationship("Page", back_populates="translations")
    
    # Ensure unique translation per page and locale
    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('page_id', 'locale', name='uq_page_translation'),
    )
