#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="/opt/dataguardian"
NGINX_CONF="/opt/dataguardian/nginx/nginx-bluegreen.conf"
HEALTH_TIMEOUT=60
HEALTH_INTERVAL=2

cd "$APP_DIR"

if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Create .env from .env.template first"
    exit 1
fi

source .env

get_active_color() {
    if grep -q "127.0.0.1:5000" "$NGINX_CONF" | grep -v "#"; then
        echo "blue"
    else
        echo "green"
    fi
}

wait_for_health() {
    local port=$1
    local name=$2
    local elapsed=0
    
    echo -e "${YELLOW}Waiting for $name to be healthy...${NC}"
    
    while [ $elapsed -lt $HEALTH_TIMEOUT ]; do
        if curl -sf "http://localhost:$port/_stcore/health" > /dev/null 2>&1; then
            echo -e "${GREEN}$name is healthy${NC}"
            return 0
        fi
        sleep $HEALTH_INTERVAL
        elapsed=$((elapsed + HEALTH_INTERVAL))
        echo -n "."
    done
    
    echo -e "\n${RED}$name failed health check after ${HEALTH_TIMEOUT}s${NC}"
    return 1
}

switch_traffic() {
    local target_color=$1
    local target_port=$2
    
    echo -e "${YELLOW}Switching traffic to $target_color (port $target_port)...${NC}"
    
    sed -i "s/upstream dataguardian_active {/upstream dataguardian_active {\n        # Active: $target_color/g" "$NGINX_CONF"
    sed -i "s/server 127.0.0.1:500[01];/server 127.0.0.1:$target_port;/" "$NGINX_CONF"
    
    docker exec dataguardian-nginx nginx -s reload
    
    echo -e "${GREEN}Traffic switched to $target_color${NC}"
}

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}DataGuardian Pro Blue-Green Deploy${NC}"
echo -e "${BLUE}================================${NC}"

CURRENT_COLOR=$(get_active_color)
if [ "$CURRENT_COLOR" = "blue" ]; then
    NEW_COLOR="green"
    NEW_PORT="5001"
    OLD_PORT="5000"
else
    NEW_COLOR="blue"
    NEW_PORT="5000"
    OLD_PORT="5001"
fi

echo -e "Current active: ${GREEN}$CURRENT_COLOR${NC}"
echo -e "Deploying to: ${YELLOW}$NEW_COLOR${NC}"

echo -e "\n${YELLOW}Step 1: Pull latest images${NC}"
docker compose -f docker-compose.prod.yml pull

echo -e "\n${YELLOW}Step 2: Start $NEW_COLOR instance${NC}"
if [ "$NEW_COLOR" = "green" ]; then
    docker compose -f docker-compose.prod.yml --profile green up -d app-green
else
    docker compose -f docker-compose.prod.yml up -d app-blue
fi

echo -e "\n${YELLOW}Step 3: Health check${NC}"
if ! wait_for_health "$NEW_PORT" "$NEW_COLOR"; then
    echo -e "${RED}Deployment failed - $NEW_COLOR is not healthy${NC}"
    echo -e "${YELLOW}Rolling back...${NC}"
    docker compose -f docker-compose.prod.yml stop "app-$NEW_COLOR"
    exit 1
fi

echo -e "\n${YELLOW}Step 4: Switch traffic${NC}"
switch_traffic "$NEW_COLOR" "$NEW_PORT"

sleep 5
if curl -sf "https://dataguardianpro.nl/health" > /dev/null 2>&1; then
    echo -e "${GREEN}Production health check passed${NC}"
else
    echo -e "${YELLOW}Warning: Production health check failed, but continuing...${NC}"
fi

echo -e "\n${YELLOW}Step 5: Stop old $CURRENT_COLOR instance${NC}"
docker compose -f docker-compose.prod.yml stop "app-$CURRENT_COLOR"

echo -e "\n${YELLOW}Step 6: Update scanner workers${NC}"
docker compose -f docker-compose.prod.yml up -d scanner-worker

echo -e "\n${BLUE}================================${NC}"
echo -e "${GREEN}DEPLOYMENT COMPLETE${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Active: ${GREEN}$NEW_COLOR${NC} (port $NEW_PORT)"
echo -e "Standby: ${YELLOW}$CURRENT_COLOR${NC} (stopped)"
echo -e "\nRollback command:"
echo -e "  ${YELLOW}./scripts/rollback.sh${NC}"
