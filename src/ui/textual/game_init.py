"""Game initialization utilities for Veinborn."""
import logging
from pathlib import Path


def setup_logging(log_dir: Path = None):
    """
    Configure logging for Veinborn MVP.

    Args:
        log_dir: Directory for log files. If None, uses ./logs relative to cwd
    """
    if log_dir is None:
        log_dir = Path.cwd() / "logs"

    # Create logs directory if it doesn't exist
    log_dir.mkdir(exist_ok=True)

    # INFO to a size-bounded file with extra= fields (core.logging_setup); no console in
    # normal mode (debug mode in scripts/run_debug.py still shows console output)
    from core.logging_setup import setup_logging as configure
    configure(log_dir / 'veinborn.log', logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info("Veinborn logging initialized")
    logger.info(f"Log file: {log_dir / 'veinborn.log'}")
