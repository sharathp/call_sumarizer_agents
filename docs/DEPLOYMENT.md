# Deployment Guide

This guide covers production deployment options for the AI Call Center Assistant system.

## Overview

The system can be deployed in multiple configurations:
- **Local Development**: Direct Python execution with uv
- **Docker Container**: Containerized deployment with docker-compose
- **Cloud Platforms**: Streamlit Cloud, AWS, GCP, Azure
- **Enterprise**: On-premises with custom infrastructure

## Prerequisites

### System Requirements
- **Python**: 3.12 or higher
- **Memory**: Minimum 2GB RAM, recommended 4GB+ for concurrent processing
- **Storage**: 1GB+ for dependencies and temporary audio files
- **Network**: Outbound HTTPS access for API calls

### Required API Keys
- **OpenAI API Key**: For transcription (Whisper), summarization, and quality scoring (required)

### Optional Services
- **LangSmith API Key**: For workflow debugging and tracing
- **Redis**: For session state management (future enhancement)

## Local Development Deployment

### Quick Setup

```bash
# Clone repository
git clone <your-repo-url>
cd call_summarizer_agents

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run CLI
uv run python main.py data/sample_transcripts/customer_support.txt

# Run web interface
uv run streamlit run ui/streamlit_app.py
```

### Environment Configuration

```bash
# Copy template and configure API keys
cp .env.template .env
# Edit .env with your actual API keys
```

See `.env.template` for all available configuration options.

## Docker Deployment

### Using Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  call-assistant:
    build: .
    ports:
      - "8501:8501"  # Streamlit UI
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data:ro
      - ./uploads:/app/uploads
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Redis for session management
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Docker Commands

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f call-assistant

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d
```

### Custom Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Default command
CMD ["uv", "run", "streamlit", "run", "ui/streamlit_app.py", "--server.address", "0.0.0.0"]
```

## Cloud Platform Deployment

### Streamlit Cloud

1. **Repository Setup:**
   ```bash
   # Push code to GitHub/GitLab
   git remote add origin https://github.com/yourusername/call-summarizer-agents
   git push -u origin main
   ```

2. **Streamlit Cloud Configuration:**
   - Connect GitHub repository
   - Set main file path: `ui/streamlit_app.py`
   - Add secrets in dashboard:
     ```
     OPENAI_API_KEY = "sk-your-key-here"
     ```

3. **Requirements for Streamlit Cloud:**
   ```bash
   # Generate requirements.txt for platforms that need it
   uv pip compile pyproject.toml -o requirements.txt
   ```

### AWS Deployment

#### EC2 Instance

```bash
# Launch EC2 instance (t3.medium recommended)
# Security group: Allow inbound 8501 (Streamlit), 22 (SSH)

# Install dependencies
sudo apt update
sudo apt install python3.12 python3.12-venv git

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Clone and setup
git clone <your-repo>
cd call-summarizer-agents
uv sync

# Configure environment
sudo nano .env  # Add API keys

# Setup systemd service
sudo nano /etc/systemd/system/call-assistant.service
```

#### Systemd Service Configuration

```ini
[Unit]
Description=AI Call Center Assistant
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/call-summarizer-agents
Environment=PATH=/home/ubuntu/.cargo/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/home/ubuntu/.cargo/bin/uv run streamlit run ui/streamlit_app.py --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable call-assistant
sudo systemctl start call-assistant

# Check status
sudo systemctl status call-assistant
```

#### AWS ECS (Container Service)

```json
{
  "family": "call-assistant",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "call-assistant",
      "image": "your-ecr-repo/call-assistant:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-key"
        },
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/call-assistant",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform

#### Cloud Run Deployment

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/call-assistant

# Deploy to Cloud Run
gcloud run deploy call-assistant \
  --image gcr.io/PROJECT_ID/call-assistant \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars LOG_LEVEL=INFO \
  --set-secrets OPENAI_API_KEY=openai-key:latest \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 10
```

#### App Engine Deployment

```yaml
# app.yaml
runtime: python312
service: call-assistant

env_variables:
  LOG_LEVEL: INFO

automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.6

resources:
  cpu: 1
  memory_gb: 2
  disk_size_gb: 1

handlers:
- url: /.*
  script: auto
```

## Production Considerations

### Performance Optimization

1. **Concurrent Processing:**
   ```python
   # Configure async processing for multiple calls
   MAX_CONCURRENT_CALLS = 5
   WORKER_PROCESSES = 2
   ```

2. **Caching Strategy:**
   ```python
   # Cache transcription results
   ENABLE_TRANSCRIPT_CACHE = True
   CACHE_TTL_HOURS = 24
   ```

3. **Resource Limits:**
   ```python
   # File size limits
   MAX_AUDIO_SIZE_MB = 100
   MAX_TRANSCRIPT_LENGTH = 50000
   ```

### Monitoring & Observability

#### Health Checks

```python
# Add to main.py or separate health endpoint
@app.route('/health')
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0"
    }
```

#### Logging Configuration

```python
# Structured logging for production
LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}
```

#### Metrics Collection

```python
# Key metrics to track
METRICS = [
    "calls_processed_total",
    "processing_time_seconds",
    "transcription_accuracy",
    "agent_failures_total",
    "api_requests_total"
]
```

### Security Hardening

1. **Environment Isolation:**
   ```bash
   # Use non-root user in containers
   RUN adduser --disabled-password --gecos '' appuser
   USER appuser
   ```

2. **API Security:**
   ```python
   # Rate limiting for API endpoints
   RATE_LIMITS = {
       "transcription": "10/minute",
       "processing": "5/minute"
   }
   ```

