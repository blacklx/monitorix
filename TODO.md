# TODO - Monitorix

This document tracks planned improvements, new features, and known issues.

## 📋 Status

- ✅ = Completed
- 🚧 = In Progress
- 📝 = Planned
- 🐛 = Known Issue

## 🎯 High Priority

### Backend

- [x] ✅ **Node management UI** - Add/edit/delete nodes via web interface
- [x] ✅ **Service management UI** - Add/edit/delete services via web interface
- [x] ✅ **Bulk operations** - Add multiple nodes/services at once
- [x] ✅ **Email notifications** - Send email when alerts occur
- [x] ✅ **Webhook support** - Send webhooks on alerts
- [x] ✅ **Metrics retention policy** - Automatic cleanup of old metrics
- [x] ✅ **API rate limiting** - Protect against abuse
- [x] ✅ **Database migrations** - Use Alembic for schema changes

### Frontend

- [x] ✅ **Node management** - UI to add/edit nodes
- [x] ✅ **Service management** - UI to add/edit services
- [x] ✅ **Metrics graphs** - Visualize CPU, RAM, disk over time
- [x] ✅ **Uptime statistics** - Show uptime for nodes and services
- [x] ✅ **Filtering and search** - Filter VMs, services, etc.
- [x] ✅ **Dark mode** - Dark theme
- [x] ✅ **Responsive design improvements** - Better mobile experience
- [x] ✅ **Loading states** - Better loading indicators
- [x] ✅ **Error handling** - Better error messages to users
- [x] ✅ **Multi-language support** - i18n for Norwegian, Swedish, Danish, Finnish, French, German, English
- [x] ✅ **Local setup script** - setup.sh for running directly on VM
- [x] ✅ **Prerequisites checking** - Deployment scripts check and install missing packages
- [x] ✅ **Documentation translation** - All documentation translated to English

## 🚀 Medium Priority

### Features

- [x] ✅ **Custom health checks** - Support for custom scripts/commands (backend implemented)
- [x] ✅ **Notification channels** - Multiple channels (email, Slack, Discord, etc.) - Backend and frontend implemented
- [x] ✅ **Alert rules** - Configurable alert rules - Backend and frontend implemented
- [x] ✅ **Maintenance mode** - Set nodes/services in maintenance mode (Backend and frontend UI fully implemented)
- [x] ✅ **Tags and grouping** - Organize nodes/VMs with tags (Backend and frontend implemented for nodes. VMs can be extended similarly)
- [x] ✅ **Export data** - Export metrics, nodes, VMs, services, and alerts to CSV/JSON
- [x] ✅ **Backup/restore** - UI for database backup (create, list, download, restore, delete)
- [x] ✅ **Multi-user support** - Multiple users with roles (Admin/user roles, user management UI, profile management implemented)
- [x] ✅ **Audit log** - Log all changes (backend and frontend UI implemented, basic logging in auth. Can be extended to other endpoints)

### Improvements

- [x] ✅ **WebSocket reconnection** - Improve WebSocket reconnection logic in frontend (exponential backoff, heartbeat, better status)
- [x] ✅ **WebSocket error handling** - Better error handling and logging in WebSocket broadcasts
- [x] ✅ **Database query optimization** - Add indexes for frequently queried fields (status, checked_at, recorded_at) - Comprehensive indexes implemented in migration 002
- [x] ✅ **Metrics aggregation** - Aggregate metrics for better performance - Automatic hourly/daily aggregation for long time periods, detailed metrics for recent data
- [x] ✅ **Performance optimization** - Optimize database queries (use joinedload for eager loading) - Implemented eager loading in VMs, Services, Health Checks, Alerts, Metrics, and Audit Logs endpoints
- [ ] 📝 **Caching** - Add Redis for caching frequently accessed data
- [ ] 📝 **Background jobs** - Use Celery or similar for heavy tasks
- [x] ✅ **Database indexing** - Optimize database indexes (add composite indexes) - Comprehensive indexes implemented in migration 002
- [x] ✅ **API versioning** - API versioning support implemented with header-based versioning (X-API-Version, Accept header), version utilities, and version info endpoint
- [x] ✅ **OpenAPI specification** - Complete API documentation - Enhanced with detailed descriptions, examples, tags metadata, and improved endpoint documentation
- [x] ✅ **Uptime calculation** - Improve uptime calculation accuracy - Fixed syntax error and improved calculation using actual metric timestamps and time intervals

