# -*- coding: utf-8 -*-
from tester import _get_member_wrapper, _package_logger
import logging

_logger = (
    _package_logger.getChild("tester")
    .getChild("devices")
    .getChild("machdsp")
    .getChild("MachDSP")
)
_member_wrapper = _get_member_wrapper(_logger)


class MachDSP:
    """
    MachDSP device class
    """

    __logger = _logger

    @_member_wrapper
    def __init__(self):
        """
        Constructor
        """
        pass