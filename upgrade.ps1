# Monitorix Upgrade Script for Windows PowerShell
# This script safely upgrades Monitorix while preserving all data

$ErrorActionPreference = "Stop"

# Colors for output (PowerShell compatible)
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Configuration
$BACKUP_DIR = ".\backups"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$BACKUP_FILE = "$BACKUP_DIR\backup_$TIMESTAMP.sql"

Write-ColorOutput Green "========================================"
Write-ColorOutput Green "Monitorix Upgrade Script"
Write-ColorOutput Green "========================================"
Write-Output ""

# Check if docker-compose is available
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: docker-compose not found. Please install docker-compose."
    exit 1
}

# Check if git is available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "Error: git not found. Please install git."
    exit 1
}

# Get current version
Write-ColorOutput Yellow "Checking current version..."
try {
    $CURRENT_VERSION = docker-compose exec -T backend python -c "from routers.version import CURRENT_VERSION; print(CURRENT_VERSION)" 2>$null
    if (-not $CURRENT_VERSION) {
        $CURRENT_VERSION = "unknown"
    }
} catch {
    $CURRENT_VERSION = "unknown"
}
Write-Output "Current version: $CURRENT_VERSION"
Write-Output ""

# Step 1: Create backup
Write-ColorOutput Yellow "Step 1: Creating backup..."
New-Item -ItemType Directory -Force -Path $BACKUP_DIR | Out-Null

# Check if postgres is running
$postgresRunning = docker-compose ps postgres | Select-String "Up"
if ($postgresRunning) {
    Write-Output "Creating database backup..."
    docker-compose exec -T postgres pg_dump -U monitorix monitorix | Out-File -FilePath $BACKUP_FILE -Encoding utf8
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput Green "✓ Backup created: $BACKUP_FILE"
        $backupSize = (Get-Item $BACKUP_FILE).Length / 1MB
        Write-Output "  Backup size: $([math]::Round($backupSize, 2)) MB"
    } else {
        Write-ColorOutput Red "✗ Backup failed! Aborting upgrade."
        exit 1
    }
} else {
    Write-ColorOutput Yellow "Warning: PostgreSQL not running. Starting it to create backup..."
    docker-compose up -d postgres
    Start-Sleep -Seconds 5
    docker-compose exec -T postgres pg_dump -U monitorix monitorix | Out-File -FilePath $BACKUP_FILE -Encoding utf8
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput Green "✓ Backup created: $BACKUP_FILE"
    } else {
        Write-ColorOutput Red "✗ Backup failed! Aborting upgrade."
        exit 1
    }
}
Write-Output ""

# Step 2: Pull latest code
Write-ColorOutput Yellow "Step 2: Pulling latest code..."
git fetch --tags
$LATEST_TAG = git describe --tags --abbrev=0 2>$null
if ($LATEST_TAG) {
    Write-Output "Latest version available: $LATEST_TAG"
    $response = Read-Host "Upgrade to $LATEST_TAG? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        git checkout $LATEST_TAG
    } else {
        Write-Output "Pulling latest from main branch..."
        git pull origin main
    }
} else {
    Write-Output "Pulling latest from main branch..."
    git pull origin main
}
Write-ColorOutput Green "✓ Code updated"
Write-Output ""

# Step 3: Stop services
Write-ColorOutput Yellow "Step 3: Stopping services..."
docker-compose down
Write-ColorOutput Green "✓ Services stopped"
Write-Output ""

# Step 4: Rebuild containers
Write-ColorOutput Yellow "Step 4: Rebuilding containers..."
docker-compose build
Write-ColorOutput Green "✓ Containers rebuilt"
Write-Output ""

# Step 5: Start services
Write-ColorOutput Yellow "Step 5: Starting services..."
docker-compose up -d
Write-Output "Waiting for services to be ready..."
Start-Sleep -Seconds 10

# Wait for postgres to be healthy
Write-Output "Waiting for PostgreSQL..."
for ($i = 1; $i -le 30; $i++) {
    $result = docker-compose exec -T postgres pg_isready -U monitorix 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput Green "✓ PostgreSQL is ready"
        break
    }
    if ($i -eq 30) {
        Write-ColorOutput Red "✗ PostgreSQL failed to start"
        exit 1
    }
    Start-Sleep -Seconds 2
}

# Wait for backend to be healthy
Write-Output "Waiting for backend..."
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput Green "✓ Backend is ready"
            break
        }
    } catch {
        # Continue waiting
    }
    if ($i -eq 30) {
        Write-ColorOutput Red "✗ Backend failed to start"
        Write-Output "Check logs with: docker-compose logs backend"
        exit 1
    }
    Start-Sleep -Seconds 2
}
Write-Output ""

# Step 6: Verify upgrade
Write-ColorOutput Yellow "Step 6: Verifying upgrade..."
try {
    $versionResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/version" -Method Get
    $NEW_VERSION = $versionResponse.version
} catch {
    $NEW_VERSION = "unknown"
}
Write-Output "New version: $NEW_VERSION"

if ($CURRENT_VERSION -ne $NEW_VERSION) {
    Write-ColorOutput Green "✓ Upgrade successful!"
} else {
    Write-ColorOutput Yellow "Version unchanged (already up to date or same version)"
}
Write-Output ""

# Step 7: Check service health
Write-ColorOutput Yellow "Step 7: Checking service health..."
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    $HEALTH = $healthResponse.status
    if ($HEALTH -eq "healthy") {
        Write-ColorOutput Green "✓ All services are healthy"
    } else {
        Write-ColorOutput Yellow "⚠ Health check returned: $HEALTH"
    }
} catch {
    Write-ColorOutput Yellow "⚠ Could not check health status"
}
Write-Output ""

# Summary
Write-ColorOutput Green "========================================"
Write-ColorOutput Green "Upgrade Complete!"
Write-ColorOutput Green "========================================"
Write-Output ""
Write-Output "Summary:"
Write-Output "  - Backup: $BACKUP_FILE"
Write-Output "  - Old version: $CURRENT_VERSION"
Write-Output "  - New version: $NEW_VERSION"
Write-Output ""
Write-Output "Next steps:"
Write-Output "  1. Check the web UI: http://localhost:3000"
Write-Output "  2. Verify all features work correctly"
Write-Output "  3. Check logs: docker-compose logs -f"
Write-Output ""
Write-ColorOutput Yellow "If something went wrong, restore from backup:"
Write-Output "  Get-Content $BACKUP_FILE | docker-compose exec -T postgres psql -U monitorix monitorix"
Write-Output ""