3. **Input Sanitization:**
   ```python
   # File validation
   ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.txt']
   MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
   ```

## Backup & Recovery

### Data Backup

```bash
# Backup configuration
tar -czf backup_$(date +%Y%m%d).tar.gz \
  .env \
  data/sample_transcripts/ \
  docs/

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/call-assistant"
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" .env data/ docs/
```

### Disaster Recovery

1. **Service Recovery:**
   ```bash
   # Restart service
   sudo systemctl restart call-assistant
   
   # Check logs
   journalctl -u call-assistant -f
   ```

2. **Database Recovery** (if using Redis):
   ```bash
   # Restore Redis data
   sudo systemctl stop redis
   cp backup/dump.rdb /var/lib/redis/
   sudo systemctl start redis
   ```

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer Configuration:**
   ```nginx
   upstream call_assistant {
       server app1:8501;
       server app2:8501;
       server app3:8501;
   }
   
   server {
       listen 80;
       location / {
           proxy_pass http://call_assistant;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. **Kubernetes Deployment:**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: call-assistant
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: call-assistant
     template:
       metadata:
         labels:
           app: call-assistant
       spec:
         containers:
         - name: call-assistant
           image: call-assistant:latest
           ports:
           - containerPort: 8501
           env:
           - name: OPENAI_API_KEY
             valueFrom:
               secretKeyRef:
                 name: api-keys
                 key: openai-key
           resources:
             requests:
               memory: "1Gi"
               cpu: "500m"
             limits:
               memory: "2Gi"  
               cpu: "1000m"
   ```

### Vertical Scaling

```bash
# Increase container resources
docker update --memory=4g --cpus=2 call-assistant

# EC2 instance scaling
# Upgrade to larger instance type (t3.large, t3.xlarge)
```

## Troubleshooting Deployment Issues

### Common Problems

1. **Port Conflicts:**
   ```bash
   # Check if port 8501 is in use
   lsof -i :8501
   
   # Use different port
   uv run streamlit run ui/streamlit_app.py --server.port 8502
   ```

2. **API Key Issues:**
   ```bash
   # Verify environment variables
   echo $OPENAI_API_KEY
   
   # Test API connectivity
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
   ```

3. **Memory Issues:**
   ```bash
   # Monitor memory usage
   htop
   
   # Increase swap space
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### Log Analysis

```bash
# View application logs
tail -f logs/application.log

# Search for errors
grep -i error logs/application.log

# Monitor API calls
grep -i "api" logs/application.log | tail -20
```

## CI/CD Pipeline

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
    - uses: actions/checkout@v4
    
    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
    - name: Setup Python
      run: uv python install 3.12
      
    - name: Install dependencies
      run: uv sync
      
    - name: Run tests
      run: uv run pytest tests/
      
    - name: Run linting
      run: uv run ruff check .

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build Docker image
      run: docker build -t call-assistant:${{ github.sha }} .
      
    - name: Deploy to production
      run: |
        # Your deployment commands here
        echo "Deploying to production..."
```

## Monitoring & Maintenance

### Health Monitoring

```python
# Add health check endpoint
@app.route('/health')
def health():
    checks = {
        "openai_api": test_openai_connection(),
        "disk_space": check_disk_space(),
        "memory_usage": check_memory_usage()
    }
    
    status = "healthy" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks}
```

### Log Rotation

```bash
# Configure logrotate
sudo nano /etc/logrotate.d/call-assistant

/var/log/call-assistant/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

### Automated Updates

```bash
#!/bin/bash
# update_deployment.sh

# Pull latest code
git pull origin main

# Update dependencies  
uv sync

# Restart service
sudo systemctl restart call-assistant

# Verify deployment
sleep 10
curl -f http://localhost:8501/health || echo "Health check failed"
```

## Security Configuration

### Firewall Rules

```bash
# UFW configuration
sudo ufw allow ssh
sudo ufw allow 8501/tcp  # Streamlit
sudo ufw enable
```

### SSL/TLS Setup

```nginx
# Nginx with SSL
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment Variable Security

```bash
# Use HashiCorp Vault for secrets management
export VAULT_ADDR="https://vault.company.com"
export OPENAI_API_KEY=$(vault kv get -field=api_key secret/openai)
```

## Performance Tuning

### Resource Optimization

```python
# Optimize for production
PRODUCTION_CONFIG = {
    "max_workers": 4,
    "memory_limit_mb": 1024,
    "audio_processing_timeout": 300,
    "llm_timeout": 60,
    "enable_caching": True
}
```

### Database Optimization (Redis)

```bash
# Redis production configuration
echo "maxmemory 1gb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
sudo systemctl restart redis
```

## Backup Strategies

### Automated Backups

```bash
#!/bin/bash
# daily_backup.sh

BACKUP_DIR="/backups/$(date +%Y/%m)"
mkdir -p "$BACKUP_DIR"

# Backup configuration and data
tar -czf "$BACKUP_DIR/config_$(date +%d).tar.gz" .env docs/
tar -czf "$BACKUP_DIR/data_$(date +%d).tar.gz" data/

# Clean old backups (keep 30 days)
find /backups -type f -mtime +30 -delete
```

### Recovery Procedures

```bash
# Service recovery checklist
1. Check service status: sudo systemctl status call-assistant
2. Review logs: journalctl -u call-assistant -n 50
3. Verify API connectivity: curl tests
4. Restart if needed: sudo systemctl restart call-assistant
5. Monitor for 5 minutes: watch sudo systemctl status call-assistant
```