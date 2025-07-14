"""
Logging Configuration

Sets up structured logging for the application using loguru.
Provides consistent logging format across all modules.
"""

import sys
import logging
from pathlib import Path
from typing import Any
from loguru import logger

from ...config import settings


def setup_logging():
    """
    Configure application logging with loguru.
    
    Sets up:
    - Console output with appropriate level
    - File output for production
    - Structured logging format
    - Integration with standard logging
    """
    # Remove default logger
    logger.remove()
    
    # Console logging
    log_level = settings.LOG_LEVEL
    
    if settings.LOG_FORMAT == "structured":
        # Structured JSON logging for production
        logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message} | {extra}",
            level=log_level,
            serialize=False
        )
    else:
        # Simple format for development
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True
        )
    
    # File logging
    if settings.LOG_FILE:
        log_file = Path(settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message} | {extra}",
            level=log_level,
            rotation="100 MB",
            retention="7 days",
            compression="zip"
        )
    
    # Production logging to separate files by level
    if settings.is_production:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Error logs
        logger.add(
            logs_dir / "error.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message} | {extra}",
            level="ERROR",
            rotation="50 MB",
            retention="30 days",
            compression="zip"
        )
        
        # Application logs
        logger.add(
            logs_dir / "app.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message} | {extra}",
            level="INFO",
            rotation="100 MB",
            retention="7 days",
            compression="zip"
        )
    
    # Intercept standard logging
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # Configure standard logging to use loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    
    # Disable noisy loggers
    for logger_name in ["uvicorn.access", "uvicorn.error"]:
        logging.getLogger(logger_name).handlers = []
    
    logger.info(f"Logging configured - Level: {log_level}, Format: {settings.LOG_FORMAT}")


def get_logger(name: str) -> Any:
    """
    Get a logger instance for the given module name.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Logger instance configured for the module
    """
    # For loguru, we can just return the logger instance
    # as it handles context automatically
    return logger.bind(module=name)


# Initialize logging on import
setup_logging()
