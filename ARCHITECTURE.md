# Monitorix Architecture

This document describes the architecture of the Monitorix monitoring system.

## Overview

Monitorix is a comprehensive monitoring solution for Proxmox infrastructure, providing real-time monitoring, alerting, and metrics collection.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Dashboard│  │   Nodes  │  │    VMs   │  │ Services │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              WebSocket (Real-time Updates)            │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTP/WebSocket
                       │
┌──────────────────────▼─────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    API Layer                         │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐ │  │
│  │  │  Auth  │  │  Nodes  │  │   VMs  │  │Services│ │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Business Logic Layer                     │  │
│  │  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │  Scheduler   │  │ Alert Rules  │                │  │
│  │  │  (APScheduler)│  │  Evaluation  │                │  │
│  │  └──────────────┘  └──────────────┘                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data Access Layer                        │  │
│  │  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │ SQLAlchemy   │  │   Cache      │                │  │
│  │  │    ORM       │  │  (Redis)     │                │  │
│  │  └──────────────┘  └──────────────┘                │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬─────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│  PostgreSQL  │ │   Redis    │ │  Proxmox   │
│  (Database)  │ │  (Cache)   │ │    API     │
└──────────────┘ └────────────┘ └────────────┘
```

## Components

### Frontend

- **Technology**: React 18+ with Vite
- **State Management**: React Context API
- **Real-time Updates**: WebSocket connection
- **Internationalization**: react-i18next
- **Styling**: CSS Modules

### Backend

- **Framework**: FastAPI
- **Database ORM**: SQLAlchemy
- **Task Scheduling**: APScheduler
- **Caching**: Redis (optional)
- **Background Jobs**: Celery (optional)
- **Authentication**: JWT tokens with refresh tokens
- **API Documentation**: OpenAPI/Swagger

### Database

- **Type**: PostgreSQL 15+
- **Migrations**: Alembic
- **Models**: SQLAlchemy ORM

### External Services

- **Proxmox API**: For monitoring Proxmox nodes and VMs
- **Email (SMTP)**: For alert notifications
- **Slack/Discord**: For notification channels
- **Webhooks**: For custom integrations

## Data Flow

### Monitoring Flow

1. **Scheduler** runs periodic checks (every 1-5 minutes)
2. **Proxmox Client** connects to Proxmox API
3. **Metrics** are collected and stored in database
4. **Alert Rules** are evaluated
5. **Alerts** are created if thresholds are exceeded
6. **Notifications** are sent (email, Slack, Discord, webhooks)
7. **WebSocket** broadcasts updates to frontend

### Real-time Updates

1. Frontend establishes WebSocket connection
2. Backend broadcasts updates on:
   - Node status changes
   - VM status changes
   - Service health check results
   - New alerts
   - Metrics updates
3. Frontend receives updates and updates UI

## Security

### Authentication

- JWT-based authentication
- Access tokens (short-lived, 30 minutes)
- Refresh tokens (long-lived, 7 days)
- Two-factor authentication (TOTP)

### Authorization

- Role-based access control (Admin/User)
- Endpoint-level permissions
- Resource-level permissions

### Security Features

- CSRF protection
- Security headers (CSP, HSTS, etc.)
- Input validation and sanitization
- SQL injection protection (SQLAlchemy parameterized queries)
- XSS protection
- Rate limiting
- Password policy enforcement

## Scalability

### Horizontal Scaling

- Stateless backend (can run multiple instances)
- Shared database (PostgreSQL)
- Shared cache (Redis)
- Load balancer for frontend

### Performance Optimizations

- Database indexing
- Query optimization (eager loading)
- Caching (Redis)
- Metrics aggregation
- Background job processing (Celery)

## Deployment

### Docker Compose

- All services containerized
- Easy local development
- Production-ready configuration

### Components

- `backend`: FastAPI application
- `frontend`: React application (served by Nginx)
- `postgres`: PostgreSQL database
- `redis`: Redis cache (optional)
- `celery_worker`: Celery worker (optional)

## Monitoring

### System Metrics

- Backend server CPU, memory, disk usage
- Process memory usage
- Network I/O
- System uptime

### Application Metrics

- API response times
- Database query performance
- Cache hit rates
- Alert processing times

### Prometheus Integration

- Prometheus metrics endpoint: `/api/prometheus/metrics`
- Exposes system and application metrics
- Compatible with Grafana

## Error Handling

### Backend

- Custom exception classes
- Structured error responses
- Global exception handlers
- Sentry integration (optional)

### Frontend

- Error boundaries
- User-friendly error messages
- Retry mechanisms
- Offline detection

## Logging

### Structured Logging

- JSON logging in production
- Text logging in development
- Log levels: DEBUG, INFO, WARNING, ERROR
- Contextual information

### Log Aggregation

- Compatible with log aggregation tools
- Structured JSON format
- Request/response logging
- Audit logging

## Backup and Restore

### Database Backups

- Manual backup via UI
- Automatic backup scheduling (via Celery)
- Backup storage in `backups/` directory
- Restore functionality

## Future Enhancements

- Kubernetes monitoring
- Docker container monitoring
- SNMP support
- Grafana integration
- Mobile app / PWA
- CLI tool improvements
