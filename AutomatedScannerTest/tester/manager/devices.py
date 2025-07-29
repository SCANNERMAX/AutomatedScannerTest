# -*- coding: utf-8 -*-
from PySide6 import QtCore
import ctypes
import importlib
import inspect
import os
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
        else:
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")

        # Find all Device subclasses in tester.devices
        _device_module = importlib.import_module(Device.__module__)
        _device_folder = os.path.dirname(_device_module.__file__)

        py_files = [
            f
            for f in os.listdir(_device_folder)
            if f.endswith(".py") and not f.startswith("__")
        ]

        # Cache Device for issubclass checks
        device_class = Device

        for _filename in py_files:
            _module_name = f"tester.devices.{_filename[:-3]}"
            try:
                _module = importlib.import_module(_module_name)
            except Exception as e:
                self.__logger.warning(f"Could not import {_module_name}: {e}")
                continue

            # Use inspect.getmembers only once per module
            for _name, _obj in inspect.getmembers(_module, inspect.isclass):
                # Use direct module check to avoid duplicate imports
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
        """
        Returns the network name of the current computer (host) as a string.

        Returns:
            str: The hostname of the current computer.
        """
        return socket.gethostname()

    @property
    def UserName(self) -> str:
        """
        Retrieves the current user's full name if available, otherwise returns the login username.

        Attempts to obtain the user's display name using the Windows API `GetUserNameExW` with the NameDisplay format.
        If this fails, falls back to the username returned by `os.getlogin()` or `getpass.getuser()`.

        Returns:
            str: The user's display name or login username.
        """
        try:
            username = os.getlogin()
        except Exception:
            import getpass
            username = getpass.getuser()
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

    @tester._member_logger
    def setup(self):
        """
        Initializes the device manager before running tests.

        This method logs the setup process and resets the MSO5000 device if it exists.
        """
        self.__logger.debug("Setting up the device manager.")
        mso = getattr(self, "MSO5000", None)
        if mso:
            mso.reset()

    @tester._member_logger
    def test_setup(self):
        """
        Sets up the device manager before each test.

        This method logs the setup process, resets the MSO5000 device if it exists, and clears its registers and state if supported.
        """
        self.__logger.debug("Setting up the device manager for testing.")
        mso = getattr(self, "MSO5000", None)
        if mso:
            mso.reset()
            if hasattr(mso, "clear_registers"):
                mso.clear_registers()
            if hasattr(mso, "clear"):
                mso.clear()

    @tester._member_logger
    def test_teardown(self):
        """
        Cleans up the device manager after each test.

        This method logs the teardown process for test-specific settings.
        """
        self.__logger.debug("Tearing down the device manager settings for testing.")

    @tester._member_logger
    def teardown(self):
        """
        Performs cleanup operations after running tests.

        This method logs the teardown process and resets the MSO5000 device if it exists.
        """
        self.__logger.debug("Tearing down the device manager.")
        mso = getattr(self, "MSO5000", None)
        if mso:
            mso.reset()
