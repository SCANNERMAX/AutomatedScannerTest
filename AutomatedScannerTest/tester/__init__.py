# -*- coding: utf-8 -*-
"""This application runs a series of tests designed to validate the quality of Pangolin Laser System scanners."""
from PySide6 import QtCore
import logging

__logger = logging.getLogger(__name__)
__version__ = "1.1.0"
__company__ = "Pangolin Laser Systems"
__application__ = "Automated Scanner Test"
__doc__ = "This application runs a series of tests designed to validate the quality of Pangolin Laser System scanners."

class CancelToken(QtCore.QObject):
    """
    A simple token class to signal cancellation of an operation.

    Signals
    -------
    cancelledChanged(bool)
        Emitted when the cancelled state changes.

    Properties
    ----------
    cancelled : bool
        Indicates whether the operation has been cancelled.
    """

    cancelledChanged = QtCore.Signal(bool)

    def __init__(self, parent=None):
        """
        Initialize the CancelToken.

        Parameters
        ----------
        parent : QObject, optional
            The parent QObject.
        """
        super().__init__(parent)
        app = QtCore.QCoreApplication.instance()
        if app is None or app.__class__.__name__ != "TestApplication":
            raise RuntimeError("CancelToken must be used within a TestApplication context.")
        self._cancelled = False
        __logger.debug("CancelToken initialized with cancelled=False.")

    @QtCore.Property(bool, notify=cancelledChanged)
    def cancelled(self):
        """
        Get the cancelled state.

        Returns
        -------
        bool
            True if cancelled, False otherwise.
        """
        __logger.debug(f"CancelToken.cancelled accessed, current value: {self._cancelled}.")
        return self._cancelled

    @cancelled.setter
    def cancelled(self, value):
        """
        Set the cancelled state.

        Parameters
        ----------
        value : bool
            The new cancelled state.
        """
        if self._cancelled != value:
            __logger.debug(f"CancelToken.cancelled changed from {self._cancelled} to {value}.")
            self._cancelled = value
            self.cancelledChanged.emit(self._cancelled)

    @QtCore.Slot()
    def cancel(self):
        """
        Set the cancelled state to True.
        """
        __logger.debug("CancelToken.cancel() called.")
        self.cancelled = True

    @QtCore.Slot()
    def reset(self):
        """
        Reset the cancelled state to False.
        """
        __logger.debug("CancelToken.reset() called.")
        self.cancelled = False


