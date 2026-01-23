from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from app.db.models.class_model import Class
from app.db.models.subject import Subject
from app.db.models.class_subject import ClassSubject
from app.db.models.enrollment import Enrollment
from app.db.models.user import User
from app.schemas.class_model import ClassCreate, ClassUpdate, SubjectCreate, SubjectUpdate, ClassSubjectCreate, EnrollmentCreate
from typing import List, Optional, Tuple


class ClassService:
    @staticmethod
    def create_class(db: Session, institute_id: int, class_data: ClassCreate) -> Class:
        """Create a new class for an institute."""
        # Check if class code already exists in this institute
        existing = db.query(Class).filter(
            and_(
                Class.institute_id == institute_id,
                Class.code == class_data.code
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class code already exists in this institute"
            )
        
        new_class = Class(
            institute_id=institute_id,
            name=class_data.name,
            code=class_data.code,
            description=class_data.description,
            is_active=class_data.is_active
        )
        
        db.add(new_class)
        db.commit()
        db.refresh(new_class)
        return new_class
    
    @staticmethod
    def get_classes(
        db: Session, 
        institute_id: int, 
        skip: int = 0, 
        limit: int = 50,
        is_active: Optional[bool] = None
    ) -> tuple[List[Class], int]:
        """
        Get all classes for an institute with pagination.
        
        Returns:
            Tuple of (classes list, total count)
        """
        query = db.query(Class).filter(Class.institute_id == institute_id)
        
        if is_active is not None:
            query = query.filter(Class.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        classes = query.order_by(Class.created_at.desc()).offset(skip).limit(limit).all()
        
        return classes, total
    
    @staticmethod
    def get_class(db: Session, class_id: int, institute_id: int) -> Class:
        """Get a specific class by ID, ensuring it belongs to the institute."""
        class_obj = db.query(Class).filter(
            and_(
                Class.id == class_id,
                Class.institute_id == institute_id
            )
        ).first()
        
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
        
        return class_obj
    
    @staticmethod
    def update_class(db: Session, class_id: int, institute_id: int, class_data: ClassUpdate) -> Class:
        """Update a class."""
        class_obj = ClassService.get_class(db, class_id, institute_id)
        
        # Check if code is being changed and if it already exists
        if class_data.code and class_data.code != class_obj.code:
            existing = db.query(Class).filter(
                and_(
                    Class.institute_id == institute_id,
                    Class.code == class_data.code,
                    Class.id != class_id
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Class code already exists in this institute"
                )
        
        # Update fields
        if class_data.name is not None:
            class_obj.name = class_data.name
        if class_data.code is not None:
            class_obj.code = class_data.code
        if class_data.description is not None:
            class_obj.description = class_data.description
        if class_data.is_active is not None:
            class_obj.is_active = class_data.is_active
        
        db.commit()
        db.refresh(class_obj)
        return class_obj


class SubjectService:
    @staticmethod
    def create_subject(db: Session, institute_id: int, subject_data: SubjectCreate) -> Subject:
        """Create a new subject for an institute."""
        # Check if subject code already exists in this institute
        existing = db.query(Subject).filter(
            and_(
                Subject.institute_id == institute_id,
                Subject.code == subject_data.code
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject code already exists in this institute"
            )
        
        new_subject = Subject(
            institute_id=institute_id,
            name=subject_data.name,
            code=subject_data.code,
            description=subject_data.description,
            is_active=subject_data.is_active
        )
        
        db.add(new_subject)
        db.commit()
        db.refresh(new_subject)
        return new_subject
    
    @staticmethod
    def get_subjects(
        db: Session, 
        institute_id: int, 
        skip: int = 0, 
        limit: int = 50,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Subject], int]:
        """
        Get all subjects for an institute with pagination.
        
        Returns:
            Tuple of (subjects list, total count)
        """
        query = db.query(Subject).filter(Subject.institute_id == institute_id)
        
        if is_active is not None:
            query = query.filter(Subject.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        subjects = query.order_by(Subject.created_at.desc()).offset(skip).limit(limit).all()
        
        return subjects, total
    
    @staticmethod
    def get_subject(db: Session, subject_id: int, institute_id: int) -> Subject:
        """Get a specific subject by ID, ensuring it belongs to the institute."""
        subject = db.query(Subject).filter(
            and_(
                Subject.id == subject_id,
                Subject.institute_id == institute_id
            )
        ).first()
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        return subject
    
    @staticmethod
    def update_subject(db: Session, subject_id: int, institute_id: int, subject_data: SubjectUpdate) -> Subject:
        """Update a subject."""
        subject = SubjectService.get_subject(db, subject_id, institute_id)
        
        # Check if code is being changed and if it already exists
        if subject_data.code and subject_data.code != subject.code:
            existing = db.query(Subject).filter(
                and_(
                    Subject.institute_id == institute_id,
                    Subject.code == subject_data.code,
                    Subject.id != subject_id
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subject code already exists in this institute"
                )
        
        # Update fields
        if subject_data.name is not None:
            subject.name = subject_data.name
        if subject_data.code is not None:
            subject.code = subject_data.code
        if subject_data.description is not None:
            subject.description = subject_data.description
        if subject_data.is_active is not None:
            subject.is_active = subject_data.is_active
        
        db.commit()
        db.refresh(subject)
        return subject


class ClassSubjectService:
    @staticmethod
    def assign_subject_to_class(
        db: Session,
        institute_id: int,
        assignment_data: ClassSubjectCreate
    ) -> ClassSubject:
        """Assign a subject to a class, optionally with a teacher."""
        # Verify class belongs to institute
        class_obj = db.query(Class).filter(
            and_(
                Class.id == assignment_data.class_id,
                Class.institute_id == institute_id
            )
        ).first()
        
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
        
        # Verify subject belongs to institute
        subject = db.query(Subject).filter(
            and_(
                Subject.id == assignment_data.subject_id,
                Subject.institute_id == institute_id
            )
        ).first()
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        # If teacher is assigned, verify teacher belongs to institute and is a TEACHER
        if assignment_data.teacher_id:
            teacher = db.query(User).filter(
                and_(
                    User.id == assignment_data.teacher_id,
                    User.institute_id == institute_id,
                    User.role == "TEACHER",
                    User.is_active == True
                )
            ).first()
            
            if not teacher:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Teacher not found or inactive"
                )
        
        # Check if assignment already exists
        existing = db.query(ClassSubject).filter(
            and_(
                ClassSubject.class_id == assignment_data.class_id,
                ClassSubject.subject_id == assignment_data.subject_id
            )
        ).first()
        
        if existing:
            # Update teacher assignment if provided
            if assignment_data.teacher_id:
                existing.teacher_id = assignment_data.teacher_id
                db.commit()
                db.refresh(existing)
            return existing
        
        # Create new assignment
        new_assignment = ClassSubject(
            class_id=assignment_data.class_id,
            subject_id=assignment_data.subject_id,
            teacher_id=assignment_data.teacher_id
        )
        
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)
        return new_assignment
    
    @staticmethod
    def get_class_subjects(db: Session, class_id: int, institute_id: int) -> List[ClassSubject]:
        """Get all subjects assigned to a class."""
        # Verify class belongs to institute
        ClassService.get_class(db, class_id, institute_id)
        
        return db.query(ClassSubject).filter(
            ClassSubject.class_id == class_id
        ).all()
    
    @staticmethod
    def get_teacher_assignments(
        db: Session,
        teacher_id: int,
        institute_id: int
    ) -> List[ClassSubject]:
        """Get all class-subject assignments for a teacher."""
        # Verify teacher belongs to institute
        teacher = db.query(User).filter(
            and_(
                User.id == teacher_id,
                User.institute_id == institute_id,
                User.role == "TEACHER"
            )
        ).first()
        
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        return db.query(ClassSubject).filter(
            ClassSubject.teacher_id == teacher_id
        ).all()


class EnrollmentService:
    @staticmethod
    def enroll_student(
        db: Session,
        institute_id: int,
        enrollment_data: EnrollmentCreate
    ) -> Enrollment:
        """Enroll a student in a class."""
        # Verify class belongs to institute
        class_obj = ClassService.get_class(db, enrollment_data.class_id, institute_id)
        
        # Verify student belongs to institute and is a STUDENT
        student = db.query(User).filter(
            and_(
                User.id == enrollment_data.student_id,
                User.institute_id == institute_id,
                User.role == "STUDENT",
                User.is_active == True
            )
        ).first()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found or inactive"
            )
        
        # Check if already enrolled
        existing = db.query(Enrollment).filter(
            and_(
                Enrollment.student_id == enrollment_data.student_id,
                Enrollment.class_id == enrollment_data.class_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student is already enrolled in this class"
            )
        
        new_enrollment = Enrollment(
            student_id=enrollment_data.student_id,
            class_id=enrollment_data.class_id
        )
        
        db.add(new_enrollment)
        db.commit()
        db.refresh(new_enrollment)
        return new_enrollment
    
    @staticmethod
    def get_student_enrollments(
        db: Session,
        student_id: int,
        institute_id: int
    ) -> List[Enrollment]:
        """Get all classes a student is enrolled in."""
        # Verify student belongs to institute
        student = db.query(User).filter(
            and_(
                User.id == student_id,
                User.institute_id == institute_id,
                User.role == "STUDENT"
            )
        ).first()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        return db.query(Enrollment).filter(
            Enrollment.student_id == student_id
        ).all()
