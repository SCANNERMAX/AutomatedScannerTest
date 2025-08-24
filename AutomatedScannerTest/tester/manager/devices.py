# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtNetwork
import importlib
import inspect
import logging
import os

from tester.devices.mso5000 import MSO5000
from tester.devices import Device

logger = logging.getLogger(__name__)

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
        logger.debug("[DeviceManager] Initializing DeviceManager...")
        app = QtCore.QCoreApplication.instance()
        if not (app and hasattr(app, "addSettingsToObject")):
            logger.critical("[DeviceManager] TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        app.addSettingsToObject(self)
        self.MSO5000 = MSO5000()

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
        import platform
        if platform.system() == "Windows":
            try:
                import ctypes
                GetUserNameEx = ctypes.windll.secur32.GetUserNameExW
                NameDisplay = 3
                size = ctypes.c_ulong(0)
                # First call to get the required buffer size
                if not GetUserNameEx(NameDisplay, None, ctypes.byref(size)):
                    # Now allocate buffer and get the name
                    nameBuffer = ctypes.create_unicode_buffer(size.value)
                    if GetUserNameEx(NameDisplay, nameBuffer, ctypes.byref(size)):
                        return nameBuffer.value
            except Exception:
                pass
        else:
            try:
                import pwd
                username = os.getenv("USER") or os.getenv("USERNAME") or os.path.basename(os.path.expanduser("~"))
                if username:
                    user_info = pwd.getpwnam(username)
                    return user_info.pw_gecos.split(',')[0]  # Full name is usually first part
            except Exception:
                pass
        return None

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when application settings are modified.

        This method is triggered when the settings are changed in the TesterApp.
        It can be extended to update device configurations or reload settings as needed.
        """
        pass

    def _reset_mso(self, context):
        """
        Helper method to reset the MSO5000 device.

        Args:
            context (str): Additional context for logging (e.g., during teardown).
        """
        mso = getattr(self, "MSO5000", None)
        if mso:
            reset_method = getattr(mso, "reset", None)
            if callable(reset_method):
                try:
                    reset_method()
                except Exception as e:
                    logger.warning(f"[DeviceManager] Failed to reset MSO5000{context}: {e}")

    @QtCore.Slot()
    def setup(self):
        """
        Prepare the device manager and devices before running tests.

        This method resets the MSO5000 device if present, ensuring a clean state before tests.
        """
        self._reset_mso("")

    @QtCore.Slot()
    def test_setup(self):
        """
        Prepare the device manager and devices before each individual test.

        This method resets and clears the MSO5000 device if present, ensuring a clean state for each test.
        """
        mso = getattr(self, "MSO5000", None)
        if mso:
            for method_name, log_msg in [
                ("reset", "Error during test_setup for MSO5000"),
                ("clear_registers", "Error clearing registers for MSO5000"),
                ("clear", "Error clearing MSO5000"),
            ]:
                method = getattr(mso, method_name, None)
                if callable(method):
                    try:
                        method()
                    except Exception as e:
                        logger.warning(f"[DeviceManager] {log_msg}: {e}")

    @QtCore.Slot()
    def test_teardown(self):
        """
        Clean up after each individual test.

        This method can be extended to perform any necessary cleanup after a test completes.
        """
        pass

    @QtCore.Slot()
    def teardown(self):
        """
        Clean up and reset devices after all tests.

        This method resets the MSO5000 device if present, ensuring devices are left in a safe state.
        """
        self._reset_mso(" during teardown")
