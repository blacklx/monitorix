# Version History

## Current Version: 1.2.0

### What's New in 1.2.0

- 🎯 **Project Rebranding**: Renamed to Monitorix
- 📊 **VM Details Modal**: Full detail view with metrics charts and uptime statistics
- 📥 **Metrics Export**: CSV and JSON export functionality
- ⚡ **Performance Improvements**: Database indexes for better query performance
- 🔧 **Maintenance Mode UI**: Toggle buttons in Nodes and Services pages
- 🔌 **WebSocket Status Indicator**: Real-time connection status in navigation
- 📈 **Improved Uptime Calculation**: More accurate tracking using metrics data
- 🚨 **Enhanced Alerts**: Bulk resolve, delete, enhanced filtering

### Upgrade from 1.1.0

If you're upgrading from 1.1.0:

1. **Pull latest code:**
   ```bash
   git pull
   ```

2. **Run database migrations** (new indexes):
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

3. **Rebuild containers** (optional, for latest changes):
   ```bash
   docker-compose build
   docker-compose up -d
   ```

### Upgrade from 1.0.0

If you're upgrading from 1.0.0:

1. **Pull latest code:**
   ```bash
   git pull
   ```

2. **Rebuild frontend** (for i18n support):
   ```bash
   docker-compose build frontend
   docker-compose up -d frontend
   ```

3. **Run database migrations**:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

## Version 1.1.0

### What's New in 1.1.0

- 🌍 **Multi-language Support**: Full internationalization with 7 languages
- 🚀 **Improved Deployment**: Local setup script and enhanced remote deployment
- 📚 **Better Documentation**: All docs in English, new quick start guide
- ✅ **Prerequisites Checking**: Automatic detection and installation of missing packages

## Version 1.0.0

Initial release with core functionality.

---

See [CHANGELOG.md](CHANGELOG.md) for detailed change history.
