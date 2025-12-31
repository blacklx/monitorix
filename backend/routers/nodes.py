from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Node
from schemas import NodeCreate, NodeUpdate, NodeResponse, BulkNodeCreate, BulkNodeResponse
from auth import get_current_active_user
from proxmox_client import ProxmoxClient
from scheduler import check_node, sync_vms
from uptime import calculate_node_uptime
from rate_limiter import limiter
import asyncio

router = APIRouter(prefix="/api/nodes", tags=["nodes"])


@router.get("", response_model=List[NodeResponse])
async def get_nodes(
    tag: Optional[str] = Query(None, description="Filter nodes by tag name"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get all Proxmox nodes.
    
    Returns a list of all configured Proxmox nodes with their current status.
    Optionally filter by tag to get only nodes with a specific tag.
    
    **Example**: `/api/nodes?tag=production` returns only nodes tagged with "production"
    """
    query = db.query(Node)
    if tag:
        # Filter nodes that have this tag in their tags array
        # PostgreSQL JSONB @> operator checks if array contains the value
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import JSONB
        query = query.filter(cast(Node.tags, JSONB).contains([tag]))
    nodes = query.all()
    return nodes


@router.post("", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_node(
    request: Request,
    node_data: NodeCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new node"""
    # Check if node name already exists
    existing = db.query(Node).filter(Node.name == node_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Node with this name already exists"
        )
    
    # Test connection
    client = ProxmoxClient(node_data.url, node_data.username, node_data.token)
    if not client.test_connection():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to connect to Proxmox node"
        )
    
    node = Node(
        name=node_data.name,
        url=node_data.url,
        username=node_data.username,
        token=node_data.token,
        is_local=node_data.is_local,
        tags=node_data.tags
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    
    # Initial sync
    await check_node(node)
    await sync_vms(node)
    db.commit()
    
    return node


@router.post("/bulk", response_model=BulkNodeResponse)
@limiter.limit("5/minute")
async def bulk_create_nodes(
    request: Request,
    bulk_data: BulkNodeCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create multiple nodes at once"""
    created = []
    failed = []
    
    for node_data in bulk_data.nodes:
        try:
            # Check if node name already exists
            existing = db.query(Node).filter(Node.name == node_data.name).first()
            if existing:
                failed.append({
                    "node": node_data.dict(),
                    "error": "Node with this name already exists"
                })
                continue
            
            # Test connection
            client = ProxmoxClient(node_data.url, node_data.username, node_data.token)
            if not client.test_connection():
                failed.append({
                    "node": node_data.dict(),
                    "error": "Failed to connect to Proxmox node"
                })
                continue
            
            # Create node
            node = Node(
                name=node_data.name,
                url=node_data.url,
                username=node_data.username,
                token=node_data.token,
                is_local=node_data.is_local,
                tags=node_data.tags
            )
            db.add(node)
            db.commit()
            db.refresh(node)
            
            # Initial sync (don't wait for completion)
            asyncio.create_task(check_node(node))
            asyncio.create_task(sync_vms(node))
            
            created.append(node)
        except Exception as e:
            db.rollback()
            failed.append({
                "node": node_data.dict(),
                "error": str(e)
            })
    
    return BulkNodeResponse(created=created, failed=failed)


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a specific node"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    return node


@router.put("/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: int,
    node_data: NodeUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update a node"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    if node_data.name is not None:
        node.name = node_data.name
    if node_data.url is not None:
        node.url = node_data.url
    if node_data.username is not None:
        node.username = node_data.username
    if node_data.token is not None:
        node.token = node_data.token
    if node_data.is_active is not None:
        node.is_active = node_data.is_active
    if node_data.is_local is not None:
        node.is_local = node_data.is_local
    if node_data.maintenance_mode is not None:
        node.maintenance_mode = node_data.maintenance_mode
    if node_data.tags is not None:
        node.tags = node_data.tags
    
    db.commit()
    db.refresh(node)
    return node


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a node"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    db.delete(node)
    db.commit()


@router.post("/{node_id}/sync", response_model=NodeResponse)
async def sync_node(
    node_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Manually sync a node"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    await check_node(node)
    await sync_vms(node)
    db.commit()
    db.refresh(node)
    return node


@router.get("/{node_id}/uptime")
async def get_node_uptime(
    node_id: int,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get uptime statistics for a node"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    uptime_data = calculate_node_uptime(db, node_id, hours)
    return uptime_data


@router.post("/test-connection")
async def test_connection(
    node_data: NodeCreate,
    current_user = Depends(get_current_active_user)
):
    """Test connection to a Proxmox node without saving it"""
    try:
        client = ProxmoxClient(node_data.url, node_data.username, node_data.token)
        if client.test_connection():
            return {"success": True, "message": "Connection successful"}
        else:
            return {"success": False, "message": "Failed to connect to Proxmox node"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/{node_id}/maintenance-mode")
async def toggle_maintenance_mode(
    node_id: int,
    maintenance_mode: bool = Query(..., description="Maintenance mode status"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Toggle maintenance mode for a node"""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    node.maintenance_mode = maintenance_mode
    db.commit()
    db.refresh(node)
    return node

