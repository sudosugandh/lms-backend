from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.db.models.page import PageType


class PageTranslationBase(BaseModel):
    locale: str
    name: str
    description: Optional[str] = None
    embedded_code: Optional[str] = None


class PageTranslationCreate(PageTranslationBase):
    pass


class PageTranslationResponse(PageTranslationBase):
    id: int
    page_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PageBase(BaseModel):
    page_type: PageType = PageType.CUSTOM
    slug: str
    sequence: int = 0
    add_in_header_menu: bool = False
    show_menu_on_footer: bool = False
    show_after_login: bool = False
    show_only_to_logged_in_user: bool = False
    enable_tab: bool = False
    use_web_view_url: bool = False
    enable_for_blog: bool = False
    widget_color: Optional[str] = None
    custom_page_url: Optional[str] = None
    page_id: Optional[int] = None  # Parent page ID
    is_approved: bool = True


class PageCreate(PageBase):
    translations: List[PageTranslationCreate]


class PageUpdate(BaseModel):
    slug: Optional[str] = None
    sequence: Optional[int] = None
    add_in_header_menu: Optional[bool] = None
    show_menu_on_footer: Optional[bool] = None
    show_after_login: Optional[bool] = None
    show_only_to_logged_in_user: Optional[bool] = None
    enable_tab: Optional[bool] = None
    use_web_view_url: Optional[bool] = None
    enable_for_blog: Optional[bool] = None
    widget_color: Optional[str] = None
    custom_page_url: Optional[str] = None
    page_id: Optional[int] = None
    is_approved: Optional[bool] = None
    translations: Optional[List[PageTranslationCreate]] = None


class PageResponse(PageBase):
    id: int
    institute_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    translations: List[PageTranslationResponse] = []
    parent: Optional['PageResponse'] = None
    children: List['PageResponse'] = []
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Update forward reference
PageResponse.model_rebuild()


class PageSequenceUpdate(BaseModel):
    page_sequences: List[dict]  # [{"id": 1, "sequence": 0}, {"id": 2, "sequence": 1}, ...]
