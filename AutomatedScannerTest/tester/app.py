# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore
import logging
from logging.handlers import RotatingFileHandler
import sys

from tester.manager.worker import TestWorker
from tester import __application__, __company__, __version__, __doc__, CancelToken
from tester.gui.gui import TesterWindow

logger = logging.getLogger(__name__)


class TesterSettings(QtCore.QSettings):
    """
    Extends QSettings to provide convenience methods for getting and setting grouped settings,
    with type conversion and a signal for when settings are modified.
    """

    settingsModified = QtCore.Signal()

    def getSetting(self, group: str, key: str, default=None):
        """
        Retrieve a setting value from a group, with type conversion and default value support.

        Args:
            group (str): The group name in the settings.
            key (str): The key name for the setting.
            default: The default value to use if the key does not exist.

        Returns:
            The value of the setting, converted to the type of default if provided.
        """
        if group:
            self.beginGroup(group)
        value = self.value(key, defaultValue=default) if self.contains(key) else default
        if not self.contains(key):
            self.setValue(key, default)
            self.sync()
        if group:
            self.endGroup()
        if default is not None and not isinstance(value, type(default)):
            try:
                value = type(default)(value)
            except Exception:
                value = default
        return value

    def setSetting(self, group: str, key: str, value):
        """
        Set a setting value in a group and emit a signal indicating modification.

        Args:
            group (str): The group name in the settings.
            key (str): The key name for the setting.
            value: The value to set.
        """
        if group:
            self.beginGroup(group)
        self.setValue(key, value)
        self.sync()
        if group:
            self.endGroup()
        self.settingsModified.emit()


class TesterApp(QtWidgets.QApplication):
    """
    Main application class for the Automated Scanner Tester.

    Handles application initialization, settings management, command-line parsing,
    logging setup, and message handling. Provides access to application-wide settings
    and data directory, and emits status messages for UI or CLI display.
    """

    statusMessage = QtCore.Signal(str)

    @property
    def ConfigurationPath(self) -> str:
        """
        Returns the current data directory used by the application.

        Returns:
            str: Path to the application's data directory.
        """
        return getattr(self, "_configuration_path", None)

    def __init__(self, argv, *args, **kwargs):
        """
        Initializes the TesterApp instance.

        Sets up application metadata, data directory, settings, command-line options,
        and logging. Ensures only one QApplication instance is created.

        Args:
            argv (list): Command-line arguments.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Raises:
            RuntimeError: If another QApplication instance already exists.
        """
        if QtWidgets.QApplication.instance() is not None:
            raise RuntimeError("Only one QApplication instance is allowed.")
        super().__init__(argv, *args, **kwargs)

        self.__settings = TesterSettings(
            QtCore.QSettings.Format.IniFormat,
            QtCore.QSettings.Scope.SystemScope,
            __company__,
            __application__,
        )
        self.__settings.settingsModified.connect(self.onSettingsModified)
        self.onSettingsModified()

        self.setApplicationDisplayName(f"{__application__} v{__version__}")
        self.setApplicationName(__application__)
        self.setOrganizationName(__company__)
        self.setOrganizationDomain("pangolin.com")
        self.setApplicationVersion(__version__)
        self.setQuitOnLastWindowClosed(True)

        self._setup_python_logging()
        self._setup_qt_logging()
        self._setup_commandline()
        self.aboutToQuit.connect(self.cleanup)

    class SafeFormatter(logging.Formatter):
        def format(self, record):
            # Provide defaults for custom fields if not present
            for attr, default in [
                (
                    "qt_file",
                    record.filename if hasattr(record, "filename") else "unknown",
                ),
                ("qt_line", record.lineno if hasattr(record, "lineno") else -1),
                (
                    "qt_func",
                    record.funcName if hasattr(record, "funcName") else "unknown",
                ),
                ("qt_category", "general"),
            ]:
                if not hasattr(record, attr):
                    setattr(record, attr, default)
            return super().format(record)

    def _setup_python_logging(self):
        """
        Sets up Python logging for the application.
        Logs everything to both file and console for all loggers.
        """
        log_dir = QtCore.QStandardPaths.writableLocation(
            QtCore.QStandardPaths.AppLocalDataLocation
        )
        now = QtCore.QDateTime.currentDateTime()
        timestamp = now.toString("yyyyMMdd_HHmmss")
        log_file_name = f"log_{timestamp}.log"
        log_file_path = QtCore.QDir(log_dir).filePath(log_file_name)

        # Get the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # Detailed formatter for file logging
        file_formatter = self.SafeFormatter(
            "%(asctime)s %(levelname)s: %(message)s [%(qt_file)s:%(qt_line)s - %(qt_func)s] [%(qt_category)s]"
        )

        # Console formatter (can be detailed or simple)
        console_formatter = self.SafeFormatter("%(levelname)s: %(message)s")

        # File handler (logs everything)
        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)

        # Console handler (logs everything)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)

        self._qt_log_file_path = log_file_path
        root_logger.info(f"Python logging initialized. Log file: {log_file_path}")

        # Delete log files older than 30 days
        dir_obj = QtCore.QDir(log_dir)
        log_files = dir_obj.entryInfoList(["*.log"], QtCore.QDir.Files)
        old_files = [f for f in log_files if f.lastModified().daysTo(now) > 30]
        for file_info in old_files:
            QtCore.QFile.remove(file_info.filePath())

    def _setup_qt_logging(self):
        """
        Installs the custom Qt message handler to redirect Qt logs to Python logger.
        """
        # Fix: PySide6 expects the message handler to be a static function
        QtCore.qInstallMessageHandler(self.qt_message_handler)

        QtCore.qInfo(
            f"Qt logging redirected to Python logger. Log file: {self._qt_log_file_path}"
        )

    def _setup_commandline(self):
        """
        Parses command-line arguments and sets up the application based on provided options.
        """
        self.options = QtCore.QCommandLineParser()
        context = self.options.__class__.__name__
        self.options.setApplicationDescription(__doc__)

        options = (
            (
                ["d", "directory"],
                "Set the data directory.",
                "directory",
                str(self.ConfigurationPath),
            ),
            (["r", "run"], "Run test(s) in commandline mode.", None, None),
            (["l", "list"], "List the available tests.", None, None),
            (["s", "serial"], "The serial number on which to test.", "serial", ""),
            (["m", "model"], "The model number on which to test.", "model", ""),
            (["t", "test"], "Select a single test to run.", "test", None),
            (["x", "exitcodes"], "Display exit codes and their meaning.", None, None),
        )
        addOption = self.options.addOption
        for names, desc, value_name, default in options:
            addOption(
                QtCore.QCommandLineOption(
                    names,
                    QtCore.QCoreApplication.translate(context, desc),
                    value_name or "",
                    default if default is not None else "",
                )
            )
        self.options.addHelpOption()
        self.options.addVersionOption()
        self.options.process(self)

    @staticmethod
    def qt_message_handler(mode, context, message):
        """
        Custom Qt message handler for logging and status message emission.
        Redirects Qt messages to Python logger.

        Args:
            mode (QtCore.QtMsgType): The type of Qt message.
            context (QtCore.QMessageLogContext): Context of the message.
            message (str): The message text.
        """
        # Fix: Static method, cannot use 'self'
        file = getattr(context, "file", "unknown")
        line = getattr(context, "line", -1)
        function = getattr(context, "function", "unknown")
        category = getattr(context, "category", "general")
        extra = {
            "qt_file": file,
            "qt_line": line,
            "qt_func": function,
            "qt_category": category,
        }

        level_map = {
            QtCore.QtMsgType.QtDebugMsg: logging.DEBUG,
            QtCore.QtMsgType.QtInfoMsg: logging.INFO,
            QtCore.QtMsgType.QtWarningMsg: logging.WARNING,
            QtCore.QtMsgType.QtCriticalMsg: logging.ERROR,
            QtCore.QtMsgType.QtFatalMsg: logging.CRITICAL,
        }
        level = level_map.get(mode, logging.INFO)
        log_msg = f"{message}"

        logger.log(level, log_msg, extra=extra)

    def addSettingsToObject(self, obj: QtCore.QObject) -> None:
        """
        Adds a QObject to the application settings.
        Args:
            obj (QtCore.QObject): The QObject to add to the settings.
        """
        if not isinstance(obj, QtCore.QObject):
            raise TypeError("obj must be an instance of QtCore.QObject")
        obj.settings = self.__settings
        _name = obj.__class__.__name__
        obj.getSetting = lambda key, default=None: self.__settings.getSetting(
            _name, key, default
        )
        obj.setSetting = lambda key, value: self.__settings.setSetting(
            _name, key, value
        )
        onSettingsModified = getattr(obj, "onSettingsModified", None)
        if callable(onSettingsModified):
            self.__settings.settingsModified.connect(onSettingsModified)
            onSettingsModified()

    @QtCore.Slot()
    def onSettingsModified(self) -> None:
        """
        Slot called when application settings are modified.

        Updates the data directory from settings.
        """
        logger.debug("[TesterApp] Settings modified.")
        settings_path = self.__settings.fileName()
        configuration_path = QtCore.QFileInfo(settings_path).absolutePath()
        self._configuration_path = configuration_path

    @QtCore.Slot()
    def cleanup(self) -> None:
        """
        Cleanup function called when the application is about to quit.
        """
        logger.info("Application is exiting. Performing cleanup...")
        self.__settings.sync()
        # Add any additional cleanup code here if necessary
        logger.info("Cleanup complete.")


def main() -> int:
    """
    Entry point for the Automated Scanner Tester application.

    Initializes the application, sets up either CLI or GUI mode, and starts the event loop.

    Returns:
        int: The exit code from the application.
    """
    app = TesterApp(sys.argv)
    if len(sys.argv) > 1:
        worker = TestWorker()
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        worker.closeSignal.connect(thread.quit)
        worker.closeSignal.connect(worker.deleteLater)
        thread.started.connect(worker.onRunCli)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        thread.wait()
    else:
        window = TesterWindow()
        app.statusMessage.connect(window.onUpdateStatus)
        window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
