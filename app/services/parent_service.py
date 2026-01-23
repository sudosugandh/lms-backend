from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from typing import List, Optional
from app.db.models.parent import ParentStudentLink
from app.db.models.user import User, UserRole
from app.db.models.class_model import Class
from app.db.models.enrollment import Enrollment
from app.schemas.parent import ParentStudentLinkCreate


class ParentService:
    @staticmethod
    def create_parent_student_link(
        db: Session,
        institute_id: int,
        parent_id: int,
        link_data: ParentStudentLinkCreate
    ) -> ParentStudentLink:
        """Create a link between parent and student."""
        # Verify parent exists and is a parent
        parent = db.query(User).filter(
            and_(
                User.id == parent_id,
                User.institute_id == institute_id,
                User.role == UserRole.PARENT,
                User.is_active == True
            )
        ).first()
        
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent not found or inactive"
            )
        
        # Verify student exists and belongs to institute
        student = db.query(User).filter(
            and_(
                User.id == link_data.student_id,
                User.institute_id == institute_id,
                User.role == UserRole.STUDENT,
                User.is_active == True
            )
        ).first()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found or inactive"
            )
        
        # Check if link already exists
        existing = db.query(ParentStudentLink).filter(
            and_(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.student_id == link_data.student_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Link already exists between parent and student"
            )
        
        link = ParentStudentLink(
            parent_id=parent_id,
            student_id=link_data.student_id,
            relationship_type=link_data.relationship_type,
            is_active=link_data.is_active
        )
        
        db.add(link)
        db.commit()
        db.refresh(link)
        return link
    
    @staticmethod
    def get_parent_students(
        db: Session,
        parent_id: int,
        institute_id: int
    ) -> List[User]:
        """Get all students linked to a parent."""
        # Verify parent exists and belongs to institute
        parent = db.query(User).filter(
            and_(
                User.id == parent_id,
                User.institute_id == institute_id,
                User.role == UserRole.PARENT
            )
        ).first()
        
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent not found"
            )
        
        # Get linked students
        links = db.query(ParentStudentLink).filter(
            and_(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.is_active == True
            )
        ).all()
        
        student_ids = [link.student_id for link in links]
        
        if not student_ids:
            return []
        
        students = db.query(User).filter(
            and_(
                User.id.in_(student_ids),
                User.institute_id == institute_id,
                User.role == UserRole.STUDENT,
                User.is_active == True
            )
        ).all()
        
        return students
    
    @staticmethod
    def verify_parent_student_link(
        db: Session,
        parent_id: int,
        student_id: int,
        institute_id: int
    ) -> bool:
        """Verify that a parent is linked to a specific student."""
        link = db.query(ParentStudentLink).filter(
            and_(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.student_id == student_id,
                ParentStudentLink.is_active == True
            )
        ).first()
        
        if not link:
            return False
        
        # Verify both users belong to institute
        parent = db.query(User).filter(
            and_(
                User.id == parent_id,
                User.institute_id == institute_id
            )
        ).first()
        
        student = db.query(User).filter(
            and_(
                User.id == student_id,
                User.institute_id == institute_id
            )
        ).first()
        
        return parent is not None and student is not None
    
    @staticmethod
    def get_all_parent_links(
        db: Session,
        institute_id: int,
        parent_id: Optional[int] = None,
        student_id: Optional[int] = None
    ) -> List[ParentStudentLink]:
        """Get all parent-student links (admin only)."""
        query = db.query(ParentStudentLink).join(User, ParentStudentLink.parent_id == User.id).filter(
            User.institute_id == institute_id
        )
        
        if parent_id:
            query = query.filter(ParentStudentLink.parent_id == parent_id)
        
        if student_id:
            query = query.filter(ParentStudentLink.student_id == student_id)
        
        return query.all()
