import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./adversarial_ai.db")

# Database connection settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "adversarial_ai")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# JWT Authentication
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-for-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

CHROMA_DIR: str = os.getenv("CHROMA_DIR", "./chroma")
CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "rag_collection")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


TOP_K: int = int(os.getenv("TOP_K", 4))
MAX_TOKENS_CONTEXT: int = int(os.getenv("MAX_TOKENS_CONTEXT", 2000))