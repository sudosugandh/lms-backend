from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.cms_service import CMSService
from app.schemas.cms import PublicWebsiteData, WebsiteSettingsResponse, NavigationItemResponse, PageContentResponse
from typing import List

router = APIRouter(prefix="/website", tags=["public-website"])


@router.get("/data", response_model=PublicWebsiteData)
async def get_public_website_data(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all public website data for the resolved institute."""
    if not hasattr(request.state, 'institute_id'):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Institute not resolved: institute_id missing"
        )
    institute_id = request.state.institute_id
    
    try:
        data = CMSService.get_public_website_data(db, institute_id)
        
        # Ensure settings exists
        if not data.get("settings"):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Website settings could not be loaded"
            )
        
        # Convert settings to response model
        settings_data = data["settings"]
        settings_response = WebsiteSettingsResponse(**settings_data.__dict__)
        
        # Convert navigation items
        navigation_response = [NavigationItemResponse(**item.__dict__) for item in data["navigation"]]
        
        # Convert pages (handle empty dict)
        pages_response = {}
        for slug, page in data["pages"].items():
            pages_response[slug] = PageContentResponse(**page.__dict__)
        
        return PublicWebsiteData(
            settings=settings_response,
            navigation=navigation_response,
            pages=pages_response
        )
    except HTTPException:
        raise
    except Exception as e:
        from fastapi import HTTPException, status
        import traceback
        error_detail = str(e)
        error_traceback = traceback.format_exc()
        # Log the error but don't expose full traceback in production
        print(f"ERROR in get_public_website_data: {error_detail}")
        print(error_traceback)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading website data: {error_detail}"
        )


@router.get("/settings", response_model=WebsiteSettingsResponse)
async def get_website_settings(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get website settings for the resolved institute."""
    if not hasattr(request.state, 'institute_id'):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Institute not resolved: institute_id missing"
        )
    institute_id = request.state.institute_id
    settings = CMSService.get_website_settings(db, institute_id)
    
    if not settings:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website settings not found"
        )
    
    return WebsiteSettingsResponse(**settings.__dict__)


@router.get("/navigation", response_model=List[NavigationItemResponse])
async def get_navigation(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get navigation items for the resolved institute."""
    if not hasattr(request.state, 'institute_id'):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Institute not resolved: institute_id missing"
        )
    institute_id = request.state.institute_id
    items = CMSService.get_navigation_items(db, institute_id)
    
    return [NavigationItemResponse(**item.__dict__) for item in items]


@router.get("/pages/{page_slug}", response_model=PageContentResponse)
async def get_page_content(
    page_slug: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get published page content for the resolved institute."""
    if not hasattr(request.state, 'institute_id'):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Institute not resolved: institute_id missing"
        )
    institute_id = request.state.institute_id
    page = CMSService.get_page_content(db, institute_id, page_slug, published_only=True)
    
    if not page:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page '{page_slug}' not found or not published"
        )
    
    return PageContentResponse(**page.__dict__)
