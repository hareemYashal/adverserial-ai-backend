import yaml
from pathlib import Path
from typing import List, Dict

class Multi_PersonaService:
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

    def get_by_name(self, name: str) -> Dict:
        for p in self.personas:
            if p["name"].lower() == name.lower():
                return p
        return None

multi_persona_services = Multi_PersonaService()
