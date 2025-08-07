#!/usr/bin/env python3
"""
Test script to verify database connectivity and models
"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine, SessionLocal, Base
from app.models import User, Project, Document, Persona

def test_database_connection():
    """Test basic database connectivity"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_create_tables():
    """Test creating database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def test_basic_crud():
    """Test basic CRUD operations"""
    db = SessionLocal()
    try:
        # Test User creation
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashedpassword123"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ User created: {user}")

        # Test Project creation
        project = Project(
            title="Test Project",
            description="A test project for verification",
            user_id=user.id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        print(f"✅ Project created: {project}")

        # Test Document creation
        document = Document(
            filename="test_document.txt",
            content="This is test content",
            file_type="text/plain",
            project_id=project.id
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        print(f"✅ Document created: {document}")

        # Test Persona creation
        persona = Persona(
            name="Test Persona",
            description="A test persona",
            personality_traits={"trait1": "value1", "trait2": "value2"},
            system_prompt="You are a test persona"
        )
        db.add(persona)
        db.commit()
        db.refresh(persona)
        print(f"✅ Persona created: {persona}")

        # Test relationships
        user_with_projects = db.query(User).filter(User.id == user.id).first()
        print(f"✅ User has {len(user_with_projects.projects)} project(s)")
        
        project_with_documents = db.query(Project).filter(Project.id == project.id).first()
        print(f"✅ Project has {len(project_with_documents.documents)} document(s)")

        # Clean up test data
        db.delete(document)
        db.delete(project)
        db.delete(persona)
        db.delete(user)
        db.commit()
        print("✅ Test data cleaned up successfully!")
        
        return True
    except Exception as e:
        print(f"❌ CRUD operations failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Run all database tests"""
    print("🔍 Testing database setup...")
    print("=" * 50)
    
    success = True
    
    # Test connection
    success &= test_database_connection()
    
    # Test table creation
    success &= test_create_tables()
    
    # Test CRUD operations
    success &= test_basic_crud()
    
    print("=" * 50)
    if success:
        print("🎉 All database tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())