# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtNetwork
import importlib
import inspect
import os
import logging

from tester.devices import Device

# Configure Python logging
__logger = logging.getLogger(__name__)

class DeviceManager(QtCore.QObject):
    """
    Manages and initializes all device instances for automated scanner testing.

    This class dynamically discovers all subclasses of `Device` in the `tester.devices` package,
    instantiates them, and attaches them as attributes. It provides setup and teardown routines
    for preparing devices before and after tests, and uses Python logging for status and error reporting.

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
        __logger.debug("Initializing DeviceManager...")
        app = QtCore.QCoreApplication.instance()
        if app is not None and app.__class__.__name__ == "TesterApp":
            __logger.debug(f"TesterApp instance found: {app}")
            self.__settings = app.get_settings()
            __logger.debug(f"Settings object obtained: {self.__settings}")
            self.__settings.settingsModified.connect(self.onSettingsModified)
            __logger.debug("Connected settingsModified signal to onSettingsModified slot.")
            self.onSettingsModified()
            __logger.debug("Settings initialized.")
        else:
            __logger.critical("TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")

        # Discover and instantiate all Device subclasses in tester.devices using Qt file system access
        _device_module = importlib.import_module(Device.__module__)
        __logger.debug(f"Device base module: {Device.__module__}, file: {_device_module.__file__}")
        _device_folder = QtCore.QFileInfo(_device_module.__file__).absolutePath()
        __logger.debug(f"Device folder resolved to: {_device_folder}")
        dir_obj = QtCore.QDir(_device_folder)
        py_files = [f for f in dir_obj.entryList(["*.py"], QtCore.QDir.Files) if not f.startswith("__")]
        __logger.debug(f"Python files found for device discovery: {py_files}")

        imported_modules = {}
        for _filename in py_files:
            _module_name = f"tester.devices.{_filename[:-3]}"
            __logger.debug(f"Attempting to import module: {_module_name}")
            try:
                if _module_name in imported_modules:
                    _module = imported_modules[_module_name]
                    __logger.debug(f"Module {_module_name} loaded from cache.")
                else:
                    _module = importlib.import_module(_module_name)
                    imported_modules[_module_name] = _module
                    __logger.debug(f"Module {_module_name} imported successfully.")
            except Exception as e:
                __logger.warning(f"Could not import {_module_name}: {e}")
                continue

            for _name, _obj in inspect.getmembers(_module, inspect.isclass):
                __logger.debug(f"Inspecting class: {_name} in module: {_module_name}")
                if (
                    _obj.__module__ == _module.__name__
                    and issubclass(_obj, Device)
                    and _obj is not Device
                ):
                    __logger.debug(f"Found Device subclass: {_name} in module: {_module_name}")
                    try:
                        _device = _obj()
                        __logger.debug(f"Instantiated device: {_name}")
                        _device.findInstrument()
                        __logger.debug(f"Called findInstrument() on device: {_name}")
                        setattr(self, _name, _device)
                        __logger.debug(f"Device '{_name}' instantiated and attached as attribute.")
                    except Exception as e:
                        __logger.warning(f"Could not instantiate {_name}: {e}")

        __logger.debug("Device discovery and instantiation complete.")

    @QtCore.Property(str)
    def ComputerName(self) -> str:
        """
        Get the network name of the current computer (host).

        Returns:
            str: The local host name, or a fallback if unavailable.
        """
        __logger.debug("Retrieving ComputerName property...")
        host = QtNetwork.QHostInfo.localHostName()
        if host:
            __logger.debug(f"ComputerName resolved via QHostInfo: {host}")
            return host
        try:
            nodename = os.uname().nodename
            __logger.debug(f"ComputerName resolved via os.uname: {nodename}")
            return nodename
        except Exception as e:
            __logger.warning(f"os.uname() failed: {e}")
            import socket
            hostname = socket.gethostname()
            __logger.debug(f"ComputerName resolved via socket.gethostname: {hostname}")
            return hostname

    @QtCore.Property(str)
    def UserName(self) -> str:
        """
        Get the current user's name, derived from the home directory or environment.

        Returns:
            str: The user's name.
        """
        __logger.debug("Retrieving UserName property...")
        home_path = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.HomeLocation)
        if home_path:
            username = os.path.basename(home_path.rstrip("/\\"))
            __logger.debug(f"UserName resolved via home path: {username}")
            return username
        try:
            username = os.getlogin()
            __logger.debug(f"UserName resolved via os.getlogin: {username}")
            return username
        except Exception as e:
            __logger.warning(f"os.getlogin() failed: {e}")
            username = os.environ.get("USERNAME", "unknown")
            __logger.debug(f"UserName resolved via environment: {username}")
            return username

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when application settings are modified.

        This method is triggered when the settings are changed in the TesterApp.
        It can be extended to update device configurations or reload settings as needed.
        """
        __logger.debug("Settings modified, updating device manager.")

    @QtCore.Slot()
    def setup(self):
        """
        Prepare the device manager and devices before running tests.

        This method resets the MSO5000 device if present, ensuring a clean state before tests.
        """
        __logger.debug("Setting up the device manager.")
        mso = getattr(self, "MSO5000", None)
        if mso:
            __logger.debug("MSO5000 device found, resetting...")
            try:
                mso.reset()
                __logger.debug("MSO5000 device reset successfully.")
            except Exception as e:
                __logger.warning(f"Failed to reset MSO5000: {e}")
        else:
            __logger.debug("MSO5000 device not found during setup.")

    @QtCore.Slot()
    def test_setup(self):
        """
        Prepare the device manager and devices before each individual test.

        This method resets and clears the MSO5000 device if present, ensuring a clean state for each test.
        """
        __logger.debug("Setting up the device manager for testing.")
        mso = getattr(self, "MSO5000", None)
        if mso:
            __logger.debug("MSO5000 device found, resetting and clearing...")
            try:
                mso.reset()
                __logger.debug("MSO5000 device reset successfully.")
                clear_registers = getattr(mso, "clear_registers", None)
                if callable(clear_registers):
                    clear_registers()
                    __logger.debug("MSO5000 registers cleared.")
                clear = getattr(mso, "clear", None)
                if callable(clear):
                    clear()
                    __logger.debug("MSO5000 device cleared.")
            except Exception as e:
                __logger.warning(f"Error during test_setup for MSO5000: {e}")
        else:
            __logger.debug("MSO5000 device not found during test_setup.")

    @QtCore.Slot()
    def test_teardown(self):
        """
        Clean up after each individual test.

        This method can be extended to perform any necessary cleanup after a test completes.
        """
        __logger.debug("Tearing down the device manager settings for testing.")

    @QtCore.Slot()
    def teardown(self):
        """
        Clean up and reset devices after all tests.

        This method resets the MSO5000 device if present, ensuring devices are left in a safe state.
        """
        __logger.debug("Tearing down the device manager.")
        mso = getattr(self, "MSO5000", None)
        if mso:
            __logger.debug("MSO5000 device found, resetting...")
            try:
                mso.reset()
                __logger.debug("MSO5000 device reset successfully.")
            except Exception as e:
                __logger.warning(f"Failed to reset MSO5000 during teardown: {e}")
        else:
            __logger.debug("MSO5000 device not found during teardown.")
