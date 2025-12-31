#!/bin/bash

# Monitorix Upgrade Script
# This script safely upgrades Monitorix while preserving all data

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Monitorix Upgrade Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${YELLOW}Warning: Running as root. Consider using a non-root user.${NC}"
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose not found. Please install docker-compose.${NC}"
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: git not found. Please install git.${NC}"
    exit 1
fi

# Get current version
echo -e "${YELLOW}Checking current version...${NC}"
CURRENT_VERSION=$(docker-compose exec -T backend python -c "from routers.version import CURRENT_VERSION; print(CURRENT_VERSION)" 2>/dev/null || echo "unknown")
echo -e "Current version: ${GREEN}${CURRENT_VERSION}${NC}"
echo ""

# Step 1: Create backup
echo -e "${YELLOW}Step 1: Creating backup...${NC}"
mkdir -p "${BACKUP_DIR}"

# Check if postgres is running
if docker-compose ps postgres | grep -q "Up"; then
    echo "Creating database backup..."
    docker-compose exec -T postgres pg_dump -U monitorix monitorix > "${BACKUP_FILE}"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Backup created: ${BACKUP_FILE}${NC}"
        BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
        echo -e "  Backup size: ${BACKUP_SIZE}"
    else
        echo -e "${RED}✗ Backup failed! Aborting upgrade.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Warning: PostgreSQL not running. Starting it to create backup...${NC}"
    docker-compose up -d postgres
    sleep 5
    docker-compose exec -T postgres pg_dump -U monitorix monitorix > "${BACKUP_FILE}"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Backup created: ${BACKUP_FILE}${NC}"
    else
        echo -e "${RED}✗ Backup failed! Aborting upgrade.${NC}"
        exit 1
    fi
fi
echo ""

# Step 2: Pull latest code
echo -e "${YELLOW}Step 2: Pulling latest code...${NC}"
git fetch --tags
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LATEST_TAG" ]; then
    echo "Latest version available: ${LATEST_TAG}"
    read -p "Upgrade to ${LATEST_TAG}? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git checkout "${LATEST_TAG}"
    else
        echo "Pulling latest from main branch..."
        git pull origin main
    fi
else
    echo "Pulling latest from main branch..."
    git pull origin main
fi
echo -e "${GREEN}✓ Code updated${NC}"
echo ""

# Step 3: Stop services
echo -e "${YELLOW}Step 3: Stopping services...${NC}"
docker-compose down
echo -e "${GREEN}✓ Services stopped${NC}"
echo ""

# Step 4: Rebuild containers
echo -e "${YELLOW}Step 4: Rebuilding containers...${NC}"
docker-compose build
echo -e "${GREEN}✓ Containers rebuilt${NC}"
echo ""

# Step 5: Start services
echo -e "${YELLOW}Step 5: Starting services...${NC}"
docker-compose up -d
echo "Waiting for services to be ready..."
sleep 10

# Wait for postgres to be healthy
echo "Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U monitorix > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ PostgreSQL failed to start${NC}"
        exit 1
    fi
    sleep 2
done

# Wait for backend to be healthy
echo "Waiting for backend..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Backend failed to start${NC}"
        echo "Check logs with: docker-compose logs backend"
        exit 1
    fi
    sleep 2
done
echo ""

# Step 6: Verify upgrade
echo -e "${YELLOW}Step 6: Verifying upgrade...${NC}"
NEW_VERSION=$(curl -s http://localhost:8000/api/version | grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
echo -e "New version: ${GREEN}${NEW_VERSION}${NC}"

if [ "$CURRENT_VERSION" != "$NEW_VERSION" ]; then
    echo -e "${GREEN}✓ Upgrade successful!${NC}"
else
    echo -e "${YELLOW}Version unchanged (already up to date or same version)${NC}"
fi
echo ""

# Step 7: Check service health
echo -e "${YELLOW}Step 7: Checking service health...${NC}"
HEALTH=$(curl -s http://localhost:8000/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
if [ "$HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✓ All services are healthy${NC}"
else
    echo -e "${YELLOW}⚠ Health check returned: ${HEALTH}${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Upgrade Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Summary:"
echo "  - Backup: ${BACKUP_FILE}"
echo "  - Old version: ${CURRENT_VERSION}"
echo "  - New version: ${NEW_VERSION}"
echo ""
echo "Next steps:"
echo "  1. Check the web UI: http://localhost:3000"
echo "  2. Verify all features work correctly"
echo "  3. Check logs: docker-compose logs -f"
echo ""
echo -e "${YELLOW}If something went wrong, restore from backup:${NC}"
echo "  docker-compose exec postgres psql -U monitorix monitorix < ${BACKUP_FILE}"
echo ""

