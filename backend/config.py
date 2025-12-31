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
    refresh_token_expire_days: int = 7  # Refresh tokens valid for 7 days
    # Admin user creation
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@monitorix.local")
    admin_password: Optional[str] = os.getenv("ADMIN_PASSWORD", None)  # Auto-generated if not set
    
    # Proxmox
    proxmox_nodes: str = os.getenv("PROXMOX_NODES", "")
    proxmox_verify_ssl: bool = os.getenv("PROXMOX_VERIFY_SSL", "true").lower() == "true"
    proxmox_ca_bundle: Optional[str] = os.getenv("PROXMOX_CA_BUNDLE", None)
    
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
    
    # Frontend URL (for password reset links)
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Security headers
    environment: str = os.getenv("ENVIRONMENT", "development")
    enable_hsts: bool = os.getenv("ENABLE_HSTS", "false").lower() == "true"
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: Optional[str] = os.getenv("LOG_FILE", None)
    use_json_logging: Optional[bool] = None  # Auto-detect from ENVIRONMENT if None
    
    # Sentry Error Tracking
    sentry_enabled: bool = os.getenv("SENTRY_ENABLED", "false").lower() == "true"
    sentry_dsn: Optional[str] = os.getenv("SENTRY_DSN", None)
    sentry_environment: str = os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))
    sentry_traces_sample_rate: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))  # 10% of transactions
    sentry_profiles_sample_rate: float = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))  # 10% of profiles
    
    # CORS Configuration
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS", "*") != "*" else ["*"]
    cors_allow_credentials: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    cors_allow_methods: List[str] = os.getenv("CORS_ALLOW_METHODS", "*").split(",") if os.getenv("CORS_ALLOW_METHODS", "*") != "*" else ["*"]
    cors_allow_headers: List[str] = os.getenv("CORS_ALLOW_HEADERS", "*").split(",") if os.getenv("CORS_ALLOW_HEADERS", "*") != "*" else ["*"]
    
    # Rate Limiting
    rate_limit_per_hour: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    
    # Redis Caching
    redis_enabled: bool = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    
    class Config:
        env_file = ".env"


settings = Settings()

