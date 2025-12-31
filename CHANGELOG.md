# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- See [TODO.md](TODO.md) for full list

## [1.2.0] - 2024-12-31

### Added
- VM Details Modal with metrics charts and uptime statistics
- Metrics Export functionality (CSV and JSON)
- Database performance indexes for improved query performance
- Improved uptime calculation using metrics data
- Enhanced alerts management with bulk resolve, delete, and filtering
- Maintenance Mode UI toggle buttons in Nodes and Services pages
- WebSocket status indicator in navigation bar
- Health check statistics endpoints
- Manual VM synchronization endpoint
- Project rebranding from "System Status Dashboard" to "Monitorix"

### Fixed
- Import errors in main.py and router files
- Scheduler indentation bugs causing incorrect execution
- Metrics page metric type queries
- WebSocket error handling and reconnection logic
- Missing maintenance_mode field in Service model

### Changed
- Uptime calculation now uses metrics data for improved accuracy
- Alerts page UI improved with enhanced filters and bulk actions
- VM page enhanced with detail modal
- Database default names changed to "monitorix"
- Container names updated to reflect new project name

## [1.1.0] - 2024-11-28

### Added
- Multi-language support (i18n) with 7 languages: English, Norwegian, Swedish, Danish, Finnish, French, German
- Language selector dropdown in navigation
- Database migrations using Alembic with automatic migration on startup
- API rate limiting using slowapi to protect against abuse
- Webhook support for sending alerts to external services
- Dark mode with theme toggle and system preference detection
- Responsive design optimizations for mobile and tablet devices
- Improved loading states with LoadingSpinner component
- Enhanced error handling with React ErrorBoundary
- Local setup script (`setup.sh`) for running directly on VM
- Enhanced deployment scripts with prerequisites checking
- VM setup guide for Debian 12
- Quick start guide for simplified setup
- Node and Service management UI (add/edit/delete via web interface)
- Metrics graphs using Recharts to visualize CPU, RAM, and disk over time
- Uptime statistics for nodes and services
- Email notifications via SMTP
- Metrics retention policy for automatic cleanup of old data
- Filtering and search functionality for VMs and services

### Changed
- All documentation translated to English
- Database initialization now uses Alembic migrations
- All CSS files updated to support dark mode
- Deployment scripts now check and install prerequisites automatically
- Improved error handling in frontend components and deployment scripts
- Better user guidance for missing prerequisites

## [1.0.0] - 2024-11-15

### Added
- Initial release of Monitorix
- FastAPI backend with REST API
- React frontend with Vite
- PostgreSQL database with SQLAlchemy ORM
- Proxmox API integration using proxmoxer
- Health check system supporting HTTP, ping, and port checks
- Background scheduler using APScheduler for periodic checks
- WebSocket support for real-time updates
- JWT-based authentication
- Dashboard with system overview
- Pages for Nodes, VMs, Services, and Alerts
- Docker Compose deployment configuration
- Comprehensive documentation (README, INSTALL, TODO, CONTRIBUTING, ARCHITECTURE)
