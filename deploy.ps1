# Monitorix Deployment Script for Windows PowerShell
# Checks prerequisites and optionally installs them before deployment
# Usage: .\deploy.ps1 [user@]hostname [options]

param(
    [Parameter(Mandatory=$true)]
    [string]$Hostname,
    
    [int]$Port = 22,
    [string]$Key = "",
    [string]$RemoteDir = "~/monitorix",
    [switch]$SkipBuild,
    [string]$EnvFile = "",
    [switch]$AutoInstall
)

$ErrorActionPreference = "Stop"

function Write-Info {
    Write-Host "[INFO] $args" -ForegroundColor Green
}

function Write-Warn {
    Write-Host "[WARN] $args" -ForegroundColor Yellow
}

function Write-Error {
    Write-Host "[ERROR] $args" -ForegroundColor Red
}

function Write-Guide {
    Write-Host "[GUIDE] $args" -ForegroundColor Cyan
}

# Build SSH command
$sshArgs = @()
if ($Key) {
    $sshArgs += "-i", $Key
}
$sshArgs += "-p", $Port.ToString()

# Test SSH connection
Write-Info "Testing SSH connection to $Hostname..."
$testResult = & ssh @sshArgs -o ConnectTimeout=5 -o BatchMode=yes $Hostname "echo 'Connection successful'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Cannot connect to $Hostname. Please check SSH access."
    exit 1
}
Write-Info "SSH connection successful"

# Check prerequisites
Write-Info "Checking prerequisites on remote host..."

$missingPackages = @()
$needsDockerGroup = $false

# Check for basic tools
Write-Info "Checking for basic tools..."
$curlCheck = & ssh @sshArgs $Hostname "command -v curl" 2>&1
if (-not $curlCheck) {
    $missingPackages += "curl"
}

$gitCheck = & ssh @sshArgs $Hostname "command -v git" 2>&1
if (-not $gitCheck) {
    $missingPackages += "git"
}

# Check for Docker
Write-Info "Checking for Docker..."
$dockerCheck = & ssh @sshArgs $Hostname "command -v docker" 2>&1
if (-not $dockerCheck) {
    $missingPackages += "docker"
} else {
    # Check if user can run docker without sudo
    $dockerTest = & ssh @sshArgs $Hostname "docker ps" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $needsDockerGroup = $true
    }
}

# Check for Docker Compose
Write-Info "Checking for Docker Compose..."
$composeCheck = & ssh @sshArgs $Hostname "command -v docker-compose" 2>&1
if (-not $composeCheck) {
    $missingPackages += "docker-compose"
}

