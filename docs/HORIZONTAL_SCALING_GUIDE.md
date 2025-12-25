# DataGuardian Pro - Horizontal Scaling Guide

## Complete Implementation Steps for Scanner Worker Scaling

This guide explains exactly how to achieve horizontal scaling with containerized scanner workers.

---

## Table of Contents
1. [How It Works](#how-it-works)
2. [Current Architecture vs Scaled Architecture](#architecture-comparison)
3. [Step-by-Step Implementation](#implementation-steps)
4. [Resource Configuration](#resource-configuration)
5. [Scaling Commands](#scaling-commands)
6. [Monitoring & Verification](#monitoring)
7. [Capacity Planning](#capacity-planning)

---

## How It Works

### The Queue-Based Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              HOW SCANNING WORKS                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  USER CLICKS "START SCAN"                                                  │
│           │                                                                │
│           ▼                                                                │
│  ┌─────────────────┐                                                       │
│  │  Streamlit App  │──────► Creates job with scan details                  │
│  │  (UI only)      │                                                       │
│  └────────┬────────┘                                                       │
│           │                                                                │
│           ▼                                                                │
│  ┌─────────────────┐                                                       │
│  │  Redis Queue    │◄─────── Job stored in queue                           │
│  │  (job storage)  │         Format: {job_id, scanner_type, input_data}    │
│  └────────┬────────┘                                                       │
│           │                                                                │
│           ▼                                                                │
│  ┌─────────────────────────────────────────────────────────┐               │
│  │                   SCANNER WORKERS                        │               │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │               │
│  │  │Worker 1 │  │Worker 2 │  │Worker 3 │  │Worker 4 │    │               │
│  │  │(Code)   │  │(Website)│  │(Code)   │  │(A/V)    │    │               │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘    │               │
│  │       │            │            │            │          │               │
│  │       └────────────┴────────────┴────────────┘          │               │
│  │                         │                                │               │
│  └─────────────────────────┼────────────────────────────────┘               │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────┐                                                       │
│  │  PostgreSQL     │◄─────── Results saved to database                     │
│  │  (results)      │                                                       │
│  └────────┬────────┘                                                       │
│           │                                                                │
│           ▼                                                                │
│  ┌─────────────────┐                                                       │
│  │  Streamlit App  │◄─────── UI polls for results                          │
│  │  shows results  │                                                       │
│  └─────────────────┘                                                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Key Concept: Decoupled Processing

**Before (Current):**
- User starts scan → Streamlit app runs scanner directly → UI freezes
- One slow scan blocks everything

**After (With Workers):**
- User starts scan → Job added to Redis queue → UI immediately responsive
- Workers pick up jobs independently → Multiple scans run in parallel
- UI just polls for results → Never freezes

---

## Architecture Comparison

### Current Architecture (Single Process)

```
┌─────────────────────────────────────┐
│           SINGLE VM                 │
│                                     │
│  ┌───────────────────────────────┐  │
│  │     Streamlit App             │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │ UI + All 12 Scanners    │  │  │  ◄── Everything in one process
│  │  │ running in same process │  │  │      Heavy scan = UI freeze
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
│                                     │
│  Capacity: ~8 concurrent scans      │
│  Risk: One crash = everything down  │
└─────────────────────────────────────┘
```

### Scaled Architecture (Worker Containers)

```
┌─────────────────────────────────────────────────────────────────┐
│                          SINGLE VM                              │
│                                                                 │
│  ┌─────────────────────┐   ┌─────────────────────────────────┐  │
│  │   Streamlit App     │   │         DOCKER WORKERS          │  │
│  │   (UI only)         │   │  ┌───────┐ ┌───────┐ ┌───────┐  │  │
│  │   - Fast            │   │  │ W1    │ │ W2    │ │ W3    │  │  │
│  │   - Never freezes   │   │  │ Code  │ │ Code  │ │ Web   │  │  │
│  │   - Just polls      │   │  │ 1GB   │ │ 1GB   │ │ 1GB   │  │  │
│  │     for results     │   │  └───────┘ └───────┘ └───────┘  │  │
│  └──────────┬──────────┘   │  ┌───────┐ ┌───────┐ ┌───────┐  │  │
│             │              │  │ W4    │ │ W5    │ │ W6    │  │  │
│             │              │  │ A/V   │ │ A/V   │ │ DB    │  │  │
│             │              │  │ 2GB   │ │ 2GB   │ │ 1GB   │  │  │
│             │              │  └───────┘ └───────┘ └───────┘  │  │
│             │              └─────────────────────────────────┘  │
│             │                           │                       │
│             ▼                           ▼                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    REDIS QUEUE                           │   │
│  │   Jobs waiting: [scan-123, scan-456, scan-789, ...]     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Capacity: ~48 concurrent scans (6 workers × 8 each)           │
│  Risk: Worker crash = only that job fails, others continue     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 1: Verify Redis Queue is Working

Your Redis queue is already implemented in `services/scanner_queue.py`. Verify it works:

```bash
# On your VM
ssh root@45.81.35.202

# Check Redis is running
docker exec dataguardian-redis redis-cli ping
# Should return: PONG

# Check queue status
docker exec dataguardian-redis redis-cli LLEN dataguardian:scanner:queue
# Returns number of pending jobs
```

### Step 2: Create Worker-Specific Docker Compose

Create `docker-compose.workers.yml` on your server:

```yaml
version: '3.8'

services:
  # General purpose workers (code, website, blob scans)
  scanner-worker-general:
    image: ${DOCKER_WORKER_IMAGE}:${APP_VERSION:-latest}
    environment:
      - REDIS_URL=${REDIS_URL}
      - DATABASE_URL=${DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WORKER_TYPE=general
    restart: unless-stopped
    deploy:
      replicas: 4
      resources:
        limits:
          memory: 1G
          cpus: '1'
    networks:
      - dataguardian-network

  # Heavy workers for audio/video deepfake detection
  scanner-worker-heavy:
    image: ${DOCKER_WORKER_IMAGE}:${APP_VERSION:-latest}
    environment:
      - REDIS_URL=${REDIS_URL}
      - DATABASE_URL=${DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WORKER_TYPE=heavy
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: '2'
    networks:
      - dataguardian-network

networks:
  dataguardian-network:
    external: true
```

### Step 3: Start Workers

```bash
# Navigate to app directory
cd /opt/dataguardian

# Start workers
docker compose -f docker-compose.workers.yml up -d

# Verify workers are running
docker compose -f docker-compose.workers.yml ps
```

Expected output:
```
NAME                          STATUS          PORTS
scanner-worker-general-1      Up 30 seconds   
scanner-worker-general-2      Up 30 seconds   
scanner-worker-general-3      Up 30 seconds   
scanner-worker-general-4      Up 30 seconds   
scanner-worker-heavy-1        Up 30 seconds   
scanner-worker-heavy-2        Up 30 seconds   
```

### Step 4: Scale Workers

```bash
# Scale general workers to 8
docker compose -f docker-compose.workers.yml up -d --scale scanner-worker-general=8

# Scale heavy workers to 4
docker compose -f docker-compose.workers.yml up -d --scale scanner-worker-heavy=4

# Check new count
docker compose -f docker-compose.workers.yml ps
```

---

## Resource Configuration

### Memory Allocation by Scanner Type

| Scanner Type | Memory | CPU | Reason |
|--------------|--------|-----|--------|
| Code Scanner | 1GB | 1 | Text processing, regex |
| Website Scanner | 1GB | 1 | HTML parsing, network I/O |
| Blob Scanner | 1GB | 1 | Document parsing |
| Database Scanner | 1GB | 1 | Query execution |
| Image Scanner (OCR) | 1.5GB | 1 | Tesseract needs memory |
| Audio/Video (Deepfake) | 2GB | 2 | FFmpeg + ML analysis |
| AI Model Scanner | 1.5GB | 1 | OpenAI API calls |

### Recommended Production Configuration

For ~500 monthly users, ~5,000 scans/day:

```yaml
# General workers: 6 × 1GB = 6GB RAM
scanner-worker-general:
  deploy:
    replicas: 6
    resources:
      limits:
        memory: 1G

# Heavy workers: 3 × 2GB = 6GB RAM
scanner-worker-heavy:
  deploy:
    replicas: 3
    resources:
      limits:
        memory: 2G

# Total: 12GB RAM for workers
# Plus ~4GB for Streamlit, Redis, Postgres, Nginx
# Total VM requirement: 16GB RAM
```

---

## Scaling Commands

### Quick Reference

```bash
# View current workers
docker compose -f docker-compose.workers.yml ps

# Scale up general workers
docker compose -f docker-compose.workers.yml up -d --scale scanner-worker-general=10

# Scale up heavy workers
docker compose -f docker-compose.workers.yml up -d --scale scanner-worker-heavy=5

# Scale down (during low traffic)
docker compose -f docker-compose.workers.yml up -d --scale scanner-worker-general=2

# Stop all workers
docker compose -f docker-compose.workers.yml down

# Restart workers (picks up new image version)
docker compose -f docker-compose.workers.yml pull
docker compose -f docker-compose.workers.yml up -d

# View worker logs
docker compose -f docker-compose.workers.yml logs -f

# View specific worker logs
docker compose -f docker-compose.workers.yml logs -f scanner-worker-general-1
```

### Auto-Scaling Script (Optional)

Create `scripts/auto-scale-workers.sh`:

```bash
#!/bin/bash
# Auto-scale based on queue depth

QUEUE_DEPTH=$(docker exec dataguardian-redis redis-cli -a $REDIS_PASSWORD LLEN dataguardian:scanner:queue)

if [ "$QUEUE_DEPTH" -gt 50 ]; then
    echo "High load: $QUEUE_DEPTH jobs. Scaling to 10 workers..."
    docker compose -f docker-compose.workers.yml up -d --scale scanner-worker-general=10
elif [ "$QUEUE_DEPTH" -gt 20 ]; then
    echo "Medium load: $QUEUE_DEPTH jobs. Scaling to 6 workers..."
    docker compose -f docker-compose.workers.yml up -d --scale scanner-worker-general=6
else
    echo "Low load: $QUEUE_DEPTH jobs. Scaling to 3 workers..."
    docker compose -f docker-compose.workers.yml up -d --scale scanner-worker-general=3
fi
```

---

## Monitoring

### Check Queue Health

```bash
# Number of pending jobs
docker exec dataguardian-redis redis-cli LLEN dataguardian:scanner:queue

# View pending job IDs
docker exec dataguardian-redis redis-cli LRANGE dataguardian:scanner:queue 0 10

# Check active jobs
docker exec dataguardian-redis redis-cli HKEYS dataguardian:scanner:jobs
```

### Monitor Worker Performance

```bash
# CPU/Memory usage per worker
docker stats --no-stream

# Example output:
# CONTAINER                    CPU %   MEM USAGE
# scanner-worker-general-1     2.5%    512MiB / 1GiB
# scanner-worker-general-2     5.1%    623MiB / 1GiB
# scanner-worker-heavy-1       15.2%   1.2GiB / 2GiB
```

### Health Check Dashboard

Add to your monitoring:

```bash
# Create monitoring script
cat > /opt/dataguardian/scripts/check-workers.sh << 'EOF'
#!/bin/bash
echo "=== DataGuardian Worker Status ==="
echo ""
echo "Queue Depth: $(docker exec dataguardian-redis redis-cli LLEN dataguardian:scanner:queue)"
echo ""
echo "Active Workers:"
docker compose -f docker-compose.workers.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"
echo ""
echo "Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
EOF

chmod +x /opt/dataguardian/scripts/check-workers.sh
```

---

## Capacity Planning

### Capacity Calculation Formula

```
Concurrent Scans = Number of Workers × Scans per Worker

Where:
- General worker handles ~8 concurrent scans
- Heavy worker handles ~4 concurrent scans (longer processing time)
```

### Capacity Examples

| Workers | General | Heavy | Concurrent Scans | Monthly Capacity* |
|---------|---------|-------|------------------|-------------------|
| Current | 0 | 0 | 8 | ~10,000 |
| Small | 2 | 1 | 20 | ~25,000 |
| Medium | 4 | 2 | 40 | ~50,000 |
| Large | 8 | 4 | 80 | ~100,000 |
| Enterprise | 16 | 8 | 160 | ~200,000 |

*Assuming 5-minute average scan time

### VM Size Recommendations

| Tier | VM Size | RAM | Workers | Monthly Cost (Hetzner) |
|------|---------|-----|---------|------------------------|
| Starter | CX31 | 8GB | 4 general | ~€15/month |
| Growth | CX41 | 16GB | 6+2 | ~€30/month |
| Scale | CX51 | 32GB | 12+4 | ~€60/month |
| Enterprise | CCX33 | 64GB | 24+8 | ~€140/month |

---

## Fault Tolerance

### What Happens When a Worker Crashes?

```
SCENARIO: Worker 3 crashes while processing scan-456

1. Worker 3 crashes
   └── Docker restart policy: "unless-stopped"
   └── Docker automatically restarts Worker 3

2. scan-456 job
   └── Job timeout (8 minutes) triggers
   └── Job marked as "failed" in Redis
   └── User sees "Scan failed - please retry"

3. Other workers (1, 2, 4, 5, 6)
   └── Continue processing their jobs
   └── No impact from Worker 3 crash

4. Queue continues
   └── New jobs distributed to healthy workers
   └── Worker 3 rejoins after restart
```

### Crash Recovery Configuration

Already configured in docker-compose:

```yaml
restart: unless-stopped  # Auto-restart on crash

deploy:
  resources:
    limits:
      memory: 1G  # OOM killer stops runaway memory
```

---

## Decision Matrix

### Should You Scale Workers?

| Scenario | Action | Configuration |
|----------|--------|---------------|
| <50 users, <500 scans/month | No workers needed | Current setup |
| 50-200 users | Add 2-4 general workers | 4GB extra RAM |
| 200-500 users | Add 6 general + 2 heavy | 10GB extra RAM |
| 500+ users | Add 10+ general + 4 heavy | 18GB+ extra RAM |
| Heavy deepfake usage | Add more heavy workers | 2GB per worker |

### Cost-Benefit Analysis

| Investment | Benefit |
|------------|---------|
| +€15/month (8GB more RAM) | 4x scan capacity, no UI freezes |
| +€30/month (16GB more RAM) | 8x scan capacity, isolated failures |
| +€60/month (32GB more RAM) | 16x scan capacity, enterprise-ready |

---

## Next Steps

1. **Review this guide** - Understand the architecture
2. **Decide on scale** - How many workers do you need?
3. **Upgrade VM if needed** - Ensure enough RAM
4. **Deploy workers** - Follow Step 3 above
5. **Monitor** - Use the monitoring commands
6. **Scale as needed** - Adjust based on queue depth

Ready to proceed with implementation?
