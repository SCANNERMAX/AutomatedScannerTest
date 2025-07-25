# -*- coding: utf-8 -*-
from PySide6.QtCore import QObject, QSettings

import tester


class Device(QObject):
    """
    Base class for hardware abstraction.

    Manages device-specific settings and provides a structure for instrument discovery.
    Intended to be subclassed by concrete device implementations.

    Attributes:
        logger: Logger instance for the device.
        _settings: QSettings instance for application/device settings.
        Name: Name of the device (defaults to class name).
    """

    def __init__(self, settings: QSettings):
        """
        Initialize the device instance with settings.

        Args:
            settings (QSettings): The settings object for storing device configuration.
        """
        super().__init__()
        self.logger = tester._get_class_logger(type(self))
        self._settings = settings
        self.Name = self.__class__.__name__

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
        Set a configuration setting for the device.

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
        Log a warning indicating that the 'find_instrument' method is not implemented for this device.

        This method should be overridden by subclasses to implement device-specific
        instrument discovery logic.
        """
        self.logger.warning("find_instrument() not implemented for this device.")
