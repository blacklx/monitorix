from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://monitorix:changeme@postgres:5432/monitorix")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "changeme-secret-key")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    # Admin user creation
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@monitorix.local")
    admin_password: Optional[str] = os.getenv("ADMIN_PASSWORD", None)  # Auto-generated if not set
    
    # Proxmox
    proxmox_nodes: str = os.getenv("PROXMOX_NODES", "")
    
    # Health Checks
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))
    http_timeout: int = int(os.getenv("HTTP_TIMEOUT", "5"))
    ping_timeout: int = int(os.getenv("PING_TIMEOUT", "3"))
    
    # Alerts
    alert_email_enabled: bool = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"
    alert_email_smtp_host: Optional[str] = os.getenv("ALERT_EMAIL_SMTP_HOST")
    alert_email_smtp_port: int = int(os.getenv("ALERT_EMAIL_SMTP_PORT", "587"))
    alert_email_smtp_user: Optional[str] = os.getenv("ALERT_EMAIL_SMTP_USER")
    alert_email_smtp_password: Optional[str] = os.getenv("ALERT_EMAIL_SMTP_PASSWORD")
    alert_email_from: Optional[str] = os.getenv("ALERT_EMAIL_FROM")
    alert_email_to: Optional[str] = os.getenv("ALERT_EMAIL_TO")
    
    # Metrics Retention
    metrics_retention_days: int = int(os.getenv("METRICS_RETENTION_DAYS", "30"))
    metrics_cleanup_enabled: bool = os.getenv("METRICS_CLEANUP_ENABLED", "true").lower() == "true"
    
    class Config:
        env_file = ".env"


settings = Settings()

