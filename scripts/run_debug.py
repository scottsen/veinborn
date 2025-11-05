#!/usr/bin/env python3
"""
Debug runner for Brogue with comprehensive logging.
Logs to brogue_debug.log in current directory.
"""
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Setup logging FIRST
log_file = Path(__file__).parent / "brogue_debug.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler(sys.stderr)  # Also print to stderr
    ]
)
logger = logging.getLogger('brogue')

logger.info("="*60)
logger.info("BROGUE DEBUG SESSION STARTING")
logger.info(f"Time: {datetime.now()}")
logger.info(f"Python: {sys.version}")
logger.info(f"CWD: {os.getcwd()}")
logger.info(f"Log file: {log_file}")
logger.info("="*60)

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
logger.info(f"Added to path: {src_path}")

try:
    logger.info("Importing Textual...")
    import textual
    logger.info(f"✓ Textual version: {textual.__version__}")

    logger.info("Importing core.game...")
    from core.game import Game
    logger.info("✓ core.game imported")

    logger.info("Importing ui.textual.app...")
    from ui.textual.app import BrogueApp
    logger.info("✓ ui.textual.app imported")

    logger.info("Checking terminal...")
    if not sys.stdout.isatty():
        logger.error("ERROR: Not running in a terminal (no TTY)")
        print("ERROR: Not running in a terminal", file=sys.stderr)
        sys.exit(1)
    logger.info("✓ Running in TTY")

    # Check terminal size
    try:
        import shutil
        size = shutil.get_terminal_size()
        logger.info(f"Terminal size: {size.columns}x{size.lines}")
        if size.columns < 80 or size.lines < 24:
            logger.warning(f"Terminal too small! Need 80x24, got {size.columns}x{size.lines}")
    except Exception as e:
        logger.error(f"Could not get terminal size: {e}")

    logger.info("Creating BrogueApp instance...")
    app = BrogueApp()
    logger.info("✓ BrogueApp created")

    logger.info(f"App config: mouse={app.ENABLE_MOUSE}, title={app.TITLE}")

    logger.info("Starting app.run()...")
    app.run()
    logger.info("✓ app.run() completed normally")

except KeyboardInterrupt:
    logger.info("Interrupted by user (Ctrl+C)")
    print("\n\nInterrupted by user", file=sys.stderr)
except Exception as e:
    logger.exception("FATAL ERROR:")
    print(f"\n\nFATAL ERROR: {e}", file=sys.stderr)
    print(f"See log: {log_file}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    logger.info("Cleaning up...")
    # Ensure terminal is reset
    try:
        sys.stdout.write('\033[?1000l')  # Disable mouse tracking
        sys.stdout.write('\033[?25h')    # Show cursor
        sys.stdout.write('\033[?47l')    # Exit alternate screen
        sys.stdout.flush()
        os.system('stty sane 2>/dev/null')
        logger.info("✓ Terminal reset complete")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

    logger.info("="*60)
    logger.info("BROGUE DEBUG SESSION ENDED")
    logger.info("="*60)
    print(f"\n\nDebug log saved to: {log_file}", file=sys.stderr)
