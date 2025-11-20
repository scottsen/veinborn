# Veinborn Launcher

**NEW:** You can now run Veinborn with a simple `./veinborn` command!

---

## Quick Start

```bash
# Run the game
./veinborn

# With options
./veinborn --debug    # Debug logging
./veinborn --safe     # Terminal reset on crash
./veinborn --help     # Show help
```

---

## Installation (Optional)

Install the `veinborn` command system-wide:

```bash
./install.sh
```

This creates a symlink in `~/.local/bin/` so you can run `veinborn` from anywhere.

**Note:** Make sure `~/.local/bin` is in your PATH. If not, add to `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## What It Does

The `veinborn` script is a simple wrapper that:

1. ✅ Checks for Python 3
2. ✅ Auto-installs dependencies if missing
3. ✅ Runs the appropriate launcher based on options
4. ✅ Handles terminal cleanup on errors
5. ✅ Shows helpful error messages

---

## Options

```
./veinborn              Normal mode
./veinborn --debug      Debug mode (full logging to logs/)
./veinborn --safe       Safe mode (resets terminal on crash)
./veinborn --help       Show help message
```

---

## Under the Hood

The launcher script:
- **Normal mode:** Runs `python3 run_textual.py`
- **Debug mode:** Runs `python3 scripts/run_debug.py`
- **Safe mode:** Runs `python3 scripts/run_safe.py`

You can still use the old commands directly if you prefer.

---

## Troubleshooting

**"python3: command not found"**
- Install Python 3.10 or higher

**"No module named 'textual'"**
- The launcher auto-installs dependencies
- Or manually: `pip install -r requirements.txt`

**Terminal is broken after crash**
- Type `reset` and press Enter
- Or use `./veinborn --safe` next time

---

## Files

- `veinborn` - Main launcher script
- `install.sh` - Optional system-wide installer
- `run_textual.py` - Original launcher (still works)
- `scripts/run_debug.py` - Debug mode
- `scripts/run_safe.py` - Safe mode

---

**Happy dungeon delving!** 🎮
