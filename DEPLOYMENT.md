# Deployment Guide

This guide covers deploying Monitorix in production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Production Deployment](#production-deployment)
- [Reverse Proxy Setup](#reverse-proxy-setup)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Backup Strategy](#backup-strategy)
- [Monitoring](#monitoring)
- [Scaling](#scaling)

## Prerequisites

- Server with Docker and Docker Compose installed
- Domain name (optional, for SSL)
- SMTP server (for email notifications)
- PostgreSQL 15+ (or use included Docker image)
- Minimum 2GB RAM, 10GB disk space

## Quick Start

### Using Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/yourusername/monitorix.git
cd monitorix
```

2. Run setup script:
```bash
./setup.sh
```

3. Access Monitorix:
- Frontend: `http://your-server-ip`
- API: `http://your-server-ip:8000`
- API Docs: `http://your-server-ip:8000/docs`

## Production Deployment

### Environment Variables

Create `.env` files with production values:

**backend/.env**:
```env
# Database
DATABASE_URL=postgresql://monitorix:secure-password@postgres:5432/monitorix

# Security
SECRET_KEY=your-very-secure-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=https://monitorix.example.com

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=secure-password
SMTP_FROM=noreply@example.com
SMTP_TLS=true

# Frontend URL
FRONTEND_URL=https://monitorix.example.com

# Environment
ENVIRONMENT=production
ENABLE_HSTS=true

# Redis (optional but recommended)
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secure-redis-password

# Celery (optional but recommended)
CELERY_ENABLED=true

# Sentry (optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

**frontend/.env**:
```env
VITE_API_URL=https://monitorix.example.com/api
VITE_WS_URL=wss://monitorix.example.com/ws
```

### Security Checklist

- [ ] Change all default passwords
- [ ] Use strong `SECRET_KEY`
- [ ] Enable SSL/TLS
- [ ] Configure firewall rules
- [ ] Set up regular backups
- [ ] Enable 2FA for admin users
- [ ] Review CORS settings
- [ ] Configure rate limiting
- [ ] Set up monitoring/alerting
- [ ] Review security headers

### Docker Compose Production

Update `docker-compose.yml` for production:

```yaml
services:
  backend:
    restart: always
    environment:
      - ENVIRONMENT=production
    # Add resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  frontend:
    restart: always
    # Add resource limits
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M

  postgres:
    restart: always
    # Add volume for data persistence
    volumes:
      - postgres_data:/var/lib/postgresql/data
    # Add resource limits
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

## Reverse Proxy Setup

### Nginx Configuration

```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:80;
}

server {
    listen 80;
    server_name monitorix.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name monitorix.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Prometheus metrics (optional, restrict access)
    location /api/prometheus/metrics {
        allow 10.0.0.0/8;  # Internal network
        deny all;
        proxy_pass http://backend;
    }
}
```

### Traefik Configuration

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./letsencrypt:/letsencrypt
    labels:
      - "traefik.enable=true"

  backend:
    # ... existing configuration
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`monitorix.example.com`)"
      - "traefik.http.routers.backend.entrypoints=websecure"
      - "traefik.http.routers.backend.tls.certresolver=letsencrypt"
      - "traefik.http.services.backend.loadbalancer.server.port=8000"

  frontend:
    # ... existing configuration
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`monitorix.example.com`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
      - "traefik.http.services.frontend.loadbalancer.server.port=80"
```

## SSL/TLS Configuration

### Let's Encrypt (Certbot)

1. Install Certbot:
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

2. Obtain certificate:
```bash
sudo certbot --nginx -d monitorix.example.com
```

3. Auto-renewal (cron job):
```bash
sudo certbot renew --dry-run
```

### Self-Signed Certificate (Development)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /path/to/key.pem \
  -out /path/to/cert.pem
```

## Backup Strategy

### Automated Backups

1. **Database Backups**:
   - Use Monitorix backup feature (UI)
   - Or schedule via cron:
     ```bash
     0 2 * * * docker exec monitorix_postgres pg_dump -U monitorix monitorix > /backups/monitorix_$(date +\%Y\%m\%d).sql
     ```

2. **File Backups**:
   - Backup `.env` files
   - Backup SSL certificates
   - Backup configuration files

3. **Backup Retention**:
   - Keep daily backups for 7 days
   - Keep weekly backups for 4 weeks
   - Keep monthly backups for 12 months

### Restore Procedure

1. Stop services:
```bash
docker-compose down
```

2. Restore database:
```bash
docker exec -i monitorix_postgres psql -U monitorix monitorix < backup.sql
```

3. Restore files:
```bash
cp -r backups/config/* .
```

4. Start services:
```bash
docker-compose up -d
```

## Monitoring

### System Monitoring

Monitorix includes built-in system metrics:
- CPU usage
- Memory usage
- Disk usage
- Network I/O

Access via Dashboard or `/api/system-metrics/current`

### Application Monitoring

- **Prometheus**: `/api/prometheus/metrics`
- **Health Check**: `/health`
- **Version Info**: `/api/version`

### External Monitoring

- Set up external monitoring (Nagios, Zabbix, etc.)
- Monitor Monitorix health endpoint
- Alert on downtime

## Scaling

### Horizontal Scaling

1. **Backend**:
   - Run multiple backend instances
   - Use load balancer
   - Shared database and Redis

2. **Database**:
   - Use PostgreSQL replication
   - Consider read replicas for reporting

3. **Cache**:
   - Use Redis cluster for high availability

### Vertical Scaling

- Increase server resources (CPU, RAM)
- Optimize database queries
- Enable caching
- Use SSD storage

## Maintenance

### Updates

1. Backup current installation
2. Pull latest changes:
   ```bash
   git pull origin main
   ```
3. Run migrations:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```
4. Restart services:
   ```bash
   docker-compose restart
   ```

### Log Rotation

Configure log rotation for Docker logs:

```bash
# /etc/logrotate.d/docker-containers
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=10M
    missingok
    delaycompress
    copytruncate
}
```

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

