# -*- coding: utf-8 -*-
from PySide6.QtCore import QSettings
from tester.devices import Device

class MachDSP(Device):
    """
    Represents a MachDSP device.

    This class inherits from the Device base class and is used to initialize and configure
    a MachDSP device using the provided QSettings object.

    Attributes:
        None
    """

    def __init__(self, settings: QSettings):
        """
        Initializes a new instance of the MachDSP device.

        Args:
            settings (QSettings): The QSettings object containing configuration for the device.
        """
        super().__init__("MachDSP", settings)