"""
Script to seed default permissions and role-permission mappings.
Run this after creating the permissions tables.
"""
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.permission_service import PermissionService
from app.db.models.user import UserRole


def seed_default_permissions():
    """Seed all permissions and default role mappings."""
    db: Session = SessionLocal()
    
    try:
        print("Seeding permissions...")
        permissions = PermissionService.seed_permissions(db)
        print(f"Created {len(permissions)} permissions")
        
        # Define default role-permission mappings
        role_permissions = {
            UserRole.SUPER_ADMIN.value: [],  # Will get all permissions via logic
            UserRole.ADMIN.value: [
                # Admin gets most permissions
                'dashboard.view',
                'users.view', 'users.create', 'users.edit', 'users.delete', 'users.export',
                'classes.view', 'classes.create', 'classes.edit', 'classes.delete', 'classes.export',
                'subjects.view', 'subjects.create', 'subjects.edit', 'subjects.delete', 'subjects.export',
                'attendance.view', 'attendance.create', 'attendance.edit', 'attendance.delete', 'attendance.export',
                'gradebook.view', 'gradebook.create', 'gradebook.edit', 'gradebook.delete', 'gradebook.export',
                'quizzes.view', 'quizzes.create', 'quizzes.edit', 'quizzes.delete', 'quizzes.export',
                'assignments.view', 'assignments.create', 'assignments.edit', 'assignments.delete', 'assignments.export',
                'exams.view', 'exams.create', 'exams.edit', 'exams.delete', 'exams.export',
                'timetable.view', 'timetable.create', 'timetable.edit', 'timetable.delete', 'timetable.export',
                'leave.view', 'leave.create', 'leave.edit', 'leave.delete', 'leave.approve', 'leave.export',
                'notifications.view', 'notifications.create', 'notifications.edit', 'notifications.delete', 'notifications.export',
                'fees.view', 'fees.create', 'fees.edit', 'fees.delete', 'fees.export',
                'certificates.view', 'certificates.create', 'certificates.edit', 'certificates.delete', 'certificates.export',
                'cms.view', 'cms.create', 'cms.edit', 'cms.delete', 'cms.export',
                'reports.view', 'reports.export',
                'settings.view', 'settings.edit',
            ],
            UserRole.TEACHER.value: [
                'dashboard.view',
                'classes.view',
                'attendance.view', 'attendance.create', 'attendance.edit', 'attendance.delete',
                'gradebook.view', 'gradebook.create', 'gradebook.edit', 'gradebook.delete',
                'quizzes.view', 'quizzes.create', 'quizzes.edit', 'quizzes.delete',
                'assignments.view', 'assignments.create', 'assignments.edit', 'assignments.delete',
                'timetable.view',
                'leave.create', 'leave.view',
                'notifications.view',
            ],
            UserRole.STUDENT.value: [
                'dashboard.view',
                'attendance.view',
                'gradebook.view',
                'quizzes.view', 'quizzes.take',
                'assignments.view', 'assignments.submit',
                'timetable.view',
                'leave.create', 'leave.view',
                'notifications.view',
            ],
            UserRole.PARENT.value: [
                'dashboard.view',
                'attendance.view',
                'gradebook.view',
                'timetable.view',
                'notifications.view',
            ],
        }
        
        # Get all permissions to map permission strings to IDs
        all_permissions = PermissionService.get_all_permissions(db)
        perm_map = {PermissionService.get_permission_string(p.module, p.action): p.id for p in all_permissions}
        
        print("\nSetting role permissions...")
        for role, perm_strings in role_permissions.items():
            if role == UserRole.SUPER_ADMIN.value:
                # SUPER_ADMIN gets all permissions
                permission_ids = list(perm_map.values())
            else:
                permission_ids = [perm_map[ps] for ps in perm_strings if ps in perm_map]
            
            role_perms = PermissionService.set_role_permissions(db, role, permission_ids)
            print(f"  {role}: {len(role_perms)} permissions")
        
        print("\n✅ Permissions seeded successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding permissions: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_default_permissions()
