# -*- coding: utf-8 -*-
from PySide6 import QtCore
import ctypes
import importlib
import inspect
import socket

import tester
from tester.devices import Device


class DeviceManager(QtCore.QObject):
    """
    DeviceManager is responsible for managing and initializing all device instances used for automated scanner testing.

    It dynamically discovers all subclasses of the `Device` class within the `tester.devices` module, instantiates them with the provided settings, and attaches them as attributes to itself. The class also provides setup and teardown routines for preparing devices before and after tests, with logging at each stage.

    Attributes:
        ComputerName (str): Returns the network name of the current computer (host).
        UserName (str): Returns the current user's full name if available, otherwise the login username.

    Methods:
        __init__(settings: QtCore.QSettings):
            Initializes the DeviceManager, discovers and instantiates all Device subclasses, and sets up logging.
        setup():
            Prepares the device manager and devices before running tests, including resetting the MSO5000 device.
        test_setup():
            Prepares the device manager and devices before each individual test, including resetting the MSO5000 device.
        test_teardown():
            Cleans up after each individual test.
        teardown():
            Cleans up and resets devices after tests, including resetting the MSO5000 device.
    """

    def __init__(self):
        """
        Initializes the DeviceManager by setting up logging, storing the provided settings, and dynamically discovering and instantiating all subclasses of `Device` found in the `tester.devices` module.

        Each discovered device is instantiated with the provided settings and set as an attribute of the DeviceManager instance.

        Args:
            settings (QtCore.QSettings): The settings object to be passed to each device instance.

        Raises:
            Logs a warning if any device module cannot be imported or instantiated.
        """
        app = QtCore.QCoreApplication.instance()
        if app.__class__.__name__ == "TesterApp":
            self.__logger = app.get_logger(self.__class__.__name__)
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
        else:
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")

        # Find all Device subclasses in tester.devices using Qt for file system access
        _device_module = importlib.import_module(Device.__module__)
        _device_folder = QtCore.QFileInfo(_device_module.__file__).absolutePath()

        dir_obj = QtCore.QDir(_device_folder)
        py_files = [f for f in dir_obj.entryList(["*.py"], QtCore.QDir.Files)
                    if not f.startswith("__")]

        device_class = Device

        for _filename in py_files:
            _module_name = f"tester.devices.{_filename[:-3]}"
            try:
                _module = importlib.import_module(_module_name)
            except Exception as e:
                self.__logger.warning(f"Could not import {_module_name}: {e}")
                continue

            for _name, _obj in inspect.getmembers(_module, inspect.isclass):
                if (
                    _obj.__module__ == _module.__name__
                    and issubclass(_obj, device_class)
                    and _obj is not device_class
                ):
                    try:
                        _device = _obj()
                        _device.findInstrument()
                        setattr(self, _name, _device)
                    except Exception as e:
                        self.__logger.warning(f"Could not instantiate {_name}: {e}")

    @property
    def ComputerName(self) -> str:
        return socket.gethostname()

    @property
    def UserName(self) -> str:
        try:
            import getpass
            username = getpass.getuser()
        except Exception:
            username = "unknown"
        buffer = ctypes.create_unicode_buffer(1024)
        size = ctypes.c_ulong(len(buffer))
        try:
            windll = getattr(ctypes, "windll", None)
            if windll and hasattr(windll, "secur32"):
                if windll.secur32.GetUserNameExW(3, buffer, ctypes.byref(size)):
                    return buffer.value
        except Exception:
            pass
        return username

    def onSettingsModified(self):
        self.__logger.debug("Settings modified, updating device manager.")

    def setup(self):
        self.__logger.debug("Setting up the device manager.")
        mso = getattr(self, "MSO5000", None)
        if mso:
            mso.reset()

    def test_setup(self):
        self.__logger.debug("Setting up the device manager for testing.")
        mso = getattr(self, "MSO5000", None)
        if mso:
            mso.reset()
            if hasattr(mso, "clear_registers"):
                mso.clear_registers()
            if hasattr(mso, "clear"):
                mso.clear()

    
    def test_teardown(self):
        self.__logger.debug("Tearing down the device manager settings for testing.")

    
    def teardown(self):
        self.__logger.debug("Tearing down the device manager.")
        mso = getattr(self, "MSO5000", None)
        if mso:
            mso.reset()
