# Troubleshooting Guide

This guide helps you diagnose and fix common issues with Monitorix.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Connection Issues](#connection-issues)
- [Performance Issues](#performance-issues)
- [Alert Issues](#alert-issues)
- [Database Issues](#database-issues)
- [WebSocket Issues](#websocket-issues)
- [Authentication Issues](#authentication-issues)

## Installation Issues

### Docker Compose fails to start

**Symptoms**: Containers fail to start or exit immediately.

**Solutions**:
1. Check Docker and Docker Compose versions:
   ```bash
   docker --version
   docker-compose --version
   ```

2. Check logs:
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   docker-compose logs postgres
   ```

3. Verify `.env` file exists and has correct values:
   ```bash
   cat backend/.env
   ```

4. Check port conflicts:
   ```bash
   # Check if ports are in use
   netstat -tuln | grep 8000
   netstat -tuln | grep 5432
   ```

5. Try rebuilding containers:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Database migration fails

**Symptoms**: Backend fails to start with migration errors.

**Solutions**:
1. Check database connection:
   ```bash
   psql -h localhost -U monitorix -d monitorix
   ```

2. Verify database exists:
   ```bash
   psql -h localhost -U postgres -l | grep monitorix
   ```

3. Manually run migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```

4. If migrations are corrupted, reset (WARNING: data loss):
   ```bash
   cd backend
   alembic downgrade base
   alembic upgrade head
   ```

## Connection Issues

### Cannot connect to Proxmox API

**Symptoms**: Nodes show as "offline" or "error".

**Solutions**:
1. Verify Proxmox API token:
   - Check token is valid in Proxmox web interface
   - Ensure token has not expired
   - Verify token has required permissions

2. Test connectivity:
   ```bash
   curl -k -H "Authorization: PVEAuthCookie=TOKEN=YOUR_TOKEN" https://proxmox.example.com:8006/api2/json/version
   ```

3. Check SSL certificate:
   - If using self-signed certificate, set `PROXMOX_VERIFY_SSL=false` in `.env`
   - Or provide CA bundle: `PROXMOX_CA_BUNDLE=/path/to/ca-bundle.crt`

4. Verify network connectivity:
   ```bash
   ping proxmox.example.com
   telnet proxmox.example.com 8006
   ```

5. Check firewall rules:
   - Ensure port 8006 (Proxmox API) is accessible
   - Check both server and Proxmox firewall rules

### Frontend cannot connect to backend

**Symptoms**: Frontend shows "Connection failed" or API errors.

**Solutions**:
1. Verify backend is running:
   ```bash
   curl http://localhost:8000/api/version
   ```

2. Check CORS configuration:
   - Verify `CORS_ORIGINS` in `.env` includes frontend URL
   - Check backend logs for CORS errors

3. Verify API URL in frontend:
   - Check `VITE_API_URL` in `frontend/.env`
   - Ensure URL matches backend address

4. Check network connectivity:
   ```bash
   curl http://localhost:8000/health
   ```

## Performance Issues

### Slow page loads

**Symptoms**: Pages take a long time to load.

**Solutions**:
1. Enable Redis caching:
   ```env
   REDIS_ENABLED=true
   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_PASSWORD=your-password
   ```

2. Check database performance:
   ```sql
   -- Check slow queries
   SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
   ```

3. Optimize database indexes:
   ```bash
   cd backend
   alembic upgrade head  # Ensures all indexes are created
   ```

4. Reduce check intervals for less critical resources

5. Enable metrics aggregation (automatic for periods > 24 hours)

### High memory usage

**Symptoms**: Backend uses excessive memory.

**Solutions**:
1. Check system metrics in Dashboard
2. Review metrics retention policy
3. Enable metrics cleanup:
   ```env
   METRICS_RETENTION_DAYS=30
   ```

4. Reduce number of concurrent checks
5. Increase server RAM or add swap space

### Database growing too large

**Symptoms**: Database size increases rapidly.

**Solutions**:
1. Configure metrics retention:
   ```env
   METRICS_RETENTION_DAYS=30
   ```

2. Clean up old metrics manually:
   ```sql
   DELETE FROM metrics WHERE recorded_at < NOW() - INTERVAL '30 days';
   ```

3. Vacuum database:
   ```sql
   VACUUM ANALYZE;
   ```

## Alert Issues

### Alerts not being created

**Symptoms**: Alert rules configured but no alerts triggered.

**Solutions**:
1. Verify alert rules are active:
   - Check "Active" checkbox in Alert Rules page
   - Verify rule conditions match current metrics

2. Check alert rule cooldown:
   - Ensure cooldown period has passed
   - Check `last_triggered` timestamp

3. Verify metrics are being collected:
   - Check Metrics page for recent data
   - Verify nodes/VMs are online

4. Review scheduler logs:
   ```bash
   docker-compose logs backend | grep alert
   ```

### Notifications not being sent

**Symptoms**: Alerts created but no notifications received.

**Solutions**:
1. **Email notifications**:
   - Verify SMTP settings in `.env`
   - Test SMTP connection:
     ```bash
     telnet smtp.example.com 587
     ```
   - Check spam folder
   - Review backend logs for SMTP errors

2. **Slack notifications**:
   - Verify webhook URL is correct
   - Test webhook manually:
     ```bash
     curl -X POST -H 'Content-type: application/json' \
       --data '{"text":"Test"}' \
       YOUR_SLACK_WEBHOOK_URL
     ```
   - Check notification channel is active
   - Verify alert type and severity filters

3. **Discord notifications**:
   - Verify webhook URL is correct
   - Test webhook manually (similar to Slack)
   - Check notification channel configuration

4. **Webhooks**:
   - Verify webhook URL is accessible
   - Check webhook is active
   - Review backend logs for webhook errors

## Database Issues

### Database connection errors

**Symptoms**: Backend fails with "could not connect to database" errors.

**Solutions**:
1. Verify PostgreSQL is running:
   ```bash
   docker-compose ps postgres
   # or
   systemctl status postgresql
   ```

2. Check database credentials:
   ```bash
   psql -h localhost -U monitorix -d monitorix
   ```

3. Verify connection string in `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/monitorix
   ```

4. Check PostgreSQL logs:
   ```bash
   docker-compose logs postgres
   # or
   tail -f /var/log/postgresql/postgresql.log
   ```

### Database locks or deadlocks

**Symptoms**: Operations hang or fail with lock errors.

**Solutions**:
1. Check for long-running queries:
   ```sql
   SELECT pid, now() - pg_stat_activity.query_start AS duration, query
   FROM pg_stat_activity
   WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 minutes';
   ```

2. Kill blocking queries (if safe):
   ```sql
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE ...;
   ```

3. Restart database (if safe):
   ```bash
   docker-compose restart postgres
   ```

## WebSocket Issues

### WebSocket connection fails

**Symptoms**: Frontend shows "WebSocket disconnected" or no real-time updates.

**Solutions**:
1. Check WebSocket URL:
   - WebSocket URL is automatically constructed from the current page URL
   - For local development: Uses `ws://localhost:8000/ws`
   - For production (Nginx proxy): Uses relative path `ws://` or `wss://` based on page protocol
   - No manual configuration needed when using Nginx proxy

2. Check firewall rules:
   - Ensure port 8000 is open
   - Verify WebSocket upgrade is allowed

3. Check reverse proxy configuration:
   - Nginx: Ensure WebSocket upgrade headers
   - Traefik: Verify WebSocket support enabled

4. Review backend logs:
   ```bash
   docker-compose logs backend | grep websocket
   ```

5. Test WebSocket connection:
   ```bash
   wscat -c ws://localhost:8000/ws
   ```

### WebSocket reconnection loops

**Symptoms**: WebSocket constantly reconnecting.

**Solutions**:
1. Check backend health:
   ```bash
   curl http://localhost:8000/health
   ```

2. Verify backend is not overloaded
3. Check network stability
4. Review WebSocket heartbeat settings
5. Check browser console for errors
6. **If WebSocket disconnects when testing Proxmox connections**:
   - This was a known issue where connection tests blocked the event loop
   - Fixed in recent versions: Connection tests now run in thread pool with 10-second timeout
   - Ensure you're running the latest version
   - Check backend logs for any errors during connection tests
   - If issue persists, check if Proxmox node is reachable and responding

## Authentication Issues

### Cannot log in

**Symptoms**: Login fails with "Incorrect username or password".

**Solutions**:
1. Verify admin user was created:
   - Check backend logs during first startup
   - Admin password is generated and logged

2. Reset admin password (if needed):
   - Stop backend
   - Connect to database
   - Update password hash (use `get_password_hash` from backend)

3. Check token expiration:
   - Access tokens expire after 30 minutes
   - Refresh tokens expire after 7 days
   - Re-login if tokens expired

### 2FA not working

**Symptoms**: Cannot enable or verify 2FA.

**Solutions**:
1. Verify authenticator app time is synchronized
2. Check TOTP secret was saved correctly
3. Ensure 6-digit code is entered correctly
4. Try disabling and re-enabling 2FA
5. Review backend logs for 2FA errors

## Getting Help

If you cannot resolve an issue:

1. Check logs:
   ```bash
   docker-compose logs backend > backend.log
   docker-compose logs frontend > frontend.log
   ```

2. Collect system information:
   - Monitorix version
   - Operating system
   - Docker version (if applicable)
   - Database version

3. Open a GitHub issue with:
   - Description of the problem
   - Steps to reproduce
   - Logs (sanitized)
   - System information

