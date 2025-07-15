# -*- coding: utf-8 -*-
"""This application runs a series of tests designed to validate the quality of Pangolin Laser System scanners."""
import logging

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
    _module = class_.__module__
    _name = class_.__name__
    return logging.getLogger(_package_name).getChild(_module).getChild(_name)


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

    def wrapper(*args, **kwargs):
        try:
            logger = _get_class_logger(args[0].__class__)
            logger.debug(
                f"Calling function: {func.__name__} with arguments: {args} and keyword arguments: {kwargs}"
            )
            _result = func(*args, **kwargs)
            logger.debug(f"Function: {func.__name__} returned: {_result}")
            return _result
        except Exception as e:
            logger.error(f"Function: {func.__name__} failed with error: {e}")
            raise e

    return wrapper
