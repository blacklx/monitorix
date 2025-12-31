from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import json
import logging
from datetime import datetime
from database import init_db, get_db
from routers import auth, nodes, vms, services, dashboard, metrics, alerts, webhooks, health_checks, notification_channels
from scheduler import start_scheduler, stop_scheduler, set_broadcast_function
from config import settings
from rate_limiter import limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected WebSocket clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            try:
                self.active_connections.remove(connection)
            except ValueError:
                pass

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
    description="API for monitoring Proxmox nodes, VMs, and services",
    version="1.1.0",
    lifespan=lifespan
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(nodes.router)
app.include_router(vms.router)
app.include_router(services.router)
app.include_router(dashboard.router)
app.include_router(metrics.router)
app.include_router(alerts.router)
app.include_router(webhooks.router)
app.include_router(notification_channels.router)
app.include_router(health_checks.router)


@app.get("/")
async def root():
    return {"message": "Monitorix API", "version": "1.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and wait for messages
            data = await websocket.receive_text()
            # Echo back or handle client messages
            await websocket.send_json({"type": "pong", "message": "Connection active"})
    except WebSocketDisconnect:
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

