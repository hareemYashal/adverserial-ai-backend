from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectResponse, ProjectCreate, ProjectUpdate, ProjectWithDocuments

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Project not found"}},
)

@router.get("/", response_model=List[ProjectResponse], summary="Get all projects")
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve all projects with optional filtering by user.
    
    - **skip**: Number of projects to skip (for pagination)
    - **limit**: Maximum number of projects to return
    - **user_id**: Filter projects by user ID (optional)
    """
    query = db.query(Project)
    if user_id:
        query = query.filter(Project.user_id == user_id)
    
    projects = query.offset(skip).limit(limit).all()
    return projects

@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project by ID")
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific project by its ID.
    
    - **project_id**: The ID of the project to retrieve
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    return project

@router.get("/{project_id}/with-documents", response_model=ProjectWithDocuments, summary="Get project with documents")
async def get_project_with_documents(project_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a project with all its associated documents.
    
    - **project_id**: The ID of the project to retrieve
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    return project

@router.get("/user/{user_id}", response_model=List[ProjectResponse], summary="Get projects by user")
async def get_projects_by_user(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all projects for a specific user.
    
    - **user_id**: The ID of the user whose projects to retrieve
    - **skip**: Number of projects to skip (for pagination)
    - **limit**: Maximum number of projects to return
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    projects = db.query(Project).filter(Project.user_id == user_id).offset(skip).limit(limit).all()
    return projects

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create new project")
async def create_project(project: ProjectCreate, user_id: int, db: Session = Depends(get_db)):
    """
    Create a new project for a user.
    
    - **project**: Project data to create
    - **user_id**: The ID of the user who will own the project
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    db_project = Project(
        title=project.title,
        description=project.description,
        user_id=user_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.put("/{project_id}", response_model=ProjectResponse, summary="Update project")
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing project.
    
    - **project_id**: The ID of the project to update
    - **project_update**: Updated project data
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    # Update fields if provided
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete project")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """
    Delete a project and all its associated documents.
    
    - **project_id**: The ID of the project to delete
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    
    db.delete(db_project)
    db.commit()
    return None

@router.get("/search/{title}", response_model=List[ProjectResponse], summary="Search projects by title")
async def search_projects_by_title(
    title: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Search projects by title (case-insensitive partial match).
    
    - **title**: Title to search for
    - **skip**: Number of projects to skip (for pagination)
    - **limit**: Maximum number of projects to return
    """
    projects = db.query(Project).filter(
        Project.title.ilike(f"%{title}%")
    ).offset(skip).limit(limit).all()
    return projects

@router.get("/user/{user_id}/count", summary="Get project count for user")
async def get_user_project_count(user_id: int, db: Session = Depends(get_db)):
    """
    Get the count of projects for a specific user.
    
    - **user_id**: The ID of the user
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    count = db.query(Project).filter(Project.user_id == user_id).count()
    return {"user_id": user_id, "project_count": count} 