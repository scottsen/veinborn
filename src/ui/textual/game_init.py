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

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,  # INFO for normal, DEBUG for development
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'veinborn.log'),
            logging.StreamHandler()  # Also print to console
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("Veinborn logging initialized")
    logger.info(f"Log file: {log_dir / 'veinborn.log'}")
