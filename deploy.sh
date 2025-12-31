#!/bin/bash

# Monitorix Deployment Script
# Checks prerequisites and optionally installs them before deployment
# Usage: ./deploy.sh [user@]hostname [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SSH_PORT=22
SSH_KEY=""
REMOTE_DIR="~/monitorix"
SKIP_BUILD=false
ENV_FILE=""
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
if [ $# -lt 1 ]; then
    echo "Usage: $0 [user@]hostname [options]"
    echo ""
    echo "Options:"
    echo "  -p PORT          SSH port (default: 22)"
    echo "  -k KEY           SSH private key path"
    echo "  -d DIR           Remote directory (default: ~/monitorix)"
    echo "  --skip-build     Skip Docker image build"
    echo "  --env-file FILE  Path to .env file to copy"
    echo "  --auto-install   Automatically install missing prerequisites (non-interactive)"
    exit 1
fi

HOST=$1
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        -p)
            SSH_PORT="$2"
            shift 2
            ;;
        -k)
            SSH_KEY="$2"
            shift 2
            ;;
        -d)
            REMOTE_DIR="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --auto-install)
            AUTO_INSTALL=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build SSH command
SSH_CMD="ssh"
if [ -n "$SSH_KEY" ]; then
    SSH_CMD="$SSH_CMD -i $SSH_KEY"
fi
SSH_CMD="$SSH_CMD -p $SSH_PORT"

# Test SSH connection
print_info "Testing SSH connection to $HOST..."
if ! $SSH_CMD -o ConnectTimeout=5 -o BatchMode=yes $HOST "echo 'Connection successful'" > /dev/null 2>&1; then
    print_error "Cannot connect to $HOST. Please check:"
    print_error "  - SSH access is configured"
    print_error "  - Hostname/IP is correct"
    print_error "  - Port is correct ($SSH_PORT)"
    print_error "  - SSH key is correct (if using -k)"
    exit 1
fi
print_info "SSH connection successful"

# Check prerequisites
print_info "Checking prerequisites on remote host..."

MISSING_PACKAGES=()
NEEDS_DOCKER_GROUP=false

# Check for basic tools
print_info "Checking for basic tools..."
if ! $SSH_CMD $HOST "command -v curl > /dev/null 2>&1"; then
    MISSING_PACKAGES+=("curl")
fi
if ! $SSH_CMD $HOST "command -v git > /dev/null 2>&1"; then
    MISSING_PACKAGES+=("git")
fi

# Check for Docker
print_info "Checking for Docker..."
if ! $SSH_CMD $HOST "command -v docker > /dev/null 2>&1"; then
    MISSING_PACKAGES+=("docker")
else
    # Check if user can run docker without sudo
    if ! $SSH_CMD $HOST "docker ps > /dev/null 2>&1"; then
        NEEDS_DOCKER_GROUP=true
    fi
fi

# Check for Docker Compose
print_info "Checking for Docker Compose..."
if ! $SSH_CMD $HOST "command -v docker-compose > /dev/null 2>&1"; then
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
        INSTALL_CHOICE="y"
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
            OS_TYPE=$($SSH_CMD $HOST "if [ -f /etc/os-release ]; then . /etc/os-release && echo \$ID; else echo 'unknown'; fi")
            
            if [ "$OS_TYPE" = "debian" ] || [ "$OS_TYPE" = "ubuntu" ]; then
                # Update package list
                print_info "Updating package list..."
                $SSH_CMD $HOST "sudo apt update"
                
                # Install basic tools
                if [[ " ${MISSING_PACKAGES[@]} " =~ " curl " ]] || [[ " ${MISSING_PACKAGES[@]} " =~ " git " ]]; then
                    TO_INSTALL=""
                    [[ " ${MISSING_PACKAGES[@]} " =~ " curl " ]] && TO_INSTALL="$TO_INSTALL curl "
                    [[ " ${MISSING_PACKAGES[@]} " =~ " git " ]] && TO_INSTALL="$TO_INSTALL git "
                    if [ -n "$TO_INSTALL" ]; then
                        print_info "Installing: $TO_INSTALL"
                        $SSH_CMD $HOST "sudo apt install -y $TO_INSTALL"
                    fi
                fi
                
                # Install Docker
                if [[ " ${MISSING_PACKAGES[@]} " =~ " docker " ]]; then
                    print_info "Installing Docker..."
                    $SSH_CMD $HOST "curl -fsSL https://get.docker.com -o /tmp/get-docker.sh && sudo sh /tmp/get-docker.sh"
                fi
                
                # Install Docker Compose
                if [[ " ${MISSING_PACKAGES[@]} " =~ " docker-compose " ]]; then
                    print_info "Installing Docker Compose..."
                    $SSH_CMD $HOST "sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose"
                fi
                
                # Add user to docker group
                if [ "$NEEDS_DOCKER_GROUP" = true ] || [[ " ${MISSING_PACKAGES[@]} " =~ " docker " ]]; then
                    print_info "Adding user to docker group..."
                    $SSH_CMD $HOST "sudo usermod -aG docker \$(whoami) || true"
                    print_warn "You may need to log out and back in for docker group to take effect."
                    print_warn "For now, we'll continue - if you get permission errors, log out and back in."
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
            if [[ " ${MISSING_PACKAGES[@]} " =~ " curl " ]] && ! $SSH_CMD $HOST "command -v curl > /dev/null 2>&1"; then
                print_error "curl installation failed"
                FAILED_CHECKS=$((FAILED_CHECKS + 1))
            fi
            if [[ " ${MISSING_PACKAGES[@]} " =~ " git " ]] && ! $SSH_CMD $HOST "command -v git > /dev/null 2>&1"; then
                print_error "git installation failed"
                FAILED_CHECKS=$((FAILED_CHECKS + 1))
            fi
            if [[ " ${MISSING_PACKAGES[@]} " =~ " docker " ]] && ! $SSH_CMD $HOST "command -v docker > /dev/null 2>&1"; then
                print_error "Docker installation failed"
                FAILED_CHECKS=$((FAILED_CHECKS + 1))
            fi
            if [[ " ${MISSING_PACKAGES[@]} " =~ " docker-compose " ]] && ! $SSH_CMD $HOST "command -v docker-compose > /dev/null 2>&1"; then
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
            
            OS_TYPE=$($SSH_CMD $HOST "if [ -f /etc/os-release ]; then . /etc/os-release && echo \$ID; else echo 'unknown'; fi")
            
            if [ "$OS_TYPE" = "debian" ] || [ "$OS_TYPE" = "ubuntu" ]; then
                print_guide "For Debian/Ubuntu, run these commands on the VM:"
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
                    echo "  # Log out and back in"
                    echo ""
                fi
                
                if [[ " ${MISSING_PACKAGES[@]} " =~ " docker-compose " ]]; then
                    echo "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
                    echo "  sudo chmod +x /usr/local/bin/docker-compose"
                    echo ""
                fi
                
                if [ "$NEEDS_DOCKER_GROUP" = true ]; then
                    echo "  sudo usermod -aG docker \$USER"
                    echo "  # Log out and back in"
                    echo ""
                fi
            else
                print_guide "See VM_SETUP.md for installation instructions for $OS_TYPE"
            fi
            
            print_guide "After installing, run this deployment script again."
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

