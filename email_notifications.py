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

