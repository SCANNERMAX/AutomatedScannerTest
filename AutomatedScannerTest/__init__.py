# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import logging
import logging.handlers

def _get_member_wrapper(name):
    _logger = logging.getLogger(name)
    def function_wrapper(func):
        def wrapper(*args, **kwargs):
            try:
                _logger.debug(
                    f"Calling function: {func.__name__} with arguments: {args} and keyword arguments: {kwargs}"
                )
                _result = func(*args, **kwargs)
                _logger.debug(f"Function: {func.__name__} returned: {_result}")
                return _result
            except Exception as e:
                _logger.error(f"Function: {func.__name__} failed with error: {e}")
                raise e

        return wrapper

    return function_wrapper, _logger

