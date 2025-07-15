# -*- coding: utf-8 -*-
import importlib
import inspect
from PySide6.QtCore import QObject, QSettings
import pyvisa

import tester


class Device(QObject):
    """
    Device base class for hardware abstraction.
    This class provides a foundation for device objects, managing device-specific settings
    and providing a structure for instrument discovery. It is intended to be subclassed
    by specific device implementations.
    Methods:
        _get_setting(key: str, default=None):
        _set_setting(key: str, value):
        find_instrument():
            Should be overridden by subclasses to provide device-specific instrument discovery logic.
    """

    def __init__(self, name: str, settings: QSettings):
        """
        Initializes the device instance with a name and settings.

        Args:
            name (str): The name of the device.
            settings (QSettings): The settings object for device configuration.

        Attributes:
            logger: Logger instance for the class.
            __settings (QSettings): Stores the settings object.
            Name (str): The name of the device.

        Calls:
            find_instrument(): Attempts to locate and initialize the instrument.
        """
        super().__init__()
        self.logger = tester._get_class_logger(self.__class__)
        self.__settings = settings
        self.Name = name
        self.find_instrument()

    def _get_setting(self, key: str, default=None):
        """
        Retrieve a setting value for the device from the application's settings storage.

        Args:
            key (str): The name of the setting to retrieve.
            default (optional): The value to return if the setting is not found. Defaults to None.

        Returns:
            The value of the requested setting if it exists, otherwise the default value.
        """
        self.__settings.beginGroup("Devices")
        self.__settings.beginGroup(self.Name)
        _value = self.__settings.value(key, default)
        self.__settings.endGroup()
        self.__settings.endGroup()
        return _value

    def _set_setting(self, key: str, value):
        """
        Sets a configuration setting for the device.

        This method stores the given key-value pair in the device's settings group,
        organizing it under the "Devices" group and the specific device's name.

        Args:
            key (str): The name of the setting to set.
            value: The value to assign to the setting.
        """
        self.__settings.beginGroup("Devices")
        self.__settings.beginGroup(self.Name)
        self.__settings.setValue(key, value)
        self.__settings.endGroup()
        self.__settings.endGroup()

    def find_instrument(self):
        """
        Logs a warning indicating that the 'find_instrument' method is not implemented for this device.

        This method should be overridden by subclasses to provide device-specific instrument discovery logic.
        """
        self.logger.warning("find_instrument() not implemented for this device.")
