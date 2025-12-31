"""
Copyright 2024 Monitorix Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import json
import logging
from datetime import datetime
from database import init_db, get_db
from routers import auth, nodes, vms, services, dashboard, metrics, alerts, webhooks, health_checks, notification_channels, users, alert_rules, export, backup, audit_logs, version
from scheduler import start_scheduler, stop_scheduler, set_broadcast_function
from config import settings
from rate_limiter import limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from exceptions import global_exception_handler, validation_exception_handler, MonitorixException
from middleware.security_headers import SecurityHeadersMiddleware

# Initialize Sentry early (before logging setup to catch all errors)
from sentry_config import init_sentry
init_sentry()

# Setup structured logging
from logging_config import setup_logging
setup_logging(
    log_level=settings.log_level,
    use_json=settings.use_json_logging,
    log_file=settings.log_file
)
logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
        except ValueError:
            logger.warning("Attempted to remove WebSocket connection that was not in active_connections")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        disconnected = []
        success_count = 0
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                success_count += 1
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                logger.warning(f"Failed to send WebSocket message to client: {error_type}: {error_msg}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            try:
                self.active_connections.remove(connection)
            except ValueError:
                pass
        
        if disconnected:
            logger.info(f"Removed {len(disconnected)} dead WebSocket connection(s). Active: {len(self.active_connections)}")
        
        return success_count

manager = ConnectionManager()


def create_admin_user_if_needed():
    """Create admin user if no users exist"""
    from database import SessionLocal
    from models import User
    from auth import get_password_hash
    import secrets
    
    db = SessionLocal()
    try:
        # Check if any users exist
        user_count = db.query(User).count()
        if user_count > 0:
            logger.info("Users already exist, skipping admin user creation")
            return None
        
        # Generate password if not set
        if settings.admin_password:
            admin_password = settings.admin_password
        else:
            admin_password = secrets.token_urlsafe(16)
            logger.info(f"Generated admin password: {admin_password}")
        
        # Create admin user
        hashed_password = get_password_hash(admin_password)
        admin_user = User(
            username=settings.admin_username,
            email=settings.admin_email,
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        logger.info(f"Created admin user: {settings.admin_username}")
        return admin_password
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        db.rollback()
        return None
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Running database migrations...")
    try:
        from migrations import run_migrations
        run_migrations()
    except Exception as e:
        logger.warning(f"Migration failed, falling back to init_db: {e}")
        logger.info("Initializing database...")
        init_db()
    
    # Create admin user if needed
    logger.info("Checking for admin user...")
    admin_password = create_admin_user_if_needed()
    if admin_password:
        logger.warning("=" * 60)
        logger.warning("ADMIN USER CREATED")
        logger.warning(f"Username: {settings.admin_username}")
        logger.warning(f"Email: {settings.admin_email}")
        logger.warning(f"Password: {admin_password}")
        logger.warning("=" * 60)
        logger.warning("SAVE THIS PASSWORD - IT WILL NOT BE SHOWN AGAIN!")
        logger.warning("=" * 60)
        # Also print to stdout for easier extraction
        print(f"\n{'=' * 60}")
        print(f"ADMIN USER CREATED")
        print(f"Username: {settings.admin_username}")
        print(f"Email: {settings.admin_email}")
        print(f"Password: {admin_password}")
        print(f"{'=' * 60}\n")
    
    logger.info("Starting scheduler...")
    # Set broadcast function for scheduler
    set_broadcast_function(broadcast_update)
    start_scheduler()
    yield
    # Shutdown
    logger.info("Stopping scheduler...")
    stop_scheduler()


app = FastAPI(
    title="Monitorix API",
    description="""
    ## Monitorix - Professional Proxmox Monitoring API
    
    A comprehensive REST API for monitoring Proxmox nodes, virtual machines, and services.
    
    ### Features
    
    * **Node Management**: Monitor Proxmox nodes with real-time status and metrics
    * **VM Monitoring**: Track virtual machines with CPU, memory, and disk usage
    * **Service Health Checks**: HTTP/HTTPS, ping, port, and custom health checks
    * **Alerting**: Configurable alert rules with email, Slack, and Discord notifications
    * **Metrics**: Historical metrics tracking with export capabilities
    * **User Management**: Multi-user support with admin roles
    * **Audit Logging**: Comprehensive audit trail of all system changes
    * **Backup/Restore**: Database backup and restore functionality
    
    ### Authentication
    
    Most endpoints require authentication using JWT tokens. Use the `/api/auth/login` endpoint
    to obtain an access token, then include it in the `Authorization` header:
    
    ```
    Authorization: Bearer <your-access-token>
    ```
    
    ### Rate Limiting
    
    API endpoints are rate-limited to prevent abuse. Default limits:
    - 1000 requests per hour
    - 100 requests per minute
    
    ### WebSocket
    
    Real-time updates are available via WebSocket at `/ws`. Connect to receive live updates
    for node status, VM status, service health checks, and alerts.
    """,
    version="1.2.0",
    lifespan=lifespan,
    tags_metadata=[
        {
            "name": "auth",
            "description": "Authentication endpoints. Login, logout, password reset, and token refresh.",
        },
        {
            "name": "nodes",
            "description": "Proxmox node management. Add, update, delete, and sync nodes.",
        },
        {
            "name": "vms",
            "description": "Virtual machine operations. View VM details, sync, and get uptime statistics.",
        },
        {
            "name": "services",
            "description": "Service health check management. Create, update, and monitor services.",
        },
        {
            "name": "dashboard",
            "description": "Dashboard statistics and overview data.",
        },
        {
            "name": "metrics",
            "description": "Metrics retrieval and export. Historical CPU, memory, and disk usage data.",
        },
        {
            "name": "alerts",
            "description": "Alert management. View, resolve, and delete alerts.",
        },
        {
            "name": "health-checks",
            "description": "Health check results and statistics for services.",
        },
        {
            "name": "webhooks",
            "description": "Webhook configuration for alert notifications.",
        },
        {
            "name": "notification-channels",
            "description": "Notification channel management (Slack, Discord).",
        },
        {
            "name": "users",
            "description": "User management endpoints (admin only).",
        },
        {
            "name": "alert-rules",
            "description": "Configurable alert rules for automated alerting based on metrics.",
        },
        {
            "name": "export",
            "description": "Data export endpoints for nodes, VMs, services, and alerts (CSV/JSON).",
        },
        {
            "name": "backup",
            "description": "Database backup and restore operations (admin only).",
        },
        {
            "name": "audit-logs",
            "description": "Audit log viewing and statistics (admin only).",
        },
    ],
    contact={
        "name": "Monitorix",
        "url": "https://github.com/blacklx/monitorix",
    },
    license_info={
        "name": "Apache License 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware (add before CORS)
# Only enable HSTS if explicitly enabled (should be used with HTTPS)
enable_hsts = settings.enable_hsts
app.add_middleware(SecurityHeadersMiddleware, enable_hsts=enable_hsts)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
# All routers are included with /api prefix for backward compatibility
# Future versions can use /api/v1, /api/v2, etc.
app.include_router(auth.router)
app.include_router(nodes.router)
app.include_router(vms.router)
app.include_router(services.router)
app.include_router(dashboard.router)
app.include_router(metrics.router)
app.include_router(alerts.router)
app.include_router(webhooks.router)
app.include_router(notification_channels.router)
app.include_router(users.router)
app.include_router(alert_rules.router)
app.include_router(health_checks.router)
app.include_router(export.router)
app.include_router(backup.router)
app.include_router(audit_logs.router)
app.include_router(version.router)

# API versioning support
# Current implementation uses /api prefix (equivalent to v1)
# Future versions can be added with /api/v2, /api/v3, etc.
# Clients can specify version via:
# - X-API-Version header: "v1"
# - Accept header: "application/json; version=v1"
from api_version import get_api_version, CURRENT_API_VERSION, SUPPORTED_VERSIONS

@app.get("/api/versions")
async def get_supported_versions():
    """
    Get list of supported API versions.
    
    Returns information about available API versions and the current default version.
    """
    return {
        "current_version": CURRENT_API_VERSION,
        "supported_versions": SUPPORTED_VERSIONS,
        "default_version": CURRENT_API_VERSION,
        "versioning_strategy": "Header-based (X-API-Version or Accept header)"
    }

# Add exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(MonitorixException, global_exception_handler)


@app.get("/", tags=["info"])
async def root():
    """
    API root endpoint.
    
    Returns basic API information including version and API versioning information.
    """
    return {
        "message": "Monitorix API",
        "version": "1.2.0",
        "api_version": CURRENT_API_VERSION,
        "supported_api_versions": SUPPORTED_VERSIONS,
        "docs": "/docs",
        "redoc": "/redoc",
        "versioning": {
            "method": "Header-based",
            "headers": ["X-API-Version", "Accept (version parameter)"],
            "default": CURRENT_API_VERSION
        }
    }


@app.get("/health", tags=["info"])
async def health():
    """
    Health check endpoint.
    
    Returns the health status of the API. Useful for monitoring and load balancers.
    """
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and wait for messages
            data = await websocket.receive_text()
            
            # Handle heartbeat ping
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    # Send pong response
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    })
                    continue
            except (json.JSONDecodeError, KeyError):
                # Not a ping message, ignore for now
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {type(e).__name__}: {e}")
        manager.disconnect(websocket)


# Function to broadcast updates (can be called from scheduler)
async def broadcast_update(update_type: str, data: dict):
    """Broadcast update to all connected WebSocket clients"""
    await manager.broadcast({
        "type": update_type,
        "data": data,
        "timestamp": str(datetime.utcnow())
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

