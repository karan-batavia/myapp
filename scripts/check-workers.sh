#!/bin/bash

APP_DIR="/opt/dataguardian"
cd "$APP_DIR" 2>/dev/null || cd "$(dirname "$0")/.."

source .env 2>/dev/null || true

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           DataGuardian Pro - Worker Status                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 QUEUE STATUS"
echo "────────────────────────────────────────────────────────────────"
QUEUE_DEPTH=$(docker exec dataguardian-redis redis-cli LLEN dataguardian:scanner:queue 2>/dev/null || echo "N/A")
ACTIVE_JOBS=$(docker exec dataguardian-redis redis-cli HLEN dataguardian:scanner:jobs 2>/dev/null || echo "N/A")
echo "  Pending Jobs:  $QUEUE_DEPTH"
echo "  Active Jobs:   $ACTIVE_JOBS"
echo ""

echo "🔧 WORKER CONTAINERS"
echo "────────────────────────────────────────────────────────────────"
docker compose -f docker/docker-compose.workers.yml ps 2>/dev/null || echo "  No workers running"
echo ""

echo "💻 RESOURCE USAGE"
echo "────────────────────────────────────────────────────────────────"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null | grep -E "(scanner-worker|NAME)" || echo "  Unable to get stats"
echo ""

echo "📈 CAPACITY"
echo "────────────────────────────────────────────────────────────────"
GENERAL_COUNT=$(docker compose -f docker/docker-compose.workers.yml ps -q scanner-worker-general 2>/dev/null | wc -l)
HEAVY_COUNT=$(docker compose -f docker/docker-compose.workers.yml ps -q scanner-worker-heavy 2>/dev/null | wc -l)
TOTAL_CAPACITY=$((GENERAL_COUNT * 8 + HEAVY_COUNT * 4))
echo "  General Workers: $GENERAL_COUNT (8 scans each)"
echo "  Heavy Workers:   $HEAVY_COUNT (4 scans each)"
echo "  Total Capacity:  ~$TOTAL_CAPACITY concurrent scans"
echo ""

echo "🔄 QUICK COMMANDS"
echo "────────────────────────────────────────────────────────────────"
echo "  Scale up:   docker compose -f docker/docker-compose.workers.yml up -d --scale scanner-worker-general=8"
echo "  Scale down: docker compose -f docker/docker-compose.workers.yml up -d --scale scanner-worker-general=2"
echo "  View logs:  docker compose -f docker/docker-compose.workers.yml logs -f"
echo "  Auto-scale: ./scripts/auto-scale-workers.sh"
echo ""
