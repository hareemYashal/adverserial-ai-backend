#!/usr/bin/env python3
"""
Setup script for Adversarial AI Writing Assistant Backend
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def setup_environment():
    """Set up the Python virtual environment."""
    print("🚀 Setting up Adversarial AI Writing Assistant Backend\n")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print("❌ Python 3.9 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")
    
    # Create virtual environment
    venv_path = Path("venv")
    if not venv_path.exists():
        run_command(f"{sys.executable} -m venv venv", "Creating virtual environment")
    else:
        print("✅ Virtual environment already exists")
    
    # Determine activation script
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate"
        pip_command = "venv\\Scripts\\pip"
        python_command = "venv\\Scripts\\python"
    else:  # Unix/Linux/MacOS
        activate_script = "source venv/bin/activate"
        pip_command = "venv/bin/pip"
        python_command = "venv/bin/python"
    
    # Install dependencies
    run_command(f"{pip_command} install --upgrade pip", "Upgrading pip")
    run_command(f"{pip_command} install -r requirements.txt", "Installing dependencies")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy("env.example", ".env")
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your configuration")
    
    # Create uploads directory
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    print("✅ Created uploads directory")
    
    # Test database connection
    result = run_command(f"{python_command} -c \"from app.database import engine; print('Database connection test passed')\"", "Testing database connection")
    
    if result:
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print(f"1. Activate virtual environment: {activate_script}")
        print("2. Edit .env file with your configuration")
        print("3. Run the application: uvicorn app.main:app --reload")
        print("4. Access API documentation: http://localhost:8000/docs")
        print("\n🧪 Run tests: pytest")
    else:
        print("\n❌ Setup completed with errors. Please check the configuration.")

if __name__ == "__main__":
    setup_environment()
