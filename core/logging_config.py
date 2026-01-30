import logging
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logging():
    """Setup application logging."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def log_error(message, exc=None):
    """Log an error message."""
    logger = logging.getLogger(__name__)
    if exc:
        logger.error(f"{message}: {str(exc)}", exc_info=True)
    else:
        logger.error(message)

def log_info(message):
    """Log an info message."""
    logger = logging.getLogger(__name__)
    logger.info(message)

def log_warning(message):
    """Log a warning message."""
    logger = logging.getLogger(__name__)
    logger.warning(message)

# Initialize logging on import
setup_logging()
