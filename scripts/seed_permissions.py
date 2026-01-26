"""
Seed script to initialize permissions system:
- Seed all available permissions
- Assign all permissions to ADMIN role (full access)
- Assign appropriate permissions to TEACHER, STUDENT, PARENT roles
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.permission_service import PermissionService


def seed_permissions():
    """Seed permissions and assign to roles."""
    db: Session = SessionLocal()
    
    try:
        print("Seeding permissions...")
        
        # Step 1: Seed all permissions
        permissions = PermissionService.seed_permissions(db)
        print(f"✓ Created {len(permissions)} permissions")
        
        # Step 2: Get all permission IDs
        all_permissions = PermissionService.get_all_permissions(db)
        all_permission_ids = [p.id for p in all_permissions]
        
        if not all_permission_ids:
            print("❌ No permissions found. Cannot assign to roles.")
            return
        
        # Step 3: Assign ALL permissions to ADMIN role (full access)
        admin_perms = PermissionService.set_role_permissions(db, "ADMIN", all_permission_ids)
        print(f"✓ Assigned {len(admin_perms)} permissions to ADMIN role")
        
        # Step 4: Assign appropriate permissions to TEACHER role
        teacher_permissions = []
        for perm in all_permissions:
            # Teachers can view most things, create/edit their own content
            if perm.action in ['view', 'create', 'edit']:
                if perm.module in ['dashboard', 'attendance', 'gradebook', 'quizzes', 'assignments', 
                                   'timetable', 'leave', 'notifications', 'reports']:
                    teacher_permissions.append(perm.id)
            # Teachers can take/submit their own content
            if perm.action in ['take', 'submit']:
                teacher_permissions.append(perm.id)
        
        if teacher_permissions:
            teacher_perms = PermissionService.set_role_permissions(db, "TEACHER", teacher_permissions)
            print(f"✓ Assigned {len(teacher_perms)} permissions to TEACHER role")
        
        # Step 5: Assign appropriate permissions to STUDENT role
        student_permissions = []
        for perm in all_permissions:
            # Students can view their own data and submit assignments/take quizzes
            if perm.action == 'view':
                if perm.module in ['dashboard', 'attendance', 'gradebook', 'quizzes', 'assignments', 
                                   'timetable', 'leave', 'notifications']:
                    student_permissions.append(perm.id)
            if perm.action in ['take', 'submit']:
                if perm.module in ['quizzes', 'assignments']:
                    student_permissions.append(perm.id)
            if perm.action == 'create':
                if perm.module in ['leave']:
                    student_permissions.append(perm.id)
        
        if student_permissions:
            student_perms = PermissionService.set_role_permissions(db, "STUDENT", student_permissions)
            print(f"✓ Assigned {len(student_perms)} permissions to STUDENT role")
        
        # Step 6: Assign appropriate permissions to PARENT role
        parent_permissions = []
        for perm in all_permissions:
            # Parents can view their children's data
            if perm.action == 'view':
                if perm.module in ['dashboard', 'attendance', 'gradebook', 'timetable', 
                                   'notifications', 'reports']:
                    parent_permissions.append(perm.id)
        
        if parent_permissions:
            parent_perms = PermissionService.set_role_permissions(db, "PARENT", parent_permissions)
            print(f"✓ Assigned {len(parent_perms)} permissions to PARENT role")
        
        db.commit()
        print("\n✅ Permissions seeded successfully!")
        print("\nPermission Summary:")
        print(f"  - Total Permissions: {len(all_permissions)}")
        print(f"  - ADMIN: {len(admin_perms)} permissions (full access)")
        print(f"  - TEACHER: {len(teacher_perms) if teacher_permissions else 0} permissions")
        print(f"  - STUDENT: {len(student_perms) if student_permissions else 0} permissions")
        print(f"  - PARENT: {len(parent_perms) if parent_permissions else 0} permissions")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding permissions: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_permissions()
