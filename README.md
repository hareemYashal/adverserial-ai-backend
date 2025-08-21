# 🤖 Adversarial AI Writing Assistant - Backend

A powerful FastAPI backend for the Adversarial AI Writing Assistant that provides multi-persona document analysis, file processing, and comprehensive user management.

## 🌟 Features

- **🔐 JWT Authentication** - Complete user registration, login, and token management
- **📁 Project Management** - Organize documents into projects with user associations
- **📄 Multi-format Document Upload** - Support for PDF, DOCX, and TXT files with text extraction
- **🎭 AI Persona System** - Manage multiple AI personas with personality traits for document analysis
- **🔍 Advanced Search** - Search personas by traits, documents by content, and projects by criteria
- **📊 RESTful API** - Comprehensive API with automatic OpenAPI documentation
- **🧪 Comprehensive Testing** - 43+ tests covering all functionality with 100% pass rate
- **🗄️ Database Management** - SQLAlchemy ORM with PostgreSQL/SQLite support

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL (optional, SQLite used by default)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/adversarial-ai-backend.git
   cd adversarial-ai-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   # The database will be created automatically on first run
   # For PostgreSQL, ensure your DATABASE_URL is configured in .env
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## 📖 API Documentation

### Authentication Endpoints
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login user and get JWT token
- `GET /auth/me` - Get current user info
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - Logout user

### Project Management
- `GET /projects/` - List all projects
- `POST /projects/` - Create new project
- `GET /projects/{id}` - Get specific project
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project

### Document Management
- `POST /documents/` - Create document (text content)
- `GET /documents/` - List documents
- `GET /documents/{id}` - Get specific document
- `PUT /documents/{id}` - Update document
- `DELETE /documents/{id}` - Delete document

### File Upload
- `POST /upload/document` - Upload single file
- `POST /upload/documents/batch` - Upload multiple files
- `GET /upload/document/{id}/status` - Get processing status
- `POST /upload/document/{id}/reprocess` - Reprocess document

### Persona Management
- `GET /personas/` - List all personas
- `POST /personas/` - Create new persona
- `GET /personas/{id}` - Get specific persona
- `PUT /personas/{id}` - Update persona
- `DELETE /personas/{id}` - Delete persona
- `GET /personas/search/traits` - Search personas by traits

### User Management
- `GET /users/` - List users (admin)
- `POST /users/` - Create user (deprecated - use /auth/register)
- `GET /users/{id}` - Get user details
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

## 🗄️ Database Schema

### Models
- **User** - User accounts with authentication
- **Project** - Document organization containers
- **Document** - Uploaded files and text content
- **Persona** - AI personality configurations

### Relationships
- Users have many Projects
- Projects have many Documents
- Documents belong to Projects
- Personas are independent entities

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./test.db` | Database connection string |
| `SECRET_KEY` | `dev-secret-key-change-for-production` | JWT secret key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiration time |
| `OPENAI_API_KEY` | None | OpenAI API key (for future LLM integration) |

### Supported File Types
- **PDF** - Portable Document Format
- **DOCX** - Microsoft Word documents
- **TXT** - Plain text files

## 🧪 Testing

Run the complete test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_auth_api.py          # Authentication tests
pytest tests/test_all_crud_apis.py     # CRUD operation tests
pytest tests/test_file_upload_api.py   # File upload tests
pytest tests/test_file_service.py      # File service tests

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Coverage
- **Authentication**: 18/18 tests passing
- **CRUD Operations**: 13/13 tests passing
- **File Processing**: 12/12 tests passing
- **File Services**: 11/11 tests passing
- **Total**: 43+ tests with 100% pass rate

## 🏗️ Project Structure

```
adversarial-ai-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration settings
│   ├── database.py            # Database setup and session management
│   ├── models/                # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── document.py
│   │   └── persona.py
│   ├── schemas/               # Pydantic schemas for API
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── document.py
│   │   └── persona.py
│   ├── routers/               # API route handlers
│   │   ├── __init__.py
|   │   ├── analysis.py
|   │   ├── mutli_analysis.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── projects.py
│   │   ├── documents.py
│   │   ├── personas.py
│   │   └── file_upload.py
│   └── services/              # Business logic services
│       ├── __init__.py
│       ├── auth_service.py
│       ├── analysis_service.py
│       ├── multi_analysis_service.py
│       ├── persona_service.py
│       ├── multi_persona_service.py
│       └── file_service.py
├── tests/                     # Comprehensive test suite
│   ├── test_auth_api.py
│   ├── test_all_crud_apis.py
│   ├── test_file_upload_api.py
│   └── test_file_service.py
├── uploads/                   # File upload directory (auto-created)
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore patterns
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── AUTHENTICATION_GUIDE.md   # Detailed authentication guide
```

## 🚀 Deployment

### Local Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment

#### Using Docker (Recommended)
```dockerfile
# Dockerfile example
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Using Gunicorn
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Setup for Production
1. Set `SECRET_KEY` to a secure random string
2. Configure `DATABASE_URL` for PostgreSQL
3. Set up file storage (local or cloud)
4. Configure CORS settings for your frontend domain

## 🔮 Future Enhancements

### Phase 2 - Alpha Development (Weeks 4-7)
- **LLM Integration** - OpenAI GPT-4o integration for document analysis
- **Multi-Persona Orchestration** - Parallel persona critiques
- **RAG Pipeline** - Vector database and contextual analysis
- **Citation Verification** - Reference validation using CrossRef/PubMed

### Phase 3 - Beta Development (Weeks 8-10)
- **Performance Optimization** - Async processing and caching
- **Frontend Integration** - Next.js dashboard
- **Advanced Analytics** - Usage metrics and insights
- **Production Deployment** - Docker containerization and CI/CD

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation for API changes
- Ensure all tests pass before submitting PR

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- SQLAlchemy for powerful ORM capabilities
- Pydantic for data validation
- pytest for comprehensive testing framework

## 📞 Support

For support, email support@yourcompany.com or create an issue in this repository.

---

**Built with ❤️ for the Adversarial AI Writing Assistant Project**