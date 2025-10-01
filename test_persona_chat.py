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
    
    # Message 1: Who are the authors of these 2 documents
    print("\n=== Message 1: Who Are The Authors Of These 2 Documents ===")
    
    chat_data = {
        "project_id": 4,
        "question": "who are the authors of these documents",
        "persona": "Elon Musk",
        "persona_description": "Elon Musk",
        "session_id": "f9c1dbfd-3849-4fd8-902a-b95978f21a19",
        "document_ids": "69,60"  # Two documents
    }
    
    response = requests.post(f"{BASE_URL}/api/persona-chat/simple", data=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Message 2: Analyze these 2 documents
    print("\n=== Message 2: Analyze These 2 Documents ===")
    
    chat_data["question"] = "analyze these 2 documents from your perspective and compare them"
    
    response = requests.post(f"{BASE_URL}/api/persona-chat/simple", data=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Message 3: What do you think about both
    print("\n=== Message 3: What Do You Think About Both ===")
    
    chat_data["question"] = "what do you think about the ideas in both documents?"
    
    response = requests.post(f"{BASE_URL}/api/persona-chat/simple", data=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    main()