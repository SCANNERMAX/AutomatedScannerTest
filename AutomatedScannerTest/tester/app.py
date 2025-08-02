# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore
import sys

from tester.manager.worker import TestWorker
from tester import __application__, __company__, __version__, __doc__
from tester.gui.gui import TesterWindow
from tester.manager.sequence import TestSequenceModel


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
    @property
    def DataDirectory(self) -> str:
        return getattr(self, "_data_directory", None)

    def __init__(self, argv, *args, **kwargs):
        if QtWidgets.QApplication.instance() is not None:
            raise RuntimeError("Only one QApplication instance is allowed.")
        super().__init__(argv, *args, **kwargs)

        base_dir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppLocalDataLocation)
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
            (["d", "directory"], "Set the data directory.", "directory", str(self.DataDirectory)),
            (["cli"], "Run in commandline mode.", None, None),
            (["l", "list"], "List the available tests.", None, None),
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

        self._setup_qt_logging()

    def _setup_qt_logging(self):
        log_dir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppLocalDataLocation)
        QtCore.QDir(log_dir).mkpath(".")
        log_file_path = QtCore.QDir(log_dir).filePath("tester_qt.log")
        self._qt_log_file = open(log_file_path, "a", encoding="utf-8")
        self._qt_log_file_path = log_file_path
        self._console_logging_enabled = not self.options.isSet("cli")
        QtCore.qInstallMessageHandler(self.qt_message_handler)
        QtCore.qInfo(f"Qt logging initialized. Log file: {log_file_path}")

    def onSettingsModified(self) -> None:
        old_data_directory = self.DataDirectory
        new_data_directory = self.__settings.getSetting(
            "", "DataDirectory", str(old_data_directory)
        )
        self._data_directory = new_data_directory

    def qt_message_handler(self, mode: QtCore.QtMsgType, context: QtCore.QMessageLogContext, message: str) -> None:
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

    def get_settings(self) -> TesterSettings:
        return self.__settings


def main() -> int:
    app = TesterApp(sys.argv)
    if app.options.isSet("list") or app.options.isSet("cli"):
        worker = TestWorker()
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run_cli)
        thread.finished.connect(app.quit)
        thread.start()
        return app.exec()
    else:
        window = TesterWindow()
        window.show()
        return app.exec()
