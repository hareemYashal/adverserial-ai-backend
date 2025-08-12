"""
Comprehensive CRUD tests for all API endpoints.
"""

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_crud_all.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestAllCRUDAPIs:
    """Comprehensive CRUD tests for all API endpoints."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Create a test client and database."""
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        with TestClient(app) as test_client:
            yield test_client
        
        # Clean up
        Base.metadata.drop_all(bind=engine)
        try:
            if os.path.exists("test_crud_all.db"):
                os.unlink("test_crud_all.db")
        except PermissionError:
            pass  # Ignore file locking issues on Windows
    
    # ==================== HEALTH ENDPOINTS ====================
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Adversarial AI Writing Assistant API"
        assert data["status"] == "running"
        assert "endpoints" in data
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_api_test_endpoint(self, client):
        """Test API test endpoint."""
        response = client.get("/api/test")
        assert response.status_code == 200
        data = response.json()
        assert "API is working!" in data["message"]
        assert data["framework"] == "FastAPI"
    
    # ==================== USERS CRUD TESTS ====================
    
    def test_users_crud_complete_workflow(self, client):
        """Test complete Users CRUD workflow."""
        
        # CREATE USER 1
        user1_data = {
            "username": "john_doe",
            "email": "john.doe@example.com",
            "password": "securePassword123"
        }
        response = client.post("/users/", json=user1_data)
        assert response.status_code == 201
        user1 = response.json()
        assert user1["username"] == "john_doe"
        assert user1["email"] == "john.doe@example.com"
        assert user1["is_active"] == True
        assert "id" in user1
        user1_id = user1["id"]
        
        # CREATE USER 2
        user2_data = {
            "username": "jane_smith",
            "email": "jane.smith@example.com",
            "password": "anotherPassword456"
        }
        response = client.post("/users/", json=user2_data)
        assert response.status_code == 201
        user2 = response.json()
        user2_id = user2["id"]
        
        # READ ALL USERS
        response = client.get("/users/")
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 2  # May have more from other tests
        assert any(u["username"] == "john_doe" for u in users)
        assert any(u["username"] == "jane_smith" for u in users)
        
        # READ USER BY ID
        response = client.get(f"/users/{user1_id}")
        assert response.status_code == 200
        user = response.json()
        assert user["username"] == "john_doe"
        assert user["id"] == user1_id
        
        # READ USER BY USERNAME
        response = client.get("/users/by-username/john_doe")
        assert response.status_code == 200
        user = response.json()
        assert user["id"] == user1_id
        
        # READ USER BY EMAIL
        response = client.get("/users/by-email/john.doe@example.com")
        assert response.status_code == 200
        user = response.json()
        assert user["id"] == user1_id
        
        # UPDATE USER
        update_data = {
            "username": "john_doe_updated",
            "email": "john.updated@example.com"
        }
        response = client.put(f"/users/{user1_id}", json=update_data)
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["username"] == "john_doe_updated"
        assert updated_user["email"] == "john.updated@example.com"
        
        # GET ACTIVE USERS COUNT
        response = client.get("/users/active/count")
        assert response.status_code == 200
        count_data = response.json()
        assert count_data["active_users_count"] == 2
        
        # DELETE USER
        response = client.delete(f"/users/{user2_id}")
        assert response.status_code == 204
        
        # VERIFY DELETION
        response = client.get(f"/users/{user2_id}")
        assert response.status_code == 404
        
        # VERIFY REMAINING USER COUNT  
        response = client.get("/users/")
        assert response.status_code == 200
        users = response.json()
        # Check that jane_smith was deleted and john_doe_updated exists
        assert not any(u["username"] == "jane_smith" for u in users)
        assert any(u["username"] == "john_doe_updated" for u in users)
        
        # Store user1_id for use in other tests
        self.user_id = user1_id
    
    def test_users_error_cases(self, client):
        """Test Users API error cases."""
        
        # Duplicate username
        user_data = {
            "username": "john_doe_updated",  # Already exists from previous test
            "email": "duplicate@example.com",
            "password": "password123"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
        
        # Non-existent user
        response = client.get("/users/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
        
        # Non-existent username
        response = client.get("/users/by-username/nonexistent")
        assert response.status_code == 404
    
    # ==================== PROJECTS CRUD TESTS ====================
    
    def test_projects_crud_complete_workflow(self, client):
        """Test complete Projects CRUD workflow."""
        
        # Get user ID from previous test
        response = client.get("/users/")
        users = response.json()
        user_id = users[0]["id"]
        
        # CREATE PROJECT 1
        project1_data = {
            "title": "AI Research Project",
            "description": "A comprehensive study on AI applications in education"
        }
        response = client.post(f"/projects/?user_id={user_id}", json=project1_data)
        assert response.status_code == 201
        project1 = response.json()
        assert project1["title"] == "AI Research Project"
        assert project1["user_id"] == user_id
        project1_id = project1["id"]
        
        # CREATE PROJECT 2
        project2_data = {
            "title": "Machine Learning Study",
            "description": "Analysis of ML algorithms and their performance"
        }
        response = client.post(f"/projects/?user_id={user_id}", json=project2_data)
        assert response.status_code == 201
        project2 = response.json()
        project2_id = project2["id"]
        
        # READ ALL PROJECTS
        response = client.get("/projects/")
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) == 2
        
        # READ PROJECTS BY USER
        response = client.get(f"/projects/user/{user_id}")
        assert response.status_code == 200
        user_projects = response.json()
        assert len(user_projects) == 2
        
        # READ PROJECT BY ID
        response = client.get(f"/projects/{project1_id}")
        assert response.status_code == 200
        project = response.json()
        assert project["title"] == "AI Research Project"
        
        # SEARCH PROJECTS BY TITLE
        response = client.get("/projects/search/AI")
        assert response.status_code == 200
        search_results = response.json()
        assert len(search_results) == 1
        assert search_results[0]["title"] == "AI Research Project"
        
        # UPDATE PROJECT
        update_data = {
            "title": "Advanced AI Research Project",
            "description": "Updated description with advanced topics"
        }
        response = client.put(f"/projects/{project1_id}", json=update_data)
        assert response.status_code == 200
        updated_project = response.json()
        assert updated_project["title"] == "Advanced AI Research Project"
        
        # GET USER PROJECT COUNT
        response = client.get(f"/projects/user/{user_id}/count")
        assert response.status_code == 200
        count_data = response.json()
        assert count_data["project_count"] == 2
        
        # DELETE PROJECT
        response = client.delete(f"/projects/{project2_id}")
        assert response.status_code == 204
        
        # VERIFY DELETION
        response = client.get(f"/projects/{project2_id}")
        assert response.status_code == 404
        
        # Store project1_id for use in other tests
        self.project_id = project1_id
    
    def test_projects_error_cases(self, client):
        """Test Projects API error cases."""
        
        # Non-existent user
        project_data = {
            "title": "Test Project",
            "description": "Test description"
        }
        response = client.post("/projects/?user_id=99999", json=project_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    # ==================== DOCUMENTS CRUD TESTS ====================
    
    def test_documents_crud_complete_workflow(self, client):
        """Test complete Documents CRUD workflow."""
        
        # Create a user and project for this test
        user_data = {
            "username": "doc_test_user",
            "email": "doctest@example.com", 
            "password": "docPassword123"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 201
        user = response.json()
        user_id = user["id"]
        
        # Create a project for documents
        project_data = {
            "title": "Document Test Project",
            "description": "A project for testing document operations"
        }
        response = client.post(f"/projects/?user_id={user_id}", json=project_data)
        assert response.status_code == 201
        project = response.json()
        project_id = project["id"]
        
        # CREATE DOCUMENT 1
        doc1_data = {
            "filename": "research_paper.txt",
            "content": "This is a comprehensive research paper about artificial intelligence and machine learning. The paper explores various algorithms, methodologies, and practical applications in modern technology.",
            "file_type": "text/plain",
            "project_id": project_id
        }
        response = client.post("/documents/", json=doc1_data)
        assert response.status_code == 201
        doc1 = response.json()
        assert doc1["filename"] == "research_paper.txt"
        assert doc1["project_id"] == project_id
        doc1_id = doc1["id"]
        
        # CREATE DOCUMENT 2
        doc2_data = {
            "filename": "methodology.pdf",
            "content": "Detailed methodology section covering research design, data collection, and analysis procedures.",
            "file_type": "application/pdf",
            "project_id": project_id
        }
        response = client.post("/documents/", json=doc2_data)
        assert response.status_code == 201
        doc2 = response.json()
        doc2_id = doc2["id"]
        
        # READ ALL DOCUMENTS
        response = client.get("/documents/")
        assert response.status_code == 200
        documents = response.json()
        assert len(documents) == 2
        
        # READ DOCUMENTS BY PROJECT
        response = client.get(f"/documents/project/{project_id}")
        assert response.status_code == 200
        project_docs = response.json()
        assert len(project_docs) == 2
        
        # READ DOCUMENT BY ID
        response = client.get(f"/documents/{doc1_id}")
        assert response.status_code == 200
        document = response.json()
        assert document["filename"] == "research_paper.txt"
        
        # FILTER BY FILE TYPE
        response = client.get("/documents/?file_type=text/plain")
        assert response.status_code == 200
        text_docs = response.json()
        assert len(text_docs) == 1
        assert text_docs[0]["file_type"] == "text/plain"
        
        # SEARCH BY FILENAME
        response = client.get("/documents/search/research")
        assert response.status_code == 200
        search_results = response.json()
        assert len(search_results) == 1
        assert "research" in search_results[0]["filename"].lower()
        
        # GET DOCUMENTS BY TYPE
        response = client.get("/documents/by-type/application/pdf")
        assert response.status_code == 200
        pdf_docs = response.json()
        assert len(pdf_docs) == 1
        assert pdf_docs[0]["file_type"] == "application/pdf"
        
        # UPDATE DOCUMENT
        update_data = {
            "filename": "updated_research_paper.txt",
            "content": "Updated content with new findings and conclusions from the research study."
        }
        response = client.put(f"/documents/{doc1_id}", json=update_data)
        assert response.status_code == 200
        updated_doc = response.json()
        assert updated_doc["filename"] == "updated_research_paper.txt"
        
        # GET PROJECT DOCUMENT COUNT
        response = client.get(f"/documents/project/{project_id}/count")
        assert response.status_code == 200
        count_data = response.json()
        assert count_data["document_count"] == 2
        
        # GET FILE TYPE STATISTICS
        response = client.get("/documents/stats/file-types")
        assert response.status_code == 200
        stats = response.json()
        assert len(stats) >= 1
        assert any(stat["file_type"] == "text/plain" for stat in stats)
        
        # DELETE DOCUMENT
        response = client.delete(f"/documents/{doc2_id}")
        assert response.status_code == 204
        
        # VERIFY DELETION
        response = client.get(f"/documents/{doc2_id}")
        assert response.status_code == 404
        
        # Store doc1_id for use in other tests
        self.doc_id = doc1_id
    
    def test_documents_error_cases(self, client):
        """Test Documents API error cases."""
        
        # Non-existent project
        doc_data = {
            "filename": "test.txt",
            "content": "test content",
            "file_type": "text/plain",
            "project_id": 99999
        }
        response = client.post("/documents/", json=doc_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    # ==================== PERSONAS CRUD TESTS ====================
    
    def test_personas_crud_complete_workflow(self, client):
        """Test complete Personas CRUD workflow."""
        
        # CREATE PERSONA 1 - Critical Academic Reviewer
        persona1_data = {
            "name": "Critical Academic Reviewer",
            "description": "A rigorous academic reviewer focused on methodology, evidence quality, and scholarly standards",
            "personality_traits": {
                "style": "critical",
                "tone": "analytical",
                "focus": "methodology",
                "expertise": "academic_writing",
                "approach": "systematic"
            },
            "system_prompt": "You are a critical academic reviewer with expertise in research methodology. Evaluate documents for logical consistency, evidence quality, citation accuracy, and adherence to academic standards."
        }
        response = client.post("/personas/", json=persona1_data)
        assert response.status_code == 201
        persona1 = response.json()
        assert persona1["name"] == "Critical Academic Reviewer"
        assert persona1["is_active"] == True
        persona1_id = persona1["id"]
        
        # CREATE PERSONA 2 - Utilitarian Philosopher
        persona2_data = {
            "name": "Utilitarian Philosopher",
            "description": "Evaluates writing from utilitarian ethics perspective, focusing on practical outcomes",
            "personality_traits": {
                "philosophy": "utilitarian",
                "tone": "practical",
                "focus": "outcomes",
                "approach": "consequentialist"
            },
            "system_prompt": "You are a utilitarian philosopher. Evaluate this writing based on practical utility, potential positive outcomes, and the principle of greatest good for the greatest number."
        }
        response = client.post("/personas/", json=persona2_data)
        assert response.status_code == 201
        persona2 = response.json()
        persona2_id = persona2["id"]
        
        # CREATE PERSONA 3 - Kantian Ethicist
        persona3_data = {
            "name": "Kantian Ethicist",
            "description": "Provides critique based on Kantian deontological ethics and categorical imperatives",
            "personality_traits": {
                "philosophy": "kantian",
                "tone": "principled",
                "focus": "duty_ethics",
                "approach": "deontological"
            },
            "system_prompt": "You are a Kantian ethicist. Evaluate this writing through the lens of deontological ethics, categorical imperatives, and universal moral principles."
        }
        response = client.post("/personas/", json=persona3_data)
        assert response.status_code == 201
        persona3 = response.json()
        persona3_id = persona3["id"]
        
        # READ ALL PERSONAS
        response = client.get("/personas/")
        assert response.status_code == 200
        personas = response.json()
        assert len(personas) == 3
        
        # READ ACTIVE PERSONAS ONLY
        response = client.get("/personas/?active_only=true")
        assert response.status_code == 200
        active_personas = response.json()
        assert len(active_personas) == 3
        
        # READ PERSONA BY ID
        response = client.get(f"/personas/{persona1_id}")
        assert response.status_code == 200
        persona = response.json()
        assert persona["name"] == "Critical Academic Reviewer"
        
        # SEARCH BY NAME
        response = client.get("/personas/by-name/Critical")
        assert response.status_code == 200
        search_results = response.json()
        assert len(search_results) == 1
        assert "Critical" in search_results[0]["name"]
        
        # SEARCH BY PERSONALITY TRAITS
        response = client.get("/personas/search/traits?trait_key=philosophy&trait_value=utilitarian")
        assert response.status_code == 200
        trait_results = response.json()
        assert len(trait_results) == 1
        assert trait_results[0]["name"] == "Utilitarian Philosopher"
        
        # UPDATE PERSONA
        update_data = {
            "name": "Enhanced Critical Academic Reviewer",
            "description": "An enhanced version with focus on interdisciplinary analysis",
            "personality_traits": {
                "style": "critical",
                "tone": "analytical",
                "focus": "methodology",
                "expertise": "interdisciplinary_analysis",
                "approach": "systematic"
            }
        }
        response = client.put(f"/personas/{persona1_id}", json=update_data)
        assert response.status_code == 200
        updated_persona = response.json()
        assert updated_persona["name"] == "Enhanced Critical Academic Reviewer"
        
        # DEACTIVATE PERSONA
        response = client.patch(f"/personas/{persona3_id}/deactivate")
        assert response.status_code == 200
        deactivated_persona = response.json()
        assert deactivated_persona["is_active"] == False
        
        # ACTIVATE PERSONA
        response = client.patch(f"/personas/{persona3_id}/activate")
        assert response.status_code == 200
        activated_persona = response.json()
        assert activated_persona["is_active"] == True
        
        # GET ACTIVE PERSONAS
        response = client.get("/personas/active")
        assert response.status_code == 200
        active_personas = response.json()
        assert len(active_personas) == 3
        
        # GET STATUS STATISTICS
        response = client.get("/personas/stats/status")
        assert response.status_code == 200
        stats = response.json()
        assert len(stats) >= 1
        active_count = next((s["count"] for s in stats if s["is_active"]), 0)
        assert active_count == 3
        
        # DELETE PERSONA
        response = client.delete(f"/personas/{persona2_id}")
        assert response.status_code == 204
        
        # VERIFY DELETION
        response = client.get(f"/personas/{persona2_id}")
        assert response.status_code == 404
        
        # VERIFY REMAINING PERSONA COUNT
        response = client.get("/personas/")
        assert response.status_code == 200
        personas = response.json()
        assert len(personas) == 2
        
        # Store persona IDs for use in other tests
        self.persona1_id = persona1_id
        self.persona3_id = persona3_id
    
    def test_personas_error_cases(self, client):
        """Test Personas API error cases."""
        
        # First create a persona to test duplicate
        persona_data = {
            "name": "Test Duplicate Persona",
            "description": "Original persona",
            "personality_traits": {"test": "original"},
            "system_prompt": "Original prompt"
        }
        response = client.post("/personas/", json=persona_data)
        assert response.status_code == 201
        
        # Now try to create duplicate
        duplicate_persona_data = {
            "name": "Test Duplicate Persona",  # Same name as above
            "description": "Duplicate persona",
            "personality_traits": {"test": "value"},
            "system_prompt": "Test prompt"
        }
        response = client.post("/personas/", json=duplicate_persona_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    # ==================== INTEGRATION TESTS ====================
    
    def test_complete_workflow_integration(self, client):
        """Test complete workflow integration across all entities."""
        
        # Create fresh test data for integration
        # CREATE USER
        user_data = {
            "username": "integration_user",
            "email": "integration@example.com",
            "password": "integrationPassword123"
        }
        response = client.post("/users/", json=user_data)
        assert response.status_code == 201
        user = response.json()
        user_id = user["id"]
        
        # CREATE PROJECT
        project_data = {
            "title": "Integration Test Project",
            "description": "A project for testing integration"
        }
        response = client.post(f"/projects/?user_id={user_id}", json=project_data)
        assert response.status_code == 201
        project = response.json()
        project_id = project["id"]
        
        # CREATE DOCUMENT
        doc_data = {
            "filename": "integration_doc.txt",
            "content": "This is an integration test document.",
            "file_type": "text/plain",
            "project_id": project_id
        }
        response = client.post("/documents/", json=doc_data)
        assert response.status_code == 201
        document = response.json()
        
        # CREATE PERSONA
        persona_data = {
            "name": "Integration Test Persona",
            "description": "A persona for integration testing",
            "personality_traits": {"test": "integration"},
            "system_prompt": "Integration test prompt"
        }
        response = client.post("/personas/", json=persona_data)
        assert response.status_code == 201
        persona = response.json()
        
        # VERIFY INTEGRATION
        assert user["username"] == "integration_user"
        assert project["user_id"] == user_id
        assert document["project_id"] == project_id
        assert persona["name"] == "Integration Test Persona"
        
        print("\\n✅ All CRUD operations completed successfully!")
        print(f"📊 Integration test: user {user_id}, project {project_id}, document {document['id']}, persona {persona['id']}")
    
    # ==================== PAGINATION AND FILTERING TESTS ====================
    
    def test_pagination_and_filtering(self, client):
        """Test pagination and filtering across endpoints."""
        
        # Test Users pagination
        response = client.get("/users/?skip=0&limit=1")
        assert response.status_code == 200
        users_page = response.json()
        assert len(users_page) <= 1
        
        # Test Projects pagination with user filter
        users = client.get("/users/").json()
        user_id = users[0]["id"]
        response = client.get(f"/projects/?user_id={user_id}&skip=0&limit=10")
        assert response.status_code == 200
        
        # Test Documents filtering by project and file type
        projects = client.get("/projects/").json()
        project_id = projects[0]["id"]
        response = client.get(f"/documents/?project_id={project_id}&file_type=text/plain")
        assert response.status_code == 200
        filtered_docs = response.json()
        for doc in filtered_docs:
            assert doc["project_id"] == project_id
            assert doc["file_type"] == "text/plain"
        
        # Test Personas filtering
        response = client.get("/personas/?active_only=true&skip=0&limit=5")
        assert response.status_code == 200
        active_personas = response.json()
        for persona in active_personas:
            assert persona["is_active"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
