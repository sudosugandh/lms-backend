from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    total_marks: int = 0
    duration_minutes: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    allow_multiple_attempts: bool = False


class QuizCreate(QuizBase):
    class_id: int
    subject_id: int


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    total_marks: Optional[int] = None
    duration_minutes: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None  # DRAFT, PUBLISHED, CLOSED
    allow_multiple_attempts: Optional[bool] = None
    is_active: Optional[bool] = None


class QuizResponse(QuizBase):
    id: int
    institute_id: int
    class_id: int
    subject_id: int
    created_by: int
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class QuizQuestionBase(BaseModel):
    question_text: str
    question_type: str  # MCQ or DESCRIPTIVE
    marks: int = 1
    order: int = 0


class QuizQuestionCreate(QuizQuestionBase):
    quiz_id: Optional[int] = None  # Optional since it comes from URL path
    options: Optional[List[QuizOptionBase]] = None  # For MCQ questions - will be List[QuizOptionBase] (without question_id)


class QuizQuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    marks: Optional[int] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class QuizQuestionResponse(QuizQuestionBase):
    id: int
    quiz_id: int
    is_active: bool
    created_at: datetime
    options: Optional[List] = None  # Will be List[QuizOptionResponse] after class definition
    
    class Config:
        from_attributes = True


class QuizOptionBase(BaseModel):
    option_text: str
    is_correct: bool = False
    order: int = 0


class QuizOptionCreate(QuizOptionBase):
    question_id: int


class QuizOptionResponse(QuizOptionBase):
    id: int
    question_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Rebuild models to resolve forward references
QuizQuestionCreate.model_rebuild()
QuizQuestionResponse.model_rebuild()


# Update forward reference after QuizOptionResponse is defined
QuizQuestionResponse.model_fields['options'].annotation = Optional[List[QuizOptionResponse]]


class QuizAttemptBase(BaseModel):
    quiz_id: int


class QuizAttemptResponse(BaseModel):
    id: int
    quiz_id: int
    student_id: int
    started_at: datetime
    submitted_at: Optional[datetime] = None
    time_taken_minutes: Optional[int] = None
    status: str
    total_marks_obtained: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime
    student_name: Optional[str] = None
    quiz_title: Optional[str] = None
    
    class Config:
        from_attributes = True


class QuizAttemptAnswerBase(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None  # For MCQ
    descriptive_answer: Optional[str] = None  # For descriptive


class QuizAttemptAnswerCreate(QuizAttemptAnswerBase):
    attempt_id: int


class QuizAttemptAnswerResponse(QuizAttemptAnswerBase):
    id: int
    attempt_id: int
    marks_obtained: Optional[int] = None
    is_correct: Optional[bool] = None
    graded_by: Optional[int] = None
    graded_at: Optional[datetime] = None
    feedback: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuizAttemptWithAnswers(QuizAttemptResponse):
    answers: List[QuizAttemptAnswerResponse] = []


class QuizAttemptSubmit(BaseModel):
    """Request model for submitting quiz attempt with answers"""
    answers: List[QuizAttemptAnswerBase]


class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    total_marks: int = 0
    deadline: datetime
    allow_late_submission: bool = False
    attachment_url: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    class_id: int
    subject_id: int


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    total_marks: Optional[int] = None
    deadline: Optional[datetime] = None
    allow_late_submission: Optional[bool] = None
    attachment_url: Optional[str] = None
    is_active: Optional[bool] = None


class AssignmentResponse(AssignmentBase):
    id: int
    institute_id: int
    class_id: int
    subject_id: int
    created_by: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    creator_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class AssignmentSubmissionBase(BaseModel):
    assignment_id: int
    submission_text: Optional[str] = None
    attachment_url: Optional[str] = None


class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    pass


class AssignmentSubmissionResponse(AssignmentSubmissionBase):
    id: int
    student_id: int
    submitted_at: datetime
    is_late: bool
    status: str
    marks_obtained: Optional[int] = None
    graded_by: Optional[int] = None
    graded_at: Optional[datetime] = None
    feedback: Optional[str] = None
    created_at: datetime
    student_name: Optional[str] = None
    assignment_title: Optional[str] = None
    
    class Config:
        from_attributes = True


class AssignmentSubmissionGrade(BaseModel):
    """Request model for grading assignment submission"""
    marks_obtained: int
    feedback: Optional[str] = None


class ResultBase(BaseModel):
    result_type: str  # QUIZ or ASSIGNMENT
    total_marks: int
    marks_obtained: int
    percentage: float
    grade: Optional[str] = None
    status: str = "PENDING"
    remarks: Optional[str] = None


class ResultResponse(ResultBase):
    id: int
    institute_id: int
    student_id: int
    class_id: int
    subject_id: int
    quiz_id: Optional[int] = None
    assignment_id: Optional[int] = None
    quiz_attempt_id: Optional[int] = None
    assignment_submission_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    quiz_title: Optional[str] = None
    assignment_title: Optional[str] = None
    
    class Config:
        from_attributes = True


class GradingBase(BaseModel):
    result_id: int
    grading_details: Optional[str] = None
    feedback: Optional[str] = None


class GradingResponse(GradingBase):
    id: int
    institute_id: int
    graded_by: int
    graded_at: datetime
    created_at: datetime
    grader_name: Optional[str] = None
    
    class Config:
        from_attributes = True
