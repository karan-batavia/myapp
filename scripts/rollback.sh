#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="/opt/dataguardian"
NGINX_CONF="/opt/dataguardian/nginx/nginx-bluegreen.conf"

cd "$APP_DIR"

get_active_color() {
    if grep -q "server 127.0.0.1:5000;" "$NGINX_CONF"; then
        echo "blue"
    else
        echo "green"
    fi
}

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}DataGuardian Pro Rollback${NC}"
echo -e "${BLUE}================================${NC}"

CURRENT_COLOR=$(get_active_color)
if [ "$CURRENT_COLOR" = "blue" ]; then
    ROLLBACK_COLOR="green"
    ROLLBACK_PORT="5001"
else
    ROLLBACK_COLOR="blue"
    ROLLBACK_PORT="5000"
fi

echo -e "Current active: ${GREEN}$CURRENT_COLOR${NC}"
echo -e "Rolling back to: ${YELLOW}$ROLLBACK_COLOR${NC}"

echo -e "\n${YELLOW}Step 1: Start $ROLLBACK_COLOR instance${NC}"
if [ "$ROLLBACK_COLOR" = "green" ]; then
    docker compose -f docker-compose.prod.yml --profile green up -d app-green
else
    docker compose -f docker-compose.prod.yml up -d app-blue
fi

echo -e "\n${YELLOW}Step 2: Wait for $ROLLBACK_COLOR to be healthy${NC}"
for i in {1..30}; do
    if curl -sf "http://localhost:$ROLLBACK_PORT/_stcore/health" > /dev/null 2>&1; then
        echo -e "${GREEN}$ROLLBACK_COLOR is healthy${NC}"
        break
    fi
    sleep 2
    echo -n "."
done

echo -e "\n${YELLOW}Step 3: Switch traffic to $ROLLBACK_COLOR${NC}"
sed -i "s/server 127.0.0.1:500[01];/server 127.0.0.1:$ROLLBACK_PORT;/" "$NGINX_CONF"
docker exec dataguardian-nginx nginx -s reload

echo -e "\n${YELLOW}Step 4: Stop $CURRENT_COLOR${NC}"
docker compose -f docker-compose.prod.yml stop "app-$CURRENT_COLOR"

echo -e "\n${BLUE}================================${NC}"
echo -e "${GREEN}ROLLBACK COMPLETE${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Active: ${GREEN}$ROLLBACK_COLOR${NC}"
