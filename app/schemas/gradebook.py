from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.db.models.gradebook import TermType


class GradebookEntryBase(BaseModel):
    student_id: int
    class_id: int
    subject_id: int
    academic_year: str = Field(..., description="Academic year e.g., '2024-2025'")
    term: TermType
    quiz_weight: float = Field(default=0.30, ge=0.0, le=1.0, description="Weight for quizzes (0.0-1.0)")
    assignment_weight: float = Field(default=0.40, ge=0.0, le=1.0, description="Weight for assignments (0.0-1.0)")
    exam_weight: float = Field(default=0.30, ge=0.0, le=1.0, description="Weight for exams (0.0-1.0)")
    remarks: Optional[str] = None


class GradebookEntryCreate(GradebookEntryBase):
    pass


class GradebookEntryUpdate(BaseModel):
    quiz_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    assignment_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    exam_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    status: Optional[str] = None  # DRAFT, PUBLISHED, LOCKED
    remarks: Optional[str] = None


class GradebookEntryResponse(GradebookEntryBase):
    id: int
    institute_id: int
    quiz_total_marks: float
    quiz_obtained_marks: float
    quiz_weighted_score: float
    assignment_total_marks: float
    assignment_obtained_marks: float
    assignment_weighted_score: float
    exam_total_marks: float
    exam_obtained_marks: float
    exam_weighted_score: float
    total_marks: float
    obtained_marks: float
    percentage: float
    letter_grade: Optional[str] = None
    grade_point: Optional[float] = None
    status: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Additional fields for response
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class GradebookCalculateRequest(BaseModel):
    class_id: int
    subject_id: Optional[int] = None
    academic_year: str
    term: TermType
    quiz_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    assignment_weight: float = Field(default=0.40, ge=0.0, le=1.0)
    exam_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    recalculate: bool = Field(default=False, description="Recalculate existing entries")


class GradebookBulkUpdateRequest(BaseModel):
    entry_ids: List[int]
    status: Optional[str] = None
    remarks: Optional[str] = None


class GradeDistributionResponse(BaseModel):
    id: int
    institute_id: int
    class_id: int
    subject_id: Optional[int] = None
    academic_year: str
    term: TermType
    total_students: int
    a_plus_count: int
    a_count: int
    b_plus_count: int
    b_count: int
    c_plus_count: int
    c_count: int
    d_count: int
    f_count: int
    average_percentage: float
    highest_percentage: float
    lowest_percentage: float
    calculated_at: datetime
    
    # Additional fields
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class GradebookHistoryResponse(BaseModel):
    id: int
    gradebook_entry_id: int
    changed_by: Optional[int] = None
    change_type: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_reason: Optional[str] = None
    created_at: datetime
    
    # Additional fields
    changed_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReportCardRequest(BaseModel):
    student_id: int
    academic_year: str
    term: Optional[TermType] = None  # If None, generate for all terms
    include_remarks: bool = True
    include_attendance: bool = True
    include_analytics: bool = True


class GradebookAnalyticsResponse(BaseModel):
    total_students: int
    average_percentage: float
    highest_percentage: float
    lowest_percentage: float
    pass_count: int
    fail_count: int
    pass_percentage: float
    grade_distribution: dict  # { "A+": 5, "A": 10, ... }
    subject_wise_average: Optional[dict] = None  # { "subject_id": average_percentage }
    class_rank: Optional[dict] = None  # { "student_id": rank }
