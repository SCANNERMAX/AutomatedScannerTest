# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtNetwork
import importlib
import inspect
import os

from tester.devices import Device


class DeviceManager(QtCore.QObject):
    """
    Manages and initializes all device instances for automated scanner testing.

    This class dynamically discovers all subclasses of `Device` in the `tester.devices` package,
    instantiates them, and attaches them as attributes. It provides setup and teardown routines
    for preparing devices before and after tests, and uses Qt logging for status and error reporting.

    Attributes:
        ComputerName (str): The network name of the current computer (host).
        UserName (str): The current user's name, derived from the home directory or environment.
    """

    def __init__(self):
        """
        Initialize the DeviceManager, discover and instantiate all Device subclasses, and
        connect to application settings.

        Raises:
            RuntimeError: If not running inside a TesterApp instance.
        """
        super().__init__()
        app = QtCore.QCoreApplication.instance()
        if app is not None and app.__class__.__name__ == "TesterApp":
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
            QtCore.qInfo("[DeviceManager] Settings initialized.")
        else:
            QtCore.qCritical("[DeviceManager] TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")

        # Discover and instantiate all Device subclasses in tester.devices
        _device_module = importlib.import_module(Device.__module__)
        _device_folder = QtCore.QFileInfo(_device_module.__file__).absolutePath()
        dir_obj = QtCore.QDir(_device_folder)
        py_files = [f for f in dir_obj.entryList(["*.py"], QtCore.QDir.Files) if not f.startswith("__")]

        for _filename in py_files:
            _module_name = f"tester.devices.{_filename[:-3]}"
            try:
                _module = importlib.import_module(_module_name)
            except Exception as e:
                QtCore.qWarning(f"[DeviceManager] Could not import {_module_name}: {e}")
                continue

            for _name, _obj in inspect.getmembers(_module, inspect.isclass):
                if (
                    _obj.__module__ == _module.__name__
                    and issubclass(_obj, Device)
                    and _obj is not Device
                ):
                    try:
                        _device = _obj()
                        _device.findInstrument()
                        setattr(self, _name, _device)
                        QtCore.qInfo(f"[DeviceManager] Device '{_name}' instantiated and attached.")
                    except Exception as e:
                        QtCore.qWarning(f"[DeviceManager] Could not instantiate {_name}: {e}")

    @QtCore.Property(str)
    def ComputerName(self) -> str:
        """
        Get the network name of the current computer (host).

        Returns:
            str: The local host name, or a fallback if unavailable.
        """
        host = QtNetwork.QHostInfo.localHostName()
        if host:
            return host
        try:
            return os.uname().nodename
        except Exception:
            import socket
            return socket.gethostname()

    @QtCore.Property(str)
    def UserName(self) -> str:
        """
        Get the current user's name, derived from the home directory or environment.

        Returns:
            str: The user's name.
        """
        home_path = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.HomeLocation)
        if home_path:
            return os.path.basename(home_path.rstrip("/\\"))
        return QtCore.QProcessEnvironment.systemEnvironment().value("USERNAME", "unknown")

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when application settings are modified.
        """
        QtCore.qDebug("[DeviceManager] Settings modified, updating device manager.")

    @QtCore.Slot()
    def setup(self):
        """
        Prepare the device manager and devices before running tests.
        Resets the MSO5000 device if present.
        """
        QtCore.qDebug("[DeviceManager] Setting up the device manager.")
        mso = getattr(self, "MSO5000", None)
        if mso:
            mso.reset()

    @QtCore.Slot()
    def test_setup(self):
        """
        Prepare the device manager and devices before each individual test.
        Resets and clears the MSO5000 device if present.
        """
        QtCore.qDebug("[DeviceManager] Setting up the device manager for testing.")
        mso = getattr(self, "MSO5000", None)
        if mso:
            mso.reset()
            if hasattr(mso, "clear_registers"):
                mso.clear_registers()
            if hasattr(mso, "clear"):
                mso.clear()

    @QtCore.Slot()
    def test_teardown(self):
        """
        Clean up after each individual test.
        """
        QtCore.qDebug("[DeviceManager] Tearing down the device manager settings for testing.")

    @QtCore.Slot()
    def teardown(self):
        """
        Clean up and reset devices after all tests.
        Resets the MSO5000 device if present.
        """
        QtCore.qDebug("[DeviceManager] Tearing down the device manager.")
        mso = getattr(self, "MSO5000", None)
        if mso:
            mso.reset()
