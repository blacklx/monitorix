# VM Setup Guide for Debian 12

This guide helps you set up a fresh Debian 12 VM for running Monitorix.

## Initial VM Setup

### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Required Packages

```bash
sudo apt install -y curl git nano ufw
```

### Step 3: Install Docker

```bash
# Install Docker using official script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Verify installation
docker --version
```

**Important**: Log out and back in for the docker group to take effect.

### Step 4: Install Docker Compose

```bash
# Download latest Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### Step 5: Configure Firewall (Optional but Recommended)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS (if using Nginx Proxy Manager)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Or allow direct access (if not using proxy)
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8000/tcp  # Backend

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Step 6: Verify Docker Works

```bash
# Test Docker (should work without sudo after logging back in)
docker ps

# Test Docker Compose
docker-compose --version
```

## SSH Configuration (Optional)

### Set Up SSH Key Authentication

On your local machine:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to VM
ssh-copy-id user@your-vm-ip
```

### Disable Password Authentication (Security)

On the VM:

```bash
sudo nano /etc/ssh/sshd_config
```

Set:
```
PasswordAuthentication no
PubkeyAuthentication yes
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

## Monitorix Deployment

Once your VM is set up, deploy the dashboard:

### Option 1: Local Setup (Recommended)

```bash
# On the VM
cd ~/monitorix
chmod +x setup.sh
./setup.sh
```

### Option 2: Remote Deployment

```bash
# From your local machine
./deploy.sh user@your-vm-ip
```

See [DEPLOY.md](DEPLOY.md) for more details.

## Upgrading to Debian Trixie (Testing)

If you want to upgrade from Debian 12 (Bookworm) to Debian Trixie (Testing):

**⚠️ Warning**: Upgrading to testing/unstable can break things. Only do this if you're comfortable with potential issues.

```bash
# Backup first!
sudo apt update && sudo apt upgrade -y

# Change sources to testing
sudo sed -i 's/bookworm/testing/g' /etc/apt/sources.list
sudo sed -i 's/bookworm/testing/g' /etc/apt/sources.list.d/*.list

# Update package lists
sudo apt update

# Upgrade system
sudo apt full-upgrade -y

# Reboot
sudo reboot
```

After reboot, verify everything still works:

```bash
docker --version
docker-compose --version
docker ps
```

## Maintenance

### Keep System Updated

```bash
# Regular updates
sudo apt update && sudo apt upgrade -y

# Reboot if kernel was updated
sudo reboot
```

### Monitor Disk Space

```bash
df -h
```

### Monitor Resource Usage

```bash
# CPU and memory
htop

# Or
top
```

## Security Checklist

- [ ] Firewall configured (UFW)
- [ ] SSH key authentication enabled
- [ ] Password authentication disabled (if using keys)
- [ ] Regular system updates scheduled
- [ ] Strong passwords for all services
- [ ] SSL/TLS certificates configured (via Nginx Proxy Manager)
- [ ] Regular backups configured

---

**Your VM is now ready for Monitorix deployment!**

See [DEPLOY.md](DEPLOY.md) for deployment instructions.

