# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore
import sys

from AutomatedScannerTest.tester.manager.worker import TestWorker
from tester import __application__, __company__, __version__, __doc__
from tester.gui.gui import TesterWindow
from tester.manager.sequence import TestSequenceModel


class TesterSettings(QtCore.QSettings):
    """
    QSettings subclass with a custom signal for when settings are modified.
    Provides convenience methods for grouped settings access.

    Signals
    -------
    settingsModified : Signal
        Emitted when a setting is modified.

    Methods
    -------
    getSetting(group, key, default=None)
        Get a setting value from a specific group, or set and return the default if not present.
    setSetting(group, key, value)
        Set a setting value in a specific group and emit the settingsModified signal.
    """
    settingsModified = QtCore.Signal()

    def getSetting(self, group: str, key: str, default=None):
        """
        Get a setting value from a specific group. If not present, write the default value.

        Args:
            group (str): The group name in QSettings.
            key (str): The key to retrieve.
            default: The default value to set and return if the key is not present.

        Returns:
            The value from QSettings, or the default if not present, cast to the type of default.
        """
        self.beginGroup(group)
        value = self.value(key, defaultValue=default) if self.contains(key) else default
        if not self.contains(key):
            self.setValue(key, default)
            self.sync()
        self.endGroup()
        if default is not None and not isinstance(value, type(default)):
            try:
                value = type(default)(value)
            except Exception:
                value = default
        return value

    def setSetting(self, group: str, key: str, value):
        """
        Set a setting value in a specific group and emit the settingsModified signal.

        Args:
            group (str): The group name in QSettings.
            key (str): The key to set.
            value: The value to set.
        """
        self.beginGroup(group)
        self.setValue(key, value)
        self.sync()
        self.endGroup()
        self.settingsModified.emit()


class TesterApp(QtWidgets.QApplication):
    """
    Custom QApplication subclass for the AutomatedScannerTest tester GUI.

    Handles application-wide settings, logging, and command-line options.

    Properties
    ----------
    DataDirectory : str
        The current data directory used by the application.

    Methods
    -------
    __init__(argv, *args, **kwargs)
        Initialize the TesterApp instance.
    _setup_qt_logging()
        Set up Qt logging to both console and a log file.
    onSettingsModified()
        Read settings from QSettings and update the data directory if needed.
    qt_message_handler(mode, context, message)
        Route Qt messages to both the console and a log file with context.
    get_settings()
        Get the application settings.
    """

    @property
    def DataDirectory(self) -> str:
        """
        Returns the current data directory used by the application.

        Returns:
            str: The data directory path.
        """
        return getattr(self, "_data_directory", None)

    def __init__(self, argv, *args, **kwargs):
        """
        Initialize the TesterApp instance.

        Args:
            argv (list): Command-line arguments.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Raises:
            RuntimeError: If more than one QApplication instance is created.
        """
        if QtWidgets.QApplication.instance() is not None:
            raise RuntimeError("Only one QApplication instance is allowed.")
        super().__init__(argv, *args, **kwargs)

        # Use QDir for data directory (standard application data folder)
        base_dir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppLocalDataLocation)
        app_dir = QtCore.QDir(base_dir)
        app_dir.mkpath(__application__)
        self._data_directory = app_dir.filePath(__application__)

        # Initialize settings
        self.__settings = TesterSettings(
            QtCore.QSettings.Format.IniFormat,
            QtCore.QSettings.Scope.SystemScope,
            __company__,
            __application__,
            self,
        )
        self.__settings.settingsModified.connect(self.onSettingsModified)
        self.onSettingsModified()

        # Set application properties
        self.setApplicationDisplayName(f"{__application__} v{__version__}")
        self.setApplicationName(__application__)
        self.setOrganizationName(__company__)
        self.setOrganizationDomain("pangolin.com")
        self.setApplicationVersion(__version__)
        self.setQuitOnLastWindowClosed(True)

        # Setup Qt logging to console and file
        self._setup_qt_logging()

        # Command line options
        self.options = QtCore.QCommandLineParser()
        _context = self.options.__class__.__name__
        self.options.setApplicationDescription(__doc__)

        options = [
            (["d", "directory"], "Set the data directory.", "directory", str(self.DataDirectory)),
            (["gui"], "Disable the GUI.", None, None),
            (["l", "list"], "List the available tests.", None, None),
            (["r", "run"], "Run the tests.", None, None),
            (["s", "serial"], "The serial number on which to test.", "serial", ""),
            (["m", "model"], "The model number on which to test.", "model", ""),
            (["t", "test"], "The test to run.", "test", None),
        ]
        for names, desc, value_name, default in options:
            opt = QtCore.QCommandLineOption(
                names,
                QtCore.QCoreApplication.translate(_context, desc),
                value_name or "",
                default or "",
            )
            self.options.addOption(opt)

        self.options.addHelpOption()
        self.options.addVersionOption()
        self.options.process(self)

    def _setup_qt_logging(self):
        """
        Set up Qt logging to both console and a log file.
        """
        log_dir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppLocalDataLocation)
        QtCore.QDir(log_dir).mkpath(".")
        log_file_path = QtCore.QDir(log_dir).filePath("tester_qt.log")
        self._qt_log_file = open(log_file_path, "a", encoding="utf-8")
        self._qt_log_file_path = log_file_path
        QtCore.qInstallMessageHandler(self.qt_message_handler)
        QtCore.qInfo(f"Qt logging initialized. Log file: {log_file_path}")

    def onSettingsModified(self) -> None:
        """
        Read settings from QSettings and update the data directory if needed.
        """
        old_data_directory = self.DataDirectory
        new_data_directory = self.__settings.getSetting(
            "", "DataDirectory", str(old_data_directory)
        )
        if new_data_directory and old_data_directory and new_data_directory != old_data_directory:
            self._data_directory = new_data_directory
        else:
            self._data_directory = new_data_directory

    def qt_message_handler(self, mode: QtCore.QtMsgType, context: QtCore.QMessageLogContext, message: str) -> None:
        """
        Route Qt messages to both the console and a log file with context.

        Args:
            mode (QtCore.QtMsgType): The type of Qt message.
            context (QtCore.QMessageLogContext): The context of the message.
            message (str): The message to log.
        """
        msg = f"{message} | {getattr(context, 'file', 'unknown')}:{getattr(context, 'line', -1)} - {getattr(context, 'function', 'unknown')} [{getattr(context, 'category', 'general')}]"
        prefix = {
            QtCore.QtMsgType.QtDebugMsg: "DEBUG",
            QtCore.QtMsgType.QtInfoMsg: "INFO",
            QtCore.QtMsgType.QtWarningMsg: "WARNING",
            QtCore.QtMsgType.QtCriticalMsg: "CRITICAL",
            QtCore.QtMsgType.QtFatalMsg: "FATAL",
        }.get(mode, "LOG")
        full_msg = f"{prefix}: {msg}"
        print(full_msg)
        try:
            self._qt_log_file.write(full_msg + "\n")
            self._qt_log_file.flush()
        except Exception:
            pass

    def get_settings(self) -> TesterSettings:
        """
        Get the application settings.

        Returns:
            TesterSettings: The settings instance.
        """
        return self.__settings


def main() -> int:
    """
    Main entry point for the GUI tester application.

    Returns:
        int: The exit code from the application event loop.
    """
    app = TesterApp(sys.argv)
    if app.options.isSet("gui"):
        window = TesterWindow()
        window.show()
        return app.exec()
    else:
        # Launch worker and start a test sequence
        worker = TestWorker(TestSequenceModel())
        worker.start()
        worker.wait()  # Wait for the worker to finish
        return 0
