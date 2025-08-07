#!/usr/bin/env python3
"""Minimal FastAPI test to check compatibility"""

print("Testing imports...")

try:
    from fastapi import FastAPI
    print("✅ FastAPI imported successfully")
except Exception as e:
    print(f"❌ FastAPI import failed: {e}")
    exit(1)

try:
    from pydantic import BaseModel
    print("✅ Pydantic imported successfully")
except Exception as e:
    print(f"❌ Pydantic import failed: {e}")
    exit(1)

# Create minimal app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

print("✅ Minimal FastAPI app created successfully")
print("🚀 Run with: uvicorn test_minimal:app --reload")