#-*- coding: utf-8 -*-
from PySide6 import QtCore
import ctypes
import importlib
import inspect
import os
import socket

import tester
from tester.devices import Device


class DeviceManager:
    """
    Manages and initializes all device instances used for automated scanner testing.

    Dynamically discovers all subclasses of the `Device` class within the `tester.devices` module,
    instantiates them with the provided settings, and attaches them as attributes to itself.
    Provides setup and teardown routines for preparing devices before and after tests.

    Args:
        settings (QtCore.QSettings): The settings object to be passed to each device instance.

    Attributes:
        ComputerName (str): The network name of the current computer (host).
        UserName (str): The current user's full name if available, otherwise the login username.
    """

    def __init__(self, settings: QtCore.QSettings):
        """
        Initialize the DeviceManager.

        Discovers and instantiates all Device subclasses in tester.devices, calling their
        find_instrument() method and attaching them as attributes.

        Args:
            settings (QtCore.QSettings): The settings object to be passed to each device instance.
        """
        self.__logger = tester._get_class_logger(self.__class__)
        self.__settings = settings

        # Efficiently discover and instantiate all Device subclasses in tester.devices
        _device_module = importlib.import_module(Device.__module__)
        _device_folder = os.path.dirname(_device_module.__file__)
        py_files = (f for f in os.listdir(_device_folder) if f.endswith(".py") and not f.startswith("__"))
        device_class = Device
        for _filename in py_files:
            _module_name = f"tester.devices.{_filename[:-3]}"
            try:
                _module = importlib.import_module(_module_name)
            except Exception as e:
                self.__logger.warning(f"Could not import {_module_name}: {e}")
                continue
            # Use a generator expression for class filtering
            for _name, _obj in inspect.getmembers(_module, inspect.isclass):
                if _obj.__module__ == _module.__name__ and issubclass(_obj, device_class) and _obj is not device_class:
                    try:
                        _device = _obj(self.__settings)
                        _device.find_instrument()
                        setattr(self, _name, _device)
                    except Exception as e:
                        self.__logger.warning(f"Could not instantiate {_name}: {e}")

    @property
    def ComputerName(self) -> str:
        """
        Returns the network name of the current computer (host).

        Returns:
            str: The hostname of the current computer.
        """
        return socket.gethostname()

    @property
    def UserName(self) -> str:
        """
        Retrieves the current user's full name if available, otherwise returns the login username.

        Tries Windows API GetUserNameExW, falls back to os.getlogin() or getpass.getuser().

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

        Resets MSO5000 if present.
        """
        self.__logger.info("Setting up the device manager...")
        mso = getattr(self, "MSO5000", None)
        if mso:
            mso.reset()

    @tester._member_logger
    def test_setup(self):
        """
        Sets up the device manager before each test.

        Resets and clears MSO5000 if present.
        """
        self.__logger.info("Setting up the device manager for testing...")
        mso = getattr(self, "MSO5000", None)
        if mso:
            mso.reset()
            # Use getattr with default to avoid repeated hasattr checks
            clear_registers = getattr(mso, "clear_registers", None)
            if callable(clear_registers):
                clear_registers()
            clear = getattr(mso, "clear", None)
            if callable(clear):
                clear()

    @tester._member_logger
    def test_teardown(self):
        """
        Cleans up the device manager after each test.
        """
        self.__logger.info("Tearing down the device manager settings for testing...")

    @tester._member_logger
    def teardown(self):
        """
        Performs cleanup operations after running tests.

        Resets MSO5000 if present.
        """
        self.__logger.info("Tearing down the device manager...")
        mso = getattr(self, "MSO5000", None)
        if mso:
            mso.reset()
