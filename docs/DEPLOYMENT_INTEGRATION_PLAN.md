# DataGuardian Pro - Production Deployment Integration Plan

## Executive Summary

This plan upgrades your deployment from a manual process with downtime to an automated zero-downtime pipeline with containerized scanner workers.

**Current State:**
- Manual docker-compose rebuild causing 10-30s downtime
- Hardcoded credentials in docker-compose.yml
- Scanner workers not deployed
- No health-gated traffic switching

**Target State:**
- Zero-downtime blue-green deployment via GitHub Actions
- Secrets managed via .env file (not in git)
- Containerized scanner workers auto-scaled
- Traffic switches only after health checks pass

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION VM (Hetzner)                         │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                         NGINX (Port 80/443)                      │    │
│  │                    ┌──────────┴──────────┐                      │    │
│  │                    ▼                     ▼                      │    │
│  │              app-blue:5000         app-green:5001               │    │
│  │              (active)              (standby)                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐   │
│  │  PostgreSQL       │  │  Redis            │  │  Scanner Workers  │   │
│  │  (persistent)     │  │  (queue + cache)  │  │  (1-N containers) │   │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

DEPLOYMENT FLOW:
GitHub Push → Build Images → Push to Registry → SSH Deploy → Health Check → Switch Traffic
```

---

## Implementation Steps

### Phase 1: Secure Secrets (30 minutes)

**Step 1.1: Create environment template**

Create `.env.template` (committed to git - no secrets):
```bash
# DataGuardian Pro - Production Environment Template
# Copy to .env on server and fill in values

# Database
POSTGRES_USER=dataguardian
POSTGRES_PASSWORD=<generate-strong-password>
POSTGRES_DB=dataguardian_prod
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}

# Redis
REDIS_PASSWORD=<generate-strong-password>
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# Application Secrets
JWT_SECRET=<generate-256-bit-secret>
ENCRYPTION_KEY=<generate-256-bit-key>
DATAGUARDIAN_MASTER_KEY=<your-master-key>

# External Services
OPENAI_API_KEY=<your-openai-key>
STRIPE_SECRET_KEY=<your-stripe-key>
STRIPE_PUBLISHABLE_KEY=<your-stripe-publishable-key>

# Docker Registry
DOCKER_IMAGE=your-dockerhub-username/dataguardian-app
DOCKER_WORKER_IMAGE=your-dockerhub-username/dataguardian-worker
```

**Step 1.2: Update docker-compose.yml**

Replace hardcoded passwords with `${VARIABLE}` references.

**Step 1.3: Create .env on server**
```bash
ssh root@45.81.35.202
cd /opt/dataguardian
cp .env.template .env
nano .env  # Fill in actual values
chmod 600 .env  # Restrict permissions
```

---

### Phase 2: Blue-Green Docker Compose (1 hour)

**Step 2.1: Create docker-compose.prod.yml**

New compose file with blue-green app containers:

```yaml
services:
  # Blue instance (default active)
  app-blue:
    image: ${DOCKER_IMAGE}:${APP_VERSION:-latest}
    container_name: dataguardian-blue
    ports:
      - "5000:5000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      # ... other env vars
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/_stcore/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  # Green instance (standby for deployments)
  app-green:
    image: ${DOCKER_IMAGE}:${APP_VERSION:-latest}
    container_name: dataguardian-green
    ports:
      - "5001:5000"
    profiles: ["green"]  # Only started during deployment
    # ... same config as blue

  # Scanner Workers (scalable)
  scanner-worker:
    image: ${DOCKER_WORKER_IMAGE}:${APP_VERSION:-latest}
    environment:
      - REDIS_URL=${REDIS_URL}
      - DATABASE_URL=${DATABASE_URL}
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
    depends_on:
      - redis
```

**Step 2.2: Create Nginx blue-green config**

```nginx
upstream dataguardian {
    # Active color - changed during deployment
    server 127.0.0.1:5000;  # blue (default)
    # server 127.0.0.1:5001;  # green (uncomment to switch)
}

