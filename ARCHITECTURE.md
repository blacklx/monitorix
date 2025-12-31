# System Architecture

This document describes the system architecture for Monitorix.

## 🏗 Overview

The system consists of three main components:

1. **Backend API** - FastAPI-based REST API and WebSocket server
2. **Frontend** - React-based web interface
3. **Database** - PostgreSQL for data storage

All components run in Docker containers and are orchestrated with Docker Compose.

## 📊 System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx Proxy Manager                   │
│              (Optional, for public access)                │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐         ┌───────────────┐
│   Frontend    │         │    Backend    │
│   (React)     │◄────────┤   (FastAPI)   │
│   Port 3000   │  API    │   Port 8000   │
└───────────────┘         └───────┬───────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
            ┌───────────┐  ┌───────────┐  ┌───────────┐
            │PostgreSQL │  │ Proxmox   │  │  Health   │
            │  Database │  │   Nodes   │  │  Checks   │
            │ Port 5432 │  │           │  │           │
            └───────────┘  └───────────┘  └───────────┘
```

## 🔧 Components

### Backend API

**Technology**: FastAPI (Python 3.11)

**Main Components**:
- `main.py` - FastAPI application and WebSocket server
- `routers/` - API endpoints organized in modules
- `models.py` - SQLAlchemy database models
- `proxmox_client.py` - Proxmox API client
- `health_checks.py` - Health check implementations
- `scheduler.py` - Background job scheduler
- `auth.py` - JWT authentication
- `database.py` - Database configuration

**API Endpoints**:
- `/api/auth/*` - Authentication (login, register)
- `/api/nodes/*` - Proxmox node management
- `/api/vms/*` - VM information
- `/api/services/*` - Service management
- `/api/dashboard/*` - Dashboard statistics
- `/api/metrics/*` - Metrics data
- `/api/alerts/*` - Alert management
- `/api/health-checks/*` - Health check results
- `/ws` - WebSocket endpoint

**Background Jobs**:
- Node checks (every 60 seconds)
- Service health checks (every 60 seconds)
- Metrics collection

### Frontend

**Technology**: React 18, Vite

**Main Components**:
- `App.jsx` - Main application with routing
- `pages/` - Page components (Dashboard, Nodes, VMs, etc.)
- `components/` - Reusable components
- `contexts/` - React contexts (Auth, etc.)
- `hooks/` - Custom React hooks (useWebSocket)
- `i18n/` - Internationalization configuration and translations
  - `config.js` - i18next configuration
  - `locales/` - Translation files for 7 languages

**Routing**:
- `/login` - Login page
- `/dashboard` - Main dashboard
- `/nodes` - Proxmox nodes
- `/vms` - Virtual machines
- `/services` - Service health checks
- `/alerts` - Alert management

**State Management**:
- React Context API for global state (Auth)
- Local state with useState/useReducer
- WebSocket for real-time updates
- i18next for language management

### Database

**Technology**: PostgreSQL 15

**Tables**:
- `users` - Users and authentication
- `nodes` - Proxmox nodes
- `vms` - Virtual machines
- `services` - Services to monitor
- `health_checks` - Health check results
- `metrics` - Time-series metrics
- `alerts` - Alerts and notifications

**Relations**:
- Nodes → VMs (one-to-many)
- VMs → Services (one-to-many)
- Services → Health Checks (one-to-many)
- Nodes/VMs → Metrics (one-to-many)

## 🔄 Data Flow

### Node Sync Flow

```
1. Scheduler triggers node check (every 60s)
2. ProxmoxClient connects to Proxmox API
3. Fetch node status and VM list
4. Update database (nodes, vms tables)
5. Store metrics (metrics table)
6. Broadcast update via WebSocket
7. Frontend receives update and re-renders
```

### Health Check Flow

```
1. Scheduler triggers service check (every 60s)
2. HealthChecker performs check (HTTP/ping/port)
3. Store result in health_checks table
4. If service is down, create alert
5. Broadcast update via WebSocket
6. Frontend updates service status
```

### Authentication Flow

```
1. User submits login form
2. Frontend sends POST /api/auth/login
3. Backend validates credentials
4. Backend generates JWT token
5. Frontend stores token in localStorage
6. Frontend includes token in API requests
7. Backend validates token on each request
```

## 🔌 Integrations

### Proxmox API

**Library**: `proxmoxer`

**Endpoints Used**:
- `/api2/json/version` - API version
- `/api2/json/nodes` - Node list
- `/api2/json/nodes/{node}/status` - Node status
- `/api2/json/nodes/{node}/qemu` - QEMU VMs
- `/api2/json/nodes/{node}/lxc` - LXC containers
- `/api2/json/nodes/{node}/qemu/{vmid}/status/current` - VM status

**Authentication**: API Token (PVETokenID)

### Health Checks

**HTTP/HTTPS**:
- Async HTTP requests with `httpx`
- Configurable timeout
- Status code validation

**Ping**:
- System `ping` command
- Cross-platform (Windows/Linux)
- Configurable timeout

**Port**:
- Socket connection test
- TCP connect check
- Configurable timeout

## 🔐 Security

### Authentication

- JWT tokens with HS256 algorithm
- Token expiration (30 minutes)
- Password hashing with bcrypt

### API Security

- CORS middleware
- Input validation with Pydantic
- SQL injection protection (SQLAlchemy ORM)
- Rate limiting (planned)

### Database Security

- Password-protected PostgreSQL
- Connection pooling
- Prepared statements (via SQLAlchemy)

## 📈 Scalability

### Current Limitations

- Single instance backend
- In-memory WebSocket connections
- No caching layer
- Synchronous database operations

### Future Improvements

- Redis for caching and session management
- Celery for background jobs
- Database connection pooling
- Metrics aggregation
- Horizontal scaling support

## 🚀 Deployment

### Docker Compose

**Services**:
- `postgres` - PostgreSQL database
- `backend` - FastAPI backend
- `frontend` - React frontend (Nginx)

**Networking**:
- Containers communicate via Docker network
- Ports exposed to host for access

### Nginx Proxy Manager

**Backend**:
- Proxy to `monitorix_backend:8000`
- WebSocket support enabled

**Frontend**:
- Proxy to `monitorix_frontend:80`
- Static file serving

## 📊 Monitoring

### Metrics Collection

- CPU usage (node and VM)
- Memory usage (node and VM)
- Disk usage (node and VM)
- Network (planned)
- Response times (health checks)

### Storage

- Metrics stored in PostgreSQL
- Time-series data with timestamp
- Retention policy (planned)

## 🔄 Backup and Recovery

### Database Backup

```bash
docker-compose exec postgres pg_dump -U monitorix monitorix > backup.sql
```

### Restore

```bash
docker-compose exec -T postgres psql -U monitorix monitorix < backup.sql
```

## 🐛 Error Handling

### Backend

- Try/except blocks for error handling
- Logging with Python logging
- HTTP error responses with FastAPI

### Frontend

- Try/catch for async operations
- Error boundaries (planned)
- User-friendly error messages

### Database

- Connection retry logic
- Transaction rollback on errors
- Connection pooling for resilience

## 📚 Technology Stack

### Backend Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL driver
- `proxmoxer` - Proxmox API client
- `aiohttp` - Async HTTP client
- `apscheduler` - Job scheduler
- `python-jose` - JWT handling
- `passlib` - Password hashing

### Frontend Dependencies

- `react` - UI library
- `react-router-dom` - Routing
- `react-i18next` - Internationalization
- `i18next` - i18n framework
- `axios` - HTTP client
- `vite` - Build tool

### Infrastructure

- `docker` - Containerization
- `docker-compose` - Orchestration
- `nginx` - Web server
- `postgresql` - Database

---

**Last updated**: 2024-01-XX
