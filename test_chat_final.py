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
    
    # Message 1: Analyze 3 documents
    print("\n=== Message 1: Analyze These 3 Documents ===")
    chat_data = {
        "project_id": 4,
        "question": "analyze these 3 documents",
        "persona": "Kantian",
        "session_id": "ec2ca97c-c9be-4cf5-83e7-eccc7bd7862f",
        "document_id": "59,60,61"
    }
    
    response = requests.post(f"{BASE_URL}/api/chat", data=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Message 2: Get 5 references from each
    print("\n=== Message 2: Give Me Only 5 References From Each ===")
    chat_data["question"] = "give me only 5 references from each"
    
    response = requests.post(f"{BASE_URL}/api/chat", data=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Message 3: Authors ideology
    print("\n=== Message 3: Authors Ideology ===")
    chat_data["question"] = "3ono documents kay authors ki ideology batao"
    
    response = requests.post(f"{BASE_URL}/api/chat", data=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    main()