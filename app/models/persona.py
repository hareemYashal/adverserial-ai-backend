from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Persona(Base):
    __tablename__ = "personas"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    personality_traits = Column(JSON)  # Store traits as JSON object
    system_prompt = Column(Text)  # AI system prompt for this persona
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for default personas
    is_default = Column(Boolean, default=False)  # True for system default personas
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="personas")
    
    def __repr__(self):
        return f"<Persona(id={self.id}, name='{self.name}')>"