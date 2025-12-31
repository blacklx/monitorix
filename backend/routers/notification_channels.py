from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import NotificationChannel
from schemas import NotificationChannelCreate, NotificationChannelUpdate, NotificationChannelResponse
from auth import get_current_active_user
from notification_channels import send_slack_notification, send_discord_notification
from rate_limiter import limiter

router = APIRouter(prefix="/api/notification-channels", tags=["notification-channels"])


@router.get("", response_model=List[NotificationChannelResponse])
async def get_notification_channels(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all notification channels"""
    channels = db.query(NotificationChannel).all()
    return channels


@router.post("", response_model=NotificationChannelResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_notification_channel(
    request: Request,
    channel_data: NotificationChannelCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new notification channel"""
    # Validate channel type
    if channel_data.type not in ["slack", "discord"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Channel type must be 'slack' or 'discord'"
        )
    
    # Validate webhook URL
    if not channel_data.webhook_url.startswith("https://"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook URL must use HTTPS"
        )
    
    channel = NotificationChannel(**channel_data.dict())
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@router.get("/{channel_id}", response_model=NotificationChannelResponse)
async def get_notification_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a specific notification channel"""
    channel = db.query(NotificationChannel).filter(NotificationChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification channel not found"
        )
    return channel


@router.put("/{channel_id}", response_model=NotificationChannelResponse)
async def update_notification_channel(
    channel_id: int,
    channel_data: NotificationChannelUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update a notification channel"""
    channel = db.query(NotificationChannel).filter(NotificationChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification channel not found"
        )
    
    update_data = channel_data.dict(exclude_unset=True)
    
    # Validate webhook URL if provided
    if "webhook_url" in update_data:
        if not update_data["webhook_url"].startswith("https://"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook URL must use HTTPS"
            )
    
    for field, value in update_data.items():
        setattr(channel, field, value)
    
    db.commit()
    db.refresh(channel)
    return channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete a notification channel"""
    channel = db.query(NotificationChannel).filter(NotificationChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification channel not found"
        )
    db.delete(channel)
    db.commit()


@router.post("/{channel_id}/test")
async def test_notification_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Test a notification channel"""
    channel = db.query(NotificationChannel).filter(NotificationChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification channel not found"
        )
    
    # Send test notification
    if channel.type == "slack":
        success = await send_slack_notification(
            channel=channel,
            alert_type="test",
            severity="info",
            title="Test Notification",
            message="This is a test notification from Monitorix",
            node_name="Test Node"
        )
    elif channel.type == "discord":
        success = await send_discord_notification(
            channel=channel,
            alert_type="test",
            severity="info",
            title="Test Notification",
            message="This is a test notification from Monitorix",
            node_name="Test Node"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown channel type"
        )
    
    if success:
        return {"message": "Test notification sent successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )

