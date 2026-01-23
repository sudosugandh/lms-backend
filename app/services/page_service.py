from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from typing import List, Optional, Tuple
from app.db.models.page import Page, PageTranslation, PageType
from app.schemas.page import PageCreate, PageUpdate, PageTranslationCreate
from app.db.models.user import User


class PageService:
    @staticmethod
    def get_pages(
        db: Session,
        institute_id: int,
        skip: int = 0,
        limit: int = 100,
        locale: Optional[str] = None,
        is_approved: Optional[bool] = None
    ) -> Tuple[List[Page], int]:
        """Get all pages for an institute with pagination."""
        query = db.query(Page).filter(Page.institute_id == institute_id)
        
        if is_approved is not None:
            query = query.filter(Page.is_approved == is_approved)
        
        total = query.count()
        pages = query.order_by(Page.sequence.asc(), Page.created_at.desc()).offset(skip).limit(limit).all()
        
        # Eager load translations if locale specified
        if locale:
            for page in pages:
                translation = db.query(PageTranslation).filter(
                    and_(
                        PageTranslation.page_id == page.id,
                        PageTranslation.locale == locale
                    )
                ).first()
                if not translation:
                    # Fallback to first available translation
                    fallback = db.query(PageTranslation).filter(
                        PageTranslation.page_id == page.id
                    ).first()
        
        return pages, total
    
    @staticmethod
    def get_page(
        db: Session,
        page_id: int,
        institute_id: int
    ) -> Page:
        """Get a specific page by ID."""
        page = db.query(Page).filter(
            and_(
                Page.id == page_id,
                Page.institute_id == institute_id
            )
        ).first()
        
        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
            )
        
        return page
    
    @staticmethod
    def get_page_by_slug(
        db: Session,
        slug: str,
        institute_id: int,
        locale: Optional[str] = None
    ) -> Optional[Page]:
        """Get a page by slug."""
        page = db.query(Page).filter(
            and_(
                Page.slug == slug,
                Page.institute_id == institute_id,
                Page.is_approved == True
            )
        ).first()
        
        return page
    
    @staticmethod
    def create_page(
        db: Session,
        institute_id: int,
        page_data: PageCreate,
        created_by: int
    ) -> Page:
        """Create a new page with translations."""
        # Check if slug already exists for this institute
        existing = db.query(Page).filter(
            and_(
                Page.slug == page_data.slug,
                Page.institute_id == institute_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Page with slug '{page_data.slug}' already exists"
            )
        
        # Enforce canonical slugs for prebuilt page types
        if page_data.page_type != PageType.CUSTOM:
            canonical_slugs = {
                PageType.HOME: "home",
                PageType.ABOUT: "about",
                PageType.CONTACT: "contact",
                PageType.CAREERS: "careers"
            }
            if page_data.slug != canonical_slugs.get(page_data.page_type):
                page_data.slug = canonical_slugs.get(page_data.page_type, page_data.slug)
        
        # Create page
        page_dict = page_data.model_dump(exclude={'translations'})
        page_dict['institute_id'] = institute_id
        page_dict['created_by'] = created_by
        page = Page(**page_dict)
        db.add(page)
        db.flush()  # Get page ID
        
        # Create translations
        for translation_data in page_data.translations:
            translation = PageTranslation(
                page_id=page.id,
                **translation_data.model_dump()
            )
            db.add(translation)
        
        db.commit()
        db.refresh(page)
        return page
    
    @staticmethod
    def update_page(
        db: Session,
        page_id: int,
        institute_id: int,
        page_data: PageUpdate
    ) -> Page:
        """Update an existing page."""
        page = PageService.get_page(db, page_id, institute_id)
        
        # Check slug uniqueness if slug is being updated
        if page_data.slug and page_data.slug != page.slug:
            existing = db.query(Page).filter(
                and_(
                    Page.slug == page_data.slug,
                    Page.institute_id == institute_id,
                    Page.id != page_id
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Page with slug '{page_data.slug}' already exists"
                )
        
        # Update page fields
        update_data = page_data.model_dump(exclude_unset=True, exclude={'translations'})
        for field, value in update_data.items():
            setattr(page, field, value)
        
        # Update translations if provided
        if page_data.translations:
            # Delete existing translations
            db.query(PageTranslation).filter(PageTranslation.page_id == page_id).delete()
            
            # Create new translations
            for translation_data in page_data.translations:
                translation = PageTranslation(
                    page_id=page.id,
                    **translation_data.model_dump()
                )
                db.add(translation)
        
        db.commit()
        db.refresh(page)
        return page
    
    @staticmethod
    def delete_page(
        db: Session,
        page_id: int,
        institute_id: int
    ) -> bool:
        """Delete a page and its translations."""
        page = PageService.get_page(db, page_id, institute_id)
        
        # Check if page has children
        children = db.query(Page).filter(Page.page_id == page_id).count()
        if children > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete page with child pages. Please delete or reassign children first."
            )
        
        # Delete translations (cascade should handle this, but explicit is better)
        db.query(PageTranslation).filter(PageTranslation.page_id == page_id).delete()
        
        # Delete page
        db.delete(page)
        db.commit()
        return True
    
    @staticmethod
    def update_page_sequence(
        db: Session,
        institute_id: int,
        page_sequences: List[dict]
    ) -> List[Page]:
        """Update the sequence order of multiple pages."""
        updated_pages = []
        
        for seq_data in page_sequences:
            page_id = seq_data.get('id')
            sequence = seq_data.get('sequence', 0)
            
            if not page_id:
                continue
            
            page = db.query(Page).filter(
                and_(
                    Page.id == page_id,
                    Page.institute_id == institute_id
                )
            ).first()
            
            if page:
                page.sequence = sequence
                updated_pages.append(page)
        
        db.commit()
        
        # Refresh all updated pages
        for page in updated_pages:
            db.refresh(page)
        
        return updated_pages
