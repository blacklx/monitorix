# Monitorix

A complete status dashboard system for monitoring Proxmox nodes, VMs, and services. Built with FastAPI, React, and PostgreSQL.

[![GitHub](https://img.shields.io/badge/GitHub-blacklx%2Fmonitorix-blue)](https://github.com/blacklx/monitorix)

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Use Cases](#use-cases)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Proxmox Monitoring
- ✅ Real-time status on all Proxmox nodes (local and remote)
- ✅ Automatic discovery and synchronization of VMs
- ✅ Resource usage tracking (CPU, RAM, disk, network)
- ✅ VM status and uptime
- ✅ History and metrics with timestamps

### Service Health Checks
- ✅ HTTP/HTTPS endpoint monitoring
- ✅ Port availability checks
- ✅ Ping checks
- ✅ Configurable check intervals and timeouts
- ✅ Response time tracking
- ✅ Service uptime statistics

### Dashboard & UI
- ✅ Modern, responsive web interface
- ✅ Real-time updates via WebSocket
- ✅ Overview dashboard with statistics
- ✅ Detailed view of nodes, VMs, and services
- ✅ Node management UI (add/edit/delete)
- ✅ Service management UI (add/edit/delete)
- ✅ Metrics graphs (CPU, Memory, Disk over time)
- ✅ Uptime statistics for nodes and services
- ✅ Filtering and search for VMs and services
- ✅ Dark mode support with theme toggle
- ✅ Responsive design (mobile and tablet optimized)
- ✅ Loading states and error handling
- ✅ **Multi-language support** (Norwegian, Swedish, Danish, Finnish, French, German, English)
- ✅ Language selector with persistent preference

### Deployment
- ✅ Automated local setup script (`setup.sh`)
- ✅ Remote deployment script (`deploy.sh` / `deploy.ps1`)
- ✅ Prerequisites checking and installation
- ✅ Docker Compose deployment

### Notifications & Alerts
- ✅ Alert system for critical events
- ✅ Alert history and resolution tracking
- ✅ Email notifications via SMTP
- ✅ Webhook support for custom integrations
- ✅ Configurable alert types and severity

### Security & Data Management
- ✅ JWT-based authentication
- ✅ User registration and login
- ✅ API-based access control
- ✅ API rate limiting
- ✅ Database migrations with Alembic
- ✅ Automatic schema migrations on startup
- ✅ Metrics retention policy with automatic cleanup

## 🛠 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database
- **PostgreSQL** - Relational database
- **Proxmoxer** - Proxmox API client
- **APScheduler** - Background job scheduling
- **WebSockets** - Real-time communication

### Frontend
- **React 18** - UI library
- **React Router** - Routing
- **React i18next** - Internationalization
- **Recharts** - Chart library for metrics visualization
- **Axios** - HTTP client
- **Vite** - Build tool
- **WebSocket API** - Real-time updates
- **CSS Variables** - Theme system for dark mode

### Deployment
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Web server (frontend)
- **PostgreSQL** - Database container

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed (for local development)
- For VM deployment: Pre-configured VM with Docker and Docker Compose
- Proxmox nodes with API access
- (Optional) Nginx Proxy Manager

### Installation

#### Local Development

1. **Clone the project**
```bash
git clone https://github.com/blacklx/monitorix.git
cd monitorix
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and fill in configuration
```

3. **Start the system**
```bash
docker-compose up -d
```

4. **Open the dashboard**
```
http://localhost:3000
```

#### VM Deployment

**Run setup script directly on the VM:**

```bash
cd ~/monitorix
chmod +x setup.sh
./setup.sh
```

The script will check prerequisites and help install missing packages.

See [INSTALL.md](INSTALL.md) for detailed installation guide or [QUICKSTART.md](QUICKSTART.md) for quick start.

## 🔗 Links

- **GitHub Repository**: [https://github.com/blacklx/monitorix](https://github.com/blacklx/monitorix)
- **Issues**: [https://github.com/blacklx/monitorix/issues](https://github.com/blacklx/monitorix/issues)

## 📚 Documentation

- **[INSTALL.md](INSTALL.md)** - Detailed installation guide
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
- **[UPGRADE.md](UPGRADE.md)** - Safe upgrade guide
- **[VERSION.md](VERSION.md)** - Version history
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[ENV_VARIABLES.md](ENV_VARIABLES.md)** - Environment variables reference
- **[TODO.md](TODO.md)** - Planned improvements and features
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[VERSION.md](VERSION.md)** - Version information
- **[API Documentation](http://localhost:8000/docs)** - Swagger/OpenAPI documentation (after startup)

## 🎯 Use Cases

- **Home lab monitoring** - Monitor all Proxmox nodes and VMs
- **Service monitoring** - Keep track of critical services
- **Resource planning** - Track CPU, RAM, and disk usage over time
- **Alert management** - Get notified when something goes down

## 🔧 Configuration

### Proxmox Nodes

Configure Proxmox nodes in the `.env` file:

```env
PROXMOX_NODES=node1:https://192.168.1.10:8006:user@pam:token_id=token_secret,node2:https://192.168.1.11:8006:user@pam:token_id=token_secret
```

Format: `name:url:username:token` (comma-separated for multiple nodes)

### Health Checks

Configure health check intervals in `.env`:

```env
HEALTH_CHECK_INTERVAL=60  # seconds
HTTP_TIMEOUT=5           # seconds
PING_TIMEOUT=3           # seconds
```

## 🌐 Integration with Nginx Proxy Manager

The system is designed to run behind Nginx Proxy Manager:

- **Backend API**: Port 8000
- **Frontend**: Port 3000
- **WebSocket**: Automatically supported

See [INSTALL.md](INSTALL.md) for detailed setup.

## 🐛 Troubleshooting

### Common Issues

**Backend won't start**
- Check that PostgreSQL container is running
- Verify DATABASE_URL in .env
- See logs: `docker-compose logs backend`

**Can't connect to Proxmox**
- Verify URL, username, and token
- Test Proxmox API availability
- Check firewall rules

**Frontend shows no data**
- Check that backend is running on port 8000
- Verify REACT_APP_API_URL in .env
- Open browser console for error messages

See [INSTALL.md](INSTALL.md) for more troubleshooting.

## 🔄 Upgrading

Monitorix includes built-in version checking and safe upgrade procedures:

- **Version Display**: Current version is shown in the web UI footer
- **Update Notifications**: Automatic check for new versions on startup
- **Safe Upgrade**: Upgrade script preserves all data and configuration
- **Database Migrations**: Automatic schema updates during upgrade

See [UPGRADE.md](UPGRADE.md) for detailed upgrade instructions.

### Quick Upgrade

```bash
# Linux/Mac
./upgrade.sh

# Windows PowerShell
.\upgrade.ps1
```

The upgrade script will:
1. ✅ Create automatic backup
2. ✅ Pull latest code
3. ✅ Run database migrations
4. ✅ Rebuild containers
5. ✅ Restart services
6. ✅ Verify upgrade success

**Always backup before upgrading!**

## 🔒 Security

### Environment Variables (.env file)

The `.env` file contains sensitive credentials (database passwords, secret keys, etc.). 

**What MUST be in .env:**
- Database credentials (`POSTGRES_PASSWORD`, `DATABASE_URL`) - Required to connect to PostgreSQL
- `SECRET_KEY` - Required for JWT token signing
- `ADMIN_USERNAME` and `ADMIN_EMAIL` - For admin user creation

**What should NOT be in .env:**
- `ADMIN_PASSWORD` - **Never stored in .env**. Generated by backend and shown in installation summary only

**What should NOT be in .env:**
- Web UI user passwords - These are stored (hashed) in the PostgreSQL database after initial creation
- Application data - All application data (users, nodes, VMs, services) is stored in the database

**Security measures:**
- ✅ `.env` file is automatically excluded from Git (in `.gitignore`)
- ✅ File permissions are automatically set to `600` (owner read/write only)
- ✅ Passwords are auto-generated with cryptographically secure random values
- ✅ `.env` file is never exposed via web server or API
- ✅ Web UI passwords are hashed (bcrypt) and stored in the database, not in `.env`

See [ENV_VARIABLES.md](ENV_VARIABLES.md) for detailed information about environment variables.

**⚠️ Important for production:**
- Never commit `.env` to version control
- Ensure `.env` file permissions are `600` (check with `ls -l .env`)
- Restrict access to the directory containing `.env`
- Consider using Docker secrets or system environment variables for highly sensitive deployments
- Use a reverse proxy (Nginx, Traefik) with SSL/TLS for production

### User Registration

Public registration is **disabled by default**. An admin user is automatically created during installation with a generated password shown in the installation summary.

**Security Features:**
- ✅ No public registration (admin user created automatically)
- ✅ Password reset via email (if email is configured)
- ✅ JWT-based authentication
- ✅ API rate limiting
- ✅ Password hashing with bcrypt
- ✅ Admin role system

### Production Checklist

- **Change all default passwords** in production
- **Disable public registration** (`ALLOW_REGISTRATION=false`)
- **Use strong SECRET_KEY** (auto-generated by setup scripts)
- **Enable Proxmox SSL verification** (`PROXMOX_VERIFY_SSL=true`) - **Enabled by default**
- **Configure firewall** if exposing to network
- **Set up SSL/TLS** via reverse proxy (Nginx, Traefik, etc.)
- Use strong SECRET_KEY
- Enable SSL/TLS via Nginx Proxy Manager
- Limit Proxmox API token privileges
- Consider rate limiting in production

## 🤝 Contributing

Contributions are welcome! See [TODO.md](TODO.md) for ideas on what can be improved.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## 📝 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

**Apache License 2.0** - A permissive license that allows commercial use, modification, distribution, and private use. Includes explicit patent protection. You can use this software for any purpose, including commercial projects.

For more information, see [LICENSE_INFO.md](LICENSE_INFO.md).

## 🙏 Acknowledgments

- [Proxmox](https://www.proxmox.com/) - Virtualization platform
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [React](https://react.dev/) - UI library

---

**Made with ❤️ for Proxmox users**
