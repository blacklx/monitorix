from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime


# User schemas
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool = False
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    is_active: bool = True
    is_admin: bool = False


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


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


# Node schemas
class NodeCreate(BaseModel):
    name: str
    url: str
    username: str
    token: str
    is_local: bool = True


class NodeUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    username: Optional[str] = None
    token: Optional[str] = None
    is_active: Optional[bool] = None
    is_local: Optional[bool] = None


class NodeResponse(BaseModel):
    id: int
    name: str
    url: str
    is_local: bool
    is_active: bool
    maintenance_mode: bool
    status: str
    last_check: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BulkNodeCreate(BaseModel):
    nodes: List[NodeCreate]


class BulkNodeResponse(BaseModel):
    created: List[NodeResponse]
    failed: List[dict]  # List of {node_data, error}


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
    last_check: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Service schemas
class ServiceCreate(BaseModel):
    vm_id: Optional[int] = None
    name: str
    type: str  # http, https, ping, port, custom
    target: str
    port: Optional[int] = None
    check_interval: int = 60
    timeout: int = 5
    expected_status: int = 200
    custom_command: Optional[str] = None  # For custom health checks
    custom_script: Optional[str] = None  # For custom health check scripts


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
    created: List[ServiceResponse]
    failed: List[dict]  # List of {service_data, error}


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
