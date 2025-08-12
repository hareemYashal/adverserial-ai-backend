# 🤝 Contributing to Adversarial AI Writing Assistant

Thank you for your interest in contributing! This guide will help you get started with contributing to the Adversarial AI Writing Assistant Backend.

## 🎯 How to Contribute

### Types of Contributions
- 🐛 **Bug Reports** - Help us identify and fix issues
- ✨ **Feature Requests** - Suggest new functionality
- 📝 **Documentation** - Improve guides and API docs
- 🔧 **Code Contributions** - Bug fixes and new features
- 🧪 **Testing** - Add or improve test coverage
- 🎨 **UI/UX** - Frontend improvements (future phase)

## 🚀 Getting Started

### 1. Fork and Clone
```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/yourusername/adversarial-ai-backend.git
cd adversarial-ai-backend

# Add upstream remote
git remote add upstream https://github.com/originaluser/adversarial-ai-backend.git
```

### 2. Set Up Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install
```

### 3. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-number
```

## 📋 Development Guidelines

### Code Style
- Follow **PEP 8** Python style guidelines
- Use **type hints** for function parameters and return values
- Write **docstrings** for all functions and classes
- Use **meaningful variable and function names**

### Example Code Style
```python
from typing import List, Optional
from fastapi import HTTPException

def get_user_projects(
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    active_only: bool = False
) -> List[Project]:
    """
    Retrieve projects for a specific user.
    
    Args:
        user_id: The ID of the user
        skip: Number of projects to skip for pagination
        limit: Maximum number of projects to return
        active_only: Whether to return only active projects
        
    Returns:
        List of Project objects
        
    Raises:
        HTTPException: If user not found
    """
    # Implementation here
    pass
```

### Testing Requirements
- **Write tests** for all new features and bug fixes
- Maintain **test coverage** above 90%
- Use **descriptive test names** that explain what is being tested
- Follow **AAA pattern** (Arrange, Act, Assert)

### Example Test
```python
def test_create_project_with_valid_data(client, auth_headers):
    """Test creating a project with valid data returns 201."""
    # Arrange
    project_data = {
        "title": "Test Project",
        "description": "A test project"
    }
    
    # Act
    response = client.post("/projects/?user_id=1", json=project_data, headers=auth_headers)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["title"] == "Test Project"
```

## 🐛 Reporting Bugs

### Before Reporting
1. **Search existing issues** to avoid duplicates
2. **Test with the latest version** to ensure the bug still exists
3. **Check documentation** to verify expected behavior

### Bug Report Template
```markdown
**Bug Description**
A clear and concise description of the bug.

**Steps to Reproduce**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g. Windows 10, Ubuntu 20.04]
- Python Version: [e.g. 3.9.1]
- API Version: [e.g. 1.0.0]

**Additional Context**
Add any other context, screenshots, or logs.
```

## ✨ Feature Requests

### Feature Request Template
```markdown
**Feature Description**
A clear and concise description of the feature.

**Problem Statement**
What problem does this feature solve?

**Proposed Solution**
Describe your proposed solution.

**Alternatives Considered**
Describe any alternative solutions you've considered.

**Additional Context**
Add any other context, mockups, or examples.
```

## 🔄 Pull Request Process

### 1. Before Submitting
- [ ] Code follows project style guidelines
- [ ] All tests pass (`pytest`)
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages are descriptive
- [ ] Branch is up to date with main

### 2. PR Checklist
- [ ] **Title** clearly describes the change
- [ ] **Description** explains what and why
- [ ] **Tests** are included and passing
- [ ] **Documentation** is updated if needed
- [ ] **Breaking changes** are noted
- [ ] **Screenshots** for UI changes (future)

### 3. Commit Message Format
```
type(scope): brief description

Longer description if needed.

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(auth): add JWT token refresh endpoint

Add endpoint to refresh JWT tokens without re-authentication.
Includes rate limiting and token blacklisting.

Fixes #45
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth_api.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run tests in parallel
pytest -n auto
```

### Test Categories
1. **Unit Tests** - Test individual functions
2. **Integration Tests** - Test API endpoints
3. **End-to-End Tests** - Test complete workflows

### Writing New Tests
```python
import pytest
from fastapi.testclient import TestClient

def test_feature_name_should_do_something():
    """Test that feature does what it should do."""
    # Arrange - Set up test data
    test_data = {"key": "value"}
    
    # Act - Perform the action
    result = some_function(test_data)
    
    # Assert - Check the result
    assert result is not None
    assert result["status"] == "success"
```

## 📚 Documentation

### Documentation Types
- **API Documentation** - Auto-generated from code
- **User Guides** - Step-by-step instructions
- **Developer Guides** - Technical implementation details
- **Code Comments** - Inline explanations

### Documentation Style
- Use **clear, concise language**
- Include **code examples**
- Add **screenshots** when helpful
- Keep **up to date** with code changes

## 🚀 Development Workflow

### Typical Workflow
1. **Choose an issue** or create feature proposal
2. **Discuss approach** in issue comments
3. **Create feature branch** from main
4. **Implement changes** with tests
5. **Update documentation**
6. **Submit pull request**
7. **Address review feedback**
8. **Merge when approved**

### Code Review Process
- **All PRs** require at least one review
- **Focus on** code quality, security, and maintainability
- **Be constructive** and respectful in feedback
- **Respond promptly** to review comments

## 🏗️ Project Architecture

### Directory Structure
```
app/
├── main.py              # FastAPI app initialization
├── config.py            # Configuration settings
├── database.py          # Database setup
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── routers/             # API route handlers
└── services/            # Business logic
```

### Key Concepts
- **Models** define database structure
- **Schemas** define API request/response format
- **Routers** handle HTTP requests
- **Services** contain business logic
- **Dependencies** manage authentication and database sessions

## 🎯 Areas for Contribution

### Current Priorities
1. **LLM Integration** - OpenAI API integration
2. **RAG Pipeline** - Vector database and retrieval
3. **Citation Verification** - Academic reference validation
4. **Performance Optimization** - Async processing
5. **Frontend Development** - Next.js dashboard

### Good First Issues
- 📝 Documentation improvements
- 🧪 Adding test cases
- 🐛 Minor bug fixes
- 🔧 Code refactoring
- 📊 Adding API response examples

## ❓ Getting Help

### Resources
- **Documentation**: `/docs` endpoint when running locally
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For general questions
- **Email**: support@yourcompany.com

### Community Guidelines
- **Be respectful** and inclusive
- **Help others** when you can
- **Search before asking** to avoid duplicates
- **Provide context** when asking questions

## 🎉 Recognition

Contributors will be:
- **Listed** in the project README
- **Credited** in release notes
- **Invited** to join the contributor team
- **Mentioned** in project communications

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Thank you for contributing to the Adversarial AI Writing Assistant! 🚀**
