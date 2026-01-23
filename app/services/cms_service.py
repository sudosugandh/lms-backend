from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from typing import Optional, Dict, Any, List
from app.db.models.cms import WebsiteSettings, NavigationItem, PageContent
from app.db.models.institute import Institute
from app.schemas.cms import (
    WebsiteSettingsCreate, WebsiteSettingsUpdate,
    NavigationItemCreate, NavigationItemUpdate,
    PageContentCreate, PageContentUpdate
)


class CMSService:
    @staticmethod
    def get_website_settings(
        db: Session,
        institute_id: int
    ) -> Optional[WebsiteSettings]:
        """Get website settings for an institute."""
        settings = db.query(WebsiteSettings).filter(
            and_(
                WebsiteSettings.institute_id == institute_id,
                WebsiteSettings.is_active == True
            )
        ).first()
        
        if not settings:
            # Return default settings if none exist
            institute = db.query(Institute).filter(Institute.id == institute_id).first()
            if institute:
                settings = WebsiteSettings(
                    institute_id=institute_id,
                    site_name=institute.name,
                    site_tagline="",
                    is_active=True
                )
                db.add(settings)
                db.commit()
                db.refresh(settings)
        
        return settings
    
    @staticmethod
    def update_website_settings(
        db: Session,
        institute_id: int,
        admin_id: int,
        settings_data: WebsiteSettingsUpdate
    ) -> WebsiteSettings:
        """Update website settings for an institute."""
        settings = CMSService.get_website_settings(db, institute_id)
        
        if not settings:
            # Create if doesn't exist
            settings = WebsiteSettings(
                institute_id=institute_id,
                is_active=True
            )
            db.add(settings)
        
        update_data = settings_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        settings.updated_by = admin_id
        db.commit()
        db.refresh(settings)
        return settings
    
    @staticmethod
    def get_navigation_items(
        db: Session,
        institute_id: int
    ) -> List[NavigationItem]:
        """Get navigation items for an institute."""
        return db.query(NavigationItem).filter(
            and_(
                NavigationItem.institute_id == institute_id,
                NavigationItem.is_active == True
            )
        ).order_by(NavigationItem.order).all()
    
    @staticmethod
    def create_navigation_item(
        db: Session,
        institute_id: int,
        item_data: NavigationItemCreate
    ) -> NavigationItem:
        """Create a navigation item."""
        item = NavigationItem(
            institute_id=institute_id,
            label=item_data.label,
            url=item_data.url,
            order=item_data.order,
            is_active=item_data.is_active
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    
    @staticmethod
    def update_navigation_item(
        db: Session,
        item_id: int,
        institute_id: int,
        item_data: NavigationItemUpdate
    ) -> NavigationItem:
        """Update a navigation item."""
        item = db.query(NavigationItem).filter(
            and_(
                NavigationItem.id == item_id,
                NavigationItem.institute_id == institute_id
            )
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Navigation item not found"
            )
        
        update_data = item_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        
        db.commit()
        db.refresh(item)
        return item
    
    @staticmethod
    def delete_navigation_item(
        db: Session,
        item_id: int,
        institute_id: int
    ) -> bool:
        """Delete a navigation item."""
        item = db.query(NavigationItem).filter(
            and_(
                NavigationItem.id == item_id,
                NavigationItem.institute_id == institute_id
            )
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Navigation item not found"
            )
        
        db.delete(item)
        db.commit()
        return True
    
    @staticmethod
    def get_page_content(
        db: Session,
        institute_id: int,
        page_slug: str,
        published_only: bool = False
    ) -> Optional[PageContent]:
        """Get page content for an institute."""
        query = db.query(PageContent).filter(
            and_(
                PageContent.institute_id == institute_id,
                PageContent.page_slug == page_slug
            )
        )
        
        if published_only:
            query = query.filter(PageContent.is_published == True)
        
        return query.first()
    
    @staticmethod
    def create_or_update_page_content(
        db: Session,
        institute_id: int,
        admin_id: int,
        page_data: PageContentCreate
    ) -> PageContent:
        """Create or update page content."""
        existing = db.query(PageContent).filter(
            and_(
                PageContent.institute_id == institute_id,
                PageContent.page_slug == page_data.page_slug
            )
        ).first()
        
        if existing:
            # Update existing
            update_data = PageContentUpdate(**page_data.dict(exclude={'page_slug'})).dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(existing, field, value)
            existing.updated_by = admin_id
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new
            page = PageContent(
                institute_id=institute_id,
                page_slug=page_data.page_slug,
                title=page_data.title,
                content=page_data.content,
                meta_title=page_data.meta_title,
                meta_description=page_data.meta_description,
                is_published=page_data.is_published,
                updated_by=admin_id
            )
            db.add(page)
            db.commit()
            db.refresh(page)
            return page
    
    @staticmethod
    def get_all_pages(
        db: Session,
        institute_id: int,
        published_only: bool = False
    ) -> List[PageContent]:
        """Get all pages for an institute."""
        query = db.query(PageContent).filter(
            PageContent.institute_id == institute_id
        )
        
        if published_only:
            query = query.filter(PageContent.is_published == True)
        
        return query.order_by(PageContent.page_slug).all()
    
    @staticmethod
    def get_public_website_data(
        db: Session,
        institute_id: int
    ) -> Dict[str, Any]:
        """Get all public website data for frontend."""
        settings = CMSService.get_website_settings(db, institute_id)
        if not settings:
            # Fallback: create minimal settings if something went wrong
            institute = db.query(Institute).filter(Institute.id == institute_id).first()
            if institute:
                settings = WebsiteSettings(
                    institute_id=institute_id,
                    site_name=institute.name or "Website",
                    site_tagline="",
                    is_active=True
                )
                db.add(settings)
                db.commit()
                db.refresh(settings)
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Could not create website settings for institute {institute_id}"
                )
        
        navigation = CMSService.get_navigation_items(db, institute_id)
        pages = CMSService.get_all_pages(db, institute_id, published_only=True)
        
        # Convert pages to dict keyed by slug
        pages_dict = {page.page_slug: page for page in pages}
        
        return {
            "settings": settings,
            "navigation": navigation,
            "pages": pages_dict
        }
