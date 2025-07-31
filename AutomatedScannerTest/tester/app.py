# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore
import logging
from logging.handlers import RotatingFileHandler
import sys

from tester import __application__, __company__, __version__, __doc__
from tester.gui.gui import TesterWindow
from tester.manager.sequence import TestSequenceModel


class TesterSettings(QtCore.QSettings):
    """
    QSettings subclass with a custom signal for when settings are modified.
    Provides convenience methods for grouped settings access.
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
        if self.contains(key):
            value = self.value(key, defaultValue=default)
        else:
            self.setValue(key, default)
            self.sync()
            value = default
        self.endGroup()
        # Ensure the returned value is of the same type as default
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


class QtContextFilter(logging.Filter):
    """
    Logging filter that injects Qt context attributes into log records.
    """
    __slots__ = ()
    def filter(self, record):
        """
        Add Qt context attributes to the log record if missing.

        Args:
            record (logging.LogRecord): The log record.

        Returns:
            bool: Always True.
        """
        record.file = getattr(record, "file", "unknown")
        record.line = getattr(record, "line", -1)
        record.function = getattr(record, "function", "unknown")
        record.category = getattr(record, "category", "general")
        return True


class QtFormatter(logging.Formatter):
    """
    Custom logging formatter that appends Qt context information to log messages.
    """
    __slots__ = ()
    def format(self, record):
        """
        Format the log record with additional Qt context information.

        Args:
            record (logging.LogRecord): The log record.

        Returns:
            str: The formatted log message.
        """
        base = super().format(record)
        return f"{base} | {record.file}:{record.line} - {record.function} [{record.category}]"


class TesterApp(QtWidgets.QApplication):
    """
    Custom QApplication subclass for the AutomatedScannerTest tester GUI.

    Handles application-wide settings, logging, and command-line options.
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

        # Setup logging only once, using a standard application data folder
        self._setup_logging()

        # Set application properties
        self.setApplicationDisplayName(f"{__application__} v{__version__}")
        self.setApplicationName(__application__)
        self.setOrganizationName(__company__)
        self.setOrganizationDomain("pangolin.com")
        self.setApplicationVersion(__version__)
        self.setQuitOnLastWindowClosed(True)
        QtCore.qInstallMessageHandler(self.qt_message_handler)
        QtCore.qDebug("App initialized and settings applied")

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

    def _setup_logging(self):
        """
        Set up the RotatingFileHandler for logging in the standard application data folder.
        """
        self.__logger = logging.getLogger(__package__)
        self.__logger.setLevel(logging.DEBUG)
        if not logging.root.handlers:
            _stream_handler = logging.StreamHandler(sys.stdout)
            _stream_handler.setLevel(logging.INFO)
            _stream_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
            logging.root.addHandler(_stream_handler)
            logging.root.setLevel(logging.INFO)

        # Remove any existing file handler
        if hasattr(self, "_log_file_handler") and self._log_file_handler:
            logging.root.removeHandler(self._log_file_handler)
            self._log_file_handler.close()
            self._log_file_handler = None

        # Use a system directory for the log file (AppLocalDataLocation is cross-platform)
        log_dir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppLocalDataLocation)
        QtCore.QDir(log_dir).mkpath(".")
        log_file_path = QtCore.QDir(log_dir).filePath("tester.log")
        _file_handler = RotatingFileHandler(
            log_file_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
        )
        _file_handler.setFormatter(QtFormatter("%(asctime)s - %(levelname)s - %(message)s"))
        _file_handler.addFilter(QtContextFilter())
        logging.root.addHandler(_file_handler)
        self._log_file_handler = _file_handler
        self._log_file_path = log_file_path

    def onSettingsModified(self) -> None:
        """
        Read settings from QSettings and update the data directory if needed.
        If the data directory changes, reconfigure logging.
        """
        old_data_directory = self.DataDirectory
        new_data_directory = self.__settings.getSetting(
            "", "DataDirectory", str(old_data_directory)
        )
        if new_data_directory and old_data_directory and new_data_directory != old_data_directory:
            self._data_directory = new_data_directory
            self._setup_logging()
        else:
            self._data_directory = new_data_directory

    def qt_message_handler(self, mode: QtCore.QtMsgType, context: QtCore.QMessageLogContext, message: str) -> None:
        """
        Route Qt messages to the Python logging system with context.

        Args:
            mode (QtCore.QtMsgType): The type of Qt message.
            context (QtCore.QMessageLogContext): The context of the message.
            message (str): The message to log.
        """
        extra = {
            "file": getattr(context, "file", "unknown"),
            "line": getattr(context, "line", -1),
            "function": getattr(context, "function", "unknown"),
            "category": getattr(context, "category", "general"),
        }
        log_map = {
            QtCore.QtMsgType.QtDebugMsg: self.__logger.debug,
            QtCore.QtMsgType.QtInfoMsg: self.__logger.info,
            QtCore.QtMsgType.QtWarningMsg: self.__logger.warning,
            QtCore.QtMsgType.QtCriticalMsg: self.__logger.error,
            QtCore.QtMsgType.QtFatalMsg: self.__logger.critical,
        }
        log_func = log_map.get(mode)
        if log_func:
            log_func(message, extra=extra)
        else:
            self.__logger.warning(f"Unknown Qt message type: {mode} - {message}", extra=extra)

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance with the specified name.

        Args:
            name (str): The name of the logger.

        Returns:
            logging.Logger: The logger instance.
        """
        return self.__logger.getChild(name)

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
        ts = TestSequenceModel()
        return ts.run_nogui()
