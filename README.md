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
- **[DEPLOY.md](DEPLOY.md)** - Deployment guide
- **[VM_SETUP.md](VM_SETUP.md)** - VM setup guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
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

## 🔒 Security

- **Change all default passwords** in production
- Use strong SECRET_KEY
- Enable SSL/TLS via Nginx Proxy Manager
- Limit Proxmox API token privileges
- Consider rate limiting in production

## 🤝 Contributing

Contributions are welcome! See [TODO.md](TODO.md) for ideas on what can be improved.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## 📝 License

This project is made for personal use. Use as you wish.

## 🙏 Acknowledgments

- [Proxmox](https://www.proxmox.com/) - Virtualization platform
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [React](https://react.dev/) - UI library

---

**Made with ❤️ for Proxmox users**
