"""
Test /api/chat endpoint with 3 messages
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def main():
    # Just login
    user_data = {
        "username": "testuser111",
        "password": "test123"
    }
    
    print("Logging in...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json=user_data)
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful!")
    
    # Skip project/document creation - use existing ones
    user_id = 1  # Assume user ID 1
    print("✅ Using existing project and document!")
    
    # Message 1: Analyze these 2 documents
    print("\n=== Message 1: Analyze These 2 Documents ===")
    chat_data = {
        "project_id": 4,
        "question": "analyze these 2 documents and compare them",
        "persona": "Logical Positivist",
        "session_id": "a01e1973-fef6-4c38-a62e-c3389082a4f2",
        "document_id": "66,60"  # Two documents
    }
    
    response = requests.post(f"{BASE_URL}/api/chat", data=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Message 2: Who are the authors
    print("\n=== Message 2: Who Are The Authors ===")
    chat_data["question"] = "who are the authors of these documents?"
    
    response = requests.post(f"{BASE_URL}/api/chat", data=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Message 3: Extract references from both
    print("\n=== Message 3: Extract References From Both ===")
    chat_data["question"] = "extract references from both documents separately"
    
    response = requests.post(f"{BASE_URL}/api/chat", data=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    main()