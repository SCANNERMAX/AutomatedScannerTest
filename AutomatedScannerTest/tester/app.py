# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore
import sys

from tester.manager.worker import TestWorker
from tester import __application__, __company__, __version__, __doc__
from tester.gui.gui import TesterWindow


class TesterSettings(QtCore.QSettings):
    settingsModified = QtCore.Signal()

    def getSetting(self, group: str, key: str, default=None):
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
    def DataDirectory(self) -> str:
        """
        Returns the current data directory used by the application.

        Returns:
            str: Path to the application's data directory.
        """
        return getattr(self, "_data_directory", None)

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
        self._data_directory = app_dir.filePath(__application__)

        self.__settings = TesterSettings(
            QtCore.QSettings.Format.IniFormat,
            QtCore.QSettings.Scope.SystemScope,
            __company__,
            __application__,
            self,
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
        _context = self.options.__class__.__name__
        self.options.setApplicationDescription(__doc__)

        options = [
            (
                ["d", "directory"],
                "Set the data directory.",
                "directory",
                str(self.DataDirectory),
            ),
            (["r", "run"], "Run test(s) in commandline mode.", None, None),
            (["l", "list"], "List the available tests.", None, None),
            (["s", "serial"], "The serial number on which to test.", "serial", ""),
            (["m", "model"], "The model number on which to test.", "model", ""),
            (["t", "test"], "The test to run.", "test", None),
            (["x", "exitcodes"], "Display exit codes and their meaning.", None, None),
        ]
        for names, desc, value_name, default in options:
            self.options.addOption(
                QtCore.QCommandLineOption(
                    names,
                    QtCore.QCoreApplication.translate(_context, desc),
                    value_name or "",
                    default or "",
                )
            )
        self.options.addHelpOption()
        self.options.addVersionOption()
        self.options.process(self)
        self._setup_qt_logging()

    def _setup_qt_logging(self):
        """
        Sets up Qt logging for the application.

        Initializes the log file, enables console logging for CLI mode,
        installs the custom Qt message handler, and deletes old log files.
        """
        log_dir = QtCore.QStandardPaths.writableLocation(
            QtCore.QStandardPaths.AppLocalDataLocation
        )
        QtCore.QDir(log_dir).mkpath(".")

        # Delete log files older than 30 days using Qt native code
        dir_obj = QtCore.QDir(log_dir)
        log_files = dir_obj.entryInfoList(["*.log"], QtCore.QDir.Files)
        now = QtCore.QDateTime.currentDateTime()
        for file_info in log_files:
            mtime = file_info.lastModified()
            if mtime.daysTo(now) > 30:
                QtCore.QFile.remove(file_info.filePath())

        # Generate log file name in log_YYYYmmdd_HHMMSS.log format
        timestamp = now.toString("yyyyMMdd_HHmmss")
        log_file_name = f"log_{timestamp}.log"
        log_file_path = QtCore.QDir(log_dir).filePath(log_file_name)
        self._qt_log_file = open(log_file_path, "a", encoding="utf-8")
        self._qt_log_file_path = log_file_path
        self._console_logging_enabled = self.options.isSet("run")
        QtCore.qInstallMessageHandler(self.qt_message_handler)
        QtCore.qInfo(f"Qt logging initialized. Log file: {log_file_path}")

    def onSettingsModified(self) -> None:
        """
        Slot called when application settings are modified.

        Updates the data directory from settings.
        """
        old_data_directory = self.DataDirectory
        self._data_directory = self.__settings.getSetting(
            "", "DataDirectory", str(old_data_directory)
        )

    def qt_message_handler(
        self, mode: QtCore.QtMsgType, context: QtCore.QMessageLogContext, message: str
    ) -> None:
        """
        Custom Qt message handler for logging and status message emission.

        Logs messages to file and optionally to console. Emits statusMessage signal
        for info, warning, and critical messages.

        Args:
            mode (QtCore.QtMsgType): The type of Qt message.
            context (QtCore.QMessageLogContext): Context of the message.
            message (str): The message text.
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
        if getattr(self, "_console_logging_enabled", True):
            print(full_msg)
        try:
            self._qt_log_file.write(full_msg + "\n")
            self._qt_log_file.flush()
        except Exception:
            pass

        # Emit statusMessage for info, warning, or critical
        if mode == QtCore.QtMsgType.QtInfoMsg:
            self.statusMessage.emit(full_msg)
        elif mode == QtCore.QtMsgType.QtWarningMsg:
            self.statusMessage.emit(full_msg)
        elif mode in (QtCore.QtMsgType.QtCriticalMsg, QtCore.QtMsgType.QtFatalMsg):
            self.statusMessage.emit(full_msg)

    def get_settings(self) -> TesterSettings:
        """
        Returns the application settings object.

        Returns:
            TesterSettings: The settings instance for the application.
        """
        return self.__settings


def main() -> int:
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