# Handle missing prerequisites
if ($missingPackages.Count -gt 0 -or $needsDockerGroup) {
    Write-Warn "Missing prerequisites detected:"
    
    foreach ($pkg in $missingPackages) {
        Write-Warn "  - $pkg"
    }
    
    if ($needsDockerGroup) {
        Write-Warn "  - User needs to be added to docker group"
    }
    
    Write-Host ""
    
    if ($AutoInstall) {
        $installChoice = "1"
        Write-Info "Auto-install mode: Will attempt to install missing packages"
    } else {
        Write-Host "How would you like to proceed?"
        Write-Host "  1) Install missing packages automatically (requires sudo)"
        Write-Host "  2) Show manual installation guide"
        Write-Host "  3) Exit and install manually"
        $installChoice = Read-Host "Enter choice (1-3)"
    }
    
    switch ($installChoice) {
        { $_ -eq "1" -or $_ -eq "y" -or $_ -eq "Y" } {
            Write-Info "Installing missing packages..."
            
            # Detect OS
            $osType = (& ssh @sshArgs $Hostname "if [ -f /etc/os-release ]; then . /etc/os-release && echo `$ID; else echo 'unknown'; fi").Trim()
            
            if ($osType -eq "debian" -or $osType -eq "ubuntu") {
                # Update package list
                Write-Info "Updating package list..."
                & ssh @sshArgs $Hostname "sudo apt update" | Out-Null
                
                # Install basic tools
                $toInstall = @()
                if ($missingPackages -contains "curl") { $toInstall += "curl" }
                if ($missingPackages -contains "git") { $toInstall += "git" }
                
                if ($toInstall.Count -gt 0) {
                    Write-Info "Installing: $($toInstall -join ', ')"
                    & ssh @sshArgs $Hostname "sudo apt install -y $($toInstall -join ' ')" | Out-Null
                }
                
                # Install Docker
                if ($missingPackages -contains "docker") {
                    Write-Info "Installing Docker..."
                    & ssh @sshArgs $Hostname "curl -fsSL https://get.docker.com -o /tmp/get-docker.sh && sudo sh /tmp/get-docker.sh" | Out-Null
                }
                
                # Install Docker Compose
                if ($missingPackages -contains "docker-compose") {
                    Write-Info "Installing Docker Compose..."
                    & ssh @sshArgs $Hostname "sudo curl -L `"https://github.com/docker/compose/releases/latest/download/docker-compose-`$(uname -s)-`$(uname -m)`" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose" | Out-Null
                }
                
                # Add user to docker group
                if ($needsDockerGroup -or ($missingPackages -contains "docker")) {
                    Write-Info "Adding user to docker group..."
                    & ssh @sshArgs $Hostname "sudo usermod -aG docker `$(whoami) || true" | Out-Null
                    Write-Warn "You may need to log out and back in for docker group to take effect."
                    Write-Warn "For now, we'll continue - if you get permission errors, log out and back in."
                }
            } else {
                Write-Error "Unsupported OS type: $osType"
                Write-Error "Please install prerequisites manually. See VM_SETUP.md for instructions."
                exit 1
            }
            
            # Verify installations
            Write-Info "Verifying installations..."
            Start-Sleep -Seconds 2
            
            # Re-check prerequisites
            $failedChecks = 0
            if ($missingPackages -contains "curl") {
                $check = & ssh @sshArgs $Hostname "command -v curl" 2>&1
                if (-not $check) {
                    Write-Error "curl installation failed"
                    $failedChecks++
                }
            }
            if ($missingPackages -contains "git") {
                $check = & ssh @sshArgs $Hostname "command -v git" 2>&1
                if (-not $check) {
                    Write-Error "git installation failed"
                    $failedChecks++
                }
            }
            if ($missingPackages -contains "docker") {
                $check = & ssh @sshArgs $Hostname "command -v docker" 2>&1
                if (-not $check) {
                    Write-Error "Docker installation failed"
                    $failedChecks++
                }
            }
            if ($missingPackages -contains "docker-compose") {
                $check = & ssh @sshArgs $Hostname "command -v docker-compose" 2>&1
                if (-not $check) {
                    Write-Error "Docker Compose installation failed"
                    $failedChecks++
                }
            }
            
            if ($failedChecks -gt 0) {
                Write-Error "Some installations failed. Please install manually."
                exit 1
            }
            
            Write-Info "All prerequisites installed successfully"
        }
        "2" {
            Write-Host ""
            Write-Guide "=========================================="
            Write-Guide "Manual Installation Guide"
            Write-Guide "=========================================="
            Write-Host ""
            
            $osType = (& ssh @sshArgs $Hostname "if [ -f /etc/os-release ]; then . /etc/os-release && echo `$ID; else echo 'unknown'; fi").Trim()
            
            if ($osType -eq "debian" -or $osType -eq "ubuntu") {
                Write-Guide "For Debian/Ubuntu, run these commands on the VM:"
                Write-Host ""
                
                $toInstall = @()
                if ($missingPackages -contains "curl") { $toInstall += "curl" }
                if ($missingPackages -contains "git") { $toInstall += "git" }
                
                if ($toInstall.Count -gt 0) {
                    Write-Host "  sudo apt update"
                    Write-Host "  sudo apt install -y $($toInstall -join ' ')"
                    Write-Host ""
                }
                
                if ($missingPackages -contains "docker") {
                    Write-Host "  curl -fsSL https://get.docker.com -o get-docker.sh"
                    Write-Host "  sudo sh get-docker.sh"
                    Write-Host "  sudo usermod -aG docker `$USER"
                    Write-Host "  # Log out and back in"
                    Write-Host ""
                }
                
                if ($missingPackages -contains "docker-compose") {
                    Write-Host "  sudo curl -L `"https://github.com/docker/compose/releases/latest/download/docker-compose-`$(uname -s)-`$(uname -m)`" -o /usr/local/bin/docker-compose"
                    Write-Host "  sudo chmod +x /usr/local/bin/docker-compose"
                    Write-Host ""
                }
                
                if ($needsDockerGroup) {
                    Write-Host "  sudo usermod -aG docker `$USER"
                    Write-Host "  # Log out and back in"
                    Write-Host ""
                }
            } else {
                Write-Guide "See VM_SETUP.md for installation instructions for $osType"
            }
            
            Write-Guide "After installing, run this deployment script again."
            Write-Guide "Or see VM_SETUP.md for detailed instructions."
            exit 0
        }
        default {
            Write-Info "Exiting. Please install prerequisites manually and run this script again."
            Write-Info "See VM_SETUP.md for installation instructions."
            exit 0
        }
    }
} else {
    Write-Info "All prerequisites are installed"
}

# Final verification
Write-Info "Final verification of prerequisites..."
$finalCheckFailed = $false

$dockerCheck = & ssh @sshArgs $Hostname "command -v docker" 2>&1
if (-not $dockerCheck) {
    Write-Error "Docker is still not available"
    $finalCheckFailed = $true
}

