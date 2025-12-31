# Deployment Guide

This guide helps you deploy Monitorix to a VM.

## Prerequisites

- A VM with Debian 12 (or Ubuntu 22.04+)
- SSH access to the VM (if deploying remotely)
- User has sudo permissions (for package installation)

## Quick Deployment

### Option 1: Local Setup (Recommended)

**Run directly on the VM:**

```bash
# Copy project files to VM (via git, scp, or other method)
cd ~/monitorix

# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

The script will:
- Check for all prerequisites (Docker, Docker Compose, curl, git)
- Prompt to install missing packages or show manual guide
- Set up .env file
- Build and start all services

### Option 2: Remote Deployment

**Deploy from your local machine to VM:**

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh user@your-vm-ip
```

**Windows:**
```powershell
.\deploy.ps1 user@your-vm-ip
```

The script will:
- Check prerequisites on remote VM
- Prompt to install missing packages or show manual guide
- Copy all files to the VM
- Set up the system
- Build and start all services

### Script Options

```bash
# With SSH key
./deploy.sh user@vm-ip -k ~/.ssh/id_rsa

# With custom SSH port
./deploy.sh user@vm-ip -p 2222

# With custom remote directory
./deploy.sh user@vm-ip -d /opt/monitorix

# Skip build (use existing images)
./deploy.sh user@vm-ip --skip-build

# Copy .env file
./deploy.sh user@vm-ip --env-file .env

# Auto-install missing prerequisites (non-interactive)
./deploy.sh user@vm-ip --auto-install
```

### Prerequisites Check

The script will check for:
- **curl** - For downloading files
- **git** - For version control (optional but recommended)
- **Docker** - Container runtime
- **Docker Compose** - Container orchestration
- **Docker group membership** - User permissions

If anything is missing, you'll be prompted to:
1. **Install automatically** - Script will install missing packages (requires sudo)
2. **Show manual guide** - Display commands to run manually
3. **Exit** - Install manually and run script again

For non-interactive use, use `--auto-install` flag.

## Manual Deployment

### Step 1: Prepare Local Files

Ensure you have a `.env` file configured:

```bash
cp .env.example .env
# Edit .env with your settings
```

### Step 2: Copy Files to VM

From your local machine:

```bash
# Create directory on VM
ssh user@your-vm-ip "mkdir -p ~/monitorix"

# Copy files (excluding node_modules, .git, etc.)
rsync -avz --exclude 'node_modules' --exclude '.git' --exclude 'frontend/node_modules' \
  --exclude '*.pyc' --exclude '__pycache__' --exclude '.env' \
  ./ user@your-vm-ip:~/monitorix/
```

Or using SCP:

```bash
scp -r backend frontend docker-compose.yml .env.example \
  README.md INSTALL.md user@your-vm-ip:~/monitorix/
```

### Step 3: SSH into VM

```bash
ssh user@your-vm-ip
cd ~/monitorix
```

### Step 4: Configure Environment

```bash
# Copy and edit .env
cp .env.example .env
nano .env
```

Fill in your configuration:
- Database password
- SECRET_KEY (generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`)
- Proxmox nodes configuration

### Step 5: Start Services

```bash
# Build and start
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 6: Access Dashboard

- Frontend: `http://your-vm-ip:3000`
- Backend API: `http://your-vm-ip:8000`
- API Docs: `http://your-vm-ip:8000/docs`

## VM Setup (One-time)

If your VM doesn't have Docker installed yet:

### Debian 12

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl git

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in for group changes
exit
```

SSH back in and verify:

```bash
docker --version
docker-compose --version
docker ps
```

## Post-Deployment

### Firewall Configuration

If using UFW:

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8000/tcp  # Backend API
sudo ufw enable
```

### Set Up Nginx Proxy Manager

If you want to use a domain name:

1. Point your domain to the VM IP
2. In Nginx Proxy Manager, create proxy hosts:
   - Frontend: `status.yourdomain.com` → `your-vm-ip:3000`
   - Backend: `api.yourdomain.com` → `your-vm-ip:8000`
3. Enable SSL certificates
4. Update `.env` with new API URL:
   ```env
   REACT_APP_API_URL=https://api.yourdomain.com
   ```
5. Rebuild frontend:
   ```bash
   docker-compose build frontend
   docker-compose up -d frontend
   ```

### Systemd Service (Optional)

Create a systemd service for auto-start:

```bash
sudo nano /etc/systemd/system/monitorix.service
```

Add:

```ini
[Unit]
Description=Monitorix
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user/monitorix
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=user
Group=docker

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable monitorix
sudo systemctl start monitorix
```

## Updating

To update the system:

```bash
# On your local machine
git pull
./deploy.sh user@your-vm-ip
```

Or manually on the VM:

```bash
# On VM
cd ~/monitorix
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

## Backup

### Database Backup

```bash
# On VM
docker-compose exec postgres pg_dump -U monitorix monitorix > backup_$(date +%Y%m%d).sql

# Copy to local machine
scp user@your-vm-ip:~/monitorix/backup_*.sql ./
```

### Restore Database

```bash
# On VM
docker-compose exec -T postgres psql -U monitorix monitorix < backup.sql
```

## Troubleshooting

### Docker Permission Denied

```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Port Already in Use

Check what's using the port:

```bash
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8000
```

### Cannot Connect to Proxmox

- Verify Proxmox API is accessible from VM
- Check firewall rules
- Verify token has correct permissions
- Test manually:
  ```bash
  curl -k -H "Authorization: PVETokenID=token_id=token_secret" https://proxmox-ip:8006/api2/json/version
  ```

### Out of Disk Space

```bash
# Clean up Docker
docker system prune -a

# Remove old images
docker image prune -a

# Clean up old metrics in database
docker-compose exec postgres psql -U monitorix monitorix -c "DELETE FROM metrics WHERE recorded_at < NOW() - INTERVAL '30 days';"
```

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

## Security Considerations

1. **Change default passwords** in `.env`
2. **Use strong SECRET_KEY** (32+ characters)
3. **Enable firewall** (UFW)
4. **Use SSH keys** instead of passwords
5. **Keep system updated**: `sudo apt update && sudo apt upgrade`
6. **Use SSL/TLS** via Nginx Proxy Manager
7. **Limit SSH access** to specific IPs if possible
8. **Regular backups** of database

---

**Need help?** Check [INSTALL.md](INSTALL.md) for detailed installation instructions.
