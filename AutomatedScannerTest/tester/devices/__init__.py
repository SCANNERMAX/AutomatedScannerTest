# -*- coding: utf-8 -*-
from PySide6 import QtCore
import logging

__logger = logging.getLogger(__name__)

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
        __logger.debug(f"Initializing device with name: {name}")
        super().__init__()
        self.Name = name
        app = QtCore.QCoreApplication.instance()
        __logger.debug(f"QCoreApplication instance: {app}")
        if (
            app is not None
            and hasattr(app, "get_settings")
            and app.metaObject().className() == "TesterApp"
        ):
            __logger.debug(f"Application is TesterApp, retrieving settings.")
            self.__settings = app.get_settings()
            try:
                __logger.debug(f"Connecting settingsModified signal.")
                self.__settings.settingsModified.connect(self.onSettingsModified)
            except AttributeError as e:
                __logger.warning(f"settingsModified signal not found: {e}")
            self.onSettingsModified()
        else:
            __logger.critical(f"TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        __logger.debug(f"Device initialized successfully.")
        # Only call findInstrument if subclass has overridden it
        if type(self).findInstrument is not Device.findInstrument:
            __logger.debug(f"Subclass has overridden findInstrument, calling it.")
            self.findInstrument()
        else:
            __logger.debug(f"Using base findInstrument implementation.")

    @QtCore.Slot()
    def findInstrument(self):
        """
        Attempt to find and initialize the hardware instrument.

        Subclasses should override this method to implement device-specific discovery logic.

        Logging:
            - Warns if not implemented in subclass.
        """
        __logger.warning(f"findInstrument() not implemented for this device.")

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
        __logger.debug(f"Retrieving setting '{key}' with default '{default}'")
        try:
            value = self.__settings.getSetting(f"Devices/{self.Name}", key, default)
            __logger.debug(f"Retrieved setting '{key}': {value}")
            return value
        except AttributeError as e:
            __logger.warning(f"Settings object not initialized: {e}")
            return default
        except Exception as e:
            __logger.critical(f"Exception while retrieving setting '{key}': {e}")
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
        __logger.debug(f"Setting '{key}' to '{value}'")
        try:
            self.__settings.setSetting(f"Devices/{self.Name}", key, value)
            __logger.debug(f"Set setting '{key}' to '{value}' successfully.")
        except AttributeError as e:
            __logger.warning(f"Settings object not initialized: {e}")
        except Exception as e:
            __logger.critical(f"Exception while setting '{key}' to '{value}': {e}")

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when application settings are modified.

        Subclasses may override this to react to settings changes.

        Logging:
            - Logs when settings modification event is triggered.
        """
        __logger.debug(f"Settings modified event triggered.")
