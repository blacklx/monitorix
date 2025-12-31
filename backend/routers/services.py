from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from database import get_db
from models import Service, VM
from schemas import ServiceCreate, ServiceUpdate, ServiceResponse, BulkServiceCreate, BulkServiceResponse
from auth import get_current_active_user
from scheduler import check_service
from uptime import calculate_service_uptime
from rate_limiter import limiter
from cache import get, set, get_cache_key, invalidate_cache
from config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("", response_model=List[ServiceResponse])
async def get_services(
    vm_id: Optional[int] = Query(None, description="Filter services by VM ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get all service health checks.
    
    Returns a list of all configured services with their current health status.
    Optionally filter by VM ID to get only services associated with a specific VM.
    
    **Example**: `/api/services?vm_id=1` returns only services for VM 1
    
    Results are cached for 60 seconds.
    """
    cache_key = get_cache_key("services:list", vm_id=vm_id)
    
    # Try cache first
    cached_services = get(cache_key)
    if cached_services:
        return [ServiceResponse(**service) for service in cached_services]
    
    # Cache miss - query database
    query = db.query(Service).options(joinedload(Service.vm))
    if vm_id:
        query = query.filter(Service.vm_id == vm_id)
    services = query.all()
    
    # Serialize and cache
    services_data = [ServiceResponse.from_orm(service).dict() for service in services]
    set(cache_key, services_data, ttl=60)
    
    return services


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_service(
    request: Request,
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new service"""
    # Validate VM if provided
    if service_data.vm_id:
        vm = db.query(VM).filter(VM.id == service_data.vm_id).first()
        if not vm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="VM not found"
            )
    
    service = Service(**service_data.dict())
    db.add(service)
    db.commit()
    db.refresh(service)
    
    # Invalidate cache
    invalidate_cache("services")
    invalidate_cache("dashboard")
    
    return service


@router.post("/bulk", response_model=BulkServiceResponse)
@limiter.limit("5/minute")
async def bulk_create_services(
    request: Request,
    bulk_data: BulkServiceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Create multiple services at once.
    
    If Celery is enabled, this will run as a background job.
    Otherwise, it runs synchronously.
    """
    # Use Celery if enabled and Redis is available
    if settings.celery_enabled and settings.redis_enabled:
        try:
            from tasks import bulk_create_services_task
            
            # Prepare data for Celery task
            services_data = [service.dict() for service in bulk_data.services]
            
            # Start background task
            task = bulk_create_services_task.delay(services_data)
            
            # Return task ID for status checking
            return BulkServiceResponse(
                created=[],
                failed=[],
                task_id=task.id,
                message="Bulk service creation started in background. Use task_id to check status."
            )
        except Exception as e:
            logger.warning(f"Celery task failed, falling back to synchronous: {e}")
            # Fall through to synchronous execution
    
    # Synchronous execution (fallback or if Celery disabled)
    created = []
    failed = []
    
    for service_data in bulk_data.services:
        try:
            # Validate VM if provided
            if service_data.vm_id:
                vm = db.query(VM).filter(VM.id == service_data.vm_id).first()
                if not vm:
                    failed.append({
                        "service": service_data.dict(),
                        "error": "VM not found"
                    })
                    continue
            
            # Create service
            service = Service(**service_data.dict())
            db.add(service)
            db.commit()
            db.refresh(service)
            
            # Initial check (don't wait for completion)
            asyncio.create_task(check_service(service))
            
            created.append(service)
        except Exception as e:
            db.rollback()
            failed.append({
                "service": service_data.dict(),
                "error": str(e)
            })
    
    # Invalidate cache after bulk create
    if created:
        invalidate_cache("services")
        invalidate_cache("dashboard")
    
    return BulkServiceResponse(created=created, failed=failed)


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a specific service"""
    service = db.query(Service).options(joinedload(Service.vm)).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update a service"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    update_data = service_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)
    
    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a service"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    db.delete(service)
    db.commit()


@router.post("/{service_id}/check")
async def check_service_manual(
    service_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Manually trigger a service check"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    await check_service(service)
    return {"message": "Service check completed"}


@router.post("/test")
async def test_service(
    service_data: ServiceCreate,
    current_user = Depends(get_current_active_user)
):
    """Test a service without saving it"""
    from health_checks import HealthChecker
    
    try:
        result = None
        url = service_data.target
        
        # Build URL with port if provided
        if service_data.type in ["http", "https"]:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"{service_data.type}://{url}"
            if service_data.port:
                # Replace port in URL if it exists, or add it
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(url)
                netloc = f"{parsed.hostname}:{service_data.port}" if parsed.hostname else f":{service_data.port}"
                url = urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
        
        if service_data.type == "http" or service_data.type == "https":
            result = await HealthChecker.check_http(
                url,
                service_data.timeout,
                service_data.expected_status
            )
        elif service_data.type == "ping":
            result = HealthChecker.check_ping(
                service_data.target,
                service_data.timeout
            )
        elif service_data.type == "port":
            if not service_data.port:
                return {"success": False, "message": "Port is required for port checks"}
            result = HealthChecker.check_port(
                service_data.target,
                service_data.port,
                service_data.timeout
            )
        
        if result and result.get("status") == "up":
            return {"success": True, "message": "Service test successful"}
        else:
            return {"success": False, "message": result.get("error_message", "Service test failed")}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/{service_id}/uptime")
async def get_service_uptime(
    service_id: int,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get uptime statistics for a service"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    uptime_data = calculate_service_uptime(db, service_id, hours)
    return uptime_data


@router.post("/{service_id}/maintenance-mode")
async def toggle_service_maintenance_mode(
    service_id: int,
    maintenance_mode: bool = Query(..., description="Maintenance mode status"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Toggle maintenance mode for a service"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service.maintenance_mode = maintenance_mode
    db.commit()
    db.refresh(service)
    return service


@router.post("/{service_id}/toggle-active")
async def toggle_service_active(
    service_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Toggle active/inactive status for a service"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service.is_active = not service.is_active
    db.commit()
    db.refresh(service)
    return service

