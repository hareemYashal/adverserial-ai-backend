# 🚀 Deployment Guide

This guide covers different deployment options for the Adversarial AI Writing Assistant Backend.

## 🏠 Local Development

### Quick Start
```bash
# Clone and setup
git clone https://github.com/yourusername/adversarial-ai-backend.git
cd adversarial-ai-backend
python setup.py  # Automated setup script

# Manual setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env
uvicorn app.main:app --reload
```

### Development with Hot Reload
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🐳 Docker Deployment

### Single Container
```bash
# Build and run
docker build -t adversarial-ai-backend .
docker run -p 8000:8000 -v $(pwd)/uploads:/app/uploads adversarial-ai-backend
```

### Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

**Services included:**
- **API**: FastAPI backend on port 8000
- **Database**: PostgreSQL on port 5432
- **pgAdmin**: Database management on port 5050

## ☁️ Cloud Deployment

### Heroku

1. **Install Heroku CLI**
```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh
```

2. **Create Heroku App**
```bash
heroku create adversarial-ai-backend
heroku addons:create heroku-postgresql:hobby-dev
```

3. **Configure Environment**
```bash
heroku config:set SECRET_KEY="your-production-secret-key"
heroku config:set OPENAI_API_KEY="your-openai-key"
```

4. **Deploy**
```bash
git push heroku main
heroku open
```

### AWS EC2

1. **Launch EC2 Instance**
   - Choose Ubuntu 20.04 LTS
   - Configure security groups (ports 22, 80, 443, 8000)
   - Create or use existing key pair

2. **Setup Server**
```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3 python3-pip python3-venv nginx -y

# Clone repository
git clone https://github.com/yourusername/adversarial-ai-backend.git
cd adversarial-ai-backend

# Setup application
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure Nginx**
```nginx
# /etc/nginx/sites-available/adversarial-ai
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

4. **Setup Systemd Service**
```ini
# /etc/systemd/system/adversarial-ai.service
[Unit]
Description=Adversarial AI Backend
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/adversarial-ai-backend
Environment=PATH=/home/ubuntu/adversarial-ai-backend/venv/bin
EnvironmentFile=/home/ubuntu/adversarial-ai-backend/.env
ExecStart=/home/ubuntu/adversarial-ai-backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

5. **Start Services**
```bash
sudo systemctl enable adversarial-ai
sudo systemctl start adversarial-ai
sudo systemctl enable nginx
sudo systemctl start nginx
```

### DigitalOcean App Platform

1. **Create `app.yaml`**
```yaml
name: adversarial-ai-backend
services:
- name: api
  source_dir: /
  github:
    repo: yourusername/adversarial-ai-backend
    branch: main
  run_command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: SECRET_KEY
    value: your-secret-key
  - key: DATABASE_URL
    value: ${db.DATABASE_URL}
databases:
- name: db
  engine: PG
  version: "13"
  size: db-s-dev-database
```

2. **Deploy**
```bash
doctl apps create --spec app.yaml
```

## 🔒 Production Configuration

### Environment Variables
```bash
# Required for production
SECRET_KEY=your-super-secret-production-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
OPENAI_API_KEY=your-openai-api-key

# Optional optimizations
WORKERS=4
MAX_CONNECTIONS=100
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Database Setup
```sql
-- PostgreSQL setup
CREATE DATABASE adversarial_ai;
CREATE USER ai_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE adversarial_ai TO ai_user;
```

### Security Checklist
- [ ] Change default SECRET_KEY
- [ ] Use HTTPS in production
- [ ] Configure CORS for your domain only
- [ ] Set up database backups
- [ ] Configure rate limiting
- [ ] Set up monitoring and logging
- [ ] Use environment variables for secrets
- [ ] Configure firewall rules

## 📊 Monitoring and Logging

### Health Checks
```bash
# Check API health
curl http://your-domain/health

# Check database connection
curl http://your-domain/api/test
```

### Logging Configuration
```python
# Add to app/main.py for production logging
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/api.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

### Performance Monitoring
```bash
# Install monitoring tools
pip install prometheus-fastapi-instrumentator

# Add to main.py
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to server
      run: |
        # Add your deployment script here
        ssh user@server "cd /app && git pull && systemctl restart adversarial-ai"
```

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Errors**
```bash
# Check database status
sudo systemctl status postgresql
# Check connection
psql -h localhost -U username -d database_name
```

2. **Permission Issues**
```bash
# Fix file permissions
sudo chown -R www-data:www-data /path/to/app
sudo chmod -R 755 /path/to/app
```

3. **Port Already in Use**
```bash
# Find process using port
sudo lsof -i :8000
# Kill process
sudo kill -9 PID
```

4. **Memory Issues**
```bash
# Check memory usage
free -h
# Check application memory
ps aux | grep python
```

### Logs Location
- **Application**: `/var/log/adversarial-ai/`
- **Nginx**: `/var/log/nginx/`
- **System**: `/var/log/syslog`

### Performance Optimization
```bash
# Use Gunicorn with multiple workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Configure PostgreSQL
# Edit /etc/postgresql/13/main/postgresql.conf
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
```

## 📞 Support

For deployment issues:
1. Check the logs first
2. Verify environment variables
3. Test database connectivity
4. Check firewall and security groups
5. Create an issue on GitHub with error details

---

**Happy Deploying! 🚀**
