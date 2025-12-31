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
