"""Logging utilities for the Risk Assessment module.

This module provides a single reusable function, :func:`get_logger`, that
configures and returns a :class:`logging.Logger` instance with both console
and file handlers. It is intended to be imported by any other module in the
``risk_assessment`` package (data loading, preprocessing, training,
evaluation, etc.) so that logging behavior is consistent across the
project.
"""

import logging
from pathlib import Path
from typing import Optional

DEFAULT_LOG_DIR = Path("risk_assessment/reports/logs")
DEFAULT_LOG_FILE = "risk_assessment.log"
DEFAULT_LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(
    name: str,
    log_dir: Optional[Path] = None,
    log_file: str = DEFAULT_LOG_FILE,
    level: int = logging.INFO,
) -> logging.Logger:
    """Create and return a configured, reusable logger.

    The returned logger writes messages to both the console (stdout) and a
    log file, using a consistent timestamped format. Calling this function
    multiple times with the same ``name`` will not attach duplicate
    handlers, so it is safe to call from any module.

    Args:
        name: Name of the logger, typically ``__name__`` of the calling
            module.
        log_dir: Directory in which the log file should be created. If
            ``None``, defaults to ``risk_assessment/reports/logs``.
        log_file: Name of the log file. Defaults to
            ``"risk_assessment.log"``.
        level: Logging level to apply to the logger and its handlers.
            Defaults to ``logging.INFO``.

    Returns:
        logging.Logger: A configured logger instance with console and file
        handlers attached.

    Raises:
        OSError: If the log directory cannot be created due to filesystem
            permission issues.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding duplicate handlers if the logger already exists.
    if logger.handlers:
        return logger

    logger.propagate = False

    formatter = logging.Formatter(fmt=DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    # Console handler.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler.
    try:
        target_dir = log_dir if log_dir is not None else DEFAULT_LOG_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        log_path = target_dir / log_file

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as error:
        logger.warning("Could not set up file logging: %s", error)

    return logger