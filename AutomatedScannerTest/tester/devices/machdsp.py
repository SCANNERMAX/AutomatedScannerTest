# -*- coding: utf-8 -*-
from PySide6.QtCore import QSettings
import tester
from tester.devices import Device

class MachDSP(Device):
    """
    Represents a MachDSP device, inheriting from the Device base class.
    This class is responsible for initializing and configuring a MachDSP device
    using the provided QSettings object.
    Attributes:
        Inherits all attributes from the Device base class.
    """

    def __init__(self, settings: QSettings):
        """
        Initializes the MachDSP device with the provided settings.

        Args:
            settings (QSettings): The settings object used to configure the device.
        """
        super().__init__("MachDSP", settings)