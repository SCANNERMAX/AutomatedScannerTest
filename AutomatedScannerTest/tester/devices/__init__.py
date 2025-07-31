# -*- coding: utf-8 -*-
from PySide6 import QtCore

class Device(QtCore.QObject):
    """
    Device base class for hardware abstraction.
    """

    def __init__(self, name: str):
        super().__init__()
        app = QtCore.QCoreApplication.instance()
        if app.__class__.__name__ == "TesterApp":
            self.logger = app.get_logger(self.__class__.__name__)
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
        else:
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        self.Name = name
        # Only call findInstrument if subclass has overridden it
        if self.__class__.findInstrument is not Device.findInstrument:
            self.findInstrument()

    def findInstrument(self):
        if self.logger:
            self.logger.warning("findInstrument() not implemented for this device.")

    def getSetting(self, key: str, default=None):
        self.logger.debug("Retrieving setting '%s' for device '%s'", key, self.Name)
        return self.__settings.getSetting(f"Devices/{self.Name}", key, default)

    def setSetting(self, key: str, value):
        self.logger.debug("Setting '%s' to '%s' for device '%s'", key, value, self.Name)
        self.__settings.setSetting(f"Devices/{self.Name}", key, value)

    @QtCore.Slot()
    def onSettingsModified(self):
        if self.logger:
            self.logger.debug("Settings modified for device: %s", self.Name)
