from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from input_validation import (
    validate_username, validate_url, sanitize_string,
    validate_no_sql_injection, validate_no_xss
)


# User schemas
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool = False
    is_active: bool
    totp_enabled: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    is_active: bool = True
    is_admin: bool = False
    
    @field_validator('username')
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        is_valid, error = validate_username(v)
        if not is_valid:
            raise ValueError(error)
        return sanitize_string(v, max_length=50)
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        # EmailStr already validates format, but we sanitize
        return sanitize_string(v, max_length=254)
    
    @field_validator('password')
    @classmethod
    def validate_password_safety(cls, v: str) -> str:
        # Check for SQL injection patterns
        is_valid, error = validate_no_sql_injection(v)
        if not is_valid:
            raise ValueError(error)
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    
    @field_validator('username')
    @classmethod
    def validate_username_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        is_valid, error = validate_username(v)
        if not is_valid:
            raise ValueError(error)
        return sanitize_string(v, max_length=50)
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return sanitize_string(v, max_length=254)
    
    @field_validator('password')
    @classmethod
    def validate_password_safety(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        is_valid, error = validate_no_sql_injection(v)
        if not is_valid:
            raise ValueError(error)
        return v


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TwoFactorSetupResponse(BaseModel):
    secret: str
    uri: str
    qr_code: str
    message: str


class TwoFactorVerifyRequest(BaseModel):
    token: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP token")


class TwoFactorEnableRequest(BaseModel):
    token: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP token to verify setup")


class LoginRequest(BaseModel):
    username: str
    password: str
    totp_token: Optional[str] = Field(None, min_length=6, max_length=6, description="6-digit TOTP token (required if 2FA is enabled)")


# Node schemas
class NodeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1, max_length=500)
    username: str = Field(..., min_length=1, max_length=100)
    token: str = Field(..., min_length=1, max_length=500)
    verify_ssl: bool = Field(default=True, description="Whether to verify SSL certificates")
    is_local: bool = True
    tags: Optional[List[str]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        sanitized = sanitize_string(v, max_length=100)
        is_valid, error = validate_no_xss(sanitized)
        if not is_valid:
            raise ValueError(error)
        return sanitized
    
    @field_validator('url')
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        is_valid, error = validate_url(v, require_https=False)
        if not is_valid:
            raise ValueError(error)
        return sanitize_string(v, max_length=500)
    
    @field_validator('username')
    @classmethod
    def validate_username_safe(cls, v: str) -> str:
        sanitized = sanitize_string(v, max_length=100)
        is_valid, error = validate_no_sql_injection(sanitized)
        if not is_valid:
            raise ValueError(error)
        return sanitized
    
    @field_validator('token')
    @classmethod
    def validate_token_safe(cls, v: str) -> str:
        # Don't sanitize token (might contain special chars), but check for SQL injection
        is_valid, error = validate_no_sql_injection(v)
        if not is_valid:
            raise ValueError(error)
        return v


class NodeUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    username: Optional[str] = None
    token: Optional[str] = None
    verify_ssl: Optional[bool] = None
    is_active: Optional[bool] = None
    is_local: Optional[bool] = None
    maintenance_mode: Optional[bool] = None
    tags: Optional[List[str]] = None


class NodeResponse(BaseModel):
    id: int
    name: str
    url: str
    is_local: bool
    is_active: bool
    maintenance_mode: bool
    status: str
    tags: Optional[List[str]] = None
    last_check: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BulkNodeCreate(BaseModel):
    nodes: List[NodeCreate]


class BulkNodeResponse(BaseModel):
    created: List[NodeResponse] = []
    failed: List[dict] = []  # List of {node_data, error}
    task_id: Optional[str] = None
    message: Optional[str] = None


# VM schemas
class VMResponse(BaseModel):
    id: int
    node_id: int
    vmid: int
    name: str
    status: str
    cpu_usage: float
    memory_usage: float
    memory_total: int
    disk_usage: float
    disk_total: int
    uptime: int
    tags: Optional[List[str]] = None
    last_check: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Service schemas
class ServiceCreate(BaseModel):
    vm_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=20)  # http, https, ping, port, custom
    target: str = Field(..., min_length=1, max_length=500)
    port: Optional[int] = Field(None, ge=1, le=65535)
    check_interval: int = Field(default=60, ge=10, le=3600)  # 10 seconds to 1 hour
    timeout: int = Field(default=5, ge=1, le=60)  # 1 to 60 seconds
    expected_status: int = Field(default=200, ge=100, le=599)
    custom_command: Optional[str] = Field(None, max_length=1000)  # For custom health checks
    custom_script: Optional[str] = Field(None, max_length=5000)  # For custom health check scripts
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        sanitized = sanitize_string(v, max_length=100)
        is_valid, error = validate_no_xss(sanitized)
        if not is_valid:
            raise ValueError(error)
        return sanitized
    
    @field_validator('target')
    @classmethod
    def validate_target(cls, v: str) -> str:
        # Target can be URL, IP, or hostname - basic sanitization
        sanitized = sanitize_string(v, max_length=500)
        is_valid, error = validate_no_sql_injection(sanitized)
        if not is_valid:
            raise ValueError(error)
        return sanitized
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = ["http", "https", "ping", "port", "custom"]
        if v.lower() not in valid_types:
            raise ValueError(f"Type must be one of: {', '.join(valid_types)}")
        return v.lower()
    
    @field_validator('custom_command', 'custom_script')
    @classmethod
    def validate_custom_safe(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        sanitized = sanitize_string(v, max_length=5000)
        is_valid, error = validate_no_sql_injection(sanitized)
        if not is_valid:
            raise ValueError(error)
        return sanitized


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    target: Optional[str] = None
    port: Optional[int] = None
    check_interval: Optional[int] = None
    timeout: Optional[int] = None
    is_active: Optional[bool] = None
    maintenance_mode: Optional[bool] = None
    expected_status: Optional[int] = None


class ServiceResponse(BaseModel):
    id: int
    vm_id: Optional[int]
    name: str
    type: str
    target: str
    port: Optional[int]
    check_interval: int
    timeout: int
    is_active: bool
    maintenance_mode: bool
    expected_status: int
    custom_command: Optional[str]
    custom_script: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class BulkServiceCreate(BaseModel):
    services: List[ServiceCreate]


class BulkServiceResponse(BaseModel):
    created: List[ServiceResponse] = []
    failed: List[dict] = []  # List of {service_data, error}
    task_id: Optional[str] = None
    message: Optional[str] = None


# Health check schemas
class HealthCheckResponse(BaseModel):
    id: int
    service_id: int
    status: str
    response_time: Optional[float]
    status_code: Optional[int]
    error_message: Optional[str]
    checked_at: datetime

    class Config:
        from_attributes = True


# Metric schemas
class MetricResponse(BaseModel):
    id: int
    node_id: Optional[int]
    vm_id: Optional[int]
    metric_type: str
    value: float
    unit: str
    recorded_at: datetime

    class Config:
        from_attributes = True


# Alert schemas
class AlertResponse(BaseModel):
    id: int
    user_id: Optional[int]
    alert_type: str
    severity: str
    title: str
    message: str
    node_id: Optional[int]
    vm_id: Optional[int]
    service_id: Optional[int]
    is_resolved: bool
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Dashboard schemas
class DashboardStats(BaseModel):
    total_nodes: int
    online_nodes: int
    total_vms: int
    running_vms: int
    total_services: int
    healthy_services: int
    active_alerts: int


# Webhook schemas
class WebhookCreate(BaseModel):
    name: str
    url: str
    method: str = "POST"
    headers: Optional[Dict] = None
    alert_types: Optional[List[str]] = None
    is_active: bool = True


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict] = None
    alert_types: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: int
    name: str
    url: str
    method: str
    headers: Optional[Dict]
    alert_types: Optional[List[str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Notification channel schemas
class NotificationChannelCreate(BaseModel):
    name: str
    type: str  # slack, discord
    webhook_url: str
    alert_types: Optional[List[str]] = None
    severity_filter: Optional[List[str]] = None
    is_active: bool = True


class NotificationChannelUpdate(BaseModel):
    name: Optional[str] = None
    webhook_url: Optional[str] = None
    alert_types: Optional[List[str]] = None
    severity_filter: Optional[List[str]] = None
    is_active: Optional[bool] = None


class NotificationChannelResponse(BaseModel):
    id: int
    name: str
    type: str
    webhook_url: str
    alert_types: Optional[List[str]] = None
    severity_filter: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Alert rule schemas
class AlertRuleCreate(BaseModel):
    name: str
    metric_type: str  # cpu, memory, disk, response_time
    operator: str  # >, <, >=, <=, ==
    threshold: float
    severity: str = "warning"  # info, warning, critical
    node_id: Optional[int] = None
    vm_id: Optional[int] = None
    service_id: Optional[int] = None
    cooldown_minutes: int = 5
    is_active: bool = True


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    metric_type: Optional[str] = None
    operator: Optional[str] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None
    node_id: Optional[int] = None
    vm_id: Optional[int] = None
    service_id: Optional[int] = None
    cooldown_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    id: int
    name: str
    metric_type: str
    operator: str
    threshold: float
    severity: str
    node_id: Optional[int] = None
    vm_id: Optional[int] = None
    service_id: Optional[int] = None
    cooldown_minutes: int
    is_active: bool
    last_triggered: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    resource_name: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
