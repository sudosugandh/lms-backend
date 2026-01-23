from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from datetime import date, datetime, timedelta
from typing import List, Optional
from app.db.models.leave import LeaveType, LeaveRequest, LeaveStatus
from app.db.models.user import User, UserRole
from app.db.models.class_model import Class
from app.db.models.attendance import Attendance
from app.schemas.leave import LeaveTypeCreate, LeaveRequestCreate
from app.services.class_service import ClassService


class LeaveTypeService:
    @staticmethod
    def create_leave_type(
        db: Session,
        institute_id: int,
        leave_type_data: LeaveTypeCreate
    ) -> LeaveType:
        """Create a new leave type for an institute."""
        # Check if code already exists
        existing = db.query(LeaveType).filter(
            and_(
                LeaveType.institute_id == institute_id,
                LeaveType.code == leave_type_data.code
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave type code already exists"
            )
        
        leave_type = LeaveType(
            institute_id=institute_id,
            name=leave_type_data.name,
            code=leave_type_data.code,
            description=leave_type_data.description,
            max_days_per_year=leave_type_data.max_days_per_year,
            requires_approval=leave_type_data.requires_approval,
            is_active=leave_type_data.is_active
        )
        
        db.add(leave_type)
        db.commit()
        db.refresh(leave_type)
        return leave_type
    
    @staticmethod
    def get_leave_types(
        db: Session,
        institute_id: int
    ) -> List[LeaveType]:
        """Get all leave types for an institute."""
        return db.query(LeaveType).filter(
            and_(
                LeaveType.institute_id == institute_id,
                LeaveType.is_active == True
            )
        ).all()


class LeaveRequestService:
    @staticmethod
    def calculate_days(start_date: date, end_date: date) -> int:
        """Calculate number of days between dates (inclusive)."""
        if end_date < start_date:
            return 0
        return (end_date - start_date).days + 1
    
    @staticmethod
    def create_leave_request(
        db: Session,
        institute_id: int,
        user_id: int,
        leave_request_data: LeaveRequestCreate
    ) -> LeaveRequest:
        """Create a new leave request."""
        # Verify user belongs to institute
        user = db.query(User).filter(
            and_(
                User.id == user_id,
                User.institute_id == institute_id,
                User.role.in_(["TEACHER", "STUDENT"]),
                User.is_active == True
            )
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or invalid role"
            )
        
        # Verify leave type exists and belongs to institute
        leave_type = db.query(LeaveType).filter(
            and_(
                LeaveType.id == leave_request_data.leave_type_id,
                LeaveType.institute_id == institute_id,
                LeaveType.is_active == True
            )
        ).first()
        
        if not leave_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave type not found"
            )
        
        # Validate dates
        if leave_request_data.end_date < leave_request_data.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        # Calculate number of days
        number_of_days = LeaveRequestService.calculate_days(
            leave_request_data.start_date,
            leave_request_data.end_date
        )
        
        # Check leave type limit
        if leave_type.max_days_per_year:
            # Count days used this year
            year_start = date(leave_request_data.start_date.year, 1, 1)
            year_end = date(leave_request_data.start_date.year, 12, 31)
            
            approved_leaves = db.query(LeaveRequest).filter(
                and_(
                    LeaveRequest.user_id == user_id,
                    LeaveRequest.leave_type_id == leave_type.id,
                    LeaveRequest.status == "APPROVED",
                    LeaveRequest.start_date >= year_start,
                    LeaveRequest.end_date <= year_end
                )
            ).all()
            
            total_used = sum(req.number_of_days for req in approved_leaves)
            
            if total_used + number_of_days > leave_type.max_days_per_year:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Leave limit exceeded. Available: {leave_type.max_days_per_year - total_used} days"
                )
        
        # Check for overlapping leave requests
        overlapping = db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.user_id == user_id,
                LeaveRequest.status.in_(["PENDING", "APPROVED"]),
                or_(
                    and_(
                        LeaveRequest.start_date <= leave_request_data.end_date,
                        LeaveRequest.end_date >= leave_request_data.start_date
                    )
                )
            )
        ).first()
        
        if overlapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Overlapping leave request exists"
            )
        
        # Create leave request
        leave_request = LeaveRequest(
            institute_id=institute_id,
            user_id=user_id,
            leave_type_id=leave_request_data.leave_type_id,
            start_date=leave_request_data.start_date,
            end_date=leave_request_data.end_date,
            number_of_days=number_of_days,
            reason=leave_request_data.reason,
            status="PENDING"
        )
        
        db.add(leave_request)
        db.commit()
        db.refresh(leave_request)
        
        # Create notification for admin
        from app.services.notification_service import NotificationService
        NotificationService.create_notification(
            db=db,
            institute_id=institute_id,
            title="New Leave Request",
            message=f"{user.name} has requested leave from {leave_request_data.start_date} to {leave_request_data.end_date}",
            notification_type="LEAVE_STATUS_UPDATE",
            target_role="ADMIN",
            notification_metadata={"leave_request_id": leave_request.id, "user_id": user_id}
        )
        
        return leave_request
    
    @staticmethod
    def get_user_leave_requests(
        db: Session,
        user_id: int,
        institute_id: int,
        status: Optional[str] = None
    ) -> List[LeaveRequest]:
        """Get all leave requests for a user."""
        # Verify user belongs to institute
        user = db.query(User).filter(
            and_(
                User.id == user_id,
                User.institute_id == institute_id
            )
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        query = db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.user_id == user_id,
                LeaveRequest.institute_id == institute_id
            )
        )
        
        if status:
            query = query.filter(LeaveRequest.status == status)
        
        return query.order_by(LeaveRequest.created_at.desc()).all()
    
    @staticmethod
    def get_institute_leave_requests(
        db: Session,
        institute_id: int,
        status: Optional[str] = None
    ) -> List[LeaveRequest]:
        """Get all leave requests for an institute (admin only)."""
        query = db.query(LeaveRequest).filter(
            LeaveRequest.institute_id == institute_id
        )
        
        if status:
            query = query.filter(LeaveRequest.status == status)
        
        return query.order_by(LeaveRequest.created_at.desc()).all()
    
    @staticmethod
    def approve_leave_request(
        db: Session,
        leave_request_id: int,
        institute_id: int,
        admin_id: int,
        rejection_reason: Optional[str] = None
    ) -> LeaveRequest:
        """Approve a leave request (admin only)."""
        leave_request = db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.id == leave_request_id,
                LeaveRequest.institute_id == institute_id
            )
        ).first()
        
        if not leave_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )
        
        if leave_request.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Leave request is already {leave_request.status}"
            )
        
        leave_request.status = "APPROVED"
        leave_request.approved_by = admin_id
        leave_request.approved_at = datetime.utcnow()
        leave_request.rejection_reason = None
        
        db.commit()
        db.refresh(leave_request)
        
        # Create notification for user
        from app.services.notification_service import NotificationService
        NotificationService.create_notification(
            db=db,
            institute_id=institute_id,
            title="Leave Request Approved",
            message=f"Your leave request from {leave_request.start_date} to {leave_request.end_date} has been approved",
            notification_type="LEAVE_STATUS_UPDATE",
            target_user_id=leave_request.user_id,
            notification_metadata={"leave_request_id": leave_request.id}
        )
        
        return leave_request
    
    @staticmethod
    def reject_leave_request(
        db: Session,
        leave_request_id: int,
        institute_id: int,
        admin_id: int,
        rejection_reason: str
    ) -> LeaveRequest:
        """Reject a leave request (admin only)."""
        leave_request = db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.id == leave_request_id,
                LeaveRequest.institute_id == institute_id
            )
        ).first()
        
        if not leave_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )
        
        if leave_request.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Leave request is already {leave_request.status}"
            )
        
        leave_request.status = "REJECTED"
        leave_request.approved_by = admin_id
        leave_request.approved_at = datetime.utcnow()
        leave_request.rejection_reason = rejection_reason
        
        db.commit()
        db.refresh(leave_request)
        
        # Create notification for user
        from app.services.notification_service import NotificationService
        NotificationService.create_notification(
            db=db,
            institute_id=institute_id,
            title="Leave Request Rejected",
            message=f"Your leave request from {leave_request.start_date} to {leave_request.end_date} has been rejected. Reason: {rejection_reason}",
            notification_type="LEAVE_STATUS_UPDATE",
            target_user_id=leave_request.user_id,
            notification_metadata={"leave_request_id": leave_request.id}
        )
        
        return leave_request