$composeCheck = & ssh @sshArgs $Hostname "command -v docker-compose" 2>&1
if (-not $composeCheck) {
    Write-Error "Docker Compose is still not available"
    $finalCheckFailed = $true
}

if ($finalCheckFailed) {
    Write-Error "Prerequisites check failed. Please install missing packages and try again."
    exit 1
}

Write-Info "All prerequisites verified successfully"
Write-Host ""

# Create remote directory
Write-Info "Creating remote directory: $RemoteDir"
& ssh @sshArgs $Hostname "mkdir -p $RemoteDir" | Out-Null

# Copy files using SCP
Write-Info "Copying files to $Hostname`:$RemoteDir..."

$scpArgs = @()
if ($Key) {
    $scpArgs += "-i", $Key
}
$scpArgs += "-P", $Port.ToString(), "-r"

# Copy backend
Write-Info "Copying backend..."
& scp @scpArgs backend $Hostname`:$RemoteDir/ 2>&1 | Out-Null

# Copy frontend
Write-Info "Copying frontend..."
& scp @scpArgs frontend $Hostname`:$RemoteDir/ 2>&1 | Out-Null

# Copy docker-compose.yml
Write-Info "Copying docker-compose.yml..."
& scp @scpArgs docker-compose.yml $Hostname`:$RemoteDir/ 2>&1 | Out-Null

# Copy .env.example
Write-Info "Copying .env.example..."
& scp @scpArgs .env.example $Hostname`:$RemoteDir/ 2>&1 | Out-Null

# Copy documentation
Write-Info "Copying documentation..."
& scp @scpArgs README.md INSTALL.md DEPLOY.md QUICKSTART.md VM_SETUP.md $Hostname`:$RemoteDir/ 2>&1 | Out-Null

# Copy .env file if provided
if ($EnvFile -and (Test-Path $EnvFile)) {
    Write-Info "Copying .env file..."
    & scp @scpArgs $EnvFile $Hostname`:$RemoteDir/.env 2>&1 | Out-Null
} elseif (Test-Path ".env") {
    $response = Read-Host "Copy local .env file to remote? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Info "Copying .env file..."
        & scp @scpArgs .env $Hostname`:$RemoteDir/.env 2>&1 | Out-Null
    } else {
        Write-Warn "Skipping .env file copy"
    }
} else {
    Write-Warn "No .env file found. You'll need to create one on the VM"
}

# Set up .env if it doesn't exist
Write-Info "Setting up .env file if needed..."
$envSetupScript = @"
cd $RemoteDir
if [ ! -f .env ]; then
    POSTGRES_PASSWORD=`$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-25)
    SECRET_KEY=`$(openssl rand -base64 48 | tr -d '=+/' | cut -c1-50)
    ADMIN_PASSWORD=`$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-20)
    cat > .env << 'ENVEOF'
# Monitorix Environment Configuration
# Auto-generated on `$(date)

# Database Configuration
POSTGRES_USER=monitorix
POSTGRES_PASSWORD=`${POSTGRES_PASSWORD}
POSTGRES_DB=monitorix
DATABASE_URL=postgresql://monitorix:`${POSTGRES_PASSWORD}@postgres:5432/monitorix

# Security
SECRET_KEY=`${SECRET_KEY}

# Admin User (auto-created on first startup)
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@monitorix.local
ADMIN_PASSWORD=`${ADMIN_PASSWORD}

# Proxmox Configuration
# Format: name:url:username:token (comma-separated for multiple nodes)
# Example: node1:https://192.168.1.10:8006:user@pam:monitorix=abc123-def456-...
PROXMOX_NODES=

# Proxmox SSL Verification (Security)
# Set to 'true' to verify SSL certificates (recommended for production)
# Set to 'false' to disable SSL verification (only for self-signed certificates or testing)
PROXMOX_VERIFY_SSL=true

# Optional: Path to custom CA bundle file for SSL verification
# PROXMOX_CA_BUNDLE=/path/to/ca-bundle.crt

# Health Check Settings
HEALTH_CHECK_INTERVAL=60
HTTP_TIMEOUT=5
PING_TIMEOUT=3

# Email Alerts (Optional)
ALERT_EMAIL_ENABLED=false
ALERT_EMAIL_SMTP_HOST=
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_SMTP_USER=
ALERT_EMAIL_SMTP_PASSWORD=
ALERT_EMAIL_FROM=
ALERT_EMAIL_TO=

# Metrics Retention
METRICS_RETENTION_DAYS=30
METRICS_CLEANUP_ENABLED=true

