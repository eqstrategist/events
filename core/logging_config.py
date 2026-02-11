import logging
import logging.handlers
import os

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Rotation: 5 MB per file, keep 10 backups (~50 MB total history)
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 10

_initialized = False

def setup_logging():
    """Setup application logging with rotation. Safe to call multiple times."""
    global _initialized
    if _initialized:
        return logging.getLogger("events")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    logger = logging.getLogger("events")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT
        )
        fh.setFormatter(formatter)
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(sh)
    _initialized = True
    return logger