## 💡 Low Priority / Ideas

### Features

- [ ] 📝 **Mobile app** - Native or PWA
- [ ] 📝 **CLI tool** - Command-line tool
- [ ] 📝 **Grafana integration** - Export metrics to Grafana
- [ ] 📝 **Prometheus exporter** - Prometheus metrics endpoint
- [ ] 📝 **SNMP monitoring** - Support for SNMP
- [ ] 📝 **Docker container monitoring** - Monitor Docker containers
- [ ] 📝 **Kubernetes integration** - Monitor K8s clusters
- [ ] 📝 **Network topology** - Visualize network topology
- [ ] 📝 **Cost tracking** - Track costs per VM/node
- [ ] 📝 **Capacity planning** - Recommendations based on usage

### UI/UX

- [ ] 📝 **Dashboard widgets** - Customizable dashboard widgets
- [ ] 📝 **Themes** - Multiple color schemes and themes
- [ ] 📝 **Keyboard shortcuts** - Shortcuts for power users
- [ ] 📝 **Bulk actions** - Perform actions on multiple items
- [ ] 📝 **Drag and drop** - Reorganize dashboard
- [ ] 📝 **Charts library** - Better chart library (Chart.js, D3.js)
- [ ] 📝 **Real-time notifications** - Browser notifications
- [ ] 📝 **Print views** - Printer-friendly views

### Technical

- [ ] 📝 **Unit tests** - Test coverage for backend
- [ ] 📝 **Integration tests** - Test entire system
- [ ] 📝 **E2E tests** - Test frontend with Playwright/Cypress
- [ ] 📝 **CI/CD pipeline** - Automatic testing and deployment
- [ ] 📝 **Docker optimizations** - Multi-stage builds, smaller images
- [ ] 📝 **Health checks** - Container health checks
- [ ] 📝 **Monitoring** - Monitor the system itself
- [x] ✅ **Logging** - Structured JSON logging implemented with auto-detection (JSON in production, text in development), configurable log levels, and optional file logging
- [x] ✅ **Error tracking** - Sentry error tracking implemented with FastAPI integration, automatic exception capture, user context, and performance monitoring

## 🐛 Known Issues

### Backend

- [x] ✅ **Import errors** - Fixed missing imports in main.py, routers (limiter, Request, datetime)
- [x] ✅ **Scheduler indentation** - Fixed indentation bug in check_node function
- [x] ✅ **Service maintenance_mode** - Added missing maintenance_mode field to Service model
- [x] ✅ **WebSocket broadcasts** - Added WebSocket broadcasts in scheduler for real-time updates
- [x] ✅ **Database session handling** - Improved database session management in scheduler
- [x] ✅ **Proxmox SSL verification** - Configurable SSL verification implemented (enabled by default)
- [x] ✅ **Error handling** - Improved error handling with global exception handlers, structured error responses, and better user feedback
- [x] ✅ **Token refresh** - JWT refresh tokens implemented with automatic refresh in frontend
- [x] ✅ **WebSocket error handling** - ConnectionManager.broadcast now logs errors and removes dead connections

### Frontend

- [x] ✅ **WebSocket reconnection** - Improved with exponential backoff, heartbeat/ping-pong, better error handling, and reconnection status
- [x] ✅ **Error boundaries** - React error boundaries implemented
- [x] ✅ **Loading states** - Loading indicators implemented
- [x] ✅ **Form validation** - Form validation implemented for Nodes, Services, Login, and other forms
- [x] ✅ **Maintenance mode UI** - UI controls for setting nodes/services in maintenance mode fully implemented
- [x] ✅ **WebSocket status indicator** - Show connection status in UI with reconnection info