# Frontend Configuration
FRONTEND_URL=http://localhost:3000
REACT_APP_API_URL=http://localhost:8000
VITE_API_URL=http://localhost:8000
ENVEOF
    sed -i "s/`${POSTGRES_PASSWORD}/`$POSTGRES_PASSWORD/g" .env
    sed -i "s/`${SECRET_KEY}/`$SECRET_KEY/g" .env
    sed -i "s/`${ADMIN_PASSWORD}/`$ADMIN_PASSWORD/g" .env
    chmod 600 .env
    echo 'Created .env with auto-generated passwords'
    echo 'File permissions set to 600 (owner read/write only)'
fi
"@
& ssh @sshArgs $Hostname $envSetupScript | Out-Null

# Build and start services
if (-not $SkipBuild) {
    Write-Info "Building Docker images (this may take a while)..."
    & ssh @sshArgs $Hostname "cd $RemoteDir && docker-compose build" | Out-Null
} else {
    Write-Info "Skipping build (using existing images)"
}

Write-Info "Stopping existing services (if any)..."
& ssh @sshArgs $Hostname "cd $RemoteDir && docker-compose down" 2>&1 | Out-Null

Write-Info "Starting services..."
& ssh @sshArgs $Hostname "cd $RemoteDir && docker-compose up -d" | Out-Null

# Wait for services
Write-Info "Waiting for services to start..."
Start-Sleep -Seconds 10

# Check status
Write-Info "Checking service status..."
& ssh @sshArgs $Hostname "cd $RemoteDir && docker-compose ps"

# Get VM IP
$vmIP = (& ssh @sshArgs $Hostname "hostname -I | awk '{print `$1}'").Trim()

# Get generated passwords for summary
Write-Info "Retrieving installation summary..."
$postgresPassword = (& ssh @sshArgs $Hostname "cd $RemoteDir && grep '^POSTGRES_PASSWORD=' .env | cut -d'=' -f2" 2>&1).Trim()
if (-not $postgresPassword -or $postgresPassword -match "error") {
    $postgresPassword = "***"
}
$secretKey = (& ssh @sshArgs $Hostname "cd $RemoteDir && grep '^SECRET_KEY=' .env | cut -d'=' -f2" 2>&1).Trim()
if (-not $secretKey -or $secretKey -match "error") {
    $secretKey = "***"
}
$adminPassword = (& ssh @sshArgs $Hostname "cd $RemoteDir && grep '^ADMIN_PASSWORD=' .env | cut -d'=' -f2" 2>&1).Trim()
if (-not $adminPassword -or $adminPassword -match "error") {
    $adminPassword = ""
}

Write-Info ""
Write-Info "=========================================="
Write-Info "Deployment completed successfully!"
Write-Info "=========================================="
Write-Info ""
Write-Info "╔══════════════════════════════════════════════════════════╗"
Write-Info "║                    INSTALLATION SUMMARY                   ║"
Write-Info "╚══════════════════════════════════════════════════════════╝"
Write-Info ""
Write-Info "📍 Access URLs:"
Write-Info "   Frontend:  http://$vmIP:3000"
Write-Info "   Backend:   http://$vmIP:8000"
Write-Info "   API Docs:  http://$vmIP:8000/docs"
Write-Info ""
Write-Info "🔐 Generated Credentials:"
Write-Info "   PostgreSQL User:     monitorix"
Write-Info "   PostgreSQL Password: $postgresPassword"
Write-Info "   Database Name:       monitorix"
Write-Info ""
Write-Info "👤 Monitorix Admin User:"
Write-Info "   Username:            admin"
Write-Info "   Email:               admin@monitorix.local"
if ($adminPassword -and $adminPassword -ne "***") {
    Write-Info "   Password:            $adminPassword"
}
Write-Info ""
Write-Warn "⚠️  IMPORTANT: Save these credentials!"
Write-Warn "   All passwords are stored in: $RemoteDir/.env"
Write-Warn "   SSH into VM to view: ssh $Hostname 'cat $RemoteDir/.env'"
Write-Info ""
Write-Info "📋 Next Steps:"
Write-Info "   1. SSH into VM: ssh $Hostname"
Write-Info "   2. Register first user: http://$vmIP:3000"
Write-Info "   3. Configure Proxmox nodes:"
Write-Info "      cd $RemoteDir && nano .env"
Write-Info "      Add: PROXMOX_NODES=node1:https://ip:8006:user@pam:token"
Write-Info "   4. Restart services: docker-compose restart"
Write-Info ""
Write-Info "📝 Configuration File:"
Write-Info "   Location: $RemoteDir/.env (on VM)"
Write-Info "   View: ssh $Hostname 'cat $RemoteDir/.env'"
Write-Info ""
Write-Warn "🔒 Security Reminders:"
Write-Warn "   - Passwords are auto-generated and secure"
Write-Warn "   - Configure firewall if exposing to network"
Write-Warn "   - Set up SSL via Nginx Proxy Manager for production"
Write-Info ""
Write-Info "✨ Monitorix is ready to use!"
Write-Info ""
