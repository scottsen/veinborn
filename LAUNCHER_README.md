# Brogue Launcher

**NEW:** You can now run Brogue with a simple `./brogue` command!

---

## Quick Start

```bash
# Run the game
./brogue

# With options
./brogue --debug    # Debug logging
./brogue --safe     # Terminal reset on crash
./brogue --help     # Show help
```

---

## Installation (Optional)

Install the `brogue` command system-wide:

```bash
./install.sh
```

This creates a symlink in `~/.local/bin/` so you can run `brogue` from anywhere.

**Note:** Make sure `~/.local/bin` is in your PATH. If not, add to `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## What It Does

The `brogue` script is a simple wrapper that:

1. ✅ Checks for Python 3
2. ✅ Auto-installs dependencies if missing
3. ✅ Runs the appropriate launcher based on options
4. ✅ Handles terminal cleanup on errors
5. ✅ Shows helpful error messages

---

## Options

```
./brogue              Normal mode
./brogue --debug      Debug mode (full logging to logs/)
./brogue --safe       Safe mode (resets terminal on crash)
./brogue --help       Show help message
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
- Or use `./brogue --safe` next time

---

## Files

- `brogue` - Main launcher script
- `install.sh` - Optional system-wide installer
- `run_textual.py` - Original launcher (still works)
- `scripts/run_debug.py` - Debug mode
- `scripts/run_safe.py` - Safe mode

---

**Happy dungeon delving!** 🎮
