# -*- coding: utf-8 -*-
from PySide6 import QtCore

from AutomatedScannerTest.tester.app import TesterApp


class Device(QtCore.QObject):
    """
    Device base class for hardware abstraction.
    """

    def __init__(self, name: str):
        super().__init__()
        app = TesterApp.instance()
        if isinstance(app, TesterApp):
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

    Name = QtCore.Property(
        str,
        fget=lambda self: self.getSetting("Name", ""),
        fset=lambda self, value: self.setSetting("Name", value),
        doc="Name of the device, used for identification.",
    )

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
