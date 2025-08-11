# -*- coding: utf-8 -*-
from PySide6 import QtCore
import logging

logger = logging.getLogger(__name__)

class Device(QtCore.QObject):
    """
    Device base class for hardware abstraction.

    Provides a common interface for all hardware devices, including settings management
    and a mechanism for device discovery. Subclasses should override findInstrument()
    to implement device-specific discovery logic.
    """

    def __init__(self, name: str):
        """
        Initialize the Device.

        Args:
            name (str): The name of the device, used for settings and logging.

        Raises:
            RuntimeError: If the application instance is not a TesterApp.

        Logging:
            - Logs initialization steps, application instance checks, settings retrieval,
              signal connection, and device initialization status.
        """
        logger.debug(f"[Device] Initializing device with name: {name}")
        super().__init__()
        self.Name = name
        app = QtCore.QCoreApplication.instance()
        if not (app and hasattr(app, "addSettingsToObject")):
            logger.critical(f"[Device] TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        app.addSettingsToObject(self)
        logger.debug(f"[Device] Device initialized successfully.")
        # Only call findInstrument if subclass has overridden it
        if type(self).findInstrument is not Device.findInstrument:
            logger.debug(f"[Device] Subclass has overridden findInstrument, calling it.")
            self.findInstrument()
        else:
            logger.debug(f"[Device] Using base findInstrument implementation.")

    @QtCore.Slot()
    def findInstrument(self):
        """
        Attempt to find and initialize the hardware instrument.

        Subclasses should override this method to implement device-specific discovery logic.

        Logging:
            - Warns if not implemented in subclass.
        """
        logger.warning(f"[Device] findInstrument() not implemented for this device.")

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when application settings are modified.

        Subclasses may override this to react to settings changes.

        Logging:
            - Logs when settings modification event is triggered.
        """
        logger.debug(f"[Device] Settings modified event triggered.")
