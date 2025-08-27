from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)  # Original filename
    unique_filename = Column(String)  # Unique filename in storage
    content = Column(Text)  # Extracted text content
    file_path = Column(String)  # Path to uploaded file
    file_type = Column(String)  # MIME type
    file_size = Column(Integer)  # Size in bytes
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    session_id =Column(String)
    # Processing status
    is_processed = Column(Boolean, default=False)  # Whether text extraction is complete
    processing_error = Column(Text)  # Store any processing errors
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', project_id={self.project_id}, is_processed={self.is_processed})>"