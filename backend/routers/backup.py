from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from database import get_db
from auth import get_current_active_user, get_current_admin_user
from config import settings
import subprocess
import os
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backup", tags=["backup"])

# Backup directory (relative to backend directory)
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


def get_postgres_container_name():
    """Get PostgreSQL container name from environment or use default"""
    return os.getenv("POSTGRES_CONTAINER_NAME", "monitorix_db")


def get_database_credentials():
    """Extract database credentials from DATABASE_URL"""
    db_url = settings.database_url
    # Parse postgresql://user:password@host:port/dbname
    if db_url.startswith("postgresql://"):
        parts = db_url.replace("postgresql://", "").split("@")
        if len(parts) == 2:
            user_pass = parts[0].split(":")
            host_db = parts[1].split("/")
            if len(user_pass) == 2 and len(host_db) == 2:
                host_port = host_db[0].split(":")
                return {
                    "user": user_pass[0],
                    "password": user_pass[1],
                    "host": host_port[0],
                    "port": host_port[1] if len(host_port) > 1 else "5432",
                    "database": host_db[1]
                }
    # Fallback to environment variables
    return {
        "user": os.getenv("POSTGRES_USER", "monitorix"),
        "password": os.getenv("POSTGRES_PASSWORD", "changeme"),
        "host": os.getenv("POSTGRES_HOST", "postgres"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "database": os.getenv("POSTGRES_DB", "monitorix")
    }


@router.post("/create")
async def create_backup(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create a database backup (admin only)"""
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.sql"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Try to use docker exec first (if running in Docker)
        container_name = get_postgres_container_name()
        creds = get_database_credentials()
        
        # Check if we're in Docker environment
        docker_exec_cmd = [
            "docker", "exec", container_name,
            "pg_dump",
            "-U", creds["user"],
            "-d", creds["database"],
            "--clean",
            "--if-exists"
        ]
        
        try:
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = creds["password"]
            
            result = subprocess.run(
                docker_exec_cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                with open(backup_path, "w") as f:
                    f.write(result.stdout)
                logger.info(f"Backup created successfully: {backup_filename}")
                return {
                    "success": True,
                    "filename": backup_filename,
                    "path": backup_path,
                    "size": os.path.getsize(backup_path),
                    "created_at": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"pg_dump failed: {result.stderr}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Backup failed: {result.stderr}"
                )
        except FileNotFoundError:
            # Docker not available, try direct connection
            logger.info("Docker not available, trying direct connection")
            pg_dump_cmd = [
                "pg_dump",
                "-h", creds["host"],
                "-p", creds["port"],
                "-U", creds["user"],
                "-d", creds["database"],
                "--clean",
                "--if-exists"
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = creds["password"]
            
            result = subprocess.run(
                pg_dump_cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=300
            )
            
            if result.returncode == 0:
                with open(backup_path, "w") as f:
                    f.write(result.stdout)
                logger.info(f"Backup created successfully: {backup_filename}")
                return {
                    "success": True,
                    "filename": backup_filename,
                    "path": backup_path,
                    "size": os.path.getsize(backup_path),
                    "created_at": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"pg_dump failed: {result.stderr}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Backup failed: {result.stderr}"
                )
                
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backup operation timed out"
        )
    except Exception as e:
        logger.error(f"Backup creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        )


@router.get("/list")
async def list_backups(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """List all available backups (admin only)"""
    try:
        backups = []
        if os.path.exists(BACKUP_DIR):
            for filename in os.listdir(BACKUP_DIR):
                if filename.endswith(".sql"):
                    filepath = os.path.join(BACKUP_DIR, filename)
                    stat = os.stat(filepath)
                    backups.append({
                        "filename": filename,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.get("/download/{filename}")
async def download_backup(
    filename: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Download a backup file (admin only)"""
    try:
        # Security: prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup file not found"
            )
        
        return FileResponse(
            filepath,
            media_type="application/sql",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download backup: {str(e)}"
        )


@router.post("/restore/{filename}")
async def restore_backup(
    filename: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Restore database from backup (admin only)"""
    try:
        # Security: prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup file not found"
            )
        
        container_name = get_postgres_container_name()
        creds = get_database_credentials()
        
        # Read backup file
        with open(filepath, "r") as f:
            backup_content = f.read()
        
        # Try docker exec first
        try:
            docker_exec_cmd = [
                "docker", "exec", "-i", container_name,
                "psql",
                "-U", creds["user"],
                "-d", creds["database"]
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = creds["password"]
            
            result = subprocess.run(
                docker_exec_cmd,
                input=backup_content,
                capture_output=True,
                text=True,
                env=env,
                timeout=600  # 10 minute timeout for restore
            )
            
            if result.returncode == 0:
                logger.info(f"Database restored successfully from {filename}")
                return {
                    "success": True,
                    "message": f"Database restored from {filename}",
                    "restored_at": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"Restore failed: {result.stderr}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Restore failed: {result.stderr}"
                )
        except FileNotFoundError:
            # Docker not available, try direct connection
            psql_cmd = [
                "psql",
                "-h", creds["host"],
                "-p", creds["port"],
                "-U", creds["user"],
                "-d", creds["database"]
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = creds["password"]
            
            result = subprocess.run(
                psql_cmd,
                input=backup_content,
                capture_output=True,
                text=True,
                env=env,
                timeout=600
            )
            
            if result.returncode == 0:
                logger.info(f"Database restored successfully from {filename}")
                return {
                    "success": True,
                    "message": f"Database restored from {filename}",
                    "restored_at": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"Restore failed: {result.stderr}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Restore failed: {result.stderr}"
                )
                
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Restore operation timed out"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore backup: {str(e)}"
        )


@router.delete("/{filename}")
async def delete_backup(
    filename: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Delete a backup file (admin only)"""
    try:
        # Security: prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup file not found"
            )
        
        os.remove(filepath)
        logger.info(f"Backup deleted: {filename}")
        return {
            "success": True,
            "message": f"Backup {filename} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backup: {str(e)}"
        )

