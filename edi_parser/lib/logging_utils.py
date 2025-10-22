"""
Logging utilities with automatic function entry/exit tracking

Provides decorators and metaclasses for adding comprehensive logging
to functions and classes without cluttering code with print statements.
"""

import logging
import functools
from typing import Callable, Any


def log_function_call(func: Callable) -> Callable:
    """
    Decorator to log function entry/exit automatically

    Usage:
        @log_function_call
        def my_function(x, y):
            return x + y

    In verbose mode (logging.DEBUG), this will log:
        → Entering my_function
        ← Exiting my_function

    Args:
        func: Function to wrap with logging

    Returns:
        Wrapped function with entry/exit logging
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)

        # Log entry
        logger.debug(f"→ Entering {func.__qualname__}")

        try:
            # Call function
            result = func(*args, **kwargs)

            # Log successful exit
            logger.debug(f"← Exiting {func.__qualname__}")

            return result

        except Exception as e:
            # Log error exit
            logger.error(f"✗ Error in {func.__qualname__}: {type(e).__name__}: {e}")
            raise

    return wrapper


class LoggedMeta(type):
    """
    Metaclass to automatically wrap all public methods with logging

    Usage:
        class MyClass(metaclass=LoggedMeta):
            def public_method(self):
                pass

            def _private_method(self):
                pass  # Won't be logged

    All public methods (not starting with _) will automatically have
    entry/exit logging in DEBUG mode.

    Note: Only applies to instance methods, not class methods or static methods.
    """

    def __new__(mcs, name, bases, namespace, **kwargs):
        # Wrap all callable public attributes with logging
        for key, value in namespace.items():
            if callable(value) and not key.startswith('_'):
                namespace[key] = log_function_call(value)

        return super().__new__(mcs, name, bases, namespace, **kwargs)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger for a module

    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance

    Usage:
        logger = get_logger(__name__)
        logger.info("Message")
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)

    return logger


def log_entry_exit(logger_name: str = None):
    """
    Parameterized decorator for entry/exit logging with custom logger

    Usage:
        @log_entry_exit('my.module')
        def my_function():
            pass

    Args:
        logger_name: Optional logger name (defaults to function's module)

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name or func.__module__)

            logger.debug(f"→ {func.__qualname__}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"← {func.__qualname__}")
                return result
            except Exception as e:
                logger.error(f"✗ {func.__qualname__}: {type(e).__name__}")
                raise

        return wrapper
    return decorator


# Convenience function for enabling verbose logging across all modules
def enable_verbose_logging(level: int = logging.DEBUG):
    """
    Enable verbose logging for all edi_parser modules

    Args:
        level: Logging level to set (default: DEBUG)

    Usage:
        enable_verbose_logging()  # Show all function entry/exit
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%H:%M:%S'
    )

    # Set level for all edi_parser loggers
    for name in list(logging.Logger.manager.loggerDict.keys()):
        if name.startswith('edi_parser'):
            logging.getLogger(name).setLevel(level)
