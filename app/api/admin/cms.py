from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.cms import (
    WebsiteSettingsUpdate, WebsiteSettingsResponse,
    NavigationItemCreate, NavigationItemUpdate, NavigationItemResponse,
    PageContentCreate, PageContentUpdate, PageContentResponse
)
from app.services.cms_service import CMSService
from app.utils.dependencies import get_institute_admin

router = APIRouter(prefix="/cms", tags=["admin-cms"])


# Website Settings endpoints
@router.get("/settings", response_model=WebsiteSettingsResponse)
async def get_settings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get website settings (Admin only)."""
    institute_id = request.state.institute_id
    settings = CMSService.get_website_settings(db, institute_id)
    
    if not settings:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website settings not found"
        )
    
    return WebsiteSettingsResponse(**settings.__dict__)


@router.put("/settings", response_model=WebsiteSettingsResponse)
async def update_settings(
    settings_data: WebsiteSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Update website settings (Admin only)."""
    institute_id = request.state.institute_id
    settings = CMSService.update_website_settings(
        db, institute_id, current_user.id, settings_data
    )
    
    return WebsiteSettingsResponse(**settings.__dict__)


# Navigation endpoints
@router.get("/navigation", response_model=List[NavigationItemResponse])
async def list_navigation(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """List navigation items (Admin only)."""
    institute_id = request.state.institute_id
    items = CMSService.get_navigation_items(db, institute_id)
    
    return [NavigationItemResponse(**item.__dict__) for item in items]


@router.post("/navigation", response_model=NavigationItemResponse, status_code=201)
async def create_navigation_item(
    item_data: NavigationItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Create navigation item (Admin only)."""
    institute_id = request.state.institute_id
    item = CMSService.create_navigation_item(db, institute_id, item_data)
    
    return NavigationItemResponse(**item.__dict__)


@router.put("/navigation/{item_id}", response_model=NavigationItemResponse)
async def update_navigation_item(
    item_id: int,
    item_data: NavigationItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Update navigation item (Admin only)."""
    institute_id = request.state.institute_id
    item = CMSService.update_navigation_item(db, item_id, institute_id, item_data)
    
    return NavigationItemResponse(**item.__dict__)


@router.delete("/navigation/{item_id}", status_code=204)
async def delete_navigation_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Delete navigation item (Admin only)."""
    institute_id = request.state.institute_id
    CMSService.delete_navigation_item(db, item_id, institute_id)
    return None


# Page Content endpoints
@router.get("/pages", response_model=List[PageContentResponse])
async def list_pages(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """List all pages (Admin only)."""
    institute_id = request.state.institute_id
    pages = CMSService.get_all_pages(db, institute_id, published_only=False)
    
    return [PageContentResponse(**page.__dict__) for page in pages]


@router.get("/pages/{page_slug}", response_model=PageContentResponse)
async def get_page(
    page_slug: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get page content (Admin only - includes unpublished)."""
    institute_id = request.state.institute_id
    page = CMSService.get_page_content(db, institute_id, page_slug, published_only=False)
    
    if not page:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page '{page_slug}' not found"
        )
    
    return PageContentResponse(**page.__dict__)


@router.post("/pages", response_model=PageContentResponse, status_code=201)
async def create_or_update_page(
    page_data: PageContentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Create or update page content (Admin only)."""
    institute_id = request.state.institute_id
    page = CMSService.create_or_update_page_content(
        db, institute_id, current_user.id, page_data
    )
    
    return PageContentResponse(**page.__dict__)


@router.put("/pages/{page_slug}", response_model=PageContentResponse)
async def update_page(
    page_slug: str,
    page_data: PageContentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Update page content (Admin only)."""
    institute_id = request.state.institute_id
    
    # Get existing page
    existing = CMSService.get_page_content(db, institute_id, page_slug, published_only=False)
    
    if not existing:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page '{page_slug}' not found"
        )
    
    # Merge update data
    update_dict = page_data.dict(exclude_unset=True)
    create_data = PageContentCreate(
        page_slug=page_slug,
        title=update_dict.get("title", existing.title),
        content=update_dict.get("content", existing.content),
        meta_title=update_dict.get("meta_title", existing.meta_title),
        meta_description=update_dict.get("meta_description", existing.meta_description),
        is_published=update_dict.get("is_published", existing.is_published)
    )
    
    page = CMSService.create_or_update_page_content(
        db, institute_id, current_user.id, create_data
    )
    
    return PageContentResponse(**page.__dict__)
