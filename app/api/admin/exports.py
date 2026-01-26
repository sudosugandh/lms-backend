from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.db.models.user import User
from app.utils.dependencies import get_institute_admin
from app.utils.csv_export import CSVExportService
from app.services.assignment_service import AssignmentSubmissionService
from app.services.leave_service import LeaveRequestService
from app.services.result_service import ResultService
from app.services.attendance_service import AttendanceService
from datetime import datetime

router = APIRouter(prefix="/exports", tags=["admin-exports"])


@router.get("/students")
async def export_students(
    request: Request,
    class_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Export student data to CSV (Admin only)."""
    institute_id = request.state.institute_id
    
    # Get all students (no pagination for export)
    from app.db.models.user import User, UserRole
    from app.db.models.enrollment import Enrollment
    from app.db.models.class_model import Class
    
    query = db.query(User).filter(
        User.institute_id == institute_id,
        User.role == UserRole.STUDENT
    )
    
    if class_id:
        # Filter by class enrollment
        enrolled_students = db.query(Enrollment.student_id).filter(
            Enrollment.class_id == class_id
        ).subquery()
        query = query.filter(User.id.in_(db.query(enrolled_students.c.student_id)))
    
    students = query.order_by(User.created_at.desc()).all()
    
    # Format for CSV
    students_data = []
    for student in students:
        # Get enrollment info
        enrollment = db.query(Enrollment).filter(
            Enrollment.student_id == student.id
        ).order_by(Enrollment.enrolled_at.desc()).first()
        
        class_name = None
        if enrollment:
            class_obj = db.query(Class).filter(Class.id == enrollment.class_id).first()
            class_name = class_obj.name if class_obj else None
        
        students_data.append({
            'id': student.id,
            'name': student.name,
            'email': student.email,
            'class_name': class_name or 'N/A',
            'is_active': student.is_active,
            'created_at': student.created_at.isoformat() if hasattr(student.created_at, 'isoformat') else str(student.created_at)
        })
    
    csv_content = CSVExportService.export_students(students_data)
    
    # Generate filename
    filename = f"students_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/attendance")
async def export_attendance(
    request: Request,
    class_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Export attendance data to CSV (Admin only)."""
    institute_id = request.state.institute_id
    
    # Parse date strings
    from datetime import date
    start_date_obj = None
    end_date_obj = None
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            pass
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Get attendance data
    attendance_records = AttendanceService.get_institute_attendance(
        db, institute_id, class_id, start_date_obj, end_date_obj
    )
    
    # Format for CSV
    attendance_data = []
    for record in attendance_records:
        from app.db.models.user import User
        from app.db.models.class_model import Class
        from app.db.models.subject import Subject
        
        student = db.query(User).filter(User.id == record.student_id).first()
        class_obj = db.query(Class).filter(Class.id == record.class_id).first()
        subject = db.query(Subject).filter(Subject.id == record.subject_id).first() if record.subject_id else None
        
        attendance_data.append({
            'student_name': student.name if student else 'Unknown',
            'class_name': class_obj.name if class_obj else 'Unknown',
            'subject_name': subject.name if subject else 'N/A',
            'attendance_date': record.attendance_date.isoformat() if hasattr(record.attendance_date, 'isoformat') else str(record.attendance_date),
            'status': record.status,
            'remarks': record.remarks or '',
            'created_at': record.created_at.isoformat() if hasattr(record.created_at, 'isoformat') else str(record.created_at)
        })
    
    csv_content = CSVExportService.export_attendance(attendance_data)
    
    filename = f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/results")
async def export_results(
    request: Request,
    class_id: Optional[int] = Query(None),
    subject_id: Optional[int] = Query(None),
    result_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Export results/grades to CSV (Admin only)."""
    institute_id = request.state.institute_id
    
    # Get results
    results = ResultService.get_institute_results(
        db, institute_id, class_id, subject_id, result_type, None
    )
    
    # Format for CSV
    results_data = []
    for result in results:
        from app.db.models.user import User
        from app.db.models.class_model import Class
        from app.db.models.subject import Subject
        from app.db.models.quiz import Quiz
        from app.db.models.assignment import Assignment
        
        student = db.query(User).filter(User.id == result.student_id).first()
        class_obj = db.query(Class).filter(Class.id == result.class_id).first()
        subject = db.query(Subject).filter(Subject.id == result.subject_id).first()
        
        quiz_title = None
        if result.quiz_id:
            quiz = db.query(Quiz).filter(Quiz.id == result.quiz_id).first()
            quiz_title = quiz.title if quiz else None
        
        assignment_title = None
        if result.assignment_id:
            assignment = db.query(Assignment).filter(Assignment.id == result.assignment_id).first()
            assignment_title = assignment.title if assignment else None
        
        results_data.append({
            'student_name': student.name if student else 'Unknown',
            'class_name': class_obj.name if class_obj else 'Unknown',
            'subject_name': subject.name if subject else 'Unknown',
            'quiz_title': quiz_title or 'N/A',
            'assignment_title': assignment_title or 'N/A',
            'total_marks': result.total_marks,
            'marks_obtained': result.marks_obtained or 0,
            'percentage': result.percentage or 0,
            'status': result.status,
            'created_at': result.created_at.isoformat() if hasattr(result.created_at, 'isoformat') else str(result.created_at)
        })
    
    csv_content = CSVExportService.export_results(results_data)
    
    filename = f"results_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/leave-requests")
async def export_leave_requests(
    request: Request,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Export leave requests to CSV (Admin only)."""
    institute_id = request.state.institute_id
    
    # Get leave requests
    leave_requests = LeaveRequestService.get_institute_leave_requests(db, institute_id, status)
    
    # Format for CSV
    requests_data = []
    for lr in leave_requests:
        from app.db.models.user import User
        from app.db.models.leave import LeaveType
        
        user = db.query(User).filter(User.id == lr.user_id).first()
        leave_type = db.query(LeaveType).filter(LeaveType.id == lr.leave_type_id).first()
        approver = db.query(User).filter(User.id == lr.approved_by).first() if lr.approved_by else None
        
        requests_data.append({
            'user_name': user.name if user else 'Unknown',
            'leave_type_name': leave_type.name if leave_type else 'Unknown',
            'start_date': lr.start_date.isoformat() if hasattr(lr.start_date, 'isoformat') else str(lr.start_date),
            'end_date': lr.end_date.isoformat() if hasattr(lr.end_date, 'isoformat') else str(lr.end_date),
            'number_of_days': lr.number_of_days,
            'reason': lr.reason or '',
            'status': lr.status,
            'approver_name': approver.name if approver else 'N/A',
            'approved_at': lr.approved_at.isoformat() if lr.approved_at and hasattr(lr.approved_at, 'isoformat') else (str(lr.approved_at) if lr.approved_at else ''),
            'rejection_reason': lr.rejection_reason or '',
            'created_at': lr.created_at.isoformat() if hasattr(lr.created_at, 'isoformat') else str(lr.created_at)
        })
    
    csv_content = CSVExportService.export_leave_requests(requests_data)
    
    filename = f"leave_requests_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/fee-invoices")
async def export_fee_invoices(
    request: Request,
    status: Optional[str] = Query(None),
    student_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_institute_admin)
):
    """Export fee invoices to CSV (Admin only)."""
    institute_id = request.state.institute_id
    
    # Get fee invoices
    from app.services.fee_service import FeeInvoiceService
    invoices = FeeInvoiceService.get_institute_invoices(
        db, institute_id, status, student_id
    )
    
    # Format for CSV
    invoices_data = []
    for invoice in invoices:
        from app.db.models.user import User
        from app.db.models.fee import FeeStructure
        
        student = db.query(User).filter(User.id == invoice.student_id).first()
        fee_structure = db.query(FeeStructure).filter(FeeStructure.id == invoice.fee_structure_id).first()
        
        # Calculate paid amount
        from app.db.models.fee import FeePayment
        payments = db.query(FeePayment).filter(FeePayment.invoice_id == invoice.id).all()
        paid_amount = sum(p.amount for p in payments)
        
        invoices_data.append({
            'student_name': student.name if student else 'Unknown',
            'invoice_number': invoice.invoice_number,
            'fee_structure_name': fee_structure.name if fee_structure else 'Unknown',
            'total_amount': invoice.total_amount,
            'paid_amount': paid_amount,
            'due_amount': invoice.total_amount - paid_amount,
            'due_date': invoice.due_date.isoformat() if hasattr(invoice.due_date, 'isoformat') else str(invoice.due_date),
            'status': invoice.status,
            'created_at': invoice.created_at.isoformat() if hasattr(invoice.created_at, 'isoformat') else str(invoice.created_at)
        })
    
    csv_content = CSVExportService.export_fee_invoices(invoices_data)
    
    filename = f"fee_invoices_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
