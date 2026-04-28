# Deployment Guide

Complete instructions for deploying Project Iceberg to production environments.

## Overview

This guide covers:
- Containerization with Docker
- Cloud deployment (AWS, GCP, Azure)
- Scaling architecture
- Security hardening
- Monitoring & logging
- High availability setup

---

## Prerequisites

- Docker & Docker Compose installed
- Cloud provider account (optional: AWS, GCP, or Azure)
- NVIDIA GPU support (optional: for faster DCT extraction)
- SSL/TLS certificates (for HTTPS)
- Domain name (for production)

---

## Local Docker Setup

### Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run backend
CMD ["python", "server.py"]
```

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  # FastAPI Backend
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      LOG_LEVEL: INFO
      UPLOAD_DIR: /app/uploads
      FAISS_INDEX_PATH: /app/data/faiss_index
    volumes:
      - ./uploads:/app/uploads
      - ./data:/app/data
      - ./keys:/app/keys
    networks:
      - iceberg
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Crawler Worker
  crawler:
    build: .
    command: python engine.py --mode crawler
    environment:
      LOG_LEVEL: INFO
      FAISS_INDEX_PATH: /app/data/faiss_index
    volumes:
      - ./data:/app/data
    networks:
      - iceberg
    depends_on:
      - backend
    restart: unless-stopped

  # Verifier Worker
  verifier:
    build: .
    command: python engine.py --mode verifier
    environment:
      LOG_LEVEL: INFO
      FAISS_INDEX_PATH: /app/data/faiss_index
    volumes:
      - ./uploads:/app/uploads
      - ./data:/app/data
    networks:
      - iceberg
    depends_on:
      - backend
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:3000"
    environment:
      VITE_API_URL: http://backend:8000
    networks:
      - iceberg
    depends_on:
      - backend
    restart: unless-stopped

networks:
  iceberg:
    driver: bridge

volumes:
  uploads:
  data:
```

### Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Runtime stage
FROM node:18-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
```

### Run Docker Compose

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access application:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

---

## Cloud Deployment

### AWS ECS (Elastic Container Service)

#### Step 1: Create ECR Repository

```bash
aws ecr create-repository --repository-name iceberg-backend --region us-east-1
aws ecr create-repository --repository-name iceberg-frontend --region us-east-1
```

#### Step 2: Push Images

```bash
# Get ECR login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push backend
docker tag iceberg-backend:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/iceberg-backend:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/iceberg-backend:latest

