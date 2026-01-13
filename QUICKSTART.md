# Veinborn Quickstart

Get playing in 5 minutes!

---

## 🎮 1. Install (1 minute)

### From PyPI (Recommended)
```bash
pip install veinborn
```

### From Source
```bash
git clone https://github.com/scottsen/veinborn
cd veinborn
pip install -e .
```

---

## 🚀 2. Run (30 seconds)

```bash
# If installed from PyPI
veinborn

# Or from source
python3 run_textual.py
```

---

## 🎯 3. Play (3 minutes)

### Essential Controls
- **Move:** Arrow keys or `hjkl` (vim-style)
- **Attack:** Bump into monsters
- **Mine:** `m` when standing on ore vein
- **Craft:** `c` when standing at forge (yellow █)
- **Descend:** `>` when standing on stairs down

### Quick Tips
1. **Start mining early** - Ore veins (shaded tiles) provide materials
2. **Find forges** - Yellow █ symbols on the map
3. **Craft weapons** - Better gear = easier combat
4. **Legacy Vault** - When you die, rare ore is saved for next run
5. **Experiment** - Try all 4 character classes (Warrior, Mage, Rogue, Healer)

---

## 📖 4. Learn More (optional)

### For Players
- **[HOW_TO_PLAY.md](HOW_TO_PLAY.md)** - Complete gameplay guide
- **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Full keybind reference
- **[docs/MECHANICS_REFERENCE.md](docs/MECHANICS_REFERENCE.md)** - Game mechanics

### For Modders
- **[docs/LUA_API.md](docs/LUA_API.md)** - Lua modding API
- **[docs/LUA_EVENT_MODDING_GUIDE.md](docs/LUA_EVENT_MODDING_GUIDE.md)** - Event system modding
- **[docs/CONTENT_CREATION.md](docs/CONTENT_CREATION.md)** - Add monsters/items

### For Developers
- **[docs/START_HERE.md](docs/START_HERE.md)** - Developer onboarding
- **[docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)** - What's implemented
- **[docs/architecture/](docs/architecture/)** - Technical architecture

---

## 🔧 5. Develop (optional)

```bash
# Clone repository
git clone https://github.com/scottsen/veinborn
cd veinborn

# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Run with debug logging
python scripts/run_debug.py
```

**Developer documentation:** [docs/START_HERE.md](docs/START_HERE.md)

---

## ❓ Troubleshooting

### "Command not found: veinborn"
- Try: `python3 -m veinborn` or `python3 run_textual.py`
- Check: `pip list | grep veinborn`

### "No module named [package]"
Make sure you installed with dependencies:
```bash
pip install -e .  # Installs all required packages
```

### Game crashes or bugs
- Check [docs/development/DEBUG_INSTRUCTIONS.md](docs/development/DEBUG_INSTRUCTIONS.md)
- Report issues: https://github.com/scottsen/veinborn/issues

---

## 🎉 That's It!

You're ready to play Veinborn. Have fun exploring the dungeons!

**Tips for your first run:**
1. Choose **Warrior** for easiest start
2. Mine every ore vein you see
3. Craft weapons as soon as you find a forge
4. Don't worry about dying - your rare ore is saved!

**Full documentation:** [docs/INDEX.md](docs/INDEX.md)
