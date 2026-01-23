from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.page import (
    PageCreate, PageUpdate, PageResponse, PageSequenceUpdate
)
from app.services.page_service import PageService
from app.utils.dependencies import get_institute_admin
from app.utils.permissions import require_permission
from app.utils.pagination import PaginatedResponse, create_paginated_response
from app.db.models.page import PageTranslation

router = APIRouter(prefix="/pages", tags=["admin-pages"])


@router.post("", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    page_data: PageCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cms", "create"))
):
    """Create a new page (Admin only)."""
    institute_id = request.state.institute_id
    page = PageService.create_page(db, institute_id, page_data, current_user.id)
    
    # Load relationships for response
    page = PageService.get_page(db, page.id, institute_id)
    
    # Format response with translations
    translations = db.query(PageTranslation).filter(PageTranslation.page_id == page.id).all()
    page_dict = {
        **page.__dict__,
        "translations": [{"id": t.id, "page_id": t.page_id, "locale": t.locale, 
                         "name": t.name, "description": t.description, 
                         "embedded_code": t.embedded_code, "created_at": t.created_at,
                         "updated_at": t.updated_at} for t in translations],
        "creator_name": current_user.name if current_user else None
    }
    
    return PageResponse.model_validate(page_dict)


@router.get("", response_model=PaginatedResponse[PageResponse])
async def list_pages(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cms", "view")),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    locale: Optional[str] = Query(None),
    is_approved: Optional[bool] = Query(None)
):
    """List all pages for the institute with pagination (Admin only)."""
    institute_id = request.state.institute_id
    pages, total = PageService.get_pages(db, institute_id, skip, limit, locale, is_approved)
    
    # Format responses
    page_responses = []
    for page in pages:
        translations = db.query(PageTranslation).filter(PageTranslation.page_id == page.id).all()
        creator = db.query(User).filter(User.id == page.created_by).first() if page.created_by else None
        
        page_dict = {
            **page.__dict__,
            "translations": [{"id": t.id, "page_id": t.page_id, "locale": t.locale,
                             "name": t.name, "description": t.description,
                             "embedded_code": t.embedded_code, "created_at": t.created_at,
                             "updated_at": t.updated_at} for t in translations],
            "parent": None,  # Can be loaded if needed
            "children": [],  # Can be loaded if needed
            "creator_name": creator.name if creator else None
        }
        page_responses.append(PageResponse.model_validate(page_dict))
    
    return create_paginated_response(
        items=page_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cms", "view"))
):
    """Get a specific page (Admin only)."""
    institute_id = request.state.institute_id
    page = PageService.get_page(db, page_id, institute_id)
    
    # Load translations
    translations = db.query(PageTranslation).filter(PageTranslation.page_id == page.id).all()
    creator = db.query(User).filter(User.id == page.created_by).first() if page.created_by else None
    
    # Load parent and children if needed
    parent = None
    if page.page_id:
        parent_page = db.query(Page).filter(Page.id == page.page_id).first()
        if parent_page:
            parent_translations = db.query(PageTranslation).filter(PageTranslation.page_id == parent_page.id).all()
            parent = {
                **parent_page.__dict__,
                "translations": [{"id": t.id, "page_id": t.page_id, "locale": t.locale,
                                 "name": t.name, "description": t.description,
                                 "embedded_code": t.embedded_code, "created_at": t.created_at,
                                 "updated_at": t.updated_at} for t in parent_translations]
            }
    
    children = []
    child_pages = db.query(Page).filter(Page.page_id == page.id).all()
    for child_page in child_pages:
        child_translations = db.query(PageTranslation).filter(PageTranslation.page_id == child_page.id).all()
        children.append({
            **child_page.__dict__,
            "translations": [{"id": t.id, "page_id": t.page_id, "locale": t.locale,
                             "name": t.name, "description": t.description,
                             "embedded_code": t.embedded_code, "created_at": t.created_at,
                             "updated_at": t.updated_at} for t in child_translations]
        })
    
    page_dict = {
        **page.__dict__,
        "translations": [{"id": t.id, "page_id": t.page_id, "locale": t.locale,
                         "name": t.name, "description": t.description,
                         "embedded_code": t.embedded_code, "created_at": t.created_at,
                         "updated_at": t.updated_at} for t in translations],
        "parent": parent,
        "children": children,
        "creator_name": creator.name if creator else None
    }
    
    return PageResponse.model_validate(page_dict)


@router.put("/{page_id}", response_model=PageResponse)
async def update_page(
    page_id: int,
    page_data: PageUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cms", "edit"))
):
    """Update a page (Admin only)."""
    institute_id = request.state.institute_id
    page = PageService.update_page(db, page_id, institute_id, page_data)
    
    # Reload with relationships
    return await get_page(page_id, request, db, current_user)


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cms", "delete"))
):
    """Delete a page (Admin only)."""
    institute_id = request.state.institute_id
    PageService.delete_page(db, page_id, institute_id)
    return None


@router.post("/sequence", response_model=List[PageResponse])
async def update_page_sequence(
    sequence_data: PageSequenceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cms", "edit"))
):
    """Update the sequence order of pages (Admin only)."""
    institute_id = request.state.institute_id
    updated_pages = PageService.update_page_sequence(
        db, institute_id, sequence_data.page_sequences
    )
    
    # Format responses
    page_responses = []
    for page in updated_pages:
        translations = db.query(PageTranslation).filter(PageTranslation.page_id == page.id).all()
        page_dict = {
            **page.__dict__,
            "translations": [{"id": t.id, "page_id": t.page_id, "locale": t.locale,
                             "name": t.name, "description": t.description,
                             "embedded_code": t.embedded_code, "created_at": t.created_at,
                             "updated_at": t.updated_at} for t in translations]
        }
        page_responses.append(PageResponse.model_validate(page_dict))
    
    return page_responses
