# Security Guide

## Container Security

### Non-Root Execution

Monitorix containers are configured to run as non-root users for improved security:

- **Backend**: Runs as user `monitorix` (UID 1000)
- **Celery Worker**: Runs as user `monitorix` (UID 1000) with `--uid=1000 --gid=1000`
- **Frontend**: Runs as user `nginx` (standard nginx:alpine user)
- **PostgreSQL**: Runs as user `postgres` (standard postgres:alpine user)
- **Redis**: Runs as user `redis` (standard redis:alpine user)

### Volume Permissions

When using bind mounts in development, you may need to adjust file permissions:

```bash
# Set correct ownership for backend directory
sudo chown -R 1000:1000 ./backend

# Set correct ownership for backups directory
sudo chown -R 1000:1000 ./backend/backups
```

**Note**: In production, use named volumes instead of bind mounts for better security and isolation.

### Port Binding

- Backend binds to port 8000 (non-privileged port, no root required)
- Frontend binds to port 80 (nginx handles this internally)
- PostgreSQL binds to port 5432
- Redis binds to port 6379

### Security Best Practices

1. **Environment Variables**: Never commit `.env` files. They contain sensitive credentials.
2. **Secret Keys**: Use strong, randomly generated `SECRET_KEY` values.
3. **Database Passwords**: Use auto-generated passwords from setup scripts.
4. **Network Security**: Use firewall rules to restrict access to exposed ports.
5. **SSL/TLS**: Use a reverse proxy (e.g., Nginx Proxy Manager) with SSL certificates for production.
6. **Regular Updates**: Keep Docker images and dependencies updated.

### Celery Worker Security

The Celery worker runs with `--uid=1000 --gid=1000` to avoid running as root. This eliminates the security warning you may see in logs.

### File System Access

The application writes temporary files to `/tmp` which has proper permissions (1777) for all users. The admin password file (`/tmp/admin_password.txt`) is created with mode 0600 (read/write for owner only).

## Production Deployment

For production deployments:

1. Use named volumes instead of bind mounts
2. Configure proper firewall rules
3. Use SSL/TLS encryption
4. Disable public user registration (`ALLOW_REGISTRATION=false`)
5. Use strong passwords and secret keys
6. Regularly update dependencies
7. Monitor logs for security events
8. Use Docker secrets or external secret management for sensitive data

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:
- Do not open public issues for security vulnerabilities
- Contact the maintainers directly
- Provide detailed information about the vulnerability
- Allow time for a fix before public disclosure

