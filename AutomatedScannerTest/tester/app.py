# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

from tester import __application__, __company__, __version__, __doc__
from tester.gui.gui import TesterWindow
from tester.manager.sequence import TestSequenceModel


class TesterSettings(QtCore.QSettings):
    """
    Subclass of QSettings with a custom signal for when settings are modified.
    """
    settingsModified = QtCore.Signal()


class QtContextFilter(logging.Filter):
    """
    Injects additional context attributes into log records for custom formatting.

    This filter ensures that every log record has the attributes 'file', 'line',
    'function', and 'category', which are used by the custom formatter to provide
    enhanced log traceability.
    """

    __slots__ = ()

    def filter(self, record):
        """
        Add context attributes to the log record if they are missing.

        Args:
            record (logging.LogRecord): The log record to filter.

        Returns:
            bool: Always True to allow the record to pass through.
        """
        record.file = getattr(record, "file", "unknown")
        record.line = getattr(record, "line", -1)
        record.function = getattr(record, "function", "unknown")
        record.category = getattr(record, "category", "general")
        return True


class QtFormatter(logging.Formatter):
    """
    Custom logging formatter that appends Qt context information to log messages.

    This formatter extends the base log message with file, line, function, and
    category information, if available.
    """

    __slots__ = ()

    def format(self, record):
        """
        Format the log record with additional Qt context information.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message.
        """
        base = super().format(record)
        return f"{base} | {record.file}:{record.line} - {record.function} [{record.category}]"


class TesterApp(QtWidgets.QApplication):
    """
    Custom QApplication subclass for the AutomatedScannerTest tester GUI.

    This class initializes the application with custom settings, logging, and
    command-line argument parsing. It also provides a property for the data
    directory and a custom Qt message handler for logging.
    """

    @property
    def DataDirectory(self) -> Path:
        """
        Get or create the root data directory for test results.

        Returns:
            Path: The data directory path.
        """
        return getattr(self, "_data_directory", None)

    def __init__(self, argv, *args, **kwargs):
        """
        Initialize the TesterApp instance.

        Sets up application settings, logging, and command-line options.

        Args:
            argv (list): List of command-line arguments.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        if QtWidgets.QApplication.instance() is not None:
            raise RuntimeError("Only one QApplication instance is allowed.")
        super().__init__(argv, *args, **kwargs)

        # Initialize settings and data directory
        self.__settings = TesterSettings(
            QtCore.QSettings.Format.IniFormat,
            QtCore.QSettings.Scope.SystemScope,
            __company__,
            __application__,
            self,
        )
        _path = Path(__file__).parent / "Test Data" / __application__
        self._data_directory = _path.resolve()
        self.__settings.settingsModified.connect(self.onSettingsModified)
        self.onSettingsModified()

        # Setup logging only once
        self.__logger = logging.getLogger(__package__)
        self.__logger.setLevel(logging.DEBUG)
        if not logging.root.handlers:
            _stream_handler = logging.StreamHandler(sys.stdout)
            _stream_handler.setLevel(logging.INFO)
            _stream_handler.setFormatter(
                logging.Formatter("%(levelname)s - %(message)s")
            )
            logging.root.addHandler(_stream_handler)
            logging.root.setLevel(logging.INFO)

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

        # Batch add options for maintainability
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
                value_name if value_name else "",
                default if value_name else "",
            )
            self.options.addOption(opt)

        self.options.addHelpOption()
        self.options.addVersionOption()
        self.options.process(self)

    def onSettingsModified(self) -> None:
        """
        Read settings from QSettings and move the log file if DataDirectory changes.

        This method checks if the data directory has changed, moves the log file if necessary,
        and ensures a RotatingFileHandler is set up for logging.
        """
        old_data_directory = getattr(self, "_data_directory", None)
        if self.__settings.contains("DataDirectory"):
            new_data_directory = Path(self.__settings.value("DataDirectory", type=str)).resolve()
            new_data_directory.mkdir(parents=True, exist_ok=True)
            QtCore.qDebug(f"Data directory set to: {new_data_directory}")
        else:
            new_data_directory = old_data_directory
            QtCore.qDebug("No DataDirectory setting found, using default.")

        # Move log file if DataDirectory changed
        if new_data_directory and old_data_directory and new_data_directory != old_data_directory:
            if self._log_file_handler and self._log_file_path:
                new_log_file_path = new_data_directory / self._log_file_path.name
                self._log_file_handler.close()
                try:
                    if self._log_file_path.exists():
                        self._log_file_path.replace(new_log_file_path)
                        self._log_file_path = new_log_file_path
                except Exception as e:
                    QtCore.qDebug(f"Failed to move log file: {e}")
                logging.root.removeHandler(self._log_file_handler)
                self._log_file_handler = None

        self._data_directory = new_data_directory

        # Ensure a RotatingFileHandler exists and is up to date
        if not self._log_file_handler:
            _file_path = self.DataDirectory / datetime.now().strftime("log_%Y%m%d_%H%M%S.log")
            _file_handler = RotatingFileHandler(
                _file_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
            )
            _file_handler.setFormatter(QtFormatter("%(asctime)s - %(levelname)s - %(message)s"))
            _file_handler.addFilter(QtContextFilter())
            logging.root.addHandler(_file_handler)
            self._log_file_handler = _file_handler
            self._log_file_path = _file_path

    def qt_message_handler(
        self, mode: QtCore.QtMsgType, context: QtCore.QMessageLogContext, message: str
    ) -> None:
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
            self.__logger.warning(
                f"Unknown Qt message type: {mode} - {message}", extra=extra
            )

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance with the specified name.
        Args:
            name (str): The name of the logger.
        Returns:
            logging.Logger: The logger instance.
        """
        return self.__logger.getLogger(name)

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

    This function initializes the TesterApp with command-line arguments,
    creates the main TesterWindow, starts the application event loop,
    and returns the exit code from the application.

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
