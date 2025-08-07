from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.models import User, Project, Document, Persona
from app.routers import users_router, projects_router, documents_router, personas_router

# Create FastAPI app
app = FastAPI(
    title="Adversarial AI Writing Assistant",
    description="A FastAPI-based backend for multi-persona document analysis and critique",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
@app.on_event("startup")
async def startup():
    """Initialize database tables on startup"""
    Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(personas_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Adversarial AI Writing Assistant API", 
        "status": "running",
        "framework": "FastAPI",
        "endpoints": {
            "users": "/users",
            "projects": "/projects", 
            "documents": "/documents",
            "personas": "/personas",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {
        "message": "API is working!", 
        "python_version": "3.13",
        "framework": "FastAPI"
    }