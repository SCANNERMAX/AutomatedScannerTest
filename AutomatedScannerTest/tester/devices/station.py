# -*- coding: utf-8 -*-
from tester import _get_class_logger, _member_logger
from tester.devices.mso5000 import MSO5000
import pyvisa


class Station:
    """Station for testing completed scanners"""

    @_member_logger
    def __init__(self):
        """Initialize the station with a name and a scanner"""
        self.__logger = _get_class_logger(self.__class__)
        self.__logger.debug("Locating connected devices using VISA resource manager.")
        _resource_manager = pyvisa.ResourceManager()
        for _device in _resource_manager.list_resources():
            try:
                self.__logger.info(f"Found device: {_device}")
                _instrument = _resource_manager.open_resource(_device)
                if MSO5000.is_device(_instrument):
                    self.__logger.info(f"Found MSO5000 oscilloscope: {_device}")
                    _device = MSO5000(_instrument)
                    setattr(self, "osc", _device)
            except:
                pass
        assert hasattr(self, "osc"), "No oscilloscope found."
