# Debug Instructions for Veinborn Display Issue

## Problem
App clears screen, shows nothing, can't quit.

## How to Debug

### Step 1: Run Debug Version

In a **separate terminal window** (NOT a split):

```bash
cd /home/scottsen/src/tia/projects/veinborn
python3 run_debug.py
```

### Step 2: What You'll See

The debug version logs everything to both:
- **stderr** (your screen)
- **veinborn_debug.log** (file)

You should see logging output on screen showing exactly what the app is doing.

### Step 3: Try to Quit

Try these keys:
- `q` - Should quit
- `Ctrl+C` - Force quit
- `Ctrl+\` - Hard kill

### Step 4: Check the Log

```bash
cat veinborn_debug.log
```

## What the Log Shows

The log will tell us:
- ✓ Did imports work?
- ✓ Did Game() initialize?
- ✓ Did widgets create?
- ✓ Did compose() complete?
- ✓ Did app.run() start?
- ✓ Did on_mount() get called?
- ✓ Did on_ready() get called?
- ❌ Where did it hang/fail?

## Common Issues to Look For

### 1. Terminal Size Too Small
Log will show: `Terminal size: WxH`
Need at least 80x24

### 2. Widget Creation Fails
Look for errors after "Creating MapWidget..." etc.

### 3. App Hangs Before on_ready()
Means Textual didn't finish initializing

### 4. No Errors But Blank Screen
Possible rendering issue with your terminal emulator

## Send Me the Log

After running:
```bash
# Show the full log
cat veinborn_debug.log

# Or just the key parts
grep -E "(ERROR|FATAL|starting|complete|called)" veinborn_debug.log
```

Copy and paste the output so I can see where it's failing.

## Emergency Terminal Reset

If terminal gets stuck:
```bash
bash fix_terminal.sh
# OR
reset
```

---

**The debug runner has full cleanup - it won't leave your terminal stuck!**
