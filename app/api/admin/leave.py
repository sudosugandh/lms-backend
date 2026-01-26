from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.leave import (
    LeaveTypeCreate, LeaveTypeUpdate, LeaveTypeResponse, LeaveRequestResponse, LeaveRequestUpdate
)
from app.services.leave_service import LeaveTypeService, LeaveRequestService
from app.utils.dependencies import get_institute_admin
from app.utils.audit import log_audit_event, AuditAction

router = APIRouter(prefix="/leave", tags=["admin-leave"])


@router.post("/types", response_model=LeaveTypeResponse, status_code=201)
async def create_leave_type(
    leave_type_data: LeaveTypeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Create a leave type (Admin only)."""
    institute_id = request.state.institute_id
    return LeaveTypeService.create_leave_type(db, institute_id, leave_type_data)


@router.get("/types", response_model=List[LeaveTypeResponse])
async def list_leave_types(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """List all leave types (Admin only)."""
    institute_id = request.state.institute_id
    return LeaveTypeService.get_all_leave_types(db, institute_id)


@router.get("/types/{leave_type_id}", response_model=LeaveTypeResponse)
async def get_leave_type(
    leave_type_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Get a specific leave type (Admin only)."""
    institute_id = request.state.institute_id
    return LeaveTypeService.get_leave_type(db, leave_type_id, institute_id)


@router.put("/types/{leave_type_id}", response_model=LeaveTypeResponse)
async def update_leave_type(
    leave_type_id: int,
    leave_type_data: LeaveTypeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Update a leave type (Admin only)."""
    institute_id = request.state.institute_id
    leave_type = LeaveTypeService.update_leave_type(
        db, leave_type_id, institute_id, leave_type_data
    )
    
    # Log audit event
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action=AuditAction.LEAVE_TYPE_UPDATED,
        request=request,
        details=f"Updated leave type #{leave_type_id}: {leave_type.name}"
    )
    
    return leave_type


@router.delete("/types/{leave_type_id}")
async def delete_leave_type(
    leave_type_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Delete a leave type (Admin only)."""
    institute_id = request.state.institute_id
    leave_type = LeaveTypeService.get_leave_type(db, leave_type_id, institute_id)
    was_hard_deleted = LeaveTypeService.delete_leave_type(db, leave_type_id, institute_id)
    
    # Log audit event
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action=AuditAction.LEAVE_TYPE_DELETED,
        request=request,
        details=f"{'Deleted' if was_hard_deleted else 'Deactivated'} leave type #{leave_type_id}: {leave_type.name}"
    )
    
    return {
        "message": "Leave type deleted successfully" if was_hard_deleted else "Leave type deactivated (has existing requests)",
        "hard_deleted": was_hard_deleted
    }


@router.get("/requests", response_model=List[LeaveRequestResponse])
async def list_leave_requests(
    request: Request,
    db: Session = Depends(get_db),
    status: str = None,
    current_user: User = Depends(get_institute_admin)
):
    """List all leave requests in institute (Admin only)."""
    institute_id = request.state.institute_id
    leave_requests = LeaveRequestService.get_institute_leave_requests(
        db, institute_id, status
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
            id=lr.id,
            institute_id=lr.institute_id,
            user_id=lr.user_id,
            leave_type_id=lr.leave_type_id,
            start_date=lr.start_date,
            end_date=lr.end_date,
            reason=lr.reason,
            number_of_days=lr.number_of_days,
            status=lr.status,
            approved_by=lr.approved_by,
            approved_at=lr.approved_at,
            rejection_reason=lr.rejection_reason,
            created_at=lr.created_at,
            updated_at=lr.updated_at,
            user_name=user.name if user else None,
            leave_type_name=leave_type.name if leave_type else None,
            approver_name=approver_name
        ))
    
    return results


@router.put("/requests/{leave_request_id}/approve", response_model=LeaveRequestResponse)
async def approve_leave_request(
    leave_request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Approve a leave request (Admin only)."""
    institute_id = request.state.institute_id
    leave_request = LeaveRequestService.approve_leave_request(
        db, leave_request_id, institute_id, current_user.id
    )
    
    # Format response
    user = db.query(User).filter(User.id == leave_request.user_id).first()
    from app.db.models.leave import LeaveType
    leave_type = db.query(LeaveType).filter(LeaveType.id == leave_request.leave_type_id).first()
    
    # Log audit event
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action=AuditAction.LEAVE_REQUEST_APPROVED,
        request=request,
        details=f"Approved leave request #{leave_request_id} for user {user.name if user else leave_request.user_id}"
    )
    
    return LeaveRequestResponse(
        id=leave_request.id,
        institute_id=leave_request.institute_id,
        user_id=leave_request.user_id,
        leave_type_id=leave_request.leave_type_id,
        start_date=leave_request.start_date,
        end_date=leave_request.end_date,
        reason=leave_request.reason,
        number_of_days=leave_request.number_of_days,
        status=leave_request.status,
        approved_by=leave_request.approved_by,
        approved_at=leave_request.approved_at,
        rejection_reason=leave_request.rejection_reason,
        created_at=leave_request.created_at,
        updated_at=leave_request.updated_at,
        user_name=user.name if user else None,
        leave_type_name=leave_type.name if leave_type else None,
        approver_name=current_user.name
    )


@router.put("/requests/{leave_request_id}/reject", response_model=LeaveRequestResponse)
async def reject_leave_request(
    leave_request_id: int,
    update_data: LeaveRequestUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Reject a leave request (Admin only)."""
    institute_id = request.state.institute_id
    
    if update_data.status != "REJECTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be REJECTED"
        )
    
    leave_request = LeaveRequestService.reject_leave_request(
        db, leave_request_id, institute_id, current_user.id, update_data.rejection_reason or ""
    )
    
    # Format response
    user = db.query(User).filter(User.id == leave_request.user_id).first()
    from app.db.models.leave import LeaveType
    leave_type = db.query(LeaveType).filter(LeaveType.id == leave_request.leave_type_id).first()
    
    # Log audit event
    log_audit_event(
        db=db,
        user_id=current_user.id,
        action=AuditAction.LEAVE_REQUEST_REJECTED,
        request=request,
        details=f"Rejected leave request #{leave_request_id} for user {user.name if user else leave_request.user_id}"
    )
    
    return LeaveRequestResponse(
        id=leave_request.id,
        institute_id=leave_request.institute_id,
        user_id=leave_request.user_id,
        leave_type_id=leave_request.leave_type_id,
        start_date=leave_request.start_date,
        end_date=leave_request.end_date,
        reason=leave_request.reason,
        number_of_days=leave_request.number_of_days,
        status=leave_request.status,
        approved_by=leave_request.approved_by,
        approved_at=leave_request.approved_at,
        rejection_reason=leave_request.rejection_reason,
        created_at=leave_request.created_at,
        updated_at=leave_request.updated_at,
        user_name=user.name if user else None,
        leave_type_name=leave_type.name if leave_type else None,
        approver_name=current_user.name
    )
