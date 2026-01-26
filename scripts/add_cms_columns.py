"""
Script to add CMS landing page columns to website_settings table
Run this if the Alembic migration fails
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import SessionLocal

def add_cms_columns():
    """Add CMS landing page columns to website_settings table."""
    db = SessionLocal()
    
    try:
        # Check if columns already exist
        result = db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'website_settings' 
            AND COLUMN_NAME IN ('banner_images', 'header_background', 'custom_css', 'custom_js')
        """))
        existing_columns = [row[0] for row in result]
        
        if 'banner_images' in existing_columns:
            print("✓ Columns already exist. Skipping migration.")
            return
        
        # Add columns
        print("Adding CMS landing page columns to website_settings table...")
        
        db.execute(text("""
            ALTER TABLE website_settings 
            ADD COLUMN banner_images JSON NULL AFTER favicon_url
        """))
        print("✓ Added banner_images column")
        
        db.execute(text("""
            ALTER TABLE website_settings 
            ADD COLUMN header_background VARCHAR(20) NULL AFTER secondary_color
        """))
        print("✓ Added header_background column")
        
        db.execute(text("""
            ALTER TABLE website_settings 
            ADD COLUMN custom_css TEXT NULL AFTER header_background
        """))
        print("✓ Added custom_css column")
        
        db.execute(text("""
            ALTER TABLE website_settings 
            ADD COLUMN custom_js TEXT NULL AFTER custom_css
        """))
        print("✓ Added custom_js column")
        
        db.commit()
        print("\n✅ Successfully added all CMS landing page columns!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_cms_columns()
