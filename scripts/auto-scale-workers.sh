#!/bin/bash
set -e

APP_DIR="/opt/dataguardian"
cd "$APP_DIR"

source .env 2>/dev/null || true

get_queue_depth() {
    docker exec dataguardian-redis redis-cli -a "$REDIS_PASSWORD" LLEN dataguardian:scanner:queue 2>/dev/null || echo "0"
}

get_worker_count() {
    docker compose -f docker/docker-compose.workers.yml ps -q scanner-worker-general 2>/dev/null | wc -l
}

QUEUE_DEPTH=$(get_queue_depth)
CURRENT_WORKERS=$(get_worker_count)

echo "=== DataGuardian Auto-Scaler ==="
echo "Queue Depth: $QUEUE_DEPTH"
echo "Current Workers: $CURRENT_WORKERS"
echo ""

if [ "$QUEUE_DEPTH" -gt 100 ]; then
    TARGET_GENERAL=12
    TARGET_HEAVY=4
    echo "CRITICAL LOAD: Scaling to $TARGET_GENERAL general + $TARGET_HEAVY heavy workers"
elif [ "$QUEUE_DEPTH" -gt 50 ]; then
    TARGET_GENERAL=8
    TARGET_HEAVY=3
    echo "HIGH LOAD: Scaling to $TARGET_GENERAL general + $TARGET_HEAVY heavy workers"
elif [ "$QUEUE_DEPTH" -gt 20 ]; then
    TARGET_GENERAL=6
    TARGET_HEAVY=2
    echo "MEDIUM LOAD: Scaling to $TARGET_GENERAL general + $TARGET_HEAVY heavy workers"
elif [ "$QUEUE_DEPTH" -gt 5 ]; then
    TARGET_GENERAL=4
    TARGET_HEAVY=2
    echo "NORMAL LOAD: Scaling to $TARGET_GENERAL general + $TARGET_HEAVY heavy workers"
else
    TARGET_GENERAL=2
    TARGET_HEAVY=1
    echo "LOW LOAD: Scaling to $TARGET_GENERAL general + $TARGET_HEAVY heavy workers"
fi

docker compose -f docker/docker-compose.workers.yml up -d \
    --scale scanner-worker-general=$TARGET_GENERAL \
    --scale scanner-worker-heavy=$TARGET_HEAVY

echo ""
echo "Workers scaled. Current status:"
docker compose -f docker/docker-compose.workers.yml ps
