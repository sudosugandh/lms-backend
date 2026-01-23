from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.parent import ParentStudentLinkCreate, ParentStudentLinkResponse
from app.services.parent_service import ParentService
from app.utils.dependencies import get_institute_admin

router = APIRouter(prefix="/parents", tags=["admin-parents"])


@router.post("/{parent_id}/students", response_model=ParentStudentLinkResponse, status_code=201)
async def link_parent_student(
    parent_id: int,
    link_data: ParentStudentLinkCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Link a parent to a student (Admin only)."""
    institute_id = request.state.institute_id
    link = ParentService.create_parent_student_link(
        db, institute_id, parent_id, link_data
    )
    
    # Format response
    student = db.query(User).filter(User.id == link.student_id).first()
    
    return ParentStudentLinkResponse(
        **link.__dict__,
        student_name=student.name if student else None
    )


@router.get("/links", response_model=List[ParentStudentLinkResponse])
async def list_parent_links(
    request: Request,
    db: Session = Depends(get_db),
    parent_id: int = None,
    student_id: int = None,
    current_user: User = Depends(get_institute_admin)
):
    """List all parent-student links (Admin only)."""
    institute_id = request.state.institute_id
    links = ParentService.get_all_parent_links(db, institute_id, parent_id, student_id)
    
    # Format response
    results = []
    for link in links:
        student = db.query(User).filter(User.id == link.student_id).first()
        results.append(ParentStudentLinkResponse(
            **link.__dict__,
            student_name=student.name if student else None
        ))
    
    return results
