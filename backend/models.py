from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    refresh_token = Column(String, nullable=True)
    refresh_token_expires = Column(DateTime, nullable=True)
    totp_secret = Column(String, nullable=True)  # TOTP secret for 2FA
    totp_enabled = Column(Boolean, default=False)  # Whether 2FA is enabled
    created_at = Column(DateTime, default=datetime.utcnow)

    alerts = relationship("Alert", back_populates="user")


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    url = Column(String, nullable=False)
    username = Column(String, nullable=False)
    token = Column(String, nullable=False)
    is_local = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    maintenance_mode = Column(Boolean, default=False)
    last_check = Column(DateTime, nullable=True)
    status = Column(String, default="unknown")  # online, offline, error
    tags = Column(JSON, nullable=True)  # Array of tag strings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vms = relationship("VM", back_populates="node", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="node", cascade="all, delete-orphan")


class VM(Base):
    __tablename__ = "vms"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    vmid = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="unknown")  # running, stopped, paused, etc.
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    memory_total = Column(Integer, default=0)
    disk_usage = Column(Float, default=0.0)
    disk_total = Column(Integer, default=0)
    uptime = Column(Integer, default=0)
    tags = Column(JSON, nullable=True)  # Array of tag strings
    last_check = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    node = relationship("Node", back_populates="vms")
    services = relationship("Service", back_populates="vm", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="vm", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    vm_id = Column(Integer, ForeignKey("vms.id"), nullable=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # http, https, ping, port, custom
    target = Column(String, nullable=False)  # URL, IP, or port
    custom_command = Column(Text, nullable=True)  # For custom health checks
    custom_script = Column(Text, nullable=True)  # For custom health check scripts
    port = Column(Integer, nullable=True)
    check_interval = Column(Integer, default=60)  # seconds
    timeout = Column(Integer, default=5)  # seconds
    is_active = Column(Boolean, default=True)
    maintenance_mode = Column(Boolean, default=False)
    expected_status = Column(Integer, default=200)  # for HTTP checks
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vm = relationship("VM", back_populates="services")
    health_checks = relationship("HealthCheck", back_populates="service", cascade="all, delete-orphan")


class HealthCheck(Base):
    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    status = Column(String, nullable=False)  # up, down, warning
    response_time = Column(Float, nullable=True)  # milliseconds
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow, index=True)

    service = relationship("Service", back_populates="health_checks")


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    vm_id = Column(Integer, ForeignKey("vms.id"), nullable=True)
    metric_type = Column(String, nullable=False)  # cpu, memory, disk, network
    value = Column(Float, nullable=False)
    unit = Column(String, default="percent")  # percent, bytes, bps, etc.
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    node = relationship("Node", back_populates="metrics")
    vm = relationship("VM", back_populates="metrics")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    alert_type = Column(String, nullable=False)  # node_down, vm_down, service_down, high_usage
    severity = Column(String, default="warning")  # info, warning, critical
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    vm_id = Column(Integer, ForeignKey("vms.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="alerts")


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    method = Column(String, default="POST")  # POST, PUT, PATCH
    headers = Column(JSON, nullable=True)  # Custom headers as JSON
    alert_types = Column(JSON, nullable=True)  # List of alert types to trigger on
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # slack, discord
    webhook_url = Column(String, nullable=False)
    alert_types = Column(JSON, nullable=True)  # List of alert types to trigger on
    severity_filter = Column(JSON, nullable=True)  # List of severities to trigger on (info, warning, critical)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    metric_type = Column(String, nullable=False)  # cpu, memory, disk, response_time
    operator = Column(String, nullable=False)  # >, <, >=, <=, ==
    threshold = Column(Float, nullable=False)
    severity = Column(String, default="warning")  # info, warning, critical
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)  # None = global
    vm_id = Column(Integer, ForeignKey("vms.id"), nullable=True)  # None = all VMs
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)  # None = all services
    cooldown_minutes = Column(Integer, default=5)  # Minutes before alerting again
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String, nullable=True)  # Store username for historical reference
    action = Column(String, nullable=False)  # create, update, delete, login, logout, etc.
    resource_type = Column(String, nullable=False)  # user, node, vm, service, alert, backup, etc.
    resource_id = Column(Integer, nullable=True)  # ID of the affected resource
    resource_name = Column(String, nullable=True)  # Name of the affected resource
    changes = Column(JSON, nullable=True)  # JSON object with before/after values
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User")
