# -*- coding: utf-8 -*-
import logging

_package_name = "PangolinLaserSystems.AutomatedScannerTest"
__version__ = 1.0
__company__ = "Pangolin Laser Systems"
__application__ = "Automated Scanner Test"


def _get_class_logger(class_):
    _module = class_.__module__
    _name = class_.__name__
    return logging.getLogger(_package_name).getChild(_module).getChild(_name)


def _member_logger(func):
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
