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
    
    # Test questions from logs
    test_questions = [
        {
            "project_id": 4,
            "question": "Tell me about these two documents",
            "persona": "Kantian",
            "session_id": "5a065dca-20da-43db-b1d4-14a8e7edc08a",
            "document_id": "83,84"
        },
        {
            "project_id": 4,
            "question": "just answer with a 'Yes' or 'No'. have I uploaded 2 documents for you to review?",
            "persona": "Kantian",
            "session_id": "5a065dca-20da-43db-b1d4-14a8e7edc08a",
            "document_id": "83,84"
        },
        {
            "project_id": 4,
            "question": "just a 'Yes' or 'No'.",
            "persona": "Kantian",
            "session_id": "5a065dca-20da-43db-b1d4-14a8e7edc08a",
            "document_id": "83,84"
        },
        {
            "project_id": 4,
            "question": "so, you're saying I haven't uploaded the documents?",
            "persona": "Kantian",
            "session_id": "5a065dca-20da-43db-b1d4-14a8e7edc08a",
            "document_id": "83,84"
        }
    ]
    
    for i, chat_data in enumerate(test_questions, 1):
        print(f"\n=== Test {i}: {chat_data['question'][:50]}... ===")
        
        response = requests.post(f"{BASE_URL}/api/chat", data=chat_data, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Answer length: {len(result.get('answer', ''))} chars")
            print(f"📋 Document IDs: {result.get('document_ids', [])}")
            print(f"🔍 Sources: {len(result.get('sources', []))}")
            answer = result.get('answer', 'No answer')
            print(f"💬 Answer: {answer[:200]}..." if len(answer) > 200 else answer)
        else:
            print(f"❌ Error: {response.text}")
        
        print("-" * 60)

if __name__ == "__main__":
    main()