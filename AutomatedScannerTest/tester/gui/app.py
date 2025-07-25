from datetime import datetime
from PySide6 import QtWidgets, QtCore
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import os

import tester


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
        if hasattr(self, "_data_directory"):
            return self._data_directory

        _data_path = os.path.join(os.path.dirname(__file__), "Test Data", tester.__application__)
        if self.settings.contains("DataDirectory"):
            _data_path = self.settings.value("DataDirectory", _data_path, type=str)
        _data_directory = Path(_data_path).resolve()
        _data_directory.mkdir(parents=True, exist_ok=True)
        self._data_directory = _data_directory
        return self._data_directory

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
        self.settings = QtCore.QSettings(
            QtCore.QSettings.Format.IniFormat,
            QtCore.QSettings.Scope.SystemScope,
            tester.__company__,
            tester.__application__,
            self,
        )

        # Setup logging only once
        self.qt_logger = logging.getLogger("Qt")
        self.qt_logger.setLevel(logging.DEBUG)
        _formatter = QtFormatter("%(asctime)s - %(levelname)s - %(message)s")
        _context_filter = QtContextFilter()

        if not logging.root.handlers:
            _stream_handler = logging.StreamHandler(sys.stdout)
            _stream_handler.setLevel(logging.INFO)
            _stream_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
            logging.root.addHandler(_stream_handler)
            logging.root.setLevel(logging.INFO)

        if not any(isinstance(h, RotatingFileHandler) for h in logging.root.handlers):
            _file_path = self.DataDirectory / datetime.now().strftime("log_%Y%m%d_%H%M%S.log")
            _file_handler = RotatingFileHandler(
                _file_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
            )
            _file_handler.setFormatter(_formatter)
            _file_handler.addFilter(_context_filter)
            logging.root.addHandler(_file_handler)

        # Set application properties
        self.setApplicationDisplayName(f"{tester.__application__} v{tester.__version__}")
        self.setApplicationName(tester.__application__)
        self.setOrganizationName(tester.__company__)
        self.setOrganizationDomain("pangolin.com")
        self.setApplicationVersion(tester.__version__)
        self.setQuitOnLastWindowClosed(True)
        QtCore.qInstallMessageHandler(self.qt_message_handler)
        QtCore.qDebug("App initialized and settings applied")

        # Command line options
        self.options = QtCore.QCommandLineParser()
        _context = self.options.__class__.__name__
        self.options.setApplicationDescription(tester.__doc__)

        # Batch add options for maintainability
        options = [
            (["d", "directory"], "Set the data directory.", "directory", str(self.DataDirectory)),
            (["s", "serial"], "The serial number on which to test.", "serial", ""),
            (["m", "model"], "The model number on which to test.", "model", ""),
            (["t", "test"], "The test to run.", "test", None),
            (["l", "list"], "List the available tests.", None, None),
            (["r", "run"], "Run the tests.", None, None),
            (["g", "nogui"], "Disable the GUI.", "gui", "false"),
        ]
        for names, desc, value_name, default in options:
            if value_name is not None:
                self.options.addOption(
                    QtCore.QCommandLineOption(
                        names,
                        QtCore.QCoreApplication.translate(_context, desc),
                        value_name,
                        default,
                    )
                )
            else:
                self.options.addOption(
                    QtCore.QCommandLineOption(
                        names,
                        QtCore.QCoreApplication.translate(_context, desc),
                    )
                )

        self.options.addHelpOption()
        self.options.addVersionOption()
        self.options.process(self)

    def qt_message_handler(
        self,
        mode: QtCore.QtMsgType,
        context: QtCore.QMessageLogContext,
        message: str
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
            QtCore.QtMsgType.QtDebugMsg: self.qt_logger.debug,
            QtCore.QtMsgType.QtInfoMsg: self.qt_logger.info,
            QtCore.QtMsgType.QtWarningMsg: self.qt_logger.warning,
            QtCore.QtMsgType.QtCriticalMsg: self.qt_logger.error,
            QtCore.QtMsgType.QtFatalMsg: self.qt_logger.critical,
        }
        log_func = log_map.get(mode)
        if log_func:
            log_func(message, extra=extra)
        else:
            self.qt_logger.warning(f"Unknown Qt message type: {mode} - {message}", extra=extra)