### Deployment

- [x] ✅ **Environment variables** - CORS configuration and rate limiting now use environment variables instead of hardcoded values
- [x] ✅ **Database migrations** - Automatic migrations on startup implemented
- [x] ✅ **Health checks** - Container health checks implemented in docker-compose.yml

## 📚 Documentation

- [ ] 📝 **API documentation** - Improve Swagger documentation
- [ ] 📝 **Developer guide** - Guide for developers
- [ ] 📝 **Architecture diagram** - Visualize system architecture
- [ ] 📝 **Deployment guide** - Detailed deployment guide
- [ ] 📝 **Troubleshooting guide** - Extended troubleshooting guide
- [ ] 📝 **FAQ** - Frequently asked questions
- [ ] 📝 **Changelog** - Track changes

## 🔒 Security

- [ ] 📝 **SSL/TLS** - Enable SSL verification for Proxmox
- [x] ✅ **Rate limiting** - Rate limiting implemented
- [x] ✅ **Input validation** - Enhanced input validation with sanitization, XSS protection, URL/email validation, and comprehensive field validators in Pydantic schemas
- [x] ✅ **SQL injection protection** - SQLAlchemy uses parameterized queries by default, plus additional validation layer in input_validation.py
- [x] ✅ **XSS protection** - HTML escaping in sanitize_string, XSS pattern detection, CSP headers, and input sanitization in schemas
- [ ] 📝 **CSRF protection** - Add CSRF tokens
- [x] ✅ **Security headers** - Security headers middleware implemented (CSP, X-Frame-Options, HSTS, etc.)
- [x] ✅ **Password policy** - Comprehensive password policy implemented with configurable requirements (length, complexity, common password checks)
- [ ] 📝 **2FA support** - Two-factor authentication

## 📊 Metrics and Analytics

- [ ] 📝 **System metrics** - Monitor the system itself
- [ ] 📝 **Usage analytics** - Track how the system is used
- [ ] 📝 **Performance metrics** - Track performance
- [ ] 📝 **Error tracking** - Track and analyze errors

## 🌍 Internationalization

- [x] ✅ **Multi-language support** - Support for multiple languages
- [x] ✅ **i18n** - Implemented internationalization
- [x] ✅ **Locale settings** - Support different date/time formats - Implemented with date-fns locale support for all 7 languages

## 📝 Notes

### Implementation Notes

- **Node management UI**: Should include validation of Proxmox connection before saving
- **Email notifications**: Consider using SendGrid, Mailgun, or SMTP
- **Metrics graphs**: Recharts is already installed, can be used directly
- **Dark mode**: Consider using CSS variables for easier implementation

### Technical Notes

- Backend uses async/await, ensure all database operations are async
- Frontend uses React hooks, ensure to follow best practices
- Database schema can change, consider using Alembic for migrations

### Prioritization

Prioritization is based on:
1. Functionality missing for basic use
2. Security and stability
3. User experience
4. Performance and scalability

---

## 🔧 Recent Fixes and Improvements (2024-12-31)

### Critical Bugs Fixed

1. **Import Errors** - Fixed missing imports in:
   - `main.py`: Added limiter, RateLimitExceeded, webhooks imports
   - `routers/nodes.py`: Added Request and limiter imports
   - `routers/webhooks.py`: Added Request, limiter, and datetime imports
   - `routers/services.py`: Added Request and limiter imports

2. **Scheduler Bugs** - Fixed:
   - Indentation error in `check_node` function
   - Indentation error in `run_service_checks` function
   - Database session handling improvements

3. **Model Updates** - Added:
   - `maintenance_mode` field to Service model (was missing but referenced in scheduler)

4. **WebSocket Integration** - Added:
   - WebSocket broadcasts in scheduler for real-time updates
   - Broadcast function integration between main.py and scheduler.py
   - Real-time updates for node, VM, and service status changes

5. **Metrics Page Bug** - Fixed:
   - Incorrect metric_type names in frontend (cpu_usage → cpu, etc.)

### New Features Implemented

