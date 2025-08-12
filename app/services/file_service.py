"""
File handling service for document upload, storage, and text extraction.
"""

import os
import uuid
import shutil
import mimetypes
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from fastapi import UploadFile, HTTPException, status
import logging

# Optional imports for file handling
try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    print("⚠️  aiofiles not available. File upload will be limited.")

try:
    from PyPDF2 import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("⚠️  PyPDF2 not available. PDF processing disabled.")

try:
    from docx import Document as DocxDocument
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False
    print("⚠️  python-docx not available. DOCX processing disabled.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileService:
    """Service for handling file operations, storage, and text extraction."""
    
    def __init__(self, upload_dir: str = "uploads"):
        """Initialize FileService with upload directory."""
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for organization
        self.document_dir = self.upload_dir / "documents"
        self.temp_dir = self.upload_dir / "temp"
        
        self.document_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Supported file types
        self.supported_types = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'text/plain': '.txt',
            'text/markdown': '.md',
            'application/rtf': '.rtf'
        }
        
        # Maximum file size (10MB)
        self.max_file_size = 10 * 1024 * 1024
    
    def validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file type and size."""
        # Check file size
        if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Seek back to beginning
            
            if file_size > self.max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size {file_size} exceeds maximum size {self.max_file_size} bytes"
                )
        
        # Check file type
        content_type = file.content_type
        if content_type not in self.supported_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {content_type} not supported. Supported types: {list(self.supported_types.keys())}"
            )
    
    async def save_file(self, file: UploadFile, project_id: int) -> Dict[str, Any]:
        """Save uploaded file to storage and return file metadata."""
        if not AIOFILES_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="File upload not available. Please install aiofiles: pip install aiofiles"
            )
        
        self.validate_file(file)
        
        # Generate unique filename
        file_extension = self.supported_types.get(file.content_type, '')
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create project subdirectory
        project_dir = self.document_dir / str(project_id)
        project_dir.mkdir(exist_ok=True)
        
        file_path = project_dir / unique_filename
        
        try:
            # Save file
            async with aiofiles.open(file_path, 'wb') as buffer:
                content = await file.read()
                await buffer.write(content)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            logger.info(f"File saved: {file_path} ({file_size} bytes)")
            
            return {
                'filename': file.filename,
                'file_path': str(file_path),
                'file_type': file.content_type,
                'file_size': file_size,
                'unique_filename': unique_filename
            }
            
        except Exception as e:
            # Clean up file if save failed
            if file_path.exists():
                file_path.unlink()
            logger.error(f"Failed to save file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text content from supported file types."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        try:
            if file_type == 'application/pdf':
                return self._extract_pdf_text(file_path)
            elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return self._extract_docx_text(file_path)
            elif file_type in ['text/plain', 'text/markdown']:
                return self._extract_text_file(file_path)
            else:
                logger.warning(f"Text extraction not implemented for {file_type}")
                return ""
                
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Text extraction failed: {str(e)}"
            )
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        if not PDF_SUPPORT:
            raise Exception("PDF processing not available. Please install PyPDF2: pip install PyPDF2")
        
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        except Exception as e:
            raise Exception(f"PDF extraction error: {str(e)}")
        
        return text.strip()
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX file."""
        if not DOCX_SUPPORT:
            raise Exception("DOCX processing not available. Please install python-docx: pip install python-docx")
        
        try:
            doc = DocxDocument(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"DOCX extraction error: {str(e)}")
    
    def _extract_text_file(self, file_path: Path) -> str:
        """Extract text from plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read().strip()
        except Exception as e:
            raise Exception(f"Text file extraction error: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from storage."""
        try:
            file_path = Path(file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information and metadata."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            return {
                'filename': file_path.name,
                'file_path': str(file_path),
                'file_type': mime_type,
                'file_size': stat.st_size,
                'created_at': stat.st_ctime,
                'modified_at': stat.st_mtime
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {str(e)}")
            return None
    
    def cleanup_temp_files(self) -> int:
        """Clean up temporary files older than 1 hour."""
        import time
        cleaned_count = 0
        current_time = time.time()
        one_hour_ago = current_time - 3600  # 1 hour in seconds
        
        try:
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < one_hour_ago:
                    file_path.unlink()
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} temporary files")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
        
        return cleaned_count


# Create global instance
file_service = FileService()
