# Migration Guide: Brogue → Veinborn

**Version**: 0.4.0
**Date**: 2025-12-10
**Status**: Complete infrastructure and code transition

---

## Overview

The project has been renamed from "Brogue" to "Veinborn" to better reflect the game's core concept of "veins of knowledge" and memory-driven gameplay. This guide helps existing users migrate smoothly.

## What Changed

### ✅ Automatically Handled (Backward Compatible)

These changes include backward compatibility with deprecation warnings:

1. **Package Name**: Now `pip install veinborn` (was `brogue`)
2. **Command Name**: Now `veinborn` (was `brogue`)
3. **Server Class**: `VeinbornServer` (was `BrogueServer` - deprecated alias available)
4. **Environment Variables**: `VEINBORN_*` (was `BROGUE_*` - old names still work with warnings)
5. **Config Files**: `~/.veinbornrc` (was `~/.broguerc` - old file still loaded with warning)

### 📦 Repository & URLs

- **GitHub**: `https://github.com/scottsen/veinborn` (was `/brogue` - automatic redirect in place)
- **PyPI**: `veinborn` (new package name)

---

## Migration Steps

### For End Users

#### 1. Update Installation

```bash
# Uninstall old version (optional)
pip uninstall brogue

# Install new version
pip install veinborn

# Or upgrade if already using veinborn name
pip install --upgrade veinborn
```

#### 2. Update Command Usage

```bash
# Old
brogue

# New
veinborn
```

#### 3. Migrate Config File (Optional but Recommended)

```bash
# If you have ~/.broguerc, rename it
mv ~/.broguerc ~/.veinbornrc

# Or for XDG-style config
mv ~/.config/brogue/ ~/.config/veinborn/
```

**Note**: The old config file will still be loaded automatically, but you'll see a deprecation warning.

#### 4. Update Environment Variables (Optional but Recommended)

If you use environment variables, update their names:

| Old (Deprecated) | New (Preferred) |
|------------------|-----------------|
| `BROGUE_HOST` | `VEINBORN_HOST` |
| `BROGUE_PORT` | `VEINBORN_PORT` |
| `BROGUE_MAX_CONNECTIONS` | `VEINBORN_MAX_CONNECTIONS` |
| `BROGUE_LOG_LEVEL` | `VEINBORN_LOG_LEVEL` |
| `BROGUE_PLAYER_NAME` | `VEINBORN_PLAYER_NAME` |
| `BROGUE_PLAYER_DEFAULT_CLASS` | `VEINBORN_PLAYER_DEFAULT_CLASS` |

**Note**: Old environment variables still work but emit deprecation warnings.

---

### For Developers

#### 1. Update Git Remote

If you have a local clone:

```bash
cd /path/to/your/brogue/checkout
git remote set-url origin git@github.com:scottsen/veinborn.git
```

**Note**: GitHub automatically redirects the old URL, but updating is recommended.

#### 2. Update Code References

```python
# Old (deprecated)
from server.websocket_server import BrogueServer
server = BrogueServer()

# New (preferred)
from server.websocket_server import VeinbornServer
server = VeinbornServer()
```

**Note**: `BrogueServer` is available as a deprecated alias that emits warnings.

#### 3. Update Environment Variable Handling

```python
# Old
host = os.getenv("BROGUE_HOST", "0.0.0.0")

# New (with backward compatibility built-in)
from server.config import config
host = config.host  # Checks VEINBORN_HOST, then BROGUE_HOST (deprecated), then default
```

#### 4. Update Config File Paths in Documentation/Scripts

```python
# Old
config_path = Path.home() / ".broguerc"

# New
config_path = Path.home() / ".veinbornrc"
```

**Note**: The config system automatically checks both paths (new first, then old with warning).

---

## Deprecation Timeline

| Feature | Status | Removal Version |
|---------|--------|-----------------|
| `BrogueServer` class alias | Deprecated in v0.4.0 | v0.5.0 |
| `BROGUE_*` environment variables | Deprecated in v0.4.0 | v0.5.0 |
| `~/.broguerc` config file | Deprecated in v0.4.0 | v0.5.0 |
| GitHub redirect `/brogue` → `/veinborn` | Permanent | N/A (GitHub feature) |

---

## Frequently Asked Questions

### Q: Will my old config file still work?

**A**: Yes! The system automatically loads `~/.broguerc` if `~/.veinbornrc` doesn't exist. You'll see a deprecation warning encouraging you to rename it.

### Q: Do I need to update my environment variables immediately?

**A**: No. Old environment variables (e.g., `BROGUE_HOST`) continue to work in v0.4.0, with deprecation warnings. They'll be removed in v0.5.0.

### Q: What happens to the old GitHub repository?

**A**: It's been renamed to `veinborn`. GitHub automatically redirects all old URLs, so existing clones, links, and bookmarks continue to work.

### Q: Will the old PyPI package (`brogue`) be updated?

**A**: No. The `brogue` package name is retired. Future updates will only be published to `veinborn`.

### Q: I'm getting deprecation warnings. How do I silence them?

**A**: Instead of silencing them, migrate to the new names. The warnings help you identify what needs updating. After migration, warnings will disappear.

### Q: What if I find a reference to "Brogue" that wasn't updated?

**A**: Please report it as an issue on GitHub: https://github.com/scottsen/veinborn/issues

---

## Testing Your Migration

After migrating, verify everything works:

```bash
# 1. Check installation
veinborn --version

# 2. Verify config loads without warnings
veinborn --create-config  # Creates ~/.veinbornrc
veinborn  # Should launch without deprecation warnings

# 3. Test server (if using multiplayer)
python src/server/run_server.py
# Check logs for any deprecation warnings
```

---

## Support

- **Issues**: https://github.com/scottsen/veinborn/issues
- **Documentation**: See README.md and docs/ directory
- **Changelog**: See CHANGELOG.md for full version history

---

## Summary

**Recommended Actions:**
1. ✅ Reinstall: `pip install veinborn`
2. ✅ Rename config: `mv ~/.broguerc ~/.veinbornrc`
3. ✅ Update env vars: `BROGUE_*` → `VEINBORN_*`
4. ✅ Update code: `BrogueServer` → `VeinbornServer`

**Timeline:**
- v0.4.0 (now): Backward compatibility with deprecation warnings
- v0.5.0 (future): Deprecated features removed

**Need Help?** Open an issue on GitHub!
