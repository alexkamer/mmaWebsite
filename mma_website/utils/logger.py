"""Structured logging configuration for MMA Website"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(app=None, name='mma_website', log_level=None):
    """
    Configure structured logging for the application

    Args:
        app: Flask app instance (optional)
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Get log level from environment or use INFO as default
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter if log_level == 'INFO' else detailed_formatter)
    logger.addHandler(console_handler)

    # File handler (rotating)
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f'{name}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Error file handler (separate file for errors)
    error_log_file = os.path.join(log_dir, f'{name}_error.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)

    # If Flask app provided, set it up
    if app:
        app.logger.handlers = logger.handlers
        app.logger.setLevel(logger.level)

    logger.info(f"Logger initialized: {name} (Level: {log_level})")

    return logger


def get_logger(name='mma_website'):
    """Get or create a logger instance"""
    return logging.getLogger(name)


# Request logging helper
class RequestLogger:
    """Helper class for logging HTTP requests"""

    @staticmethod
    def log_request(logger, request, response=None, error=None):
        """Log HTTP request details"""
        log_data = {
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string if request.user_agent else 'Unknown'
        }

        if response:
            log_data['status_code'] = response.status_code
            logger.info(f"Request: {log_data['method']} {log_data['path']} - Status: {log_data['status_code']}")

        if error:
            logger.error(f"Request failed: {log_data['method']} {log_data['path']} - Error: {str(error)}")

        return log_data


# Performance logging helper
class PerformanceLogger:
    """Helper class for logging performance metrics"""

    def __init__(self, logger, operation_name):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type:
            self.logger.error(f"Failed: {self.operation_name} (Duration: {duration:.3f}s, Error: {exc_val})")
        else:
            if duration > 1.0:
                self.logger.warning(f"Slow operation: {self.operation_name} (Duration: {duration:.3f}s)")
            else:
                self.logger.debug(f"Completed: {self.operation_name} (Duration: {duration:.3f}s)")
        return False  # Don't suppress exceptions
