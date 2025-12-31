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

# Check if .env exists
if [ ! -f .env ]; then
    print_info "Creating .env file from .env.example..."
    cp .env.example .env
    print_warn "Please edit .env file with your configuration:"
    print_warn "  nano .env"
    echo ""
    read -p "Press Enter to continue after editing .env, or Ctrl+C to exit..."
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
sleep 10

# Check service status
print_info "Checking service status..."
docker-compose ps

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

print_info ""
print_info "=========================================="
print_info "Setup completed successfully!"
print_info "=========================================="
print_info ""
print_info "Access your dashboard:"
print_info "  Frontend:  http://localhost:3000"
print_info "  Backend:   http://localhost:8000"
print_info "  API Docs:  http://localhost:8000/docs"
if [ -n "$LOCAL_IP" ]; then
    print_info ""
    print_info "Or from other machines on your network:"
    print_info "  Frontend:  http://$LOCAL_IP:3000"
    print_info "  Backend:   http://$LOCAL_IP:8000"
fi
print_info ""
print_info "Next steps:"
print_info "  1. Edit .env: nano .env"
print_info "  2. Configure Proxmox nodes in .env"
print_info "  3. Restart if needed: docker-compose restart"
print_info "  4. Register first user at http://localhost:3000"
print_info ""
print_warn "Remember to:"
print_warn "  - Change default passwords in .env"
print_warn "  - Configure firewall if needed"
print_warn "  - Set up SSL via Nginx Proxy Manager (optional)"
print_info ""

