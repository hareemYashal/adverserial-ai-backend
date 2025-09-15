import yaml

from pathlib import Path
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.persona import Persona  # assumes your SQLAlchemy model is named Persona
from app.database import get_db

class PersonaService:
    def __init__(self, persona_file: str = "app/personas.yaml"):
        self.persona_file = Path(persona_file)
        self.personas = self._load_personas()

    def _load_personas(self) -> List[Dict]:
        if not self.persona_file.exists():
            raise FileNotFoundError(f"Persona file not found: {self.persona_file}")
        with open(self.persona_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_all(self) -> List[Dict]:
        return self.personas

    def get_by_name(self, name: str, db: Optional[Session] = None) -> Dict:
        # 1. Try to get from DB (dynamic personas)
        if db is None:
            try:
                db = next(get_db())
            except Exception:
                db = None
        if db:
            persona_obj = db.query(Persona).filter(Persona.name.ilike(name)).first()
            if persona_obj:
                # Convert SQLAlchemy object to dict with at least 'name' and 'system_prompt'
                return {
                    "name": persona_obj.name,
                    "system_prompt": persona_obj.system_prompt
                }
        # 2. Fallback to static YAML
        for p in self.personas:
            if p["name"].lower() == name.lower():
                return p
        return None

persona_service = PersonaService()
