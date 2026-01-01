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
from fastapi import APIRouter, Depends, HTTPException, status
from auth import get_current_active_user
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def get_celery_app():
    """Get Celery app if enabled, otherwise return None"""
    if not settings.celery_enabled:
        return None
    try:
        from celery_app import celery_app
        return celery_app
    except ImportError:
        return None


@router.get("/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user = Depends(get_current_active_user)
):
    """
    Get the status of a Celery background task.
    
    Returns task status, result (if completed), and progress information.
    """
    app = get_celery_app()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Celery is not enabled"
        )
    
    try:
        task = app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task.state,
        }
        
        if task.state == "PENDING":
            response["message"] = "Task is waiting to be processed"
        elif task.state == "PROGRESS":
            response["message"] = "Task is in progress"
            if task.info:
                response["current"] = task.info.get("current", 0)
                response["total"] = task.info.get("total", 0)
        elif task.state == "SUCCESS":
            response["message"] = "Task completed successfully"
            response["result"] = task.result
        elif task.state == "FAILURE":
            response["message"] = "Task failed"
            response["error"] = str(task.info) if task.info else "Unknown error"
        else:
            response["message"] = f"Task state: {task.state}"
        
        return response
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving task status: {str(e)}"
        )


@router.get("/{task_id}/result")
async def get_task_result(
    task_id: str,
    current_user = Depends(get_current_active_user)
):
    """
    Get the result of a completed Celery background task.
    
    Returns the full task result if the task has completed successfully.
    """
    app = get_celery_app()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Celery is not enabled"
        )
    
    try:
        task = app.AsyncResult(task_id)
        
        if task.state == "PENDING":
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Task is still pending"
            )
        elif task.state == "PROGRESS":
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Task is still in progress"
            )
        elif task.state == "SUCCESS":
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "result": task.result
            }
        elif task.state == "FAILURE":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Task failed: {str(task.info) if task.info else 'Unknown error'}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unknown task state: {task.state}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving task result: {str(e)}"
        )

