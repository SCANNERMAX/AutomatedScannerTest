import ctypes
from PySide6 import QtCore
import importlib
import inspect
import os
import socket
import time

import tester
from tester.devices import Device


class DeviceManager:
    """
    DeviceManager is responsible for managing and initializing all device instances used for automated scanner testing. It dynamically discovers all subclasses of the `Device` class within the `tester.devices` module, instantiates them with the provided settings, and attaches them as attributes to itself. The class also provides setup and teardown routines for preparing devices before and after tests, with logging at each stage.
    Attributes:
        ComputerName (str): Returns the network name of the current computer (host).
    Methods:
        __init__(settings: QtCore.QSettings):
            Initializes the DeviceManager, discovers and instantiates all Device subclasses, and sets up logging.
        setup():
            Prepares the device manager and devices before running tests, including resetting the MSO5000 device.
        test_setup():
            Prepares the device manager and devices before each individual test, including resetting the MSO5000 device.
        teardown():
            Cleans up and resets devices after tests, including resetting the MSO5000 device.
    """

    def __init__(self, settings: QtCore.QSettings):
        """
        Initializes the station by setting up logging, storing the provided settings, and dynamically discovering and instantiating all subclasses of `Device` found in the `tester.devices` module. Each discovered device is instantiated with the provided settings and set as an attribute of the station instance.
        Args:
            settings (QtCore.QSettings): The settings object to be passed to each device instance.
        Raises:
            Logs a warning if any device module cannot be imported.
        """
        self.__logger = tester._get_class_logger(self.__class__)
        self.__settings = settings

        # Find all Device subclasses in tester.devices
        _device_module = importlib.import_module(Device.__module__)
        _device_folder = os.path.dirname(_device_module.__file__)

        for _filename in os.listdir(_device_folder):
            if _filename.endswith(".py") and not _filename.startswith("__"):
                _module_name = f"tester.devices.{_filename[:-3]}"
                try:
                    _module = importlib.import_module(_module_name)
                except Exception as e:
                    self.__logger.warning(f"Could not import {_module_name}: {e}")
                    continue

                for _name, _obj in inspect.getmembers(_module, inspect.isclass):
                    if issubclass(_obj, Device) and _obj is not Device:
                        _device = _obj(self.__settings)
                        setattr(self, _name, _device)

    @property
    def ComputerName(self) -> str:
        """
        Returns the network name of the current computer (host) as a string.

        Returns:
            str: The hostname of the machine where this code is running.
        """
        return socket.gethostname()

    @property
    def UserName(self) -> str:
        """
        Retrieves the current user's full name if available, otherwise returns the login username.

        Attempts to obtain the user's display name using the Windows API `GetUserNameExW` with the NameDisplay format.
        If this fails, falls back to the username returned by `os.getlogin()`.

        Returns:
            str: The user's display name or login username.
        """
        username = os.getlogin()
        buffer = ctypes.create_unicode_buffer(1024)
        size = ctypes.c_ulong(len(buffer))
        if ctypes.windll.secur32.GetUserNameExW(3, buffer, ctypes.byref(size)):
            return buffer.value
        return username

    @tester._member_logger
    def setup(self):
        """
        Initializes the device manager before running tests.

        This method logs the setup process, resets the MSO5000 device, and waits for 10 seconds to ensure the device is ready.
        Can be overridden in subclasses to perform additional setup steps.
        """
        self.__logger.info("Setting up the device manager...")
        self.MSO5000.reset()
        # This method can be overridden in subclasses to perform additional setup

    @tester._member_logger
    def test_setup(self):
        """
        Sets up the device manager before each test.

        This method logs the setup process, resets the MSO5000 device, and waits for 10 seconds to ensure the device is ready.
        Subclasses can override this method to perform additional setup steps as needed.
        """
        self.__logger.info("Setting up the device manager for testing...")
        # This method can be overridden in subclasses to perform additional setup
        self.MSO5000.reset()
        self.MSO5000.clear_registers()
        self.MSO5000.clear()

    @tester._member_logger
    def test_teardown(self):
        self.__logger.info("Tearing down the device manager settings for testing...")

    @tester._member_logger
    def teardown(self):
        """
        Performs cleanup operations after running tests.

        This method logs the teardown process, resets the MSO5000 device, and waits for 10 seconds to ensure proper reset.
        Subclasses can override this method to implement additional cleanup procedures.
        """
        self.__logger.info("Tearing down the device manager...")
        self.MSO5000.reset()
        # This method can be overridden in subclasses to perform additional cleanup
