# -*- coding: utf-8 -*-
from PySide6 import QtCore

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
        """
        super().__init__()
        app = QtCore.QCoreApplication.instance()
        if app is not None and app.metaObject().className() == "TesterApp":
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
        else:
            QtCore.qCritical("[Device] TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        self.Name = name
        # Only call findInstrument if subclass has overridden it
        if type(self).findInstrument is not Device.findInstrument:
            self.findInstrument()

    @QtCore.Slot()
    def findInstrument(self):
        """
        Attempt to find and initialize the hardware instrument.

        Subclasses should override this method to implement device-specific discovery logic.
        """
        QtCore.qWarning(f"[Device:{self.Name}] findInstrument() not implemented for this device.")

    def getSetting(self, key: str, default=None):
        """
        Retrieve a device-specific setting.

        Args:
            key (str): The setting key.
            default: The default value if the key does not exist.

        Returns:
            The value of the setting, or the default if not found.
        """
        QtCore.qDebug(f"[Device:{self.Name}] Retrieving setting '{key}'")
        return self.__settings.getSetting(f"Devices/{self.Name}", key, default)

    def setSetting(self, key: str, value=None):
        """
        Set a device-specific setting.

        Args:
            key (str): The setting key.
            value: The value to set for the key.
        """
        QtCore.qDebug(f"[Device:{self.Name}] Setting '{key}' to '{value}'")
        self.__settings.setSetting(f"Devices/{self.Name}", key, value)

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when application settings are modified.

        Subclasses may override this to react to settings changes.
        """
        QtCore.qDebug(f"[Device:{self.Name}] Settings modified.")
