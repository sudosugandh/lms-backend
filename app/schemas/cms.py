from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class WebsiteSettingsBase(BaseModel):
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    banner_images: Optional[List[str]] = None  # Array of banner image/video URLs
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    header_background: Optional[str] = None
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    site_name: Optional[str] = None
    site_tagline: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    footer_text: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None


class WebsiteSettingsCreate(WebsiteSettingsBase):
    pass


class WebsiteSettingsUpdate(WebsiteSettingsBase):
    pass


class WebsiteSettingsResponse(WebsiteSettingsBase):
    id: int
    institute_id: int
    is_active: bool
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NavigationItemBase(BaseModel):
    label: str
    url: str
    order: int = 0
    is_active: bool = True


class NavigationItemCreate(NavigationItemBase):
    pass


class NavigationItemUpdate(BaseModel):
    label: Optional[str] = None
    url: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class NavigationItemResponse(NavigationItemBase):
    id: int
    institute_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PageContentBase(BaseModel):
    page_slug: str  # home, about, careers, contact
    title: str
    content: Dict[str, Any]  # Structured content
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: bool = False


class PageContentCreate(PageContentBase):
    pass


class PageContentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: Optional[bool] = None


class PageContentResponse(PageContentBase):
    id: int
    institute_id: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PublicWebsiteData(BaseModel):
    """Combined public website data for frontend"""
    settings: WebsiteSettingsResponse
    navigation: List[NavigationItemResponse]
    pages: Dict[str, PageContentResponse]  # keyed by page_slug
