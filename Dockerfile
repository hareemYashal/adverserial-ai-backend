# Use Python 3.13 slim image (or switch to 3.11 for better library support)
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NLTK_DATA=/usr/local/nltk_data

# Install system dependencies (added git + curl + build essentials)
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install NLTK data during build (avoid runtime downloads)
RUN python -m nltk.downloader punkt punkt_tab -d /usr/local/nltk_data

# Copy project files
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port (not strictly required for Railway, but good practice)
EXPOSE 8000

# Health check (use PORT env var instead of hardcoding)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application (bind to Railway's PORT env var)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]