1. **VM Endpoints** - Added:
   - `POST /api/vms/{vm_id}/sync` - Manually sync VM from node
   - `GET /api/vms/{vm_id}/uptime` - Get VM uptime statistics

2. **Alerts Endpoints** - Added:
   - `GET /api/alerts/stats` - Get alert statistics
   - `POST /api/alerts/bulk-resolve` - Bulk resolve multiple alerts
   - `DELETE /api/alerts/{alert_id}` - Delete alert
   - Enhanced filtering: severity, alert_type parameters

3. **Health Checks Endpoints** - Added:
   - `GET /api/health-checks/latest/{service_id}` - Get latest health check
   - `GET /api/health-checks/stats/{service_id}` - Get health check statistics
   - Enhanced filtering: status, hours parameters

4. **Maintenance Mode** - Added:
   - `POST /api/nodes/{node_id}/maintenance-mode` - Toggle node maintenance mode
   - `POST /api/services/{service_id}/maintenance-mode` - Toggle service maintenance mode
   - `POST /api/services/{service_id}/toggle-active` - Toggle service active status
   - Frontend UI for maintenance mode toggle in Nodes page

5. **Frontend Improvements**:
   - Enhanced Alerts page with filters (severity, type), bulk actions, statistics
   - Maintenance mode toggle button in Nodes page
   - Fixed Metrics page metric type queries
   - VM Details Modal with metrics charts and uptime statistics
   - Metrics export functionality (CSV/JSON)
   - Improved VM page with detail view and sync functionality

6. **Database Performance**:
   - Comprehensive database indexes migration (002_add_performance_indexes)
   - Indexes on all frequently queried fields
   - Composite indexes for common query patterns

7. **Uptime Calculation Improvements**:
   - Uses metrics data for more accurate node uptime tracking
   - Improved VM uptime calculation using metrics
   - Better downtime calculations

### Improvements Made

- Better error handling in WebSocket broadcasts
- Improved database session management
- Real-time status updates via WebSocket
- Proper maintenance mode support for services and nodes
- Enhanced alert management with bulk operations
- Better health check statistics and filtering

### Latest Improvements (2024-12-31 - Continued)

1. **VM Details Modal** - Added:
   - Full VM detail view with modal
   - Metrics history charts (CPU, Memory, Disk)
   - Uptime statistics display
   - Manual sync functionality
   - Responsive design

2. **Database Performance** - Added:
   - Comprehensive database indexes migration (002_add_performance_indexes)
   - Indexes on status, is_active, maintenance_mode fields
   - Composite indexes for common query patterns
   - Improved query performance for large datasets

3. **Uptime Calculation** - Improved:
   - Uses metrics data for more accurate uptime tracking
   - Better calculation for nodes using CPU metrics
   - Improved VM uptime calculation
   - More accurate downtime calculations

4. **Metrics Export** - Added:
   - CSV export functionality
   - JSON export functionality
   - Export buttons in Metrics page UI

5. **Alerts Enhancements** - Added:
   - Bulk resolve functionality
   - Delete alerts
   - Enhanced filtering (severity, type)
   - Alert statistics display
   - Select all functionality

### Remaining Issues

1. **WebSocket Error Handling** - ✅ Fixed: ConnectionManager.broadcast now logs errors and removes dead connections
2. **Uptime Calculation** - ✅ Improved: Now uses metrics data for more accurate tracking
3. **Database Indexes** - ✅ Fixed: Comprehensive indexes added via migration
4. **VM Details Page** - ✅ Fixed: Full detail modal with metrics and uptime implemented
5. **Maintenance Mode UI** - ✅ Fixed: Toggle buttons added to Nodes and Services pages
6. **WebSocket Status Indicator** - ✅ Fixed: Real-time connection status shown in navigation
7. **Project Rebranding** - ✅ Fixed: Renamed to Monitorix, all references updated
8. **Repository Cleanup** - ✅ Fixed: Duplicate files removed, .gitignore improved

---

**Last updated**: 2024-12-31

**Note**: This is a living document. Add new ideas and mark completed tasks.
