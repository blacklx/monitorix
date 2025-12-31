# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Bulk operations for nodes/services
- Custom health checks
- Notification channels (Slack, Discord, etc.)
- See [TODO.md](TODO.md) for full list

## [1.2.0] - 2024-12-31

### Added
- **VM Details Modal** - Full detail view with metrics charts and uptime statistics
- **Metrics Export** - CSV and JSON export functionality
- **Database Performance Indexes** - Comprehensive indexes for better query performance
- **Improved Uptime Calculation** - More accurate tracking using metrics data
- **Enhanced Alerts Management** - Bulk resolve, delete, enhanced filtering
- **Maintenance Mode UI** - Toggle buttons in Nodes and Services pages
- **WebSocket Status Indicator** - Real-time connection status in navigation
- **Health Check Statistics** - Detailed statistics and latest check endpoints
- **VM Sync Endpoint** - Manual VM synchronization
- **Project Rebranding** - Renamed to Monitorix

### Fixed
- Import errors in main.py and routers
- Scheduler indentation bugs
- Metrics page metric type queries
- WebSocket error handling
- Service maintenance_mode field missing from model

### Changed
- Uptime calculation now uses metrics data for accuracy
- Alerts page UI improved with filters and bulk actions
- VM page enhanced with detail modal

## [1.2.0] - 2024-12-31

### Added
- **Database migrations (Alembic)** - Full Alembic integration for schema management
  - Automatic migrations on application startup
  - Migration utilities and configuration
- **API rate limiting** - Protection against API abuse using slowapi
  - Configurable rate limits via environment variables
  - Rate limiting on authentication and creation endpoints
- **Webhook support** - Send webhooks when alerts occur
  - Full CRUD API for webhook management
  - Configurable alert types per webhook
  - Test endpoint for webhooks
- **Dark mode** - Complete dark theme support
  - Theme toggle in navigation
  - CSS variables for seamless theme switching
  - System preference detection
- **Responsive design** - Mobile and tablet optimizations
  - Media queries for all pages
  - Responsive grid layouts
  - Mobile-friendly navigation
- **Loading states** - Improved loading indicators
  - LoadingSpinner component with multiple sizes
  - Better loading feedback throughout the application
- **Error handling** - Enhanced error management
  - React ErrorBoundary component
  - Better error messages and user feedback
  - Error details in development mode

### Changed
- Database initialization now uses Alembic migrations
- All CSS files updated to support dark mode
- Improved error handling in frontend components
- Enhanced user experience with loading states

## [1.1.0] - 2024-01-XX

### Added
- **Multi-language support (i18n)** - Full internationalization support
  - English (en)
  - Norwegian (no)
  - Swedish (sv)
  - Danish (da)
  - Finnish (fi)
  - French (fr)
  - German (de)
- **Language selector** - Dropdown in navigation to switch languages
- **Local setup script** - `setup.sh` for running directly on VM
- **Enhanced deployment scripts** - Prerequisites checking and installation
- **VM setup guide** - Complete guide for setting up Debian 12 VM
- **Quick start guide** - Simplified getting started documentation
- **Node management UI** - Add/edit/delete nodes via web interface
- **Service management UI** - Add/edit/delete services via web interface
- **Metrics graphs** - Visualize CPU, RAM, disk over time using Recharts
- **Uptime statistics** - Show uptime percentages for nodes and services
- **Email notifications** - Send email alerts via SMTP
- **Metrics retention policy** - Automatic cleanup of old metrics
- **Filtering and search** - Filter and search VMs and services

### Changed
- All documentation translated to English
- Deployment scripts now check prerequisites before deployment
- Deployment scripts can automatically install missing packages
- Improved error handling in deployment scripts
- Better user guidance for missing prerequisites

### Frontend
- Added `react-i18next` and `i18next` for internationalization
- All UI components now support multiple languages
- Language preference saved in localStorage
- Translation files for all supported languages

### Documentation
- All documentation files translated to English
- Added `QUICKSTART.md` for quick setup
- Added `VM_SETUP.md` for VM preparation
- Updated `DEPLOY.md` with local and remote deployment options
- Enhanced `INSTALL.md` with automated setup section

## [1.0.0] - 2024-01-XX

### Added
- Initial release of Monitorix
- Backend API with FastAPI
- Frontend with React
- PostgreSQL database
- Proxmox API integration
- Health check system (HTTP, ping, port)
- Background scheduler for periodic checks
- WebSocket support for real-time updates
- JWT-based authentication
- Dashboard with overview
- Nodes page for Proxmox node monitoring
- VMs page for VM status and resource usage
- Services page for service health checks
- Alerts page for alert management
- Docker Compose deployment
- Documentation (README, INSTALL, TODO, CHANGELOG, CONTRIBUTING, ARCHITECTURE)

### Backend
- FastAPI REST API
- SQLAlchemy ORM with PostgreSQL
- Proxmox client with proxmoxer
- Health check system with async support
- APScheduler for background jobs
- WebSocket server
- JWT authentication with passlib
- CORS middleware
- API routers for all resources

### Frontend
- React 18 with Vite
- React Router for navigation
- Axios for API calls
- WebSocket client for real-time updates
- Responsive design
- Login and registration
- Dashboard with statistics
- Nodes, VMs, Services, and Alerts pages

### Database
- Users table for authentication
- Nodes table for Proxmox nodes
- VMs table for virtual machines
- Services table for health checks
- Health_checks table for check results
- Metrics table for time-series data
- Alerts table for alerts

### Deployment
- Docker Compose configuration
- Dockerfiles for backend and frontend
- Nginx configuration for frontend
- Environment variable support
- Health checks for containers

### Documentation
- README.md with overview
- INSTALL.md with detailed installation guide
- TODO.md with planned improvements
- CHANGELOG.md (this file)
- CONTRIBUTING.md with contribution guidelines
- ARCHITECTURE.md with system architecture

## Versioning

- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backwards compatible manner
- **PATCH** version when you make backwards compatible bug fixes

---

**Note**: Dates are examples and should be updated with actual dates on release.
