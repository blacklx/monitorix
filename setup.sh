#!/bin/bash

# Monitorix Local Setup Script
# Run this script directly on the VM where you want to deploy
# Usage: ./setup.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SKIP_BUILD=false
AUTO_INSTALL=false

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_guide() {
    echo -e "${BLUE}[GUIDE]${NC} $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --auto-install)
            AUTO_INSTALL=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Usage: $0 [--skip-build] [--auto-install]"
            exit 1
            ;;
    esac
done

print_info "Monitorix - Local Setup"
print_info "======================================"
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

MISSING_PACKAGES=()
NEEDS_DOCKER_GROUP=false

# Check for basic tools
if ! command -v curl > /dev/null 2>&1; then
    MISSING_PACKAGES+=("curl")
fi
if ! command -v git > /dev/null 2>&1; then
    MISSING_PACKAGES+=("git")
fi

# Check for Docker
if ! command -v docker > /dev/null 2>&1; then
    MISSING_PACKAGES+=("docker")
else
    # Check if user can run docker without sudo
    if ! docker ps > /dev/null 2>&1; then
        NEEDS_DOCKER_GROUP=true
    fi
fi

# Check for Docker Compose
if ! command -v docker-compose > /dev/null 2>&1; then
    MISSING_PACKAGES+=("docker-compose")
fi

# Handle missing prerequisites
if [ ${#MISSING_PACKAGES[@]} -gt 0 ] || [ "$NEEDS_DOCKER_GROUP" = true ]; then
    print_warn "Missing prerequisites detected:"
    
    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        for pkg in "${MISSING_PACKAGES[@]}"; do
            print_warn "  - $pkg"
        done
    fi
    
    if [ "$NEEDS_DOCKER_GROUP" = true ]; then
        print_warn "  - User needs to be added to docker group"
    fi
    
    echo ""
    
    if [ "$AUTO_INSTALL" = true ]; then
        INSTALL_CHOICE="1"
        print_info "Auto-install mode: Will attempt to install missing packages"
    else
        echo "How would you like to proceed?"
        echo "  1) Install missing packages automatically (requires sudo)"
        echo "  2) Show manual installation guide"
        echo "  3) Exit and install manually"
        read -p "Enter choice (1-3): " INSTALL_CHOICE
    fi
    
    case $INSTALL_CHOICE in
        1|y|Y|yes|YES)
            print_info "Installing missing packages..."
            
            # Detect OS
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                OS_TYPE=$ID
            else
                OS_TYPE="unknown"
            fi
            
            if [ "$OS_TYPE" = "debian" ] || [ "$OS_TYPE" = "ubuntu" ]; then
                # Update package list
                print_info "Updating package list..."
                sudo apt update
                
                # Install basic tools
                if [[ " ${MISSING_PACKAGES[@]} " =~ " curl " ]] || [[ " ${MISSING_PACKAGES[@]} " =~ " git " ]]; then
                    TO_INSTALL=""
                    [[ " ${MISSING_PACKAGES[@]} " =~ " curl " ]] && TO_INSTALL="$TO_INSTALL curl "
                    [[ " ${MISSING_PACKAGES[@]} " =~ " git " ]] && TO_INSTALL="$TO_INSTALL git "
                    if [ -n "$TO_INSTALL" ]; then
                        print_info "Installing: $TO_INSTALL"
                        sudo apt install -y $TO_INSTALL
                    fi
                fi
                
                # Install Docker
                if [[ " ${MISSING_PACKAGES[@]} " =~ " docker " ]]; then
                    print_info "Installing Docker..."
                    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
                    sudo sh /tmp/get-docker.sh
                fi
                
                # Install Docker Compose
                if [[ " ${MISSING_PACKAGES[@]} " =~ " docker-compose " ]]; then
                    print_info "Installing Docker Compose..."
                    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
                    sudo chmod +x /usr/local/bin/docker-compose
                fi
                
                # Add user to docker group
                if [ "$NEEDS_DOCKER_GROUP" = true ] || [[ " ${MISSING_PACKAGES[@]} " =~ " docker " ]]; then
                    print_info "Adding user to docker group..."
                    sudo usermod -aG docker $USER
                    print_warn "You need to log out and back in for docker group to take effect."
                    print_warn "Or run: newgrp docker"
                    print_warn "For now, we'll continue - if you get permission errors, run 'newgrp docker' or log out and back in."
                fi
            else
                print_error "Unsupported OS type: $OS_TYPE"
                print_error "Please install prerequisites manually. See VM_SETUP.md for instructions."
                exit 1
            fi
            
            # Verify installations
            print_info "Verifying installations..."
            sleep 2
            
            # Re-check prerequisites
            FAILED_CHECKS=0
            if [[ " ${MISSING_PACKAGES[@]} " =~ " curl " ]] && ! command -v curl > /dev/null 2>&1; then
                print_error "curl installation failed"
                FAILED_CHECKS=$((FAILED_CHECKS + 1))
            fi
            if [[ " ${MISSING_PACKAGES[@]} " =~ " git " ]] && ! command -v git > /dev/null 2>&1; then
                print_error "git installation failed"
                FAILED_CHECKS=$((FAILED_CHECKS + 1))
            fi
            if [[ " ${MISSING_PACKAGES[@]} " =~ " docker " ]] && ! command -v docker > /dev/null 2>&1; then
                print_error "Docker installation failed"
                FAILED_CHECKS=$((FAILED_CHECKS + 1))
            fi
            if [[ " ${MISSING_PACKAGES[@]} " =~ " docker-compose " ]] && ! command -v docker-compose > /dev/null 2>&1; then
                print_error "Docker Compose installation failed"
                FAILED_CHECKS=$((FAILED_CHECKS + 1))
            fi
            
            if [ $FAILED_CHECKS -gt 0 ]; then
                print_error "Some installations failed. Please install manually."
                exit 1
            fi
            
            print_info "All prerequisites installed successfully"
            ;;
        2)
            echo ""
            print_guide "=========================================="
            print_guide "Manual Installation Guide"
            print_guide "=========================================="
            echo ""
            
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                OS_TYPE=$ID
            else
                OS_TYPE="unknown"
            fi
            
            if [ "$OS_TYPE" = "debian" ] || [ "$OS_TYPE" = "ubuntu" ]; then
                print_guide "For Debian/Ubuntu, run these commands:"
                echo ""
                
                if [[ " ${MISSING_PACKAGES[@]} " =~ " curl " ]] || [[ " ${MISSING_PACKAGES[@]} " =~ " git " ]]; then
                    TO_INSTALL=""
                    [[ " ${MISSING_PACKAGES[@]} " =~ " curl " ]] && TO_INSTALL="$TO_INSTALL curl "
                    [[ " ${MISSING_PACKAGES[@]} " =~ " git " ]] && TO_INSTALL="$TO_INSTALL git "
                    echo "  sudo apt update"
                    echo "  sudo apt install -y $TO_INSTALL"
                    echo ""
                fi
                
                if [[ " ${MISSING_PACKAGES[@]} " =~ " docker " ]]; then
                    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
                    echo "  sudo sh get-docker.sh"
                    echo "  sudo usermod -aG docker \$USER"
                    echo "  # Log out and back in, or run: newgrp docker"
                    echo ""
                fi
                
                if [[ " ${MISSING_PACKAGES[@]} " =~ " docker-compose " ]]; then
                    echo "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
                    echo "  sudo chmod +x /usr/local/bin/docker-compose"
                    echo ""
                fi
                
                if [ "$NEEDS_DOCKER_GROUP" = true ]; then
                    echo "  sudo usermod -aG docker \$USER"
                    echo "  # Log out and back in, or run: newgrp docker"
                    echo ""
                fi
            else
                print_guide "See VM_SETUP.md for installation instructions for $OS_TYPE"
            fi
            
            print_guide "After installing, run this setup script again."
            print_guide "Or see VM_SETUP.md for detailed instructions."
            exit 0
            ;;
        3|*)
            print_info "Exiting. Please install prerequisites manually and run this script again."
            print_info "See VM_SETUP.md for installation instructions."
            exit 0
            ;;
    esac
else
    print_info "All prerequisites are installed"
fi

# Final verification
print_info "Final verification of prerequisites..."
FINAL_CHECK_FAILED=false

if ! command -v docker > /dev/null 2>&1; then
    print_error "Docker is still not available"
    FINAL_CHECK_FAILED=true
fi

if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "Docker Compose is still not available"
    FINAL_CHECK_FAILED=true
fi

# Check Docker permissions
if ! docker ps > /dev/null 2>&1; then
    print_error "Cannot run Docker commands. You may need to:"
    print_error "  1. Run: newgrp docker"
    print_error "  2. Or log out and back in"
    print_error "  3. Or run: sudo usermod -aG docker \$USER"
    FINAL_CHECK_FAILED=true
fi

if [ "$FINAL_CHECK_FAILED" = true ]; then
    print_error "Prerequisites check failed. Please fix the issues above and try again."
    exit 1
fi

print_info "All prerequisites verified successfully"
echo ""

# Generate passwords and create .env file
if [ ! -f .env ]; then
    print_info "Creating .env file with auto-generated passwords..."
    
    # Generate secure passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    SECRET_KEY=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-50)
    ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-20)
    
    # Create .env file
    cat > .env << EOF
# Monitorix Environment Configuration
# Auto-generated on $(date)

# Database Configuration
POSTGRES_USER=monitorix
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=monitorix
DATABASE_URL=postgresql://monitorix:${POSTGRES_PASSWORD}@postgres:5432/monitorix

# Security
SECRET_KEY=${SECRET_KEY}

# Admin User (auto-created on first startup)
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@monitorix.local
ADMIN_PASSWORD=${ADMIN_PASSWORD}

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

# Frontend API URL
REACT_APP_API_URL=http://localhost:8000
VITE_API_URL=http://localhost:8000
EOF
    
    print_info ".env file created with auto-generated passwords"
    ADMIN_PASSWORD_SET=true
else
    print_info ".env file already exists, using existing configuration"
    # Read existing passwords for summary
    POSTGRES_PASSWORD=$(grep "^POSTGRES_PASSWORD=" .env | cut -d'=' -f2 || echo "***")
    SECRET_KEY=$(grep "^SECRET_KEY=" .env | cut -d'=' -f2 || echo "***")
    ADMIN_PASSWORD=$(grep "^ADMIN_PASSWORD=" .env | cut -d'=' -f2 || echo "")
    ADMIN_PASSWORD_SET=false
fi

# Build and start services
if [ "$SKIP_BUILD" = false ]; then
    print_info "Building Docker images (this may take a while)..."
    docker-compose build
else
    print_info "Skipping build (using existing images)"
fi

print_info "Stopping existing services (if any)..."
docker-compose down || true

print_info "Starting services..."
docker-compose up -d

# Wait for services to start
print_info "Waiting for services to start..."
sleep 15

# Check service status
print_info "Checking service status..."
docker-compose ps

# Get admin password from backend logs if it was auto-generated
if [ "$ADMIN_PASSWORD_SET" = false ] || [ -z "$ADMIN_PASSWORD" ]; then
    print_info "Checking for auto-generated admin password..."
    sleep 5
    ADMIN_PASSWORD_FROM_LOG=$(docker-compose logs backend 2>/dev/null | grep -i "Password:" | tail -1 | sed 's/.*Password: //' | tr -d '\r\n' || echo "")
    if [ -n "$ADMIN_PASSWORD_FROM_LOG" ]; then
        ADMIN_PASSWORD="$ADMIN_PASSWORD_FROM_LOG"
    fi
fi

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

print_info ""
print_info "=========================================="
print_info "Setup completed successfully!"
print_info "=========================================="
print_info ""
print_info "╔══════════════════════════════════════════════════════════╗"
print_info "║                    INSTALLATION SUMMARY                   ║"
print_info "╚══════════════════════════════════════════════════════════╝"
print_info ""
print_info "📍 Access URLs:"
print_info "   Frontend:  http://localhost:3000"
print_info "   Backend:   http://localhost:8000"
print_info "   API Docs:  http://localhost:8000/docs"
if [ -n "$LOCAL_IP" ]; then
    print_info ""
    print_info "   Network access:"
    print_info "   Frontend:  http://$LOCAL_IP:3000"
    print_info "   Backend:   http://$LOCAL_IP:8000"
fi
print_info ""
print_info "🔐 Generated Credentials:"
print_info "   PostgreSQL User:     monitorix"
print_info "   PostgreSQL Password:  ${POSTGRES_PASSWORD}"
print_info "   Database Name:       monitorix"
print_info ""
print_info "👤 Admin User:"
print_info "   Username:            admin"
print_info "   Email:              admin@monitorix.local"
if [ -n "$ADMIN_PASSWORD" ] && [ "$ADMIN_PASSWORD" != "***" ]; then
    print_info "   Password:            ${ADMIN_PASSWORD}"
else
    print_warn "   Password:            (Check backend logs: docker-compose logs backend | grep Password)"
fi
print_info ""
print_warn "⚠️  IMPORTANT: Save these credentials!"
print_warn "   The PostgreSQL password is stored in: .env"
print_warn "   Admin password is shown above (or in backend logs if auto-generated)"
print_warn "   Keep this file secure and back it up."
print_info ""
print_info "📋 Next Steps:"
print_info "   1. Register first user: http://localhost:3000"
print_info "   2. Configure Proxmox nodes in .env file:"
print_info "      nano .env"
print_info "      Add: PROXMOX_NODES=node1:https://ip:8006:user@pam:token"
print_info "   3. Restart services: docker-compose restart"
print_info ""
print_info "📝 Configuration File:"
print_info "   Location: $(pwd)/.env"
print_info "   Edit with: nano .env"
print_info ""
print_warn "🔒 Security Reminders:"
print_warn "   - Passwords are auto-generated and secure"
print_warn "   - Configure firewall if exposing to network"
print_warn "   - Set up SSL via Nginx Proxy Manager for production"
print_info ""
print_info "✨ Monitorix is ready to use!"
print_info ""

