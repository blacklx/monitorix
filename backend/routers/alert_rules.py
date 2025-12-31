from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import AlertRule, Node, VM, Service
from schemas import AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse
from auth import get_current_active_user
from rate_limiter import limiter

router = APIRouter(prefix="/api/alert-rules", tags=["alert-rules"])


@router.get("", response_model=List[AlertRuleResponse])
async def get_alert_rules(
    node_id: Optional[int] = None,
    vm_id: Optional[int] = None,
    service_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all alert rules, optionally filtered by node/vm/service"""
    query = db.query(AlertRule)
    
    if node_id:
        query = query.filter(AlertRule.node_id == node_id)
    if vm_id:
        query = query.filter(AlertRule.vm_id == vm_id)
    if service_id:
        query = query.filter(AlertRule.service_id == service_id)
    
    rules = query.all()
    return rules


@router.post("", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_alert_rule(
    request: Request,
    rule_data: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new alert rule"""
    # Validate metric type
    valid_metric_types = ["cpu", "memory", "disk", "response_time"]
    if rule_data.metric_type not in valid_metric_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Metric type must be one of: {', '.join(valid_metric_types)}"
        )
    
    # Validate operator
    valid_operators = [">", "<", ">=", "<=", "=="]
    if rule_data.operator not in valid_operators:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Operator must be one of: {', '.join(valid_operators)}"
        )
    
    # Validate severity
    valid_severities = ["info", "warning", "critical"]
    if rule_data.severity not in valid_severities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Severity must be one of: {', '.join(valid_severities)}"
        )
    
    # Validate node_id if provided
    if rule_data.node_id:
        node = db.query(Node).filter(Node.id == rule_data.node_id).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
    
    # Validate vm_id if provided
    if rule_data.vm_id:
        vm = db.query(VM).filter(VM.id == rule_data.vm_id).first()
        if not vm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="VM not found"
            )
    
    # Validate service_id if provided
    if rule_data.service_id:
        service = db.query(Service).filter(Service.id == rule_data.service_id).first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
    
    rule = AlertRule(**rule_data.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a specific alert rule"""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found"
        )
    return rule


@router.put("/{rule_id}", response_model=AlertRuleResponse)
@limiter.limit("20/minute")
async def update_alert_rule(
    request: Request,
    rule_id: int,
    rule_data: AlertRuleUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update an alert rule"""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found"
        )
    
    update_data = rule_data.dict(exclude_unset=True)
    
    # Validate metric type if provided
    if "metric_type" in update_data:
        valid_metric_types = ["cpu", "memory", "disk", "response_time"]
        if update_data["metric_type"] not in valid_metric_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Metric type must be one of: {', '.join(valid_metric_types)}"
            )
    
    # Validate operator if provided
    if "operator" in update_data:
        valid_operators = [">", "<", ">=", "<=", "=="]
        if update_data["operator"] not in valid_operators:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Operator must be one of: {', '.join(valid_operators)}"
            )
    
    # Validate severity if provided
    if "severity" in update_data:
        valid_severities = ["info", "warning", "critical"]
        if update_data["severity"] not in valid_severities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Severity must be one of: {', '.join(valid_severities)}"
            )
    
    # Validate node_id if provided
    if "node_id" in update_data and update_data["node_id"]:
        node = db.query(Node).filter(Node.id == update_data["node_id"]).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
    
    # Validate vm_id if provided
    if "vm_id" in update_data and update_data["vm_id"]:
        vm = db.query(VM).filter(VM.id == update_data["vm_id"]).first()
        if not vm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="VM not found"
            )
    
    # Validate service_id if provided
    if "service_id" in update_data and update_data["service_id"]:
        service = db.query(Service).filter(Service.id == update_data["service_id"]).first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
    
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_alert_rule(
    request: Request,
    rule_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete an alert rule"""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert rule not found"
        )
    db.delete(rule)
    db.commit()

