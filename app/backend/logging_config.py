"""Logging configuration for the application."""
import logging
import logging.handlers
from pathlib import Path

# Create logs directory in app root
app_root = Path(__file__).resolve().parent.parent
logs_dir = app_root / "logs"
logs_dir.mkdir(exist_ok=True)


# Setup logging
def setup_logging(name: str = "fashion_wardrobe", log_level: int = logging.DEBUG) -> logging.Logger:
    """Setup logging with file and console handlers.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(log_level)
    logger.propagate = True  # Allow propagation to root logger
    
    # File handler (rotates at 10MB) - detailed format
    log_file = logs_dir / f"{name}.log"
    detailed_format = (
        '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s'
    )
    file_formatter = logging.Formatter(
        detailed_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get or create a logger for a module.
    
    Args:
        name: Module name (usually __name__)
    
    Returns:
        Logger instance
    """
    if name is None:
        return logging.getLogger()
    
    # Get or create logger
    logger = logging.getLogger(name)
    
    # If this is the first time, configure it to use the main logger's handlers
    if not logger.handlers and name != "fashion_wardrobe_app":
        logger.setLevel(logging.DEBUG)
        logger.propagate = True  # Propagate to root/main logger
    
    return logger


# Create app logger
logger = setup_logging("fashion_wardrobe_app")

# Configure root logger to propagate to app logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
for handler in logger.handlers:
    if handler not in root_logger.handlers:
        root_logger.addHandler(handler)