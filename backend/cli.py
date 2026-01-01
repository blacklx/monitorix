#!/usr/bin/env python3
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

Monitorix CLI Tool

Command-line interface for managing Monitorix.
"""
import argparse
import sys
import os
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Node, VM, Service, Alert, User
from auth import get_password_hash, verify_password
from proxmox_client import ProxmoxClient
import json


def list_nodes(args):
    """List all nodes"""
    db = SessionLocal()
    try:
        nodes = db.query(Node).all()
        if not nodes:
            print("No nodes configured.")
            return
        
        print(f"\n{'ID':<5} {'Name':<20} {'Status':<10} {'URL':<40}")
        print("-" * 80)
        for node in nodes:
            print(f"{node.id:<5} {node.name:<20} {node.status:<10} {node.url:<40}")
    finally:
        db.close()


def list_vms(args):
    """List all VMs"""
    db = SessionLocal()
    try:
        vms = db.query(VM).all()
        if not vms:
            print("No VMs found.")
            return
        
        print(f"\n{'ID':<5} {'Name':<30} {'Status':<10} {'Node':<20}")
        print("-" * 70)
        for vm in vms:
            node_name = vm.node.name if vm.node else "Unknown"
            print(f"{vm.id:<5} {vm.name:<30} {vm.status:<10} {node_name:<20}")
    finally:
        db.close()


def list_services(args):
    """List all services"""
    db = SessionLocal()
    try:
        services = db.query(Service).all()
        if not services:
            print("No services configured.")
            return
        
        print(f"\n{'ID':<5} {'Name':<30} {'Type':<10} {'Status':<10} {'Target':<40}")
        print("-" * 100)
        for service in services:
            print(f"{service.id:<5} {service.name:<30} {service.check_type:<10} {service.status:<10} {service.target:<40}")
    finally:
        db.close()


def list_alerts(args):
    """List alerts"""
    db = SessionLocal()
    try:
        query = db.query(Alert)
        
        if args.resolved:
            query = query.filter(Alert.is_resolved == True)
        else:
            query = query.filter(Alert.is_resolved == False)
        
        if args.severity:
            query = query.filter(Alert.severity == args.severity)
        
        alerts = query.order_by(Alert.triggered_at.desc()).limit(args.limit).all()
        
        if not alerts:
            print("No alerts found.")
            return
        
        print(f"\n{'ID':<5} {'Type':<20} {'Severity':<10} {'Message':<50} {'Triggered':<20}")
        print("-" * 110)
        for alert in alerts:
            triggered = alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S") if alert.triggered_at else "N/A"
            message = alert.message[:47] + "..." if len(alert.message) > 50 else alert.message
            print(f"{alert.id:<5} {alert.alert_type:<20} {alert.severity:<10} {message:<50} {triggered:<20}")
    finally:
        db.close()


def create_user(args):
    """Create a new user"""
    db = SessionLocal()
    try:
        # Check if username exists
        existing = db.query(User).filter(User.username == args.username).first()
        if existing:
            print(f"Error: User '{args.username}' already exists.")
            return
        
        # Check if email exists
        existing_email = db.query(User).filter(User.email == args.email).first()
        if existing_email:
            print(f"Error: Email '{args.email}' is already in use.")
            return
        
        # Create user
        user = User(
            username=args.username,
            email=args.email,
            hashed_password=get_password_hash(args.password),
            is_active=True,
            is_admin=args.admin
        )
        db.add(user)
        db.commit()
        print(f"User '{args.username}' created successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
    finally:
        db.close()


def reset_admin_password(args):
    """Reset admin user password"""
    from config import settings
    import secrets
    
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(
            User.username == settings.admin_username
        ).first()
        
        if not admin_user:
            print(f"Error: Admin user '{settings.admin_username}' not found.")
            return
        
        # Generate new password if not provided
        if args.password:
            new_password = args.password
            # Ensure provided password is not too long for bcrypt (72 bytes max)
            password_bytes = new_password.encode('utf-8')
            if len(password_bytes) > 72:
                new_password = new_password[:72]
                print("Warning: Password was truncated to 72 bytes for bcrypt compatibility")
        else:
            # Use token_urlsafe(12) which generates ~16 chars, well under 72 bytes
            new_password = secrets.token_urlsafe(12)
        
        # Update password
        admin_user.hashed_password = get_password_hash(new_password)
        db.commit()
        
        print(f"\n{'=' * 60}")
        print(f"ADMIN PASSWORD RESET")
        print(f"Username: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print(f"New Password: {new_password}")
        print(f"{'=' * 60}\n")
        print("SAVE THIS PASSWORD - IT WILL NOT BE SHOWN AGAIN!")
        
        # Write password to temporary file for setup script to read
        import os
        temp_password_file = "/tmp/admin_password.txt"
        try:
            with open(temp_password_file, 'w') as f:
                f.write(new_password)
            os.chmod(temp_password_file, 0o600)  # Read/write for owner only
        except Exception as e:
            print(f"Warning: Could not write password to temp file: {e}")
    except Exception as e:
        db.rollback()
        print(f"Error resetting admin password: {e}")
    finally:
        db.close()


def test_node(args):
    """Test connection to a node"""
    db = SessionLocal()
    try:
        node = db.query(Node).filter(Node.id == args.node_id).first()
        if not node:
            print(f"Error: Node with ID {args.node_id} not found.")
            return
        
        print(f"Testing connection to node '{node.name}' ({node.url})...")
        client = ProxmoxClient(node.url, node.username, node.token)
        
        if client.test_connection():
            print("✓ Connection successful!")
        else:
            print("✗ Connection failed!")
    finally:
        db.close()


def export_data(args):
    """Export data to JSON"""
    db = SessionLocal()
    try:
        data = {}
        
        if args.type == "nodes" or args.type == "all":
            nodes = db.query(Node).all()
            data["nodes"] = [{
                "id": n.id,
                "name": n.name,
                "url": n.url,
                "username": n.username,
                "status": n.status,
                "is_active": n.is_active,
                "maintenance_mode": n.maintenance_mode
            } for n in nodes]
        
        if args.type == "vms" or args.type == "all":
            vms = db.query(VM).all()
            data["vms"] = [{
                "id": v.id,
                "name": v.name,
                "vmid": v.vmid,
                "status": v.status,
                "node_id": v.node_id
            } for v in vms]
        
        if args.type == "services" or args.type == "all":
            services = db.query(Service).all()
            data["services"] = [{
                "id": s.id,
                "name": s.name,
                "check_type": s.check_type,
                "target": s.target,
                "status": s.status,
                "is_active": s.is_active
            } for s in services]
        
        if args.type == "alerts" or args.type == "all":
            alerts = db.query(Alert).all()
            data["alerts"] = [{
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "is_resolved": a.is_resolved,
                "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None
            } for a in alerts]
        
        output = json.dumps(data, indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Data exported to {args.output}")
        else:
            print(output)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Monitorix CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List nodes
    list_nodes_parser = subparsers.add_parser("nodes", help="List all nodes")
    list_nodes_parser.set_defaults(func=list_nodes)
    
    # List VMs
    list_vms_parser = subparsers.add_parser("vms", help="List all VMs")
    list_vms_parser.set_defaults(func=list_vms)
    
    # List services
    list_services_parser = subparsers.add_parser("services", help="List all services")
    list_services_parser.set_defaults(func=list_services)
    
    # List alerts
    list_alerts_parser = subparsers.add_parser("alerts", help="List alerts")
    list_alerts_parser.add_argument("--resolved", action="store_true", help="Show resolved alerts")
    list_alerts_parser.add_argument("--severity", choices=["info", "warning", "critical"], help="Filter by severity")
    list_alerts_parser.add_argument("--limit", type=int, default=50, help="Limit number of results")
    list_alerts_parser.set_defaults(func=list_alerts)
    
    # Create user
    create_user_parser = subparsers.add_parser("create-user", help="Create a new user")
    create_user_parser.add_argument("username", help="Username")
    create_user_parser.add_argument("email", help="Email address")
    create_user_parser.add_argument("password", help="Password")
    create_user_parser.add_argument("--admin", action="store_true", help="Make user an admin")
    create_user_parser.set_defaults(func=create_user)
    
    # Reset admin password
    reset_admin_parser = subparsers.add_parser("reset-admin-password", help="Reset admin user password")
    reset_admin_parser.add_argument("--password", help="New password (auto-generated if not provided)")
    reset_admin_parser.set_defaults(func=reset_admin_password)
    
    # Test node
    test_node_parser = subparsers.add_parser("test-node", help="Test connection to a node")
    test_node_parser.add_argument("node_id", type=int, help="Node ID")
    test_node_parser.set_defaults(func=test_node)
    
    # Export data
    export_parser = subparsers.add_parser("export", help="Export data to JSON")
    export_parser.add_argument("type", choices=["nodes", "vms", "services", "alerts", "all"], help="Data type to export")
    export_parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    export_parser.set_defaults(func=export_data)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()

