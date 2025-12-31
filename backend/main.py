from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import json
import logging
from datetime import datetime
from database import init_db, get_db
from routers import auth, nodes, vms, services, dashboard, metrics, alerts, webhooks, health_checks
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

