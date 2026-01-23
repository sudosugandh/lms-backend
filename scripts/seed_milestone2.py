"""
Seed script for Milestone-2 data:
- Teachers and Students for each institute
- Classes and Subjects
- Class-Subject assignments with teachers
- Student enrollments
- Sample attendance records
"""
import sys
from pathlib import Path
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.institute import Institute
from app.db.models.user import User, UserRole
from app.db.models.class_model import Class
from app.db.models.subject import Subject
from app.db.models.class_subject import ClassSubject
from app.db.models.enrollment import Enrollment
from app.db.models.attendance import Attendance
from app.core.security import get_password_hash


def seed_milestone2_data():
    """Seed Milestone-2 test data."""
    db: Session = SessionLocal()
    
    try:
        # Get Institute 1
        institute1 = db.query(Institute).filter(Institute.code == "INST001").first()
        if not institute1:
            print("❌ Institute 1 not found. Please run seed_data.py first.")
            return
        
        # Get Admin 1
        admin1 = db.query(User).filter(User.email == "admin1@institute1.com").first()
        if not admin1:
            print("❌ Admin 1 not found. Please run seed_data.py first.")
            return
        
        # Create Teachers for Institute 1
        teachers = []
        for i in range(1, 3):
            teacher_email = f"teacher{i}@institute1.com"
            teacher = db.query(User).filter(User.email == teacher_email).first()
            if not teacher:
                teacher = User(
                    institute_id=institute1.id,
                    name=f"Teacher {i}",
                    email=teacher_email,
                    password_hash=get_password_hash("Teacher123!"),
                    role=UserRole.TEACHER,
                    is_active=True
                )
                db.add(teacher)
                db.flush()
                print(f"✓ Created Teacher {i} for Institute 1")
            else:
                print(f"✓ Teacher {i} already exists")
            teachers.append(teacher)
        
        # Create Students for Institute 1
        students = []
        for i in range(1, 6):
            student_email = f"student{i}@institute1.com"
            student = db.query(User).filter(User.email == student_email).first()
            if not student:
                student = User(
                    institute_id=institute1.id,
                    name=f"Student {i}",
                    email=student_email,
                    password_hash=get_password_hash("Student123!"),
                    role=UserRole.STUDENT,
                    is_active=True
                )
                db.add(student)
                db.flush()
                print(f"✓ Created Student {i} for Institute 1")
            else:
                print(f"✓ Student {i} already exists")
            students.append(student)
        
        # Create Classes for Institute 1
        classes = []
        class_names = ["Class 10-A", "Class 10-B"]
        for class_name in class_names:
            class_code = class_name.replace(" ", "-").replace("-", "").upper()
            class_obj = db.query(Class).filter(
                Class.institute_id == institute1.id,
                Class.code == class_code
            ).first()
            if not class_obj:
                class_obj = Class(
                    institute_id=institute1.id,
                    name=class_name,
                    code=class_code,
                    description=f"{class_name} description",
                    is_active=True
                )
                db.add(class_obj)
                db.flush()
                print(f"✓ Created {class_name}")
            else:
                print(f"✓ {class_name} already exists")
            classes.append(class_obj)
        
        # Create Subjects for Institute 1
        subjects = []
        subject_names = ["Mathematics", "Science", "English"]
        for subject_name in subject_names:
            subject_code = subject_name[:3].upper()
            subject = db.query(Subject).filter(
                Subject.institute_id == institute1.id,
                Subject.code == subject_code
            ).first()
            if not subject:
                subject = Subject(
                    institute_id=institute1.id,
                    name=subject_name,
                    code=subject_code,
                    description=f"{subject_name} description",
                    is_active=True
                )
                db.add(subject)
                db.flush()
                print(f"✓ Created Subject: {subject_name}")
            else:
                print(f"✓ Subject {subject_name} already exists")
            subjects.append(subject)
        
        # Assign subjects to classes with teachers
        # Class 10-A: Math (Teacher 1), Science (Teacher 1), English (Teacher 2)
        # Class 10-B: Math (Teacher 2), Science (Teacher 1), English (Teacher 2)
        assignments = [
            (classes[0], subjects[0], teachers[0]),  # Class 10-A, Math, Teacher 1
            (classes[0], subjects[1], teachers[0]),  # Class 10-A, Science, Teacher 1
            (classes[0], subjects[2], teachers[1]),  # Class 10-A, English, Teacher 2
            (classes[1], subjects[0], teachers[1]),  # Class 10-B, Math, Teacher 2
            (classes[1], subjects[1], teachers[0]),  # Class 10-B, Science, Teacher 1
            (classes[1], subjects[2], teachers[1]),  # Class 10-B, English, Teacher 2
        ]
        
        for class_obj, subject, teacher in assignments:
            existing = db.query(ClassSubject).filter(
                ClassSubject.class_id == class_obj.id,
                ClassSubject.subject_id == subject.id
            ).first()
            if not existing:
                assignment = ClassSubject(
                    class_id=class_obj.id,
                    subject_id=subject.id,
                    teacher_id=teacher.id
                )
                db.add(assignment)
                print(f"✓ Assigned {subject.name} to {class_obj.name} (Teacher: {teacher.name})")
            else:
                if existing.teacher_id != teacher.id:
                    existing.teacher_id = teacher.id
                    print(f"✓ Updated assignment: {subject.name} to {class_obj.name} (Teacher: {teacher.name})")
        
        # Enroll students in classes
        # First 3 students in Class 10-A, rest in Class 10-B
        enrollments_data = [
            (students[0], classes[0]),  # Student 1 -> Class 10-A
            (students[1], classes[0]),  # Student 2 -> Class 10-A
            (students[2], classes[0]),  # Student 3 -> Class 10-A
            (students[3], classes[1]),  # Student 4 -> Class 10-B
            (students[4], classes[1]),  # Student 5 -> Class 10-B
        ]
        
        for student, class_obj in enrollments_data:
            existing = db.query(Enrollment).filter(
                Enrollment.student_id == student.id,
                Enrollment.class_id == class_obj.id
            ).first()
            if not existing:
                enrollment = Enrollment(
                    student_id=student.id,
                    class_id=class_obj.id
                )
                db.add(enrollment)
                print(f"✓ Enrolled {student.name} in {class_obj.name}")
            else:
                print(f"✓ {student.name} already enrolled in {class_obj.name}")
        
        # Create sample attendance records (last 7 days)
        today = date.today()
        for day_offset in range(7):
            attendance_date = today - timedelta(days=day_offset)
            
            # Skip weekends for simplicity
            if attendance_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                continue
            
            # Mark attendance for Class 10-A students
            for student_idx, student in enumerate(students[:3]):  # First 3 students in Class 10-A
                # Randomly assign status (for demo purposes)
                status = "PRESENT" if student_idx % 2 == 0 else "ABSENT" if day_offset % 3 == 0 else "PRESENT"
                
                # Mark attendance for Math class
                math_assignment = db.query(ClassSubject).filter(
                    ClassSubject.class_id == classes[0].id,
                    ClassSubject.subject_id == subjects[0].id
                ).first()
                
                if math_assignment:
                    existing = db.query(Attendance).filter(
                        Attendance.student_id == student.id,
                        Attendance.class_id == classes[0].id,
                        Attendance.subject_id == subjects[0].id,
                        Attendance.attendance_date == attendance_date
                    ).first()
                    
                    if not existing:
                        attendance = Attendance(
                            student_id=student.id,
                            class_id=classes[0].id,
                            subject_id=subjects[0].id,
                            attendance_date=attendance_date,
                            status=status,
                            marked_by=teachers[0].id,
                            remarks=f"Attendance for {attendance_date}"
                        )
                        db.add(attendance)
        
        db.commit()
        print("\n✅ Milestone-2 seed data created successfully!")
        print("\nTest Credentials:")
        print("Teachers:")
        print("  Teacher 1: teacher1@institute1.com / Teacher123!")
        print("  Teacher 2: teacher2@institute1.com / Teacher123!")
        print("\nStudents:")
        print("  Student 1: student1@institute1.com / Student123!")
        print("  Student 2: student2@institute1.com / Student123!")
        print("  Student 3: student3@institute1.com / Student123!")
        print("  Student 4: student4@institute1.com / Student123!")
        print("  Student 5: student5@institute1.com / Student123!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding Milestone-2 data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_milestone2_data()
