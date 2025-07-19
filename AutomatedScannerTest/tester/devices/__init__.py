# -*- coding: utf-8 -*-
from PySide6.QtCore import QObject, QSettings

import tester


class Device(QObject):
    """
    Device base class for hardware abstraction.

    This class provides a foundation for device objects, managing device-specific settings
    and a structure for instrument discovery. It is intended to be subclassed by concrete
    device implementations.

    Attributes:
        logger: Logger instance for the device.
        _settings: QSettings instance for application/device settings.
        Name: Name of the device.
    """

    def __init__(self, name: str, settings: QSettings):
        """
        Initializes the device instance with a name and settings.

        Args:
            name (str): The name of the device.
            settings (QSettings): The settings object for storing device configuration.
        """
        super().__init__()
        self.logger = tester._get_class_logger(type(self))
        self._settings = settings
        self.Name = name
        self.find_instrument()

    def _get_setting(self, key: str, default=None):
        """
        Retrieve a setting value for the device from the application's settings storage.

        Args:
            key (str): The key of the setting to retrieve.
            default: The default value to return if the key does not exist.

        Returns:
            The value of the setting, or the default if not found.
        """
        group_path = f"Devices/{self.Name}"
        self._settings.beginGroup(group_path)
        value = self._settings.value(key, default)
        self._settings.endGroup()
        return value

    def _set_setting(self, key: str, value):
        """
        Sets a configuration setting for the device.

        Args:
            key (str): The key of the setting to set.
            value: The value to set for the specified key.
        """
        group_path = f"Devices/{self.Name}"
        self._settings.beginGroup(group_path)
        self._settings.setValue(key, value)
        self._settings.endGroup()

    def find_instrument(self):
        """
        Logs a warning indicating that the 'find_instrument' method is not implemented for this device.

        This method should be overridden by subclasses to implement device-specific
        instrument discovery logic.
        """
        self.logger.warning("find_instrument() not implemented for this device.")
