# Docker Deployment Guide

This guide provides comprehensive documentation for deploying the AI Call Center Assistant using Docker and Docker Compose.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Configuration](#docker-configuration)
- [Docker Compose Services](#docker-compose-services)
- [Building and Running](#building-and-running)
- [Environment Variables](#environment-variables)
- [Volume Management](#volume-management)
- [Networking](#networking)
- [Health Checks](#health-checks)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed (optional)
- `.env` file with API keys configured
- At least 4GB of available RAM
- 2GB of available disk space for images

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and run the application
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down
```

### Using Docker Directly

```bash
# Build the image
docker build -t call-center-assistant .

# Run the container
docker run -p 8501:8501 --env-file .env call-center-assistant

# Run with custom name and auto-restart
docker run -d \
  --name call-assistant \
  --restart unless-stopped \
  -p 8501:8501 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  call-center-assistant
```

## Docker Configuration

### Dockerfile Overview

The application uses a multi-stage Dockerfile for optimal image size:

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim as builder
- Installs build dependencies
- Installs uv package manager
- Creates virtual environment
- Installs Python dependencies

# Stage 2: Production
FROM python:3.12-slim
- Copies virtual environment from builder
- Adds application code
- Creates non-root user
- Configures health checks
- Sets up Streamlit server
```

### Build Arguments

```bash
# Build with custom Python version
docker build --build-arg PYTHON_VERSION=3.11 -t call-center-assistant .

# Build with specific uv version
docker build --build-arg UV_VERSION=0.8.11 -t call-center-assistant .
```

## Docker Compose Services

### Main Application Service

```yaml
app:
  build: .
  ports:
    - "8501:8501"  # Streamlit UI
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
  volumes:
    - ./data:/app/data
    - ./logs:/app/logs
```

### Optional Redis Service

Enable Redis for caching and session management:

```bash
# Run with Redis
docker-compose --profile with-redis up

# Or modify docker-compose.yml to always include Redis
```

Redis configuration:
- Port: 6379
- Persistent data volume
- Automatic reconnection on failure
- Health checks every 10 seconds

### Optional PostgreSQL Service

Enable PostgreSQL for persistent storage:

```bash
# Run with PostgreSQL
docker-compose --profile with-postgres up

# Set database password in .env
POSTGRES_PASSWORD=your-secure-password
```

PostgreSQL configuration:
- Port: 5432
- Database: call_center
- User: call_center_user
- Persistent data volume
- Health checks with pg_isready

## Building and Running

### Development Build

```bash
# Build with development dependencies
docker build -f Dockerfile.dev -t call-center-dev .

# Run with code mounting for hot reload
docker run -it \
  -p 8501:8501 \
  -v $(pwd):/app \
  --env-file .env \
  call-center-dev
```

### Production Build

```bash
# Build optimized production image
docker build \
  --target production \
  --cache-from call-center-assistant:latest \
  -t call-center-assistant:prod .

# Run production container
docker run -d \
  --name call-assistant-prod \
  --restart always \
  -p 8501:8501 \
  --env-file .env.production \
  --memory="2g" \
  --cpus="2" \
  call-center-assistant:prod
```

## Environment Variables

### Required Variables

```bash
# API Keys (required)
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...

# Optional API Keys
ANTHROPIC_API_KEY=...
LANGCHAIN_API_KEY=...
```

### Application Settings

```bash
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY=1

# Model Configuration
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4
DEFAULT_TEMPERATURE=0.7

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
```

### Using Environment Files

```bash
# Development
docker run --env-file .env.dev call-center-assistant

# Staging
docker run --env-file .env.staging call-center-assistant

# Production
docker run --env-file .env.prod call-center-assistant
```

## Volume Management

### Data Volumes

```bash
# Create named volumes
docker volume create call-center-data
docker volume create call-center-logs

# Run with named volumes
docker run -d \
  -v call-center-data:/app/data \
  -v call-center-logs:/app/logs \
  call-center-assistant

# Backup volumes
docker run --rm \
  -v call-center-data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/data-backup.tar.gz /data
```

### Bind Mounts

```bash
# Mount local directories
docker run -d \
  -v $(pwd)/data:/app/data:rw \
  -v $(pwd)/logs:/app/logs:rw \
  -v $(pwd)/custom-config:/app/config:ro \
  call-center-assistant
```

## Networking

### Port Configuration

```bash
# Custom port mapping
docker run -p 8080:8501 call-center-assistant

# Bind to specific interface
docker run -p 127.0.0.1:8501:8501 call-center-assistant

# Multiple port exposure
docker run \
  -p 8501:8501 \  # Streamlit UI
  -p 9090:9090 \  # Metrics (if enabled)
  call-center-assistant
```

### Network Isolation

```bash
# Create custom network
docker network create call-center-net

# Run containers on custom network
docker run -d \
  --network call-center-net \
  --name app \
  call-center-assistant

docker run -d \
  --network call-center-net \
  --name redis \
  redis:7-alpine
```

## Health Checks

### Container Health Monitoring

The Docker image includes built-in health checks:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s \
  --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1
```

### Manual Health Check

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' call-assistant

# View health check logs
docker inspect --format='{{json .State.Health}}' call-assistant | jq

# Test health endpoint
curl http://localhost:8501/_stcore/health
```

## Production Deployment

### Security Best Practices

1. **Run as non-root user**: Already configured in Dockerfile
2. **Use secrets management**: 
   ```bash
   # Create Docker secret
   echo "sk-..." | docker secret create openai_key -
   
   # Use in stack deployment
   docker service create \
     --secret openai_key \
     call-center-assistant
   ```

3. **Resource limits**:
   ```bash
   docker run -d \
     --memory="2g" \
     --memory-swap="2g" \
     --cpus="2" \
     --pids-limit=100 \
     call-center-assistant
   ```

4. **Read-only filesystem**:
   ```bash
   docker run -d \
     --read-only \
     --tmpfs /tmp \
     -v data-volume:/app/data \
     call-center-assistant
   ```

### Scaling with Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml call-center

# Scale service
docker service scale call-center_app=3

# Update service
docker service update \
  --image call-center-assistant:v2 \
  call-center_app
```

### Kubernetes Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: call-center-assistant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: call-center
  template:
    metadata:
      labels:
        app: call-center
    spec:
      containers:
      - name: app
        image: call-center-assistant:latest
        ports:
        - containerPort: 8501
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
```

## Troubleshooting

### Common Issues

#### Container won't start
```bash
# Check logs
docker logs call-assistant

# Debug with interactive shell
docker run -it --entrypoint /bin/bash call-center-assistant

# Check environment
docker run --rm call-center-assistant env
```

#### Permission errors
```bash
# Fix volume permissions
docker run --rm \
  -v $(pwd)/data:/data \
  alpine chown -R 1000:1000 /data
```

#### Out of memory
```bash
# Increase memory limit
docker run --memory="4g" call-center-assistant

# Check memory usage
docker stats call-assistant
```

#### Network connectivity issues
```bash
# Test DNS resolution
docker run --rm call-center-assistant nslookup api.openai.com

# Test API connectivity
docker run --rm \
  --env-file .env \
  call-center-assistant \
  python -c "import openai; print('API connected')"
```

### Debug Mode

```bash
# Run with debug logging
docker run -e LOG_LEVEL=DEBUG call-center-assistant

# Interactive debugging
docker run -it \
  -e LOG_LEVEL=DEBUG \
  -p 8501:8501 \
  --entrypoint /bin/bash \
  call-center-assistant

# Inside container
uv run python -m pdb main.py
```

### Container Inspection

```bash
# Inspect running container
docker exec -it call-assistant /bin/bash

# View processes
docker top call-assistant

# Check file system
docker exec call-assistant ls -la /app

# Monitor resource usage
docker stats --no-stream call-assistant
```

## Advanced Configuration

### Multi-Architecture Builds

```bash
# Build for multiple platforms
docker buildx create --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t call-center-assistant:multi \
  --push .
```

### Custom Entrypoint

```bash
# Override entrypoint
docker run \
  --entrypoint python \
  call-center-assistant \
  main.py --debug

# Custom startup script
docker run \
  -v $(pwd)/startup.sh:/startup.sh:ro \
  --entrypoint /startup.sh \
  call-center-assistant
```

### Compose Override Files

```bash
# Development override
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  up

# Production override
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d
```

## Monitoring and Logging

### Log Management

```bash
# View logs with timestamps
docker logs -t call-assistant

# Follow logs
docker logs -f call-assistant

# Limit log output
docker logs --tail 100 call-assistant

# Export logs
docker logs call-assistant > app.log 2>&1
```

### Metrics Collection

```yaml
# Add Prometheus metrics
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

For additional troubleshooting help, see **[Troubleshooting Guide](TROUBLESHOOTING.md#docker-issues)**.