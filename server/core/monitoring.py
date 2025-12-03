from __future__ import annotations
import logging
import traceback
import sys
import os
from typing import Any, Optional
from logging.handlers import RotatingFileHandler

# Create logs directory: server/logs
LOG_DIR = os.path.join(os.path.dirname(os.path. dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Log file paths
EVENT_LOG_FILE = os.path.join(LOG_DIR, "events. log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "errors.log")

# Formatter
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
formatter = logging. Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

# Event logger
event_logger = logging. getLogger("treeex. events")
event_logger.setLevel(logging.DEBUG)
event_logger.propagate = False

event_file_handler = RotatingFileHandler(
    EVENT_LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding="utf-8"
)
event_file_handler.setFormatter(formatter)
event_logger.addHandler(event_file_handler)

event_console_handler = logging. StreamHandler(sys. stdout)
event_console_handler.setFormatter(formatter)
event_logger.addHandler(event_console_handler)

# Error logger
error_logger = logging.getLogger("treeex.errors")
error_logger.setLevel(logging.ERROR)
error_logger. propagate = False

error_file_handler = RotatingFileHandler(
    ERROR_LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding="utf-8"
)
error_file_handler.setFormatter(formatter)
error_logger.addHandler(error_file_handler)

error_console_handler = logging.StreamHandler(sys.stderr)
error_console_handler. setFormatter(formatter)
error_logger. addHandler(error_console_handler)


def log_event(
    event: str,
    *,
    level: str = "info",
    **context: Any
) -> None:
    """
    Log an event to server/logs/events. log
    
    Args:
        event: Event name/description
        level: Log level (debug, info, warning, error)
        **context: Additional key-value pairs
    
    Example:
        log_event("user_login", user_id="123", workspace_id="abc")
    """
    log_func = getattr(event_logger, level.lower(), event_logger.info)
    
    if context:
        ctx_str = " | ". join(f"{k}={v}" for k, v in context.items())
        log_func(f"{event} | {ctx_str}")
    else:
        log_func(event)


def log_exception(
    message: str,
    exc: Optional[BaseException] = None,
    **context: Any
) -> None:
    """
    Log an exception to server/logs/errors.log
    
    Args:
        message: Error description
        exc: Exception object (uses current if None)
        **context: Additional key-value pairs
    
    Example:
        try:
            risky_operation()
        except Exception as e:
            log_exception("Failed to process", e, id="123")
    """
    if exc is None:
        exc = sys.exc_info()[1]
    
    ctx_str = ""
    if context:
        ctx_str = " | " + " | ". join(f"{k}={v}" for k, v in context.items())
    
    if exc:
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        error_logger.error(f"{message}{ctx_str}\n{''. join(tb)}")
    else:
        error_logger. error(f"{message}{ctx_str}")