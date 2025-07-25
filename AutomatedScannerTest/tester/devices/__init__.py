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
        Initialize the Device instance.

        Args:
            name (str): The name of the device.
            settings (QSettings): The settings object for storing device configuration.
        """
        super().__init__()
        self.logger = tester._get_class_logger(type(self))
        self._settings = settings
        self.Name = name
        # Only call find_instrument if subclass has overridden it
        if self.__class__.find_instrument is not Device.find_instrument:
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
        try:
            return self._settings.value(key, default)
        finally:
            self._settings.endGroup()

    def _set_setting(self, key: str, value):
        """
        Set a configuration setting for the device.

        Args:
            key (str): The key of the setting to set.
            value: The value to set for the specified key.
        """
        group_path = f"Devices/{self.Name}"
        self._settings.beginGroup(group_path)
        try:
            self._settings.setValue(key, value)
        finally:
            self._settings.endGroup()

    def find_instrument(self):
        """
        Discover and initialize the instrument associated with this device.

        This method should be overridden by subclasses to implement device-specific
        instrument discovery logic. The base implementation logs a warning.
        """
        self.logger.warning("find_instrument() not implemented for this device.")
