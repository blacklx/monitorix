# Upgrade Guide - Monitorix

This guide explains how to safely upgrade Monitorix without losing data or configuration.

## ⚠️ Important: Backup Before Upgrading

**Always create a backup before upgrading!**

```bash
# Create a backup using the built-in backup feature
# Or manually:
docker-compose exec backend python -c "from routers.backup import create_backup; create_backup()"

# Or using pg_dump directly:
docker-compose exec postgres pg_dump -U monitorix monitorix > backup_$(date +%Y%m%d_%H%M%S).sql
```

## 🔄 Upgrade Process

### Automatic Upgrade (Recommended)

We provide an upgrade script that handles the entire process safely:

```bash
# Make the script executable
chmod +x upgrade.sh

# Run the upgrade
./upgrade.sh
```

The script will:
1. ✅ Check current version
2. ✅ Create automatic backup
3. ✅ Pull latest code
4. ✅ Run database migrations
5. ✅ Rebuild containers
6. ✅ Restart services
7. ✅ Verify upgrade success

### Manual Upgrade

If you prefer to upgrade manually, follow these steps:

#### 1. Stop Services

```bash
docker-compose down
```

#### 2. Backup Database

```bash
# Create backup
docker-compose up -d postgres
docker-compose exec postgres pg_dump -U monitorix monitorix > backup_$(date +%Y%m%d_%H%M%S).sql
```

#### 3. Pull Latest Code

```bash
git pull origin main
# Or for a specific version:
git fetch --tags
git checkout v1.2.0  # Replace with desired version
```

#### 4. Run Database Migrations

```bash
# Start services
docker-compose up -d postgres backend

# Wait for services to be ready
sleep 10

# Run migrations (automatic on startup, but can be run manually)
docker-compose exec backend alembic upgrade head
```

#### 5. Rebuild and Restart

```bash
# Rebuild containers with new code
docker-compose build

# Start all services
docker-compose up -d

# Check logs to ensure everything started correctly
docker-compose logs -f
```

#### 6. Verify Upgrade

```bash
# Check version
curl http://localhost:8000/api/version

# Check health
curl http://localhost:8000/health

# Verify in UI - version should be displayed in footer
```

## 🔍 Version Checking

### Check Current Version

```bash
# Via API
curl http://localhost:8000/api/version

# Via UI
# Version is displayed in the footer of the web interface
```

### Check for Updates

The web UI automatically checks for updates on startup. You can also check manually:

```bash
# Via API (requires authentication)
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/version/check
```

## 🛡️ Data Safety

### What is Preserved During Upgrade

✅ **All data is preserved:**
- Database content (nodes, VMs, services, metrics, alerts)
- User accounts and settings
- Configuration files (`.env`)
- Docker volumes (database data)

### What Might Change

⚠️ **These may require attention:**
- Database schema (handled automatically by migrations)
- Environment variables (check `ENV_VARIABLES.md` for new variables)
- Frontend UI changes (may require browser refresh)

### Rollback Procedure

If something goes wrong, you can rollback:

```bash
# 1. Stop services
docker-compose down

# 2. Restore database backup
docker-compose up -d postgres
docker-compose exec postgres psql -U monitorix monitorix < backup_YYYYMMDD_HHMMSS.sql

# 3. Checkout previous version
git checkout v1.1.0  # Replace with previous version

# 4. Rebuild and restart
docker-compose build
docker-compose up -d
```

## 📋 Pre-Upgrade Checklist

- [ ] Backup database
- [ ] Check current version
- [ ] Review changelog for breaking changes
- [ ] Check for new environment variables
- [ ] Ensure sufficient disk space
- [ ] Plan maintenance window (if needed)

## 🚨 Troubleshooting

### Migration Fails

```bash
# Check migration status
docker-compose exec backend alembic current

# Check migration history
docker-compose exec backend alembic history

# If needed, manually run specific migration
docker-compose exec backend alembic upgrade <revision>
```

### Services Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Check container status
docker-compose ps

# Restart services
docker-compose restart
```

### Database Connection Issues

```bash
# Verify database is running
docker-compose ps postgres

# Check database connection
docker-compose exec backend python -c "from database import engine; engine.connect()"

# Verify environment variables
docker-compose exec backend env | grep DATABASE
```

## 📚 Version-Specific Upgrade Notes

### Upgrading to 1.2.0

- New features: Tags, Audit Logs, Export, Backup UI
- Database migrations: 009_add_tags, 008_add_audit_logs
- No breaking changes
- All data preserved

### Upgrading to 1.1.0

- New features: Multi-language support, improved deployment
- Database migrations: None
- No breaking changes

## 🔗 Related Documentation

- [INSTALL.md](INSTALL.md) - Initial installation
- [VERSION.md](VERSION.md) - Version history
- [CHANGELOG.md](CHANGELOG.md) - Detailed changes
- [ENV_VARIABLES.md](ENV_VARIABLES.md) - Environment variables

## 💡 Tips

1. **Test upgrades in a staging environment first** if possible
2. **Keep backups for at least 30 days** after upgrade
3. **Monitor logs** after upgrade for any issues
4. **Check the UI** to verify all features work correctly
5. **Review release notes** before upgrading

---

**Need help?** Open an issue on [GitHub](https://github.com/blacklx/monitorix/issues)

