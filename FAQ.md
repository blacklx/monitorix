# Frequently Asked Questions (FAQ)

## General

### What is Monitorix?

Monitorix is a comprehensive monitoring solution for Proxmox infrastructure. It provides real-time monitoring, alerting, and metrics collection for Proxmox nodes, VMs, and services.

### What are the system requirements?

- **Backend**: Python 3.11+, PostgreSQL 15+
- **Frontend**: Modern web browser (Chrome, Firefox, Safari, Edge)
- **Server**: Minimum 2GB RAM, 10GB disk space
- **Network**: Access to Proxmox API endpoints

### Is Monitorix free?

Yes, Monitorix is open-source and free to use under the Apache 2.0 license.

## Installation

### How do I install Monitorix?

See the [INSTALL.md](INSTALL.md) file for detailed installation instructions. Quick start:

```bash
git clone https://github.com/yourusername/monitorix.git
cd monitorix
./setup.sh
```

### Do I need Docker?

No, Docker is optional but recommended. You can also run Monitorix directly on a VM or server.

### Can I install Monitorix on Windows?

Yes, Monitorix can run on Windows using Docker or by installing Python and PostgreSQL directly.

## Configuration

### How do I add a Proxmox node?

1. Log in to Monitorix
2. Navigate to "Nodes" in the sidebar
3. Click "Add Node"
4. Enter node details (name, URL, username, token)
5. Click "Save"

### How do I get a Proxmox API token?

1. Log in to Proxmox web interface
2. Go to Datacenter → Permissions → API Tokens
3. Click "Add"
4. Create a token with appropriate permissions
5. Copy the token (you won't be able to see it again)

### What permissions does the Proxmox token need?

The token needs read permissions for:
- `/nodes` - To list and monitor nodes
- `/vms` - To list and monitor VMs
- `/status` - To check node and VM status

## Monitoring

### How often are nodes checked?

By default, nodes are checked every 1 minute. This can be configured in the scheduler settings.

### How are VMs discovered?

VMs are automatically discovered when a node is added. The system syncs VMs from Proxmox every 5 minutes.

### What metrics are collected?

- CPU usage (percentage)
- Memory usage (percentage and absolute)
- Disk usage (percentage and absolute)
- Network I/O (bytes sent/received)
- Uptime

### How long are metrics stored?

Metrics are stored indefinitely by default. You can configure retention policies to automatically delete old metrics.

## Alerts

### How do I configure alerts?

1. Navigate to "Alert Rules"
2. Click "Add Alert Rule"
3. Configure:
   - Name and description
   - Metric type (CPU, memory, disk)
   - Condition (>, <, >=, <=)
   - Threshold value
   - Severity (info, warning, critical)
4. Click "Save"

### What notification channels are supported?

- Email (SMTP)
- Slack
- Discord
- Webhooks

### How do I set up email notifications?

1. Configure SMTP settings in `.env`:
   ```
   SMTP_HOST=smtp.example.com
   SMTP_PORT=587
   SMTP_USER=your-email@example.com
   SMTP_PASSWORD=your-password
   SMTP_FROM=noreply@example.com
   ```
2. Restart the backend service

### How do I set up Slack notifications?

1. Navigate to "Notification Channels"
2. Click "Add Channel"
3. Select "Slack" as type
4. Enter your Slack webhook URL
5. Configure alert types and severity filters
6. Click "Save"

## Troubleshooting

### Nodes show as "offline" but they're actually online

1. Check Proxmox API token is valid
2. Verify network connectivity to Proxmox API
3. Check SSL certificate if using HTTPS
4. Review backend logs for errors

### VMs are not being discovered

1. Ensure the Proxmox token has read permissions for `/vms`
2. Check that VMs exist in Proxmox
3. Review scheduler logs for sync errors

### Alerts are not being sent

1. Verify notification channel configuration
2. Check email/Slack/Discord credentials
3. Review backend logs for notification errors
4. Ensure alert rules are active

### WebSocket connection fails

1. Check firewall rules (port 8000)
2. Verify WebSocket URL in frontend configuration
3. Check backend logs for WebSocket errors
4. Ensure reverse proxy (if used) supports WebSocket upgrades

## Security

### How secure is Monitorix?

Monitorix implements multiple security features:
- JWT authentication with refresh tokens
- Two-factor authentication (2FA)
- CSRF protection
- Security headers (CSP, HSTS, etc.)
- Input validation and sanitization
- Rate limiting
- Password policy enforcement

### Should I expose Monitorix to the internet?

It's recommended to use a reverse proxy (Nginx, Traefik) with SSL/TLS when exposing Monitorix to the internet. Never expose Monitorix directly without proper security measures.

### How do I enable 2FA?

1. Log in to Monitorix
2. Go to "Profile"
3. Click on "Two-Factor Authentication" tab
4. Click "Setup 2FA"
5. Scan QR code with authenticator app
6. Enter 6-digit code to enable

## Performance

### How many nodes/VMs can Monitorix handle?

Monitorix can handle hundreds of nodes and thousands of VMs, depending on:
- Server resources (CPU, RAM)
- Database performance
- Network latency to Proxmox API
- Check intervals

### How can I improve performance?

- Use Redis caching (enabled by default)
- Enable Celery for background jobs
- Optimize database indexes
- Reduce check intervals for less critical resources
- Use metrics aggregation for long time periods

## Backup and Restore

### How do I backup Monitorix?

1. Navigate to "Backup" (admin only)
2. Click "Create Backup"
3. Wait for backup to complete
4. Download backup file

### How do I restore from backup?

1. Navigate to "Backup"
2. Click "Upload Backup"
3. Select backup file
4. Click "Restore"
5. Confirm restore operation

**Warning**: Restoring a backup will overwrite all current data!

## Development

### How do I contribute?

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for development setup and contribution guidelines.

### How do I report bugs?

Open an issue on GitHub with:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Logs (if applicable)
- System information

### How do I request a feature?

Open an issue on GitHub with:
- Feature description
- Use case
- Proposed implementation (if applicable)

## License

### What license is Monitorix under?

Monitorix is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

### Can I use Monitorix commercially?

Yes, the Apache 2.0 license allows commercial use.

## Support

### Where can I get help?

- GitHub Issues: For bug reports and feature requests
- Documentation: See [README.md](README.md) and other `.md` files
- Developer Guide: See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

### Is there a community forum?

Currently, GitHub Issues is the primary support channel. Community forums may be added in the future.

