from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.leave import LeaveRequestCreate, LeaveRequestResponse
from app.services.leave_service import LeaveTypeService, LeaveRequestService
from app.utils.dependencies import get_student

router = APIRouter(prefix="/leave", tags=["student-leave"])


@router.get("/types", response_model=List[dict])
async def get_leave_types(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Get available leave types (Student only)."""
    institute_id = request.state.institute_id
    leave_types = LeaveTypeService.get_leave_types(db, institute_id)
    
    return [{"id": lt.id, "name": lt.name, "code": lt.code, "description": lt.description} for lt in leave_types]


@router.post("/requests", response_model=LeaveRequestResponse, status_code=201)
async def create_leave_request(
    leave_request_data: LeaveRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_student)
):
    """Create a leave request (Student only)."""
    institute_id = request.state.institute_id
    leave_request = LeaveRequestService.create_leave_request(
        db, institute_id, current_user.id, leave_request_data
    )
    
    # Format response
    user = db.query(User).filter(User.id == leave_request.user_id).first()
    from app.db.models.leave import LeaveType
    leave_type = db.query(LeaveType).filter(LeaveType.id == leave_request.leave_type_id).first()
    
    return LeaveRequestResponse(
        **leave_request.__dict__,
        user_name=user.name if user else None,
        leave_type_name=leave_type.name if leave_type else None,
        approver_name=None
    )


@router.get("/requests", response_model=List[LeaveRequestResponse])
async def list_leave_requests(
    request: Request,
    db: Session = Depends(get_db),
    status: str = None,
    current_user: User = Depends(get_student)
):
    """List own leave requests (Student only)."""
    institute_id = request.state.institute_id
    leave_requests = LeaveRequestService.get_user_leave_requests(
        db, current_user.id, institute_id, status
    )
    
    # Format responses
    results = []
    for lr in leave_requests:
        user = db.query(User).filter(User.id == lr.user_id).first()
        from app.db.models.leave import LeaveType
        leave_type = db.query(LeaveType).filter(LeaveType.id == lr.leave_type_id).first()
        
        approver_name = None
        if lr.approved_by:
            approver = db.query(User).filter(User.id == lr.approved_by).first()
            approver_name = approver.name if approver else None
        
        results.append(LeaveRequestResponse(
            **lr.__dict__,
            user_name=user.name if user else None,
            leave_type_name=leave_type.name if leave_type else None,
            approver_name=approver_name
        ))
    
    return results