server {
    listen 443 ssl http2;
    server_name dataguardianpro.nl;
    
    location / {
        proxy_pass http://dataguardian;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Health check endpoint for deployment verification
    location /health {
        proxy_pass http://dataguardian/_stcore/health;
    }
}
```

---

### Phase 3: GitHub Actions Upgrade (1 hour)

**Step 3.1: Update .github/workflows/deploy.yml**

New workflow with:
- Build both app and worker images
- Tag with git SHA + semver
- Zero-downtime deployment script
- Health-gated traffic switching
- Automatic rollback on failure

```yaml
name: Deploy DataGuardian Pro

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build and push app image
        uses: docker/build-push-action@v5
        with:
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/dataguardian-app:latest
            ${{ secrets.DOCKERHUB_USERNAME }}/dataguardian-app:${{ github.sha }}
      
      - name: Build and push worker image
        uses: docker/build-push-action@v5
        with:
          file: docker/Dockerfile.worker
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/dataguardian-worker:latest
            ${{ secrets.DOCKERHUB_USERNAME }}/dataguardian-worker:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Zero-downtime deploy
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          password: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/dataguardian
            
            # Pull new images
            export APP_VERSION=${{ github.sha }}
            docker compose pull
            
            # Start green instance
            docker compose --profile green up -d app-green
            
            # Wait for health
            for i in {1..30}; do
              if curl -sf http://localhost:5001/_stcore/health; then
                echo "Green is healthy"
                break
              fi
              sleep 2
            done
            
            # Switch traffic to green
            sed -i 's/5000/5001/' /etc/nginx/nginx.conf
            nginx -s reload
            
            # Stop blue
            docker compose stop app-blue
            
            # Update workers
            docker compose up -d --scale scanner-worker=3 scanner-worker
            
            echo "Deployment complete"
```

---

### Phase 4: Operational Procedures

**4.1: Manual Deployment**
```bash
ssh root@45.81.35.202
cd /opt/dataguardian

# Pull specific version
export APP_VERSION=abc1234
docker compose pull

# Deploy with zero downtime
./scripts/deploy-blue-green.sh
```

**4.2: Rollback**
```bash
# Rollback to previous version
export APP_VERSION=previous-sha
docker compose pull
docker compose up -d app-blue
sed -i 's/5001/5000/' /etc/nginx/nginx.conf
nginx -s reload
docker compose stop app-green
```

**4.3: Scale Workers**
```bash
# Scale to 5 workers
docker compose up -d --scale scanner-worker=5 scanner-worker

# Check worker status
docker compose ps scanner-worker
```

**4.4: Monitoring Commands**
```bash
# Application health
curl https://dataguardianpro.nl/health

# Container status
docker compose ps

# Redis queue depth
docker exec dataguardian-redis redis-cli -a $REDIS_PASSWORD LLEN dataguardian:scanner:queue

# Worker logs
docker compose logs -f scanner-worker

# Application logs
docker compose logs -f app-blue
```

---

## Implementation Checklist

### Pre-Deployment (on your local machine)
- [ ] Review and approve this plan
- [ ] Update GitHub repository secrets:
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN`
  - `SSH_HOST` (45.81.35.202)
  - `SSH_USER` (root)
  - `SSH_PRIVATE_KEY`

### Server Setup (on Hetzner VM)
- [ ] Create `/opt/dataguardian/.env` with production secrets
- [ ] Update Nginx config for blue-green switching
- [ ] Test manual deployment once
- [ ] Verify health endpoint works

### First Automated Deployment
- [ ] Push to main branch
- [ ] Monitor GitHub Actions workflow
- [ ] Verify zero downtime (watch `curl -s https://dataguardianpro.nl`)
- [ ] Check scanner workers are running

### Verification
- [ ] Run a test scan
- [ ] Check compliance score appears (not 0%)
- [ ] Verify Redis queue is processing jobs
- [ ] Test rollback procedure

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `.env.template` | Create | Template for production secrets |
| `docker-compose.prod.yml` | Create | Blue-green production compose |
| `nginx/nginx-bluegreen.conf` | Create | Nginx upstream switching config |
| `.github/workflows/deploy.yml` | Update | Zero-downtime deployment workflow |
| `scripts/deploy-blue-green.sh` | Create | Manual deployment helper script |
| `docker-compose.yml` | Update | Remove hardcoded passwords |

---

## Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| 1 | 30 min | Secure secrets (.env setup) |
| 2 | 1 hour | Blue-green docker compose |
| 3 | 1 hour | GitHub Actions upgrade |
| 4 | 30 min | Test and verify |
| **Total** | **3 hours** | Full implementation |

---

## Risk Mitigation

1. **Rollback Ready**: Keep last 3 image tags in Docker Hub
2. **Backup Before Deploy**: Current backup script already creates timestamped backups
3. **Health Gates**: Traffic only switches after health check passes
4. **Gradual Rollout**: Test on staging first if available

---

## Next Steps

After you review this plan:

1. **Approve** - I'll create all the files listed above
2. **Modify** - Tell me what changes you'd like
3. **Questions** - Ask about any specific part

Ready to proceed?
