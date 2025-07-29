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
        group_path = f"Devices/{self.Name}"
        self.__settings.beginGroup(group_path)
        value = self.__settings.value(key, default)
        self.__settings.endGroup()
        self.__settings.sync()
        return value

    def onSettingsModified(self):
        if self.logger:
            self.logger.debug("Settings modified for device: %s", self.Name)

    def setSetting(self, key: str, value):
        group_path = f"Devices/{self.Name}"
        self.__settings.beginGroup(group_path)
        self.__settings.setValue(key, value)
        self.__settings.endGroup()
        self.__settings.sync()
