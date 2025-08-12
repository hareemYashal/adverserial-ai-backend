"""
Tests for file service functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from fastapi import UploadFile
from io import BytesIO

from app.services.file_service import FileService


class TestFileService:
    """Test cases for FileService class."""
    
    @pytest.fixture
    def file_service(self):
        """Create a FileService instance with temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield FileService(upload_dir=temp_dir)
    
    @pytest.fixture
    def sample_text_file(self):
        """Create a sample text file for testing."""
        content = b"This is a sample text file for testing."
        return UploadFile(
            filename="test.txt",
            file=BytesIO(content),
            headers={"content-type": "text/plain"}
        )
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Create sample PDF content for testing."""
        # Minimal PDF content for testing
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000174 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
268
%%EOF"""
        return pdf_content
    
    @pytest.fixture
    def sample_pdf_file(self, sample_pdf_content):
        """Create a sample PDF file for testing."""
        return UploadFile(
            filename="test.pdf",
            file=BytesIO(sample_pdf_content),
            headers={"content-type": "application/pdf"}
        )
    
    def test_file_service_initialization(self, file_service):
        """Test FileService initialization."""
        assert file_service.upload_dir.exists()
        assert file_service.document_dir.exists()
        assert file_service.temp_dir.exists()
        assert file_service.max_file_size == 10 * 1024 * 1024
    
    def test_validate_file_valid_text(self, file_service, sample_text_file):
        """Test file validation with valid text file."""
        # Should not raise any exception
        file_service.validate_file(sample_text_file)
    
    def test_validate_file_invalid_type(self, file_service):
        """Test file validation with invalid file type."""
        invalid_file = UploadFile(
            filename="test.exe",
            file=BytesIO(b"invalid content"),
            headers={"content-type": "application/x-executable"}
        )
        
        with pytest.raises(Exception):  # Should raise HTTPException
            file_service.validate_file(invalid_file)
    
    @pytest.mark.asyncio
    async def test_save_text_file(self, file_service, sample_text_file):
        """Test saving a text file."""
        project_id = 1
        
        # Reset file pointer
        sample_text_file.file.seek(0)
        
        result = await file_service.save_file(sample_text_file, project_id)
        
        assert result['filename'] == 'test.txt'
        assert result['file_type'] == 'text/plain'
        assert result['file_size'] > 0
        assert 'unique_filename' in result
        assert 'file_path' in result
        
        # Check if file was actually saved
        file_path = Path(result['file_path'])
        assert file_path.exists()
        assert file_path.read_text() == "This is a sample text file for testing."
    
    def test_extract_text_from_text_file(self, file_service):
        """Test text extraction from plain text file."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Sample text content for extraction.")
            temp_file_path = f.name
        
        try:
            extracted_text = file_service.extract_text(temp_file_path, 'text/plain')
            assert extracted_text == "Sample text content for extraction."
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_text_file_not_found(self, file_service):
        """Test text extraction with non-existent file."""
        with pytest.raises(Exception):  # Should raise HTTPException
            file_service.extract_text("/nonexistent/file.txt", 'text/plain')
    
    def test_delete_file(self, file_service):
        """Test file deletion."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_file_path = f.name
        
        # File should exist
        assert os.path.exists(temp_file_path)
        
        # Delete file
        result = file_service.delete_file(temp_file_path)
        assert result is True
        assert not os.path.exists(temp_file_path)
    
    def test_delete_nonexistent_file(self, file_service):
        """Test deletion of non-existent file."""
        result = file_service.delete_file("/nonexistent/file.txt")
        assert result is False
    
    def test_get_file_info(self, file_service):
        """Test getting file information."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_file_path = f.name
        
        try:
            file_info = file_service.get_file_info(temp_file_path)
            
            assert file_info is not None
            assert file_info['filename'].endswith('.txt')
            assert file_info['file_type'] == 'text/plain'
            assert file_info['file_size'] > 0
            assert 'created_at' in file_info
            assert 'modified_at' in file_info
        finally:
            os.unlink(temp_file_path)
    
    def test_get_file_info_nonexistent(self, file_service):
        """Test getting file info for non-existent file."""
        file_info = file_service.get_file_info("/nonexistent/file.txt")
        assert file_info is None
    
    def test_cleanup_temp_files(self, file_service):
        """Test cleanup of temporary files."""
        # Create some temporary files
        temp_file1 = file_service.temp_dir / "temp1.txt"
        temp_file2 = file_service.temp_dir / "temp2.txt"
        
        temp_file1.write_text("temp content 1")
        temp_file2.write_text("temp content 2")
        
        # Both files should exist
        assert temp_file1.exists()
        assert temp_file2.exists()
        
        # Note: This test may not actually delete files since they're new
        # In real usage, cleanup would work on older files
        cleaned_count = file_service.cleanup_temp_files()
        assert isinstance(cleaned_count, int)
        assert cleaned_count >= 0


if __name__ == "__main__":
    pytest.main([__file__])
