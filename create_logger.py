import logging
import os
from typing import Optional

from config import Config

def _create_handler(handler_type: str, log_file: str) -> Optional[logging.Handler]:
    """Factory that returns a configured handler.

    Parameters
    ----------
    handler_type: str
        Either "console" or "file".
    log_file: str
        Path to the log file (only used for the file handler).
    """
    if handler_type == "console":
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        return console_handler
    elif handler_type == "file":
        # Ensure the directory for the log file exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        return file_handler
    return None


def setup_logger(name: str, log_file: str) -> logging.Logger:
    """Create (or retrieve) a logger with console and file handlers.

    The function guards against adding duplicate handlers when called
    multiple times. It returns a ready‑to‑use ``logging.Logger`` instance.

    Parameters
    ----------
    name: str
        Name of the logger.
    log_file: str
        Full path to the file where logs should be written.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Define a consistent log format
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Helper to check whether a handler of the same class is already attached
    def _has_handler_of_type(handler_cls):
        return any(isinstance(h, handler_cls) for h in logger.handlers)

    # Console handler (StreamHandler)
    if not _has_handler_of_type(logging.StreamHandler):
        console_handler = _create_handler("console", log_file)
        if console_handler:
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

    # File handler (FileHandler)
    if not _has_handler_of_type(logging.FileHandler):
        file_handler = _create_handler("file", log_file)
        if file_handler:
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

# Instantiate a logger for the project using the configuration defined in ``config.py``
logger = setup_logger("SmartVoage", Config().log_file)
