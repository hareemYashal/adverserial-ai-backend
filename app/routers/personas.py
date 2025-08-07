from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.persona import Persona
from app.schemas.persona import PersonaResponse, PersonaCreate, PersonaUpdate

router = APIRouter(
    prefix="/personas",
    tags=["personas"],
    responses={404: {"description": "Persona not found"}},
)

@router.get("/", response_model=List[PersonaResponse], summary="Get all personas")
async def get_personas(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Retrieve all personas with optional filtering.
    
    - **skip**: Number of personas to skip (for pagination)
    - **limit**: Maximum number of personas to return
    - **active_only**: Filter to only active personas (optional)
    """
    query = db.query(Persona)
    if active_only:
        query = query.filter(Persona.is_active == True)
    
    personas = query.offset(skip).limit(limit).all()
    return personas

@router.get("/{persona_id}", response_model=PersonaResponse, summary="Get persona by ID")
async def get_persona(persona_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific persona by its ID.
    
    - **persona_id**: The ID of the persona to retrieve
    """
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona with ID {persona_id} not found"
        )
    return persona

@router.get("/by-name/{name}", response_model=List[PersonaResponse], summary="Get personas by name")
async def get_personas_by_name(
    name: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve personas by name (case-insensitive partial match).
    
    - **name**: Name to search for
    - **skip**: Number of personas to skip (for pagination)
    - **limit**: Maximum number of personas to return
    """
    personas = db.query(Persona).filter(
        Persona.name.ilike(f"%{name}%")
    ).offset(skip).limit(limit).all()
    return personas

@router.post("/", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED, summary="Create new persona")
async def create_persona(persona: PersonaCreate, db: Session = Depends(get_db)):
    """
    Create a new AI persona.
    
    - **persona**: Persona data to create
    """
    # Check if persona name already exists
    existing_persona = db.query(Persona).filter(Persona.name == persona.name).first()
    if existing_persona:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Persona with this name already exists"
        )
    
    db_persona = Persona(
        name=persona.name,
        description=persona.description,
        personality_traits=persona.personality_traits,
        system_prompt=persona.system_prompt
    )
    db.add(db_persona)
    db.commit()
    db.refresh(db_persona)
    return db_persona

@router.put("/{persona_id}", response_model=PersonaResponse, summary="Update persona")
async def update_persona(
    persona_id: int,
    persona_update: PersonaUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing persona.
    
    - **persona_id**: The ID of the persona to update
    - **persona_update**: Updated persona data
    """
    db_persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if db_persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona with ID {persona_id} not found"
        )
    
    # Update fields if provided
    update_data = persona_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_persona, field, value)
    
    db.commit()
    db.refresh(db_persona)
    return db_persona

@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete persona")
async def delete_persona(persona_id: int, db: Session = Depends(get_db)):
    """
    Delete a persona.
    
    - **persona_id**: The ID of the persona to delete
    """
    db_persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if db_persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona with ID {persona_id} not found"
        )
    
    db.delete(db_persona)
    db.commit()
    return None

@router.patch("/{persona_id}/activate", response_model=PersonaResponse, summary="Activate persona")
async def activate_persona(persona_id: int, db: Session = Depends(get_db)):
    """
    Activate a persona (set is_active to True).
    
    - **persona_id**: The ID of the persona to activate
    """
    db_persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if db_persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona with ID {persona_id} not found"
        )
    
    db_persona.is_active = True
    db.commit()
    db.refresh(db_persona)
    return db_persona

@router.patch("/{persona_id}/deactivate", response_model=PersonaResponse, summary="Deactivate persona")
async def deactivate_persona(persona_id: int, db: Session = Depends(get_db)):
    """
    Deactivate a persona (set is_active to False).
    
    - **persona_id**: The ID of the persona to deactivate
    """
    db_persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if db_persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona with ID {persona_id} not found"
        )
    
    db_persona.is_active = False
    db.commit()
    db.refresh(db_persona)
    return db_persona

@router.get("/active", response_model=List[PersonaResponse], summary="Get active personas")
async def get_active_personas(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all active personas.
    
    - **skip**: Number of personas to skip (for pagination)
    - **limit**: Maximum number of personas to return
    """
    personas = db.query(Persona).filter(Persona.is_active == True).offset(skip).limit(limit).all()
    return personas

@router.get("/stats/status", summary="Get persona statistics by status")
async def get_persona_stats_by_status(db: Session = Depends(get_db)):
    """
    Get statistics about personas grouped by active status.
    """
    from sqlalchemy import func
    
    stats = db.query(
        Persona.is_active,
        func.count(Persona.id).label('count')
    ).group_by(Persona.is_active).all()
    
    return [
        {"is_active": stat.is_active, "count": stat.count}
        for stat in stats
    ]

@router.get("/search/traits", response_model=List[PersonaResponse], summary="Search personas by personality traits")
async def search_personas_by_traits(
    trait_key: str,
    trait_value: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Search personas by personality traits.
    
    - **trait_key**: The trait key to search for
    - **trait_value**: The trait value to search for
    - **skip**: Number of personas to skip (for pagination)
    - **limit**: Maximum number of personas to return
    """
    # This is a simplified search - in a real implementation, you might want more sophisticated JSON querying
    personas = db.query(Persona).filter(
        Persona.personality_traits.contains({trait_key: trait_value})
    ).offset(skip).limit(limit).all()
    return personas 