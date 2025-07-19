# -*- coding: utf-8 -*-
"""This application runs a series of tests designed to validate the quality of Pangolin Laser System scanners."""
import logging
from functools import wraps

_package_name = "PangolinLaserSystems.AutomatedScannerTest"
__version__ = "1.1.0"
__company__ = "Pangolin Laser Systems"
__application__ = "Automated Scanner Test"


def _get_class_logger(class_):
    """
    Returns a logger instance specific to the given class.

    The logger is retrieved using the class's module and name, creating a hierarchical logger structure.
    This allows for more granular logging control and easier identification of log messages from different classes.

    Args:
        class_ (type): The class for which to obtain a logger.

    Returns:
        logging.Logger: A logger instance scoped to the specified class.
    """
    return logging.getLogger(f"{_package_name}.{class_.__module__}.{class_.__name__}")


def _member_logger(func):
    """
    Decorator that logs the entry, arguments, return value, and exceptions of a class member function.
    Args:
        func (callable): The function to be wrapped and logged.
    Returns:
        callable: The wrapped function with logging enabled.
    Logs:
        - Function name, arguments, and keyword arguments before execution.
        - Return value after successful execution.
        - Exception details if an error occurs during execution.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = _get_class_logger(args[0].__class__)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Calling function: %s with arguments: %s and keyword arguments: %s",
                func.__name__,
                args[1:] if len(args) > 1 else "",
                kwargs,
            )
        try:
            _result = func(*args, **kwargs)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Function: %s returned: %r", func.__name__, _result)
            return _result
        except Exception as e:
            logger.error("Function: %s failed with error: %s", func.__name__, e, exc_info=True)
            raise

    return wrapper
