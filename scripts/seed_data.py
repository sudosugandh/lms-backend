"""
Seed script to create initial data:
- One Super Admin
- Two Institutes
- Each institute has localhost and 127.0.0.1 domains
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.institute import Institute
from app.db.models.domain import Domain
from app.db.models.user import User, UserRole
from app.db.models.cms import WebsiteSettings
from app.core.security import get_password_hash
from app.services.cms_service import CMSService


def seed_data():
    """Seed initial data."""
    db: Session = SessionLocal()
    
    try:
        # Create Super Admin
        super_admin = db.query(User).filter(User.email == "superadmin@lms.com").first()
        if not super_admin:
            super_admin = User(
                institute_id=None,
                name="Super Admin",
                email="superadmin@lms.com",
                password_hash=get_password_hash("SuperAdmin123!"),
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            db.add(super_admin)
            print("✓ Created Super Admin")
        else:
            print("✓ Super Admin already exists")
        
        # Create Institute 1
        institute1 = db.query(Institute).filter(Institute.code == "INST001").first()
        if not institute1:
            institute1 = Institute(
                name="Institute One",
                code="INST001",
                is_active=True
            )
            db.add(institute1)
            db.flush()  # Get the ID
            print("✓ Created Institute 1")
        else:
            print("✓ Institute 1 already exists")
        
        # Create domains for Institute 1
        for host in ["localhost", "127.0.0.1"]:
            domain1 = db.query(Domain).filter(Domain.host_name == host).first()
            if not domain1:
                domain1 = Domain(
                    institute_id=institute1.id,
                    host_name=host,
                    is_active=True
                )
                db.add(domain1)
                print(f"✓ Created domain {host} for Institute 1")
            else:
                print(f"✓ Domain {host} already exists")
        
        # Create Admin for Institute 1
        admin1 = db.query(User).filter(User.email == "admin1@institute1.com").first()
        if not admin1:
            admin1 = User(
                institute_id=institute1.id,
                name="Admin One",
                email="admin1@institute1.com",
                password_hash=get_password_hash("Admin123!"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin1)
            print("✓ Created Admin for Institute 1")
        else:
            print("✓ Admin for Institute 1 already exists")
        
        # Create Institute 2
        institute2 = db.query(Institute).filter(Institute.code == "INST002").first()
        if not institute2:
            institute2 = Institute(
                name="Institute Two",
                code="INST002",
                is_active=True
            )
            db.add(institute2)
            db.flush()  # Get the ID
            print("✓ Created Institute 2")
        else:
            print("✓ Institute 2 already exists")
        
        # Create domains for Institute 2
        # Note: Since host_name is unique, Institute 2 uses different hostnames
        # For testing with Institute 2, you can:
        # 1. Add entries to /etc/hosts: 127.0.0.1 institute2.local
        # 2. Use different ports with reverse proxy
        # 3. Manually create domains via API after setup
        for host in ["institute2.local", "institute2.localhost"]:
            domain2 = db.query(Domain).filter(Domain.host_name == host).first()
            if not domain2:
                domain2 = Domain(
                    institute_id=institute2.id,
                    host_name=host,
                    is_active=True
                )
                db.add(domain2)
                print(f"✓ Created domain {host} for Institute 2")
            else:
                print(f"✓ Domain {host} already exists")
        
        # Create Admin for Institute 2
        admin2 = db.query(User).filter(User.email == "admin2@institute2.com").first()
        if not admin2:
            admin2 = User(
                institute_id=institute2.id,
                name="Admin Two",
                email="admin2@institute2.com",
                password_hash=get_password_hash("Admin123!"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin2)
            print("✓ Created Admin for Institute 2")
        else:
            print("✓ Admin for Institute 2 already exists")
        
        # Initialize WebsiteSettings for each institute
        for institute in [institute1, institute2]:
            settings = CMSService.get_website_settings(db, institute.id)
            if settings:
                print(f"✓ WebsiteSettings already exists for {institute.name}")
            else:
                print(f"✓ Created WebsiteSettings for {institute.name}")
        
        db.commit()
        print("\n✅ Seed data created successfully!")
        print("\nTest Credentials:")
        print("Super Admin: superadmin@lms.com / SuperAdmin123!")
        print("Admin 1: admin1@institute1.com / Admin123!")
        print("Admin 2: admin2@institute2.com / Admin123!")
        print("\n⚠️  IMPORTANT: Run 'python scripts/seed_permissions.py' to seed permissions!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
