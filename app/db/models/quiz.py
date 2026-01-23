from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class QuizStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"


class QuestionType(str, enum.Enum):
    MCQ = "MCQ"
    DESCRIPTIVE = "DESCRIPTIVE"


class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    institute_id = Column(Integer, ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    total_marks = Column(Integer, nullable=False, default=0)
    duration_minutes = Column(Integer, nullable=True)  # Time limit in minutes
    start_time = Column(DateTime(timezone=True), nullable=True)  # When quiz becomes available
    end_time = Column(DateTime(timezone=True), nullable=True)  # When quiz closes
    status = Column(String(20), nullable=False, default="DRAFT")  # DRAFT, PUBLISHED, CLOSED
    allow_multiple_attempts = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    institute = relationship("Institute")
    class_ = relationship("Class")
    subject = relationship("Subject")
    creator = relationship("User", foreign_keys=[created_by])
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)  # MCQ or DESCRIPTIVE
    marks = Column(Integer, nullable=False, default=1)
    order = Column(Integer, nullable=False, default=0)  # Order in quiz
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    options = relationship("QuizOption", back_populates="question", cascade="all, delete-orphan")
    attempt_answers = relationship("QuizAttemptAnswer", back_populates="question", cascade="all, delete-orphan")


class QuizOption(Base):
    __tablename__ = "quiz_options"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)  # Only for MCQ
    order = Column(Integer, nullable=False, default=0)  # Order of option
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    question = relationship("QuizQuestion", back_populates="options")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)  # When student submits
    time_taken_minutes = Column(Integer, nullable=True)  # Actual time taken
    status = Column(String(20), nullable=False, default="IN_PROGRESS")  # IN_PROGRESS, SUBMITTED, GRADED
    total_marks_obtained = Column(Integer, nullable=True)  # Auto-calculated or manually graded
    feedback = Column(Text, nullable=True)  # Teacher feedback
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("User", foreign_keys=[student_id])
    answers = relationship("QuizAttemptAnswer", back_populates="attempt", cascade="all, delete-orphan")
    result = relationship("Result", back_populates="quiz_attempt", uselist=False)


class QuizAttemptAnswer(Base):
    __tablename__ = "quiz_attempt_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_option_id = Column(Integer, ForeignKey("quiz_options.id", ondelete="SET NULL"), nullable=True)  # For MCQ
    descriptive_answer = Column(Text, nullable=True)  # For descriptive questions
    marks_obtained = Column(Integer, nullable=True)  # Marks given for this answer
    is_correct = Column(Boolean, nullable=True)  # Auto-calculated for MCQ
    graded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)
    feedback = Column(Text, nullable=True)  # Teacher feedback for this answer
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("QuizQuestion", back_populates="attempt_answers")
    selected_option = relationship("QuizOption", foreign_keys=[selected_option_id])
    grader = relationship("User", foreign_keys=[graded_by])
