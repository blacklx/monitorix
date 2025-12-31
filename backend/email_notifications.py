"""
Email notification system
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from config import settings

logger = logging.getLogger(__name__)


def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """
    Send an email notification
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    if not settings.alert_email_enabled:
        logger.debug("Email notifications are disabled")
        return False
    
    if not all([
        settings.alert_email_smtp_host,
        settings.alert_email_smtp_user,
        settings.alert_email_smtp_password,
        settings.alert_email_from
    ]):
        logger.warning("Email configuration is incomplete")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.alert_email_from
        msg['To'] = to_email
        
        # Add plain text part
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        # Add HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(settings.alert_email_smtp_host, settings.alert_email_smtp_port) as server:
            if settings.alert_email_smtp_port == 587:
                server.starttls()
            server.login(settings.alert_email_smtp_user, settings.alert_email_smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_alert_notification(
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    node_name: Optional[str] = None,
    vm_name: Optional[str] = None,
    service_name: Optional[str] = None
) -> bool:
    """
    Send an alert notification email
    
    Args:
        alert_type: Type of alert (node_down, vm_down, service_down, high_usage)
        severity: Alert severity (info, warning, critical)
        title: Alert title
        message: Alert message
        node_name: Optional node name
        vm_name: Optional VM name
        service_name: Optional service name
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    if not settings.alert_email_to:
        logger.warning("No email recipient configured")
        return False
    
    # Build email subject
    subject = f"[{severity.upper()}] {title}"
    
    # Build email body
    body_lines = [
        f"Alert Type: {alert_type}",
        f"Severity: {severity}",
        f"Title: {title}",
        "",
        f"Message: {message}",
        ""
    ]
    
    if node_name:
        body_lines.append(f"Node: {node_name}")
    if vm_name:
        body_lines.append(f"VM: {vm_name}")
    if service_name:
        body_lines.append(f"Service: {service_name}")
    
    body = "\n".join(body_lines)
    
    # Build HTML body
    html_body = f"""
    <html>
      <head></head>
      <body>
        <h2 style="color: {'red' if severity == 'critical' else 'orange' if severity == 'warning' else 'blue'}">
          {title}
        </h2>
        <p><strong>Alert Type:</strong> {alert_type}</p>
        <p><strong>Severity:</strong> {severity}</p>
        <p><strong>Message:</strong> {message}</p>
        {f'<p><strong>Node:</strong> {node_name}</p>' if node_name else ''}
        {f'<p><strong>VM:</strong> {vm_name}</p>' if vm_name else ''}
        {f'<p><strong>Service:</strong> {service_name}</p>' if service_name else ''}
      </body>
    </html>
    """
    
    return send_email(
        to_email=settings.alert_email_to,
        subject=subject,
        body=body,
        html_body=html_body
    )


def send_password_reset_email(
    to_email: str,
    reset_token: str,
    username: str
) -> bool:
    """
    Send password reset email with reset link
    
    Args:
        to_email: User's email address
        reset_token: Password reset token
        username: User's username
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    # Build reset URL
    reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
    
    # Build email subject
    subject = "Monitorix - Password Reset Request"
    
    # Build plain text body
    body = f"""
Hello {username},

You have requested to reset your password for Monitorix.

To reset your password, click on the following link (valid for 1 hour):
{reset_url}

If you did not request this password reset, please ignore this email.

This link will expire in 1 hour for security reasons.

Best regards,
Monitorix Team
"""
    
    # Build HTML body
    html_body = f"""
    <html>
      <head></head>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #2c3e50;">Password Reset Request</h2>
          <p>Hello {username},</p>
          <p>You have requested to reset your password for Monitorix.</p>
          <p>To reset your password, click on the following button:</p>
          <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" 
               style="background-color: #3498db; color: white; padding: 12px 30px; 
                      text-decoration: none; border-radius: 5px; display: inline-block;">
              Reset Password
            </a>
          </div>
          <p>Or copy and paste this link into your browser:</p>
          <p style="word-break: break-all; color: #7f8c8d; font-size: 12px;">
            {reset_url}
          </p>
          <p style="color: #e74c3c; font-size: 14px;">
            <strong>⚠️ This link will expire in 1 hour for security reasons.</strong>
          </p>
          <p>If you did not request this password reset, please ignore this email.</p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
          <p style="color: #95a5a6; font-size: 12px;">
            Best regards,<br>
            Monitorix Team
          </p>
        </div>
      </body>
    </html>
    """
    
    return send_email(
        to_email=to_email,
        subject=subject,
        body=body,
        html_body=html_body
    )