# Tag and push frontend
docker tag iceberg-frontend:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/iceberg-frontend:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/iceberg-frontend:latest
```

#### Step 3: Create ECS Task Definition

```json
{
  "family": "iceberg-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/iceberg-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/iceberg-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Step 4: Create ECS Service

```bash
aws ecs create-service \
  --cluster iceberg \
  --service-name iceberg-backend \
  --task-definition iceberg-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

#### Step 5: Set Up Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name iceberg-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Create target group
aws elbv2 create-target-group \
  --name iceberg-backend \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx

# Register service with load balancer
# (Configure in ECS service)
```

### Google Cloud Run

#### Step 1: Set Up Project

```bash
gcloud config set project PROJECT_ID
gcloud builds submit --tag gcr.io/PROJECT_ID/iceberg-backend
```

#### Step 2: Deploy Backend

```bash
gcloud run deploy iceberg-backend \
  --image gcr.io/PROJECT_ID/iceberg-backend \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars LOG_LEVEL=INFO
```

#### Step 3: Deploy Frontend

```bash
gcloud run deploy iceberg-frontend \
  --image gcr.io/PROJECT_ID/iceberg-frontend \
  --platform managed \
  --region us-central1 \
  --environment-variables VITE_API_URL=https://iceberg-backend-xxx.a.run.app
```

### Azure Container Instances

#### Step 1: Create Container Registry

```bash
az acr create --resource-group myResourceGroup --name icebergregistry --sku Basic
```

#### Step 2: Push Images

```bash
az acr build --registry icebergregistry --image iceberg-backend:latest .
```

#### Step 3: Deploy Container

```bash
az container create \
  --resource-group myResourceGroup \
  --name iceberg-backend \
  --image icebergregistry.azurecr.io/iceberg-backend:latest \
  --ports 8000 \
  --cpu 2 \
  --memory 2
```

---

## Scaling Architecture

### Horizontal Scaling Pattern

```
┌──────────────────────────────────────┐
│     Load Balancer (nginx/ALB)        │
└───┬───────────────────────────────┬──┘
    │                               │
    ▼                               ▼
┌─────────────┐              ┌─────────────┐
│ Backend 1   │              │ Backend N   │
│ :8000       │              │ :8000       │
└─────────────┘              └─────────────┘
    │                            │
    └─────────────┬──────────────┘
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
    [Redis Queue]     [Shared FAISS Index]
    (Verifier tasks)  (S3 or EBS)
```

### Replace multiprocessing.Queue with Redis

**Install Redis:**

```bash
# Docker
docker run -d --name redis -p 6379:6379 redis:latest

# Or on server
apt-get install redis-server
systemctl start redis
```

**Update engine.py to use RQ (Redis Queue):**

```python
from rq import Queue
from redis import Redis

# Initialize Redis connection
redis_conn = Redis(host='redis', port=6379, decode_responses=True)
task_queue = Queue(connection=redis_conn)
result_queue = Queue('results', connection=redis_conn)

# Enqueue task
job = task_queue.enqueue(verify_media, url)

# Monitor job
print(job.get_status())
```

### Scale Verifier Workers

Run multiple Verifier instances across nodes:

```bash
# Node 1
python engine.py --mode verifier --worker-id verifier-1

# Node 2
python engine.py --mode verifier --worker-id verifier-2

# Node N
python engine.py --mode verifier --worker-id verifier-n
```

All workers connect to shared Redis queue and FAISS index.

### Shared FAISS Index (S3/EBS)

```python
# Save to S3
import boto3
import faiss

s3 = boto3.client('s3')
faiss.write_index(index, 'index.faiss')
s3.upload_file('index.faiss', 'iceberg-data', 'faiss_index/index.faiss')

# Load from S3
s3.download_file('iceberg-data', 'faiss_index/index.faiss', 'index.faiss')
index = faiss.read_index('index.faiss')
```

---

## Security Hardening

### 1. Environment Variables

Create `.env.production`:

```bash
LOG_LEVEL=WARNING
UPLOAD_DIR=/mnt/uploads  # Use separate volume
FAISS_INDEX_PATH=/mnt/data/faiss_index

# API Security
API_KEY_SECRET=<generate with openssl>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS
CORS_ORIGINS=https://yourdomain.com

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Database
DATABASE_URL=postgresql://user:pass@db-host:5432/iceberg
```

### 2. Implement Authentication

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import jwt
from datetime import datetime, timedelta

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            os.getenv('API_KEY_SECRET'),
            algorithms=[os.getenv('JWT_ALGORITHM')]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=403)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403)
    return user_id

@app.post("/upload")
async def upload(file: UploadFile, user: str = Depends(verify_token)):
    # Protected endpoint
    pass
```

### 3. HTTPS/TLS

#### Using Let's Encrypt + nginx

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

#### Let's Encrypt Certificate

```bash
# Install Certbot
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot certonly --standalone -d yourdomain.com

# Auto-renew (cron job)
0 3 * * * certbot renew --quiet
```

### 4. Network Security

#### Firewall Rules (UFW)

```bash
# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow SSH from specific IP
ufw allow from 203.0.113.0 to any port 22

# Deny all else
ufw default deny incoming
ufw enable
```

#### Database Access

```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=False
)
```

### 5. Input Validation

```python
from pydantic import BaseModel, Field, validator

class UploadMetadata(BaseModel):
    title: str = Field(..., max_length=200)
    source: str = Field(..., max_length=100)
    broadcast_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    
    @validator('title', 'source')
    def must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('must not be empty')
        return v
```

---

## Monitoring & Logging

### Prometheus Metrics

Install Prometheus client:

```bash
pip install prometheus-client
```

Add to `server.py`:

```python
from prometheus_client import Counter, Histogram, start_http_server
import time

# Metrics
upload_counter = Counter('uploads_total', 'Total uploads')
verification_latency = Histogram('verification_seconds', 'Verification latency')
piracy_detections = Counter('piracy_detections_total', 'Piracy detections')

# Start metrics server (port 8001)
start_http_server(8001)

@app.post("/upload")
async def upload(file: UploadFile):
    upload_counter.inc()
    return {"success": True}

@app.post("/verify")
async def verify(payload: VerifyRequest):
    with verification_latency.time():
        result = await run_verification(payload.url)
    if result.piracy_detected:
        piracy_detections.inc()
    return result
```

### ELK Stack (Elasticsearch, Logstash, Kibana)

Install Docker images:

```bash
docker run -d --name elasticsearch \
  -e discovery.type=single-node \
  -p 9200:9200 \
  docker.elastic.co/elasticsearch/elasticsearch:8.0.0

docker run -d --name kibana \
  -p 5601:5601 \
  -e "ELASTICSEARCH_HOSTS=http://elasticsearch:9200" \
  docker.elastic.co/kibana/kibana:8.0.0
```

Configure Python logging:

```python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

logger.info("Piracy detected", extra={
    "asset_id": "a1b2c3d4",
    "url": "https://example.com",
    "confidence": 0.98
})
```

### CloudWatch (AWS)

```python
import watchtower
import logging

logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler(
    log_group='/aws/ecs/iceberg-backend',
    stream_name='production'
))

logger.warning("High memory usage", extra={"memory_mb": 2048})
```

---

## Backup & Disaster Recovery

### Database Backups

```bash
# PostgreSQL backup
pg_dump iceberg > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backups (cron)
0 2 * * * pg_dump iceberg | gzip > /backups/iceberg_$(date +\%Y\%m\%d).sql.gz
```

### FAISS Index Backup

```bash
# Daily backup to S3
0 3 * * * aws s3 cp /app/data/faiss_index/index.faiss s3://iceberg-backups/faiss_$(date +\%Y\%m\%d).faiss
```

### Disaster Recovery Plan

1. **RPO (Recovery Point Objective):** 1 hour
2. **RTO (Recovery Time Objective):** 30 minutes
3. **Strategy:** Hot standby in secondary region with Route53 failover

---

## Performance Optimization

### Frontend Build Optimization

```javascript
// vite.config.js
export default {
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
        },
      },
    },
  },
};
```

### Backend Caching

```python
from functools import lru_cache
import redis
from datetime import timedelta

redis_client = redis.Redis(host='redis', port=6379)

def cache_result(expire_seconds=3600):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            result = redis_client.get(cache_key)
            if result:
                return json.loads(result)
            
            # Compute and cache
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expire_seconds, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(expire_seconds=3600)
async def get_assets():
    return await db.fetch("SELECT * FROM assets")
```

---

## Troubleshooting Production Issues

### High Memory Usage

```bash
# Check memory per container
docker stats --no-stream

# Restart service
docker-compose restart verifier

# Investigate FAISS index size
ls -lh data/faiss_index/
```

### Queue Bottleneck

```python
# Monitor queue depth
queue_size = redis_conn.llen('iceberg-tasks')
print(f"Queue depth: {queue_size}")

# Scale up verifier workers
docker-compose up -d --scale verifier=4
```

### Database Connection Pool Exhaustion

```python
# Check active connections
SELECT count(*) FROM pg_stat_activity;

# Increase pool size
pool_size=50
max_overflow=100
```

---

## Checklist Before Production

- [ ] SSL/TLS certificates installed
- [ ] Authentication/authorization implemented
- [ ] Rate limiting enabled
- [ ] Backup strategy in place
- [ ] Monitoring/alerting configured
- [ ] Secrets in environment variables (not code)
- [ ] Load testing completed (>500 concurrent users)
- [ ] Disaster recovery plan documented
- [ ] Security audit completed
- [ ] Scaling tested (horizontal + vertical)

---

See [Development Guide](Development_Guide.md) for local setup and testing.
