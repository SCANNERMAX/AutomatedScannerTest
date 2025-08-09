# -*- coding: utf-8 -*-
from PySide6 import QtCore
import logging

logger = logging.getLogger(__name__)

class Device(QtCore.QObject):
    """
    Device base class for hardware abstraction.

    Provides a common interface for all hardware devices, including settings management
    and a mechanism for device discovery. Subclasses should override findInstrument()
    to implement device-specific discovery logic.
    """

    def __init__(self, name: str):
        """
        Initialize the Device.

        Args:
            name (str): The name of the device, used for settings and logging.

        Raises:
            RuntimeError: If the application instance is not a TesterApp.

        Logging:
            - Logs initialization steps, application instance checks, settings retrieval,
              signal connection, and device initialization status.
        """
        logger.debug(f"[Device] Initializing device with name: {name}")
        super().__init__()
        self.Name = name
        app = QtCore.QCoreApplication.instance()
        logger.debug(f"[Device] QCoreApplication instance: {app}")
        if app is None or app.__class__.__name__ != "TesterApp":
            logger.critical(f"[Device] TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        logger.debug(f"[Device] Application is TesterApp, retrieving settings.")
        self._settings = app.get_settings()
        settings_modified = getattr(self._settings, "settingsModified", None)
        if callable(getattr(settings_modified, "connect", None)):
            logger.debug(f"[Device] Connecting settingsModified signal.")
            settings_modified.connect(self.onSettingsModified)
        else:
            logger.warning(f"[Device] settingsModified signal not found in settings object.")
        self.onSettingsModified()
        logger.debug(f"[Device] Device initialized successfully.")
        # Only call findInstrument if subclass has overridden it
        if type(self).findInstrument is not Device.findInstrument:
            logger.debug(f"[Device] Subclass has overridden findInstrument, calling it.")
            self.findInstrument()
        else:
            logger.debug(f"[Device] Using base findInstrument implementation.")

    @QtCore.Slot()
    def findInstrument(self):
        """
        Attempt to find and initialize the hardware instrument.

        Subclasses should override this method to implement device-specific discovery logic.

        Logging:
            - Warns if not implemented in subclass.
        """
        logger.warning(f"[Device] findInstrument() not implemented for this device.")

    def getSetting(self, key: str, default=None):
        """
        Retrieve a device-specific setting.

        Args:
            key (str): The setting key.
            default: The default value if the key does not exist.

        Returns:
            The value of the setting, or the default if not found.

        Logging:
            - Logs retrieval attempts, results, and exceptions.
        """
        logger.debug(f"[Device] Retrieving setting '{key}' with default '{default}'")
        settings = getattr(self, "_settings", None)
        if settings is None:
            logger.warning(f"[Device] Settings object not initialized.")
            return default
        try:
            value = settings.getSetting(f"Devices/{self.Name}", key, default)
            logger.debug(f"[Device] Retrieved setting '{key}': {value}")
            return value
        except Exception as e:
            logger.critical(f"[Device] Exception while retrieving setting '{key}': {e}")
            return default

    def setSetting(self, key: str, value=None):
        """
        Set a device-specific setting.

        Args:
            key (str): The setting key.
            value: The value to set for the key.

        Logging:
            - Logs setting attempts, success, and exceptions.
        """
        logger.debug(f"[Device] Setting '{key}' to '{value}'")
        settings = getattr(self, "_settings", None)
        if settings is None:
            logger.warning(f"[Device] Settings object not initialized.")
            return
        try:
            settings.setSetting(f"Devices/{self.Name}", key, value)
            logger.debug(f"[Device] Set setting '{key}' to '{value}' successfully.")
        except Exception as e:
            logger.critical(f"[Device] Exception while setting '{key}' to '{value}': {e}")

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when application settings are modified.

        Subclasses may override this to react to settings changes.

        Logging:
            - Logs when settings modification event is triggered.
        """
        logger.debug(f"[Device] Settings modified event triggered.")