if ! $SSH_CMD $HOST "command -v docker > /dev/null 2>&1"; then
    print_error "Docker is still not available"
    FINAL_CHECK_FAILED=true
fi

if ! $SSH_CMD $HOST "command -v docker-compose > /dev/null 2>&1"; then
    print_error "Docker Compose is still not available"
    FINAL_CHECK_FAILED=true
fi

if [ "$FINAL_CHECK_FAILED" = true ]; then
    print_error "Prerequisites check failed. Please install missing packages and try again."
    exit 1
fi

print_info "All prerequisites verified successfully"
echo ""

# Create remote directory
print_info "Creating remote directory: $REMOTE_DIR"
$SSH_CMD $HOST "mkdir -p $REMOTE_DIR"

# Copy files
print_info "Copying files to $HOST:$REMOTE_DIR..."

# Build rsync command
RSYNC_CMD="rsync -avz"
if [ -n "$SSH_KEY" ]; then
    RSYNC_CMD="$RSYNC_CMD -e \"ssh -i $SSH_KEY -p $SSH_PORT\""
else
    RSYNC_CMD="$RSYNC_CMD -e \"ssh -p $SSH_PORT\""
fi

# Exclude patterns
EXCLUDE="--exclude 'node_modules' --exclude '.git' --exclude 'frontend/node_modules' \
  --exclude 'backend/__pycache__' --exclude '*.pyc' --exclude '__pycache__' \
  --exclude '.env' --exclude '*.log' --exclude '.DS_Store' --exclude 'Thumbs.db'"

# Copy files
eval "$RSYNC_CMD $EXCLUDE ./ $HOST:$REMOTE_DIR/"

# Copy .env file if provided
if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
    print_info "Copying .env file..."
    $SSH_CMD $HOST "cat > $REMOTE_DIR/.env" < "$ENV_FILE"
elif [ -f ".env" ]; then
    read -p "Copy local .env file to remote? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Copying .env file..."
        $SSH_CMD $HOST "cat > $REMOTE_DIR/.env" < ".env"
    else
        print_warn "Skipping .env file copy"
    fi
else
    print_warn "No .env file found. You'll need to create one on the VM"
fi

# Set up .env if it doesn't exist
print_info "Setting up .env file if needed..."
$SSH_CMD $HOST "cd $REMOTE_DIR && if [ ! -f .env ]; then cp .env.example .env && echo 'Created .env from .env.example - please edit it!'; fi"

# Build and start services
if [ "$SKIP_BUILD" = false ]; then
    print_info "Building Docker images (this may take a while)..."
    $SSH_CMD $HOST "cd $REMOTE_DIR && docker-compose build"
else
    print_info "Skipping build (using existing images)"
fi

print_info "Stopping existing services (if any)..."
$SSH_CMD $HOST "cd $REMOTE_DIR && docker-compose down || true"

print_info "Starting services..."
$SSH_CMD $HOST "cd $REMOTE_DIR && docker-compose up -d"

# Wait for services to start
print_info "Waiting for services to start..."
sleep 10

# Check service status
print_info "Checking service status..."
$SSH_CMD $HOST "cd $REMOTE_DIR && docker-compose ps"

# Get VM IP
VM_IP=$($SSH_CMD $HOST "hostname -I | awk '{print \$1}'" | tr -d '\r\n')

print_info ""
print_info "=========================================="
print_info "Deployment completed successfully!"
print_info "=========================================="
print_info ""
print_info "Access your dashboard:"
print_info "  Frontend:  http://$VM_IP:3000"
print_info "  Backend:   http://$VM_IP:8000"
print_info "  API Docs:  http://$VM_IP:8000/docs"
print_info ""
print_info "Next steps:"
print_info "  1. SSH into VM: ssh $HOST"
print_info "  2. Edit .env: cd $REMOTE_DIR && nano .env"
print_info "  3. Configure Proxmox nodes in .env"
print_info "  4. Restart if needed: docker-compose restart"
print_info "  5. Register first user at http://$VM_IP:3000"
print_info ""
print_warn "Remember to:"
print_warn "  - Change default passwords in .env"
print_warn "  - Configure firewall if needed"
print_warn "  - Set up SSL via Nginx Proxy Manager (optional)"
print_info ""
