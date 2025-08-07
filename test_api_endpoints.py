#!/usr/bin/env python3
"""
Test script to verify all API endpoints are working correctly
"""
import sys
import os
import requests
import json
from typing import Dict, Any

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_api_endpoints():
    """Test all API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing API Endpoints")
    print("=" * 50)
    
    # Test root endpoint
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint: {data}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test health endpoint
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint: {data}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Test users endpoints
    print("\n3. Testing users endpoints...")
    try:
        # Get all users
        response = requests.get(f"{base_url}/users/")
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Get users: {len(users)} users found")
        else:
            print(f"❌ Get users failed: {response.status_code}")
        
        # Get active users count
        response = requests.get(f"{base_url}/users/active/count")
        if response.status_code == 200:
            count_data = response.json()
            print(f"✅ Active users count: {count_data}")
        else:
            print(f"❌ Active users count failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Users endpoints error: {e}")
    
    # Test projects endpoints
    print("\n4. Testing projects endpoints...")
    try:
        # Get all projects
        response = requests.get(f"{base_url}/projects/")
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Get projects: {len(projects)} projects found")
        else:
            print(f"❌ Get projects failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Projects endpoints error: {e}")
    
    # Test documents endpoints
    print("\n5. Testing documents endpoints...")
    try:
        # Get all documents
        response = requests.get(f"{base_url}/documents/")
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ Get documents: {len(documents)} documents found")
        else:
            print(f"❌ Get documents failed: {response.status_code}")
        
        # Get document stats
        response = requests.get(f"{base_url}/documents/stats/file-types")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Document stats: {stats}")
        else:
            print(f"❌ Document stats failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Documents endpoints error: {e}")
    
    # Test personas endpoints
    print("\n6. Testing personas endpoints...")
    try:
        # Get all personas
        response = requests.get(f"{base_url}/personas/")
        if response.status_code == 200:
            personas = response.json()
            print(f"✅ Get personas: {len(personas)} personas found")
        else:
            print(f"❌ Get personas failed: {response.status_code}")
        
        # Get active personas
        response = requests.get(f"{base_url}/personas/active")
        if response.status_code == 200:
            active_personas = response.json()
            print(f"✅ Active personas: {len(active_personas)} active personas found")
        else:
            print(f"❌ Active personas failed: {response.status_code}")
        
        # Get persona stats
        response = requests.get(f"{base_url}/personas/stats/status")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Persona stats: {stats}")
        else:
            print(f"❌ Persona stats failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Personas endpoints error: {e}")
    
    # Test API documentation
    print("\n7. Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ API documentation accessible")
        else:
            print(f"❌ API documentation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API documentation error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API endpoint testing completed!")
    print(f"📖 Visit http://localhost:8000/docs for interactive API documentation")

def test_sample_data_creation():
    """Test creating sample data through the API"""
    base_url = "http://localhost:8000"
    
    print("\n🧪 Testing Sample Data Creation")
    print("=" * 50)
    
    # Create a test user
    print("\n1. Creating test user...")
    try:
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        response = requests.post(f"{base_url}/users/", json=user_data)
        if response.status_code == 201:
            user = response.json()
            print(f"✅ Created user: {user['username']} (ID: {user['id']})")
            user_id = user['id']
        else:
            print(f"❌ Failed to create user: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ User creation error: {e}")
        return
    
    # Create a test project
    print("\n2. Creating test project...")
    try:
        project_data = {
            "title": "Test Project",
            "description": "A test project for API verification"
        }
        response = requests.post(f"{base_url}/projects/?user_id={user_id}", json=project_data)
        if response.status_code == 201:
            project = response.json()
            print(f"✅ Created project: {project['title']} (ID: {project['id']})")
            project_id = project['id']
        else:
            print(f"❌ Failed to create project: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Project creation error: {e}")
        return
    
    # Create a test document
    print("\n3. Creating test document...")
    try:
        document_data = {
            "filename": "test_document.txt",
            "content": "This is a test document content for API verification.",
            "file_type": "text/plain",
            "project_id": project_id
        }
        response = requests.post(f"{base_url}/documents/", json=document_data)
        if response.status_code == 201:
            document = response.json()
            print(f"✅ Created document: {document['filename']} (ID: {document['id']})")
            document_id = document['id']
        else:
            print(f"❌ Failed to create document: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Document creation error: {e}")
        return
    
    # Create a test persona
    print("\n4. Creating test persona...")
    try:
        persona_data = {
            "name": "Test Critic",
            "description": "A test persona for adversarial writing critique",
            "personality_traits": {
                "style": "critical",
                "tone": "analytical",
                "focus": "clarity"
            },
            "system_prompt": "You are a critical reviewer focused on improving writing clarity and structure."
        }
        response = requests.post(f"{base_url}/personas/", json=persona_data)
        if response.status_code == 201:
            persona = response.json()
            print(f"✅ Created persona: {persona['name']} (ID: {persona['id']})")
            persona_id = persona['id']
        else:
            print(f"❌ Failed to create persona: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Persona creation error: {e}")
        return
    
    print("\n✅ Sample data creation completed successfully!")
    print(f"📊 Created: User (ID: {user_id}), Project (ID: {project_id}), Document (ID: {document_id}), Persona (ID: {persona_id})")

def main():
    """Run all API tests"""
    print("🚀 Starting API Endpoint Testing")
    print("=" * 50)
    
    # Test basic endpoints
    test_api_endpoints()
    
    # Test data creation
    test_sample_data_creation()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("📖 Visit http://localhost:8000/docs for interactive API documentation")

if __name__ == "__main__":
    main() 