# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore
import sys
import logging
from logging.handlers import RotatingFileHandler

from tester.manager.worker import TestWorker
from tester import __application__, __company__, __version__, __doc__
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
    __logger = logger

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

        base_dir = QtCore.QStandardPaths.writableLocation(
            QtCore.QStandardPaths.AppLocalDataLocation
        )
        app_dir = QtCore.QDir(base_dir)
        app_dir.mkpath(__application__)
        self._configuration_path = app_dir.filePath(__application__)

        # Fix: Do not pass 'self' as parent to QSettings, as it is not supported.
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

        self.options = QtCore.QCommandLineParser()
        context = self.options.__class__.__name__
        self.options.setApplicationDescription(__doc__)

        options = (
            (["d", "directory"], "Set the data directory.", "directory", str(self.ConfigurationPath)),
            (["r", "run"], "Run test(s) in commandline mode.", None, None),
            (["l", "list"], "List the available tests.", None, None),
            (["s", "serial"], "The serial number on which to test.", "serial", ""),
            (["m", "model"], "The model number on which to test.", "model", ""),
            (["t", "test"], "The test to run.", "test", None),
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
        self._setup_python_logging()
        self._setup_qt_logging()

    def _setup_python_logging(self):
        """
        Sets up Python logging for the application.
        """
        log_dir = self.ConfigurationPath
        now = QtCore.QDateTime.currentDateTime()
        timestamp = now.toString("yyyyMMdd_HHmmss")
        log_file_name = f"log_{timestamp}.log"
        log_file_path = QtCore.QDir(log_dir).filePath(log_file_name)

        # Configure root logger
        self.__logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [%(filename)s:%(lineno)d - %(funcName)s]"
        )

        # File handler (logs everything)
        file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        self.__logger.addHandler(file_handler)

        # Console handler (does not show debug messages)
        if self.options.isSet("run"):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)  # Only show INFO and above
            self.__logger.addHandler(console_handler)

        self._qt_log_file_path = log_file_path
        self.__logger.info(f"Python logging initialized. Log file: {log_file_path}")

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

        QtCore.qInfo(f"Qt logging redirected to Python logger. Log file: {self._qt_log_file_path}")

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
        file = getattr(context, 'file', 'unknown')
        line = getattr(context, 'line', -1)
        function = getattr(context, 'function', 'unknown')
        category = getattr(context, 'category', 'general')
        extra = {'fileName': file, 'lineno': line, 'funcName': function}

        level_map = {
            QtCore.QtMsgType.QtDebugMsg: logging.DEBUG,
            QtCore.QtMsgType.QtInfoMsg: logging.INFO,
            QtCore.QtMsgType.QtWarningMsg: logging.WARNING,
            QtCore.QtMsgType.QtCriticalMsg: logging.ERROR,
            QtCore.QtMsgType.QtFatalMsg: logging.CRITICAL,
        }
        level = level_map.get(mode, logging.INFO)
        log_msg = f"{message} [{category}]"

        logger.log(level, log_msg, extra=extra)

    def onSettingsModified(self) -> None:
        """
        Slot called when application settings are modified.

        Updates the data directory from settings.
        """
        old_data_directory = self.ConfigurationPath
        self._configuration_path = self.__settings.getSetting(
            "", "DataDirectory", str(old_data_directory)
        )

    def get_settings(self) -> TesterSettings:
        """
        Returns the application settings object.

        Returns:
            TesterSettings: The settings instance for the application.
        """
        return self.__settings


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
        thread.started.connect(worker.run_cli)
        thread.finished.connect(app.quit)
        thread.start()
    else:
        window = TesterWindow()
        app.statusMessage.connect(window.updateStatus)
        window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
