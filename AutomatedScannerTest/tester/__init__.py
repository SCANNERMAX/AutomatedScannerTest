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
    Get a logger instance specific to the given class.

    The logger is named using the package name, module, and class name, which allows for
    hierarchical and granular logging control.

    Args:
        class_ (type): The class for which to obtain a logger.

    Returns:
        logging.Logger: Logger instance scoped to the specified class.
    """
    return logging.getLogger(f"{_package_name}.{class_.__module__}.{class_.__name__}")


def _member_logger(func):
    """
    Decorator for class member functions to log entry, arguments, return value, and exceptions.

    This decorator logs the function name, arguments, and keyword arguments before execution,
    the return value after successful execution, and exception details if an error occurs.

    Args:
        func (callable): The function to be wrapped and logged.

    Returns:
        callable: The wrapped function with logging enabled.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """
        Wrapper function that performs the logging around the decorated function.

        Args:
            self: The instance of the class.
            *args: Positional arguments for the decorated function.
            **kwargs: Keyword arguments for the decorated function.

        Returns:
            Any: The return value of the decorated function.

        Raises:
            Exception: Re-raises any exception thrown by the decorated function after logging.
        """
        logger = _get_class_logger(type(self))
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Calling function: %s with arguments: %r and keyword arguments: %r",
                func.__name__,
                args,
                kwargs,
            )
        try:
            _result = func(self, *args, **kwargs)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Function: %s returned: %r", func.__name__, _result)
            return _result
        except Exception as e:
            logger.error("Function: %s failed with error: %s", func.__name__, e, exc_info=True)
            raise

    return wrapper
