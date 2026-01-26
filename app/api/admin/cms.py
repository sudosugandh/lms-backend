from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.cms import WebsiteSettings
from app.schemas.cms import (
    WebsiteSettingsUpdate, WebsiteSettingsResponse,
    NavigationItemCreate, NavigationItemUpdate, NavigationItemResponse,
    PageContentCreate, PageContentUpdate, PageContentResponse
)
from app.services.cms_service import CMSService
from app.utils.dependencies import get_institute_admin
from app.utils.file_upload import FileUploadService
from pathlib import Path
import json

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


# File upload endpoints
@router.post("/settings/upload-logo", response_model=dict)
async def upload_logo(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Upload logo file (Admin only)."""
    institute_id = request.state.institute_id
    
    # Validate file type (images only)
    allowed_types = {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed for logo"
        )
    
    # Save file
    base_url = str(request.base_url).rstrip('/')
    file_info = await FileUploadService.save_file(
        file,
        directory=f"cms/{institute_id}/logos",
        allowed_types=allowed_types,
        max_size=5 * 1024 * 1024,  # 5MB
        base_url=base_url
    )
    
    # Update settings with logo URL
    settings = CMSService.get_website_settings(db, institute_id)
    if settings:
        update_data = WebsiteSettingsUpdate(logo_url=file_info['file_url'])
        CMSService.update_website_settings(db, institute_id, current_user.id, update_data)
    
    return {"file_url": file_info['file_url'], "filename": file_info['filename']}


@router.post("/settings/upload-favicon", response_model=dict)
async def upload_favicon(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Upload favicon file (Admin only)."""
    institute_id = request.state.institute_id
    
    # Validate file type (images only, smaller size)
    allowed_types = {'image/x-icon', 'image/png', 'image/svg+xml', 'image/jpeg'}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed for favicon"
        )
    
    # Save file
    base_url = str(request.base_url).rstrip('/')
    file_info = await FileUploadService.save_file(
        file,
        directory=f"cms/{institute_id}/favicons",
        allowed_types=allowed_types,
        max_size=1 * 1024 * 1024,  # 1MB
        base_url=base_url
    )
    
    # Update settings with favicon URL
    settings = CMSService.get_website_settings(db, institute_id)
    if settings:
        update_data = WebsiteSettingsUpdate(favicon_url=file_info['file_url'])
        CMSService.update_website_settings(db, institute_id, current_user.id, update_data)
    
    return {"file_url": file_info['file_url'], "filename": file_info['filename']}


@router.post("/settings/upload-banner", response_model=dict)
async def upload_banner(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Upload banner image (Admin only)."""
    institute_id = request.state.institute_id
    
    # Validate file type (images and videos)
    allowed_types = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'video/mp4', 'video/webm', 'video/ogg'
    }
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image and video files are allowed for banners"
        )
    
    # Save file
    base_url = str(request.base_url).rstrip('/')
    file_info = await FileUploadService.save_file(
        file,
        directory=f"cms/{institute_id}/banners",
        allowed_types=allowed_types,
        max_size=50 * 1024 * 1024,  # 50MB for videos
        base_url=base_url
    )
    
    # Get current settings and add banner to list
    # For sequential uploads, we need to get fresh data from database
    # Use a fresh query to avoid cached objects
    # Query directly to get fresh data
    settings = db.query(WebsiteSettings).filter(
        and_(
            WebsiteSettings.institute_id == institute_id,
            WebsiteSettings.is_active == True
        )
    ).first()
    
    if not settings:
        # Create if doesn't exist
        settings = WebsiteSettings(
            institute_id=institute_id,
            is_active=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    # Get existing banners
    banners = getattr(settings, 'banner_images', []) or []
    if isinstance(banners, str):
        try:
            banners = json.loads(banners)
        except:
            banners = []
    if not isinstance(banners, list):
        banners = []
    
    # Only add if not already in list (prevent duplicates)
    if file_info['file_url'] not in banners:
        banners.append(file_info['file_url'])
    
    # Update settings with new banner list
    settings.banner_images = banners
    settings.updated_by = current_user.id
    db.commit()
    db.refresh(settings)
    
    return {"file_url": file_info['file_url'], "filename": file_info['filename']}


@router.delete("/settings/delete-logo", status_code=204)
async def delete_logo(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Delete logo (Admin only)."""
    institute_id = request.state.institute_id
    settings = CMSService.get_website_settings(db, institute_id)
    if settings and settings.logo_url:
        # Delete file from filesystem
        # Extract path from URL
        if settings.logo_url.startswith('/uploads/'):
            file_path = Path('uploads') / settings.logo_url.replace('/uploads/', '')
            FileUploadService.delete_file(str(file_path))
        
        # Clear logo URL
        update_data = WebsiteSettingsUpdate(logo_url=None)
        CMSService.update_website_settings(db, institute_id, current_user.id, update_data)
    
    return None


@router.delete("/settings/delete-favicon", status_code=204)
async def delete_favicon(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Delete favicon (Admin only)."""
    institute_id = request.state.institute_id
    settings = CMSService.get_website_settings(db, institute_id)
    if settings and settings.favicon_url:
        # Delete file from filesystem
        if settings.favicon_url.startswith('/uploads/'):
            file_path = Path('uploads') / settings.favicon_url.replace('/uploads/', '')
            FileUploadService.delete_file(str(file_path))
        
        # Clear favicon URL
        update_data = WebsiteSettingsUpdate(favicon_url=None)
        CMSService.update_website_settings(db, institute_id, current_user.id, update_data)
    
    return None


@router.delete("/settings/delete-banner", status_code=204)
async def delete_banner(
    request: Request,
    banner_url: str = Query(..., description="URL of the banner to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Delete a specific banner image/video by URL (Admin only)."""
    
    institute_id = request.state.institute_id
    settings = CMSService.get_website_settings(db, institute_id)
    
    if not settings:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website settings not found"
        )
    
    # Get existing banners
    banners = getattr(settings, 'banner_images', []) or []
    if isinstance(banners, str):
        try:
            banners = json.loads(banners)
        except:
            banners = []
    if not isinstance(banners, list):
        banners = []
    
    # Remove the banner URL from the list
    original_count = len(banners)
    banners = [b for b in banners if b != banner_url]
    
    if len(banners) == original_count:
        # Banner not found in list
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found"
        )
    
    # Delete file from filesystem if it's a local file
    if banner_url.startswith('/uploads/'):
        file_path = Path('uploads') / banner_url.replace('/uploads/', '')
        FileUploadService.delete_file(str(file_path))
    
    # Update settings with new banner list
    update_data = WebsiteSettingsUpdate(banner_images=banners)
    CMSService.update_website_settings(db, institute_id, current_user.id, update_data)
    
    return None


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
