"""
Test /api/persona-chat/simple endpoint with Imran Khan persona
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def main():
    # Login
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
    
    # Message 1: Analyze these 3 documents
    print("\n=== Message 1: Analyze These 3 Documents ===")
    
    chat_data = {
        "project_id": 4,
        "question": "Analyze these 3 documents",
        "persona": "Imran Khaan",
        "persona_description": "Imraan Khan president of pakistan",
        "session_id": "fa8cc176-a073-4e2d-bf94-24c3ba41327c",
        "document_ids": "59,60,61"
    }
    
    response = requests.post(f"{BASE_URL}/api/persona-chat/simple", data=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Message 2: Give me references from all 3 documents
    print("\n=== Message 2: Give Me References From All 3 Documents ===")
    
    chat_data["question"] = "Give me references from all 3 documents"
    
    response = requests.post(f"{BASE_URL}/api/persona-chat/simple", data=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    main()