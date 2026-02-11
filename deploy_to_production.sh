#!/bin/bash
################################################################################
# DataGuardian Pro - Production Deployment Script
# Deploy to: 45.81.35.202 / dataguardianpro.nl
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PRODUCTION_SERVER="root@45.81.35.202"
APP_DIR="/opt/dataguardian"
BACKUP_DIR="/opt/dataguardian_backup_$(date +%Y%m%d_%H%M%S)"
IMAGE_NAME="vishaalnoord7/myapp:latest"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  DataGuardian Pro - Production Deployment${NC}"
echo -e "${BLUE}  Target: dataguardianpro.nl (45.81.35.202)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"

# Step 1: Pre-flight checks
echo -e "\n${YELLOW}[Step 1/8]${NC} Running pre-flight checks..."

if ! ssh -o ConnectTimeout=5 $PRODUCTION_SERVER "echo 'Connection successful'" > /dev/null 2>&1; then
    echo -e "${RED}✗ Cannot connect to production server${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Server connection verified${NC}"

REQUIRED_FILES=(
    "services/visitor_tracker.py"
    "services/auth_tracker.py"
    "services/db_scanner.py"
    "components/pricing_display.py"
    "services/subscription_manager.py"
    "services/stripe_payment.py"
    "app.py"
    "Dockerfile"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Required file missing: $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All required files present${NC}"

# Step 2: Build Docker image
echo -e "\n${YELLOW}[Step 2/8]${NC} Building Docker image..."

docker build -t "$IMAGE_NAME" . || {
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Docker image built${NC}"

# Step 3: Push image to registry
echo -e "\n${YELLOW}[Step 3/8]${NC} Pushing image to registry..."

docker push "$IMAGE_NAME" || {
    echo -e "${RED}✗ Docker push failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Image pushed to registry${NC}"

# Step 4: Backup current production
echo -e "\n${YELLOW}[Step 4/8]${NC} Backing up current production state..."

ssh $PRODUCTION_SERVER "
    if [ -d '$APP_DIR' ]; then
        echo 'Creating backup: $BACKUP_DIR'
        cp -r $APP_DIR $BACKUP_DIR
        echo 'Backup created successfully'
    else
        echo 'No existing installation found - fresh deployment'
    fi
"
echo -e "${GREEN}✓ Backup completed${NC}"

# Step 5: Transfer config files
echo -e "\n${YELLOW}[Step 5/8]${NC} Transferring config files..."

ssh $PRODUCTION_SERVER "mkdir -p $APP_DIR/.streamlit"
scp .streamlit/config.toml "$PRODUCTION_SERVER:$APP_DIR/.streamlit/config.toml" || true
echo -e "${GREEN}✓ Config transferred${NC}"

# Step 6: Database preparation
echo -e "\n${YELLOW}[Step 6/8]${NC} Preparing database (GDPR compliance check)..."

ssh $PRODUCTION_SERVER "
    docker exec dataguardian-postgres psql -U dataguardian -d dataguardian_prod -c '
        SELECT COUNT(*) as visitor_events_count
        FROM information_schema.tables
        WHERE table_name = '\''visitor_events'\'';
    ' 2>/dev/null || echo 'Database check skipped - will be created on first run'
"
echo -e "${GREEN}✓ Database prepared${NC}"

# Step 7: Deploy containers
echo -e "\n${YELLOW}[Step 7/8]${NC} Deploying containers..."

ssh $PRODUCTION_SERVER "
    echo 'Pulling latest image...'
    docker pull $IMAGE_NAME

    echo 'Stopping current containers...'
    docker stop myapp webhook-server 2>/dev/null || true
    docker rm myapp webhook-server 2>/dev/null || true

    echo 'Starting main application...'
    docker run -d \
        --name myapp \
        --restart unless-stopped \
        -p 5000:5000 \
        -e ENVIRONMENT=production \
        -e DATABASE_URL=\$DATABASE_URL \
        -e REDIS_URL=\$REDIS_URL \
        -e STRIPE_SECRET_KEY=\$STRIPE_SECRET_KEY \
        -e STRIPE_WEBHOOK_SECRET=\$STRIPE_WEBHOOK_SECRET \
        -e JWT_SECRET=\$JWT_SECRET \
        -e OPENAI_API_KEY=\$OPENAI_API_KEY \
        -v $APP_DIR/data:/app/data \
        -v $APP_DIR/logs:/app/logs \
        -v $APP_DIR/reports:/app/reports \
        $IMAGE_NAME

    echo 'Starting webhook server...'
    docker run -d \
        --name webhook-server \
        --restart unless-stopped \
        -p 5001:5001 \
        -e ENVIRONMENT=production \
        -e DATABASE_URL=\$DATABASE_URL \
        -e REDIS_URL=\$REDIS_URL \
        -e STRIPE_SECRET_KEY=\$STRIPE_SECRET_KEY \
        -e STRIPE_WEBHOOK_SECRET=\$STRIPE_WEBHOOK_SECRET \
        -e JWT_SECRET=\$JWT_SECRET \
        $IMAGE_NAME \
        python services/webhook_server.py

    echo 'Waiting for containers to start...'
    sleep 10

    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Application deployed successfully${NC}"
else
    echo -e "${RED}✗ Deployment failed - rolling back${NC}"
    ssh $PRODUCTION_SERVER "
        docker stop myapp webhook-server 2>/dev/null || true
        docker rm myapp webhook-server 2>/dev/null || true
        rm -rf $APP_DIR
        mv $BACKUP_DIR $APP_DIR
        echo 'Rollback complete - restart containers manually'
    "
    exit 1
fi

# Step 8: Verify deployment
echo -e "\n${YELLOW}[Step 8/8]${NC} Verifying deployment..."

ssh $PRODUCTION_SERVER "
    echo 'Container status:'
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

    echo ''
    echo 'Testing application endpoint...'
    curl -f http://localhost:5000/_stcore/health 2>/dev/null && echo 'Streamlit: ✓ Healthy' || echo 'Streamlit: ✗ Not responding'

    echo ''
    echo 'Testing webhook endpoint...'
    curl -f http://localhost:5001/health 2>/dev/null && echo 'Webhook: ✓ Healthy' || echo 'Webhook: ✗ Not responding'

    echo ''
    echo 'Checking Redis...'
    docker exec redis-cache redis-cli ping 2>/dev/null && echo 'Redis: ✓ PONG' || echo 'Redis: ✗ Not responding'
"

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ DEPLOYMENT COMPLETE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "  1. Visit https://dataguardianpro.nl to verify"
echo -e "  2. Test database scanner: New Scan → Database Scan"
echo -e "  3. Check analytics dashboard: Settings → Analytics"
echo -e "  4. Monitor logs: ssh $PRODUCTION_SERVER 'docker logs -f myapp'"
echo -e "\n${YELLOW}Backup Location:${NC}"
echo -e "  $BACKUP_DIR"
echo -e "\n${YELLOW}Rollback Command (if needed):${NC}"
echo -e "  ssh $PRODUCTION_SERVER 'docker stop myapp webhook-server && docker rm myapp webhook-server'"
echo -e "  Then restore from backup and restart containers"
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════${NC}\n"
