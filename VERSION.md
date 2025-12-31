# Version History

## Current Version: 1.1.0

### What's New in 1.1.0

- 🌍 **Multi-language Support**: Full internationalization with 7 languages
- 🚀 **Improved Deployment**: Local setup script and enhanced remote deployment
- 📚 **Better Documentation**: All docs in English, new quick start guide
- ✅ **Prerequisites Checking**: Automatic detection and installation of missing packages

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

3. **No database migrations needed** - schema is compatible

## Version 1.0.0

Initial release with core functionality.

---

See [CHANGELOG.md](CHANGELOG.md) for detailed change history.

