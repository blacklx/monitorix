# Quick Start Guide

Get Monitorix up and running in minutes!

## Option 1: Local Development

```bash
# 1. Clone the project
git clone https://github.com/blacklx/monitorix.git
cd monitorix

# 2. (Optional) Configure environment
# For testing, you can skip this - defaults will work!
# For production: create .env file with your settings

# 3. Start everything
docker-compose up -d
# PostgreSQL will be automatically configured and initialized

# 4. Open dashboard
# http://localhost:3000
```

## Option 2: Deploy to VM

### Option A: Local Setup (Recommended)

**Run directly on the VM:**

1. **Copy project to VM** (via git, scp, USB, etc.)
2. **SSH into VM:**
   ```bash
   ssh user@your-vm-ip
   cd ~/monitorix
   ```
3. **Run setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

The script will:
- ✅ Check for all prerequisites (Docker, Docker Compose, curl, git)
- ✅ Prompt to install missing packages or show manual guide
- ✅ Set up .env file
- ✅ Build and start services
- ✅ Show you access URLs

### Option B: Remote Deployment

**Deploy from your local machine:**

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
- ✅ Check prerequisites on remote VM
- ✅ Prompt to install missing packages or show manual guide
- ✅ Copy all files to the VM
- ✅ Build and start services
- ✅ Show you access URLs

### After Deployment

1. **SSH into your VM:**
   ```bash
   ssh user@your-vm-ip
   cd ~/monitorix
   ```

2. **Configure .env:**
   ```bash
   nano .env
   ```
   - Set database password
   - Set SECRET_KEY
   - Add Proxmox nodes

3. **Restart services:**
   ```bash
   docker-compose restart
   ```

4. **Register first user:**
   - Go to `http://your-vm-ip:3000`
   - Click "Register"
   - Create your account

## Configuration

### Proxmox Nodes

In `.env`, add your Proxmox nodes:

```env
PROXMOX_NODES=node1:https://192.168.1.10:8006:user@pam:token_id=token_secret
```

Format: `name:url:username:token`

### Create Proxmox API Token

1. Log in to Proxmox web interface
2. Go to: Datacenter → Permissions → API Tokens
3. Click "Add"
4. Fill in Token ID and User
5. Click "Generate"
6. Copy the token (shown only once!)

## Access

- **Frontend**: `http://your-ip:3000`
- **Backend API**: `http://your-ip:8000`
- **API Docs**: `http://your-ip:8000/docs`

## Next Steps

- See [INSTALL.md](INSTALL.md) for detailed installation
- See [DEPLOY.md](DEPLOY.md) for deployment options
- See [README.md](README.md) for full documentation

## Troubleshooting

**Services won't start?**
```bash
docker-compose logs
```

**Can't connect to Proxmox?**
- Verify URL, username, and token
- Check firewall rules
- Test API: `curl -k https://your-proxmox:8006/api2/json/version`

**Need help?**
- Check [INSTALL.md](INSTALL.md) troubleshooting section
- View logs: `docker-compose logs -f`

---

**That's it! You're ready to monitor your Proxmox infrastructure! 🚀**

