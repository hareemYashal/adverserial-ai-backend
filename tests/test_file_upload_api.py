"""
Tests for file upload API endpoints.
"""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from io import BytesIO

from app.main import app
from app.database import get_db, Base
from app.models.user import User
from app.models.project import Project
from app.models.document import Document


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_file_upload.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestFileUploadAPI:
    """Test cases for file upload API endpoints."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Create a test client."""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        with TestClient(app) as test_client:
            yield test_client
        
        # Clean up
        Base.metadata.drop_all(bind=engine)
        try:
            if os.path.exists("test_file_upload.db"):
                os.unlink("test_file_upload.db")
        except PermissionError:
            pass  # Ignore file locking issues on Windows
    
    @pytest.fixture
    def db_session(self):
        """Create a database session for testing."""
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user."""
        import time
        timestamp = str(int(time.time() * 1000))  # Get unique timestamp
        user = User(
            username=f"fileuploaduser_{timestamp}",
            email=f"fileupload_{timestamp}@example.com",
            hashed_password="hashedpassword"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def test_project(self, db_session, test_user):
        """Create a test project."""
        project = Project(
            title="Test Project",
            description="A test project for file uploads",
            user_id=test_user.id
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        return project
    
    def test_get_supported_file_types(self, client):
        """Test getting supported file types."""
        response = client.get("/upload/supported-types")
        assert response.status_code == 200
        
        data = response.json()
        assert "supported_types" in data
        assert "max_file_size" in data
        assert "max_file_size_mb" in data
        
        # Check that expected types are supported
        supported_types = data["supported_types"]
        assert "text/plain" in supported_types
        assert "application/pdf" in supported_types
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in supported_types
    
    def test_upload_text_document(self, client, test_project):
        """Test uploading a text document."""
        # Create a test text file
        file_content = b"This is a test document for upload testing."
        
        files = {
            "file": ("test_document.txt", BytesIO(file_content), "text/plain")
        }
        data = {
            "project_id": test_project.id
        }
        
        response = client.post("/upload/document", files=files, data=data)
        assert response.status_code == 201
        
        result = response.json()
        assert result["filename"] == "test_document.txt"
        assert result["file_type"] == "text/plain"
        assert result["project_id"] == test_project.id
        assert result["file_size"] > 0
        assert "unique_filename" in result
        assert "uploaded_at" in result
        assert result["is_processed"] == False  # Will be processed in background
    
    def test_upload_document_invalid_project(self, client):
        """Test uploading document to non-existent project."""
        file_content = b"Test content"
        
        files = {
            "file": ("test.txt", BytesIO(file_content), "text/plain")
        }
        data = {
            "project_id": 99999  # Non-existent project
        }
        
        response = client.post("/upload/document", files=files, data=data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_upload_unsupported_file_type(self, client, test_project):
        """Test uploading unsupported file type."""
        file_content = b"Executable content"
        
        files = {
            "file": ("malware.exe", BytesIO(file_content), "application/x-executable")
        }
        data = {
            "project_id": test_project.id
        }
        
        response = client.post("/upload/document", files=files, data=data)
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"].lower()
    
    def test_upload_multiple_documents(self, client, test_project):
        """Test uploading multiple documents at once."""
        files = [
            ("files", ("doc1.txt", BytesIO(b"Content of document 1"), "text/plain")),
            ("files", ("doc2.txt", BytesIO(b"Content of document 2"), "text/plain"))
        ]
        data = {
            "project_id": test_project.id
        }
        
        response = client.post("/upload/documents/batch", files=files, data=data)
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) == 2
        assert results[0]["filename"] == "doc1.txt"
        assert results[1]["filename"] == "doc2.txt"
        assert all(doc["project_id"] == test_project.id for doc in results)
    
    def test_upload_too_many_documents(self, client, test_project):
        """Test uploading too many documents at once."""
        # Create 11 files (exceeds limit of 10)
        files = [
            ("files", (f"doc{i}.txt", BytesIO(f"Content {i}".encode()), "text/plain"))
            for i in range(11)
        ]
        data = {
            "project_id": test_project.id
        }
        
        response = client.post("/upload/documents/batch", files=files, data=data)
        assert response.status_code == 400
        assert "maximum 10 files" in response.json()["detail"].lower()
    
    def test_get_document_processing_status(self, client, test_project, db_session):
        """Test getting document processing status."""
        # Create a document in the database
        document = Document(
            filename="test.txt",
            unique_filename="unique_test.txt",
            file_path="/path/to/file.txt",
            file_type="text/plain",
            file_size=100,
            project_id=test_project.id,
            is_processed=True,
            content="Sample content for testing"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        response = client.get(f"/upload/document/{document.id}/status")
        assert response.status_code == 200
        
        result = response.json()
        assert result["id"] == document.id
        assert result["filename"] == "test.txt"
        assert result["is_processed"] == True
        assert "content_preview" in result
    
    def test_get_processing_status_nonexistent_document(self, client):
        """Test getting processing status for non-existent document."""
        response = client.get("/upload/document/99999/status")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_reprocess_document(self, client, test_project, db_session):
        """Test reprocessing a document."""
        # Create a document in the database
        document = Document(
            filename="test.txt",
            unique_filename="unique_test.txt",
            file_path="/path/to/file.txt",
            file_type="text/plain",
            file_size=100,
            project_id=test_project.id,
            is_processed=True
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        
        response = client.post(f"/upload/document/{document.id}/reprocess")
        assert response.status_code == 200
        
        result = response.json()
        assert "reprocessing started" in result["message"].lower()
        assert result["document_id"] == document.id
    
    def test_reprocess_nonexistent_document(self, client):
        """Test reprocessing non-existent document."""
        response = client.post("/upload/document/99999/reprocess")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_project_processing_status(self, client, test_project, db_session):
        """Test getting project processing status summary."""
        # Create some documents
        documents = [
            Document(
                filename="doc1.txt",
                unique_filename="unique_doc1.txt",
                file_type="text/plain",
                file_size=100,
                project_id=test_project.id,
                is_processed=True
            ),
            Document(
                filename="doc2.txt",
                unique_filename="unique_doc2.txt",
                file_type="text/plain",
                file_size=200,
                project_id=test_project.id,
                is_processed=False
            )
        ]
        
        for doc in documents:
            db_session.add(doc)
        db_session.commit()
        
        response = client.get(f"/upload/project/{test_project.id}/processing-status")
        assert response.status_code == 200
        
        result = response.json()
        assert result["project_id"] == test_project.id
        assert result["total_documents"] == 2
        assert result["processed_documents"] == 1
        assert result["processing_percentage"] == 50.0
        assert result["processing_complete"] == False
    
    def test_get_project_processing_status_nonexistent_project(self, client):
        """Test getting processing status for non-existent project."""
        response = client.get("/upload/project/99999/processing-status")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__])
