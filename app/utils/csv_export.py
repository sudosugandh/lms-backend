"""
CSV Export Utility
Provides functions to convert data to CSV format
"""
from typing import List, Dict, Any, Optional
import csv
import io
from datetime import datetime


class CSVExportService:
    """Service for generating CSV exports from data."""
    
    @staticmethod
    def generate_csv(
        data: List[Dict[str, Any]],
        headers: Optional[List[str]] = None,
        field_mapping: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate CSV string from data.
        
        Args:
            data: List of dictionaries containing data
            headers: Optional list of header names (if None, uses dict keys)
            field_mapping: Optional mapping of field names to display names
        
        Returns:
            CSV string
        """
        if not data:
            return ""
        
        output = io.StringIO()
        
        # Determine headers
        if headers is None:
            if field_mapping:
                headers = list(field_mapping.keys())
            else:
                headers = list(data[0].keys()) if data else []
        
        # Map field names if provided
        display_headers = [field_mapping.get(h, h) for h in headers] if field_mapping else headers
        
        # Write header row with display names
        writer = csv.writer(output)
        writer.writerow(display_headers)
        
        # Write data rows
        for row in data:
            csv_row = []
            for header in headers:
                value = row.get(header, '')
                if value is None:
                    value = ''
                elif isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, (dict, list)):
                    value = str(value)
                else:
                    value = str(value)
                csv_row.append(value)
            writer.writerow(csv_row)
        
        return output.getvalue()
    
    @staticmethod
    def export_students(students: List[Dict[str, Any]]) -> str:
        """Export student data to CSV."""
        field_mapping = {
            'id': 'ID',
            'name': 'Name',
            'email': 'Email',
            'class_name': 'Class',
            'is_active': 'Status',
            'created_at': 'Enrolled Date'
        }
        
        # Prepare data
        csv_data = []
        for student in students:
            csv_data.append({
                'id': student.get('id', ''),
                'name': student.get('name', ''),
                'email': student.get('email', ''),
                'class_name': student.get('class_name', 'N/A'),
                'is_active': 'Active' if student.get('is_active', True) else 'Inactive',
                'created_at': student.get('created_at', '')
            })
        
        return CSVExportService.generate_csv(csv_data, field_mapping=field_mapping)
    
    @staticmethod
    def export_attendance(attendance_records: List[Dict[str, Any]]) -> str:
        """Export attendance data to CSV."""
        field_mapping = {
            'student_name': 'Student Name',
            'class_name': 'Class',
            'subject_name': 'Subject',
            'attendance_date': 'Date',
            'status': 'Status',
            'remarks': 'Remarks',
            'created_at': 'Marked At'
        }
        
        csv_data = []
        for record in attendance_records:
            csv_data.append({
                'student_name': record.get('student_name', ''),
                'class_name': record.get('class_name', ''),
                'subject_name': record.get('subject_name', 'N/A'),
                'attendance_date': record.get('attendance_date', ''),
                'status': record.get('status', ''),
                'remarks': record.get('remarks', ''),
                'created_at': record.get('created_at', '')
            })
        
        return CSVExportService.generate_csv(csv_data, field_mapping=field_mapping)
    
    @staticmethod
    def export_results(results: List[Dict[str, Any]]) -> str:
        """Export results/grades to CSV."""
        field_mapping = {
            'student_name': 'Student Name',
            'class_name': 'Class',
            'subject_name': 'Subject',
            'quiz_title': 'Quiz',
            'assignment_title': 'Assignment',
            'total_marks': 'Total Marks',
            'marks_obtained': 'Marks Obtained',
            'percentage': 'Percentage',
            'status': 'Status',
            'created_at': 'Date'
        }
        
        csv_data = []
        for result in results:
            csv_data.append({
                'student_name': result.get('student_name', ''),
                'class_name': result.get('class_name', ''),
                'subject_name': result.get('subject_name', ''),
                'quiz_title': result.get('quiz_title', 'N/A'),
                'assignment_title': result.get('assignment_title', 'N/A'),
                'total_marks': result.get('total_marks', 0),
                'marks_obtained': result.get('marks_obtained', 0),
                'percentage': f"{result.get('percentage', 0):.2f}%",
                'status': result.get('status', ''),
                'created_at': result.get('created_at', '')
            })
        
        return CSVExportService.generate_csv(csv_data, field_mapping=field_mapping)
    
    @staticmethod
    def export_leave_requests(leave_requests: List[Dict[str, Any]]) -> str:
        """Export leave requests to CSV."""
        field_mapping = {
            'user_name': 'User Name',
            'leave_type_name': 'Leave Type',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'number_of_days': 'Days',
            'reason': 'Reason',
            'status': 'Status',
            'approver_name': 'Approved By',
            'approved_at': 'Approved At',
            'rejection_reason': 'Rejection Reason',
            'created_at': 'Requested At'
        }
        
        csv_data = []
        for request in leave_requests:
            csv_data.append({
                'user_name': request.get('user_name', ''),
                'leave_type_name': request.get('leave_type_name', ''),
                'start_date': request.get('start_date', ''),
                'end_date': request.get('end_date', ''),
                'number_of_days': request.get('number_of_days', 0),
                'reason': request.get('reason', ''),
                'status': request.get('status', ''),
                'approver_name': request.get('approver_name', 'N/A'),
                'approved_at': request.get('approved_at', ''),
                'rejection_reason': request.get('rejection_reason', ''),
                'created_at': request.get('created_at', '')
            })
        
        return CSVExportService.generate_csv(csv_data, field_mapping=field_mapping)
    
    @staticmethod
    def export_fee_invoices(invoices: List[Dict[str, Any]]) -> str:
        """Export fee invoices to CSV."""
        field_mapping = {
            'student_name': 'Student Name',
            'invoice_number': 'Invoice Number',
            'fee_structure_name': 'Fee Structure',
            'total_amount': 'Total Amount',
            'paid_amount': 'Paid Amount',
            'due_amount': 'Due Amount',
            'due_date': 'Due Date',
            'status': 'Status',
            'created_at': 'Created At'
        }
        
        csv_data = []
        for invoice in invoices:
            total = invoice.get('total_amount', 0)
            paid = invoice.get('paid_amount', 0)
            due = total - paid
            
            csv_data.append({
                'student_name': invoice.get('student_name', ''),
                'invoice_number': invoice.get('invoice_number', ''),
                'fee_structure_name': invoice.get('fee_structure_name', ''),
                'total_amount': total,
                'paid_amount': paid,
                'due_amount': due,
                'due_date': invoice.get('due_date', ''),
                'status': invoice.get('status', ''),
                'created_at': invoice.get('created_at', '')
            })
        
        return CSVExportService.generate_csv(csv_data, field_mapping=field_mapping)
