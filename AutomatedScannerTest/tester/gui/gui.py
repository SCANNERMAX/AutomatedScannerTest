# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtGui, QtWidgets
import logging

from tester import CancelToken
from tester.gui.settings import SettingsDialog
from tester.gui.tester_ui import Ui_TesterWindow
from tester.manager.worker import TestWorker

_SERIAL_RE = QtCore.QRegularExpression(r"^[A-Z]{2}[0-9]{6}$")
logger = logging.getLogger(__name__)


class TesterWindow(QtWidgets.QMainWindow):
    """
    Main Qt application window for the Automated Scanner Test GUI.

    This window manages the user interface, user actions, and coordinates with the TestSequence model and worker.
    It provides actions for opening, saving, and reporting test data, as well as starting and stopping tests.
    The window uses Qt's property and signal/slot system for integration with the rest of the application.
    """

    signalGenerateReport = QtCore.Signal(str)
    """Signal emitted to generate a report, with the file path as argument."""

    signalLoadData = QtCore.Signal(str)
    """Signal emitted to load test data from a file."""

    signalSaveData = QtCore.Signal(str)
    """Signal emitted to save test data to a file."""

    signalStartTest = QtCore.Signal(str, str, str)
    """Signal emitted to start a test, with serial number, model name, and an extra argument."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the TesterWindow, set up the UI, connect signals, and configure logging.

        Args:
            *args: Positional arguments for QMainWindow.
            **kwargs: Keyword arguments for QMainWindow.

        Raises:
            RuntimeError: If the application instance is not a TesterApp.
        """
        super().__init__(*args, **kwargs)

        logger.debug(f"[TesterWindow] Initializing TesterWindow...")
        app = QtCore.QCoreApplication.instance()
        if not (app and hasattr(app, "addSettingsToObject")):
            logger.critical(f"[TesterWindow] TesterApp instance not found.")
            raise RuntimeError(
                "TesterApp instance not found. Ensure the application is initialized correctly."
            )
        app.addSettingsToObject(self)
        app.statusMessage.connect(self.updateStatus)
        logger.debug(f"[TesterWindow] Connected to TesterApp instance and settings.")
        self.__cancel = CancelToken()
        self.worker = TestWorker(self.__cancel)
        logger.debug(f"[TesterWindow] TestWorker initialized.")

        options = getattr(app, "options", None)
        if options and options.isSet("gui"):
            self.ui = Ui_TesterWindow()
            self.ui.setupUi(self)
            logger.debug(f"[TesterWindow] UI setup complete.")
            self.ui.tableSequence.setColumnWidth(0, self.firstColumnWidth)
            self.ui.tableSequence.setColumnWidth(1, self.secondColumnWidth)
            self.ui.tableSequence.verticalHeader().setVisible(False)

            # Connect UI signals using a loop for efficiency
            actions_slots = [
                (self.ui.actionAbout, self.onAbout),
                (self.ui.actionExit, self.onExit),
                (self.ui.actionOpen, self.onOpen),
                (self.ui.actionReport, self.onReport),
                (self.ui.actionSave, self.onSave),
                (self.ui.actionSettings, self.onSettings),
                (self.ui.actionStart, self.onStartTest),
                (self.ui.actionStop, self.onStopTest),
            ]
            for action, slot in actions_slots:
                action.triggered.connect(slot)
                logger.debug(
                    f"Connected UI action {action.objectName()} to slot {slot.__name__}."
                )
            self.ui.tableSequence.selectionModel().selectionChanged.connect(
                self.on_tableSequence_selectionChanged
            )
            logger.debug(f"[TesterWindow] Connected tableSequence selection model.")

            # Map worker signals to UI slots
            label_signal_map = {
                self.worker.computerNameChanged: self.ui.labelComputerName.setText,
                self.worker.durationChanged: self.ui.labelDuration.setText,
                self.worker.endTimeChanged: self.ui.labelEndTime.setText,
                self.worker.modelNameChanged: self.ui.labelModelName.setText,
                self.worker.serialNumberChanged: self.ui.labelSerialNumber.setText,
                self.worker.startTimeChanged: self.ui.labelStartTime.setText,
                self.worker.statusChanged: self.ui.labelStatus.setText,
                self.worker.testerNameChanged: self.ui.labelTesterName.setText,
                self.worker.startedTest: self.onTestStarted,
                self.worker.finishedTest: self.onTestFinished,
                self.worker.finishedTesting: self.onTestingComplete,
                self.worker.finishedGeneratingReport: self.onFinishedGeneratingReport,
                self.worker.finishedLoadingData: self.onFinishedLoadingData,
                self.worker.finishedSavingData: self.onFinishedSavingData,
            }
            for signal, slot in label_signal_map.items():
                # Fix: Use getattr(slot, "__name__", repr(slot)) to avoid error if slot is a method
                signal.connect(slot, QtCore.Qt.QueuedConnection)
                logger.debug(f"[TesterWindow] Connected worker signal {signal} to slot {getattr(slot, '__name__', repr(slot))}.")

            self.signalGenerateReport.connect(self.worker.onGenerateReport)
            self.signalLoadData.connect(self.worker.onLoadData)
            self.signalSaveData.connect(self.worker.onSaveData)
            self.signalStartTest.connect(self.worker.onStartTest)
            logger.debug(f"[TesterWindow] Connected custom signals to worker slots.")

            self.worker.setupUi(self.ui)
            self.worker.resetTestData()
            logger.debug(f"[TesterWindow] Worker UI setup and test data reset.")

            self.thread = QtCore.QThread(self)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.threadStarted)
            self.thread.start()
            logger.debug(f"[TesterWindow] Worker moved to thread and thread started.")

            # Timer to update current time label every second
            self._current_time_timer = QtCore.QTimer(self)
            self._current_time_timer.timeout.connect(self.updateCurrentTime)
            self._current_time_timer.start(1000)
            logger.debug(f"[TesterWindow] Current time timer started.")

    def updateCurrentTime(self):
        """
        Update the current time label in the UI with the current date and time.
        """
        current_time = QtCore.QDateTime.currentDateTime().toString(self.dateTimeFormat)
        self.ui.labelCurrentTime.setText(current_time)

    @QtCore.Property(str)
    def LastDirectory(self):
        """
        Property for the last directory used for file operations.

        Returns:
            str: The last directory path.
        """
        return self.getSetting("GUI", "LastDirectory")

    @LastDirectory.setter
    def LastDirectory(self, value):
        """
        Setter for the last directory used for file operations.

        Args:
            value (str): The directory path to set.
        """
        self.setSetting("LastDirectory", value)

    @QtCore.Slot()
    def onSettings(self):
        """
        Slot to open the settings dialog and apply changes if accepted.
        """
        logger.debug(f"[TesterWindow] Opening settings dialog.")
        _dialog = SettingsDialog(self.settings)
        _dialog.setWindowTitle(
            QtCore.QCoreApplication.translate("TesterWindow", "Settings")
        )
        _dialog.setWindowIcon(QtGui.QIcon(":/rsc/Pangolin.ico"))
        result = _dialog.exec()
        logger.debug(f"[TesterWindow] Settings dialog result: {result}")

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when settings are modified. Updates UI properties accordingly.
        """
        logger.debug(f"[TesterWindow] Settings modified, updating UI properties.")
        self.firstColumnWidth = int(
            self.getSetting("FirstColumnWidth", 175)
        )
        self.secondColumnWidth = int(
            self.getSetting("SecondColumnWidth", 75)
        )
        self.dateTimeFormat = str(
            self.getSetting("DateTimeFormat", "yyyy-MM-dd HH:mm:ss")
        )
        if hasattr(self, "ui"):
            self.ui.tableSequence.setColumnWidth(0, self.firstColumnWidth)
            self.ui.tableSequence.setColumnWidth(1, self.secondColumnWidth)

        logger.debug(f"[TesterWindow] firstColumnWidth={self.firstColumnWidth}, secondColumnWidth={self.secondColumnWidth}, dateTimeFormat={self.dateTimeFormat}")

    @QtCore.Slot()
    def onAbout(self):
        """
        Slot to show the About dialog with application information.
        """
        logger.debug(f"[TesterWindow] Showing About dialog.")
        _title = QtCore.QCoreApplication.translate("TesterWindow", "About")
        _version_string = QtCore.QCoreApplication.translate("TesterWindow", "Version")
        _company_string = QtCore.QCoreApplication.translate(
            "TesterWindow", "Developed by"
        )
        app = QtCore.QCoreApplication.instance()
        if not app:
            logger.critical(f"[TesterWindow] No QCoreApplication instance found.")
            raise RuntimeError(
                "No QCoreApplication instance found. Ensure the application is initialized correctly."
            )
        _application = app.applicationName()
        _version = app.applicationVersion()
        _company = app.organizationName()
        logger.debug(f"[TesterWindow] About info: {_application}, {_version}, {_company}")
        QtWidgets.QMessageBox.about(
            self,
            _title,
            f"{_application}\n{_version_string} {_version}\n{_company_string} {_company}",
        )

    @QtCore.Slot()
    def onExit(self):
        """
        Slot to handle the exit action, stopping any running test and quitting the application.
        """
        logger.debug(f"[TesterWindow] Exit menu clicked, stopping test and quitting application.")
        self.updateStatus("Exit menu clicked, stopping test and quitting application.")
        self.onStopTest()
        self.worker.stop()
        QtCore.QCoreApplication.quit()

    @QtCore.Slot()
    def onOpen(self):
        """
        Slot to open a file dialog for loading test data from a file.
        """
        logger.debug(f"[TesterWindow] Open menu clicked, opening file dialog for test data.")
        _caption = QtCore.QCoreApplication.translate(
            "TesterWindow", "Open test data file"
        )
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Data files")
        file_dialog = QtWidgets.QFileDialog(
            self, _caption, self.LastDirectory or "", f"{_filter} (*.past)"
        )
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        result = file_dialog.exec()
        logger.debug(f"[TesterWindow] Open file dialog result: {result}")
        if result == QtWidgets.QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            dir_path = QtCore.QFileInfo(file_path).absolutePath()
            logger.debug(f"[TesterWindow] File selected for loading: {file_path}")
            self.LastDirectory = dir_path
            self.updateStatus(f"Loading test data from file {file_path}.")
            self.signalLoadData.emit(file_path)
        else:
            logger.debug(f"[TesterWindow] Open file dialog canceled.")

    @QtCore.Slot()
    def onReport(self):
        """
        Slot to open a file dialog for saving a test report.
        """
        logger.debug(f"[TesterWindow] Report menu clicked, opening file dialog for report generation.")
        _title = QtCore.QCoreApplication.translate(
            "TesterWindow", "Save test report file"
        )
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Report files")
        file_dialog = QtWidgets.QFileDialog(
            self, _title, self.LastDirectory or "", f"{_filter} (*.pdf)"
        )
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        result = file_dialog.exec()
        logger.debug(f"[TesterWindow] Report file dialog result: {result}")
        if result == QtWidgets.QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            dir_path = QtCore.QFileInfo(file_path).absolutePath()
            logger.debug(f"[TesterWindow] File selected for report: {file_path}")
            self.LastDirectory = dir_path
            self.updateStatus(f"Generating report to file {file_path}.")
            self.signalGenerateReport.emit(file_path)
        else:
            logger.debug(f"[TesterWindow] Report file dialog canceled.")

    @QtCore.Slot()
    def onSave(self):
        """
        Slot to open a file dialog for saving test data to a file.
        """
        logger.debug(f"[TesterWindow] Save menu clicked, opening file dialog for saving test data.")
        _title = QtCore.QCoreApplication.translate(
            "TesterWindow", "Save test data file"
        )
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Data files")
        file_dialog = QtWidgets.QFileDialog(
            self, _title, self.LastDirectory or "", f"{_filter} (*.past)"
        )
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        result = file_dialog.exec()
        logger.debug(f"[TesterWindow] Save file dialog result: {result}")
        if result == QtWidgets.QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            dir_path = QtCore.QFileInfo(file_path).absolutePath()
            logger.debug(f"[TesterWindow] File selected for saving: {file_path}")
            self.LastDirectory = dir_path
            self.updateStatus(f"Saving test data to file {file_path}.")
            self.signalSaveData.emit(file_path)
        else:
            logger.debug(f"[TesterWindow] Save file dialog canceled.")

    @QtCore.Slot()
    def onStartTest(self):
        """
        Slot to prompt for serial number and model name, validate input, and start the test.
        """
        logger.debug(f"[TesterWindow] Start test menu clicked, prompting for serial number and model name.")
        _title = QtCore.QCoreApplication.translate(
            "TesterWindow", "Input Serial Number"
        )
        _message = QtCore.QCoreApplication.translate(
            "TesterWindow", "Enter galvo serial number (q to quit):"
        )
        serial_dialog = QtWidgets.QInputDialog(self)
        serial_dialog.setWindowTitle(_title)
        serial_dialog.setLabelText(_message)
        serial_dialog.setInputMode(QtWidgets.QInputDialog.TextInput)
        result = serial_dialog.exec()
        logger.debug(f"[TesterWindow] Serial number dialog result: {result}")
        if result != QtWidgets.QDialog.Accepted:
            logger.debug(f"[TesterWindow] Serial number input canceled.")
            return
        _serial_number = serial_dialog.textValue().strip()
        logger.debug(f"[TesterWindow] Serial number entered: {_serial_number}")
        if not _serial_number or _serial_number.lower() == "q":
            logger.debug(f"[TesterWindow] Serial number input was empty or \"q\".")
            return
        if not _SERIAL_RE.match(_serial_number):
            _title = QtCore.QCoreApplication.translate(
                "TesterWindow", "Invalid Serial Number"
            )
            _message = QtCore.QCoreApplication.translate(
                "TesterWindow",
                "Serial number must be two uppercase letters followed by six digits.",
            )
            QtWidgets.QMessageBox.warning(self, _title, _message)
            logger.warning(f"[TesterWindow] Invalid serial number format.")
            return

        _title = QtCore.QCoreApplication.translate("TesterWindow", "Input Model Name")
        _message = QtCore.QCoreApplication.translate(
            "TesterWindow", "Enter model name:"
        )
        model_dialog = QtWidgets.QInputDialog(self)
        model_dialog.setWindowTitle(_title)
        model_dialog.setLabelText(_message)
        model_dialog.setInputMode(QtWidgets.QInputDialog.TextInput)
        result = model_dialog.exec()
        logger.debug(f"[TesterWindow] Model name dialog result: {result}")
        if result != QtWidgets.QDialog.Accepted:
            logger.debug(f"[TesterWindow] Model name input canceled.")
            return
        _model_name = model_dialog.textValue().strip()
        logger.debug(f"[TesterWindow] Model name entered: {_model_name}")
        if not _model_name:
            _title = QtCore.QCoreApplication.translate(
                "TesterWindow", "Invalid Model Name"
            )
            _message = QtCore.QCoreApplication.translate(
                "TesterWindow", "Model name cannot be empty."
            )
            QtWidgets.QMessageBox.warning(self, _title, _message)
            logger.warning(f"[TesterWindow] Model name cannot be empty.")
            return

        logger.debug(f"[TesterWindow] Starting test for serial \"{_serial_number}\" and model \"{_model_name}\".")
        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(True)
        self.ui.actionReport.setEnabled(False)
        self.signalStartTest.emit(_serial_number, _model_name, "")

    @QtCore.Slot()
    def onStopTest(self):
        """
        Slot to stop the current test and update UI actions.
        """
        logger.debug(f"[TesterWindow] Stop test menu clicked, stopping the current test.")
        self.updateStatus("Stopping current test.")
        self.__cancel.cancel()
        self.ui.actionStart.setEnabled(True)
        self.ui.actionStop.setEnabled(False)
        self.ui.actionReport.setEnabled(True)

    @QtCore.Slot(object, object)
    def on_tableSequence_selectionChanged(self, selected, deselected):
        """
        Slot called when the selection in the test sequence table changes.

        Args:
            selected: The newly selected indexes.
            deselected: The previously selected indexes.
        """
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            logger.debug(f"[TesterWindow] Table row selected: {row}.")
            self.ui.widgetTest.setCurrentIndex(row)
        else:
            logger.debug(f"[TesterWindow] No table row selected.")
            self.ui.widgetTest.setCurrentIndex(-1)

    @QtCore.Slot(int, str)
    def onTestStarted(self, index: int, name: str):
        """
        Slot called when a test is started.

        Args:
            index (int): The index of the test.
            name (str): The name of the test.
        """
        logger.debug(f"[TesterWindow] Test started: index={index}, name={name}")
        self.ui.tableSequence.selectRow(index)
        self.updateStatus(f"Test {index + 1} {name} started.")

    @QtCore.Slot(int, str, bool)
    def onTestFinished(self, index: int, name: str, result: bool):
        """
        Slot called when a test is finished.

        Args:
            index (int): The index of the test.
            name (str): The name of the test.
            result (bool): The result of the test (True for pass, False for fail).
        """
        _status = "PASSED" if result else "FAILED"
        logger.debug(f"[TesterWindow] Test finished: index={index}, name={name}, result={_status}")
        self.updateStatus(f"Test {index + 1} {name} {_status}.")

    @QtCore.Slot(bool)
    def onTestingComplete(self, result: bool):
        """
        Slot called when all tests are complete.

        Args:
            result (bool): The overall result (True for pass, False for fail).
        """
        _status = "Pass" if result else "Fail"
        logger.debug(f"[TesterWindow] All tests complete. Status: {_status}")
        self.updateStatus(f"All tests complete with status {_status}.")
        self.ui.actionStart.setEnabled(True)
        self.ui.actionStop.setEnabled(False)
        self.ui.actionReport.setEnabled(True)

    @QtCore.Slot(str)
    def onFinishedGeneratingReport(self, file_path: str):
        """
        Slot called when report generation is finished.

        Args:
            file_path (str): The path to the generated report file.
        """
        logger.debug(f"[TesterWindow] Report generated: {file_path}")
        self.updateStatus(f"Report generated: {file_path}.")

    @QtCore.Slot(str)
    def onFinishedLoadingData(self, file_path: str):
        """
        Slot called when test data is loaded from a file.

        Args:
            file_path (str): The path to the loaded data file.
        """
        logger.debug(f"[TesterWindow] Data loaded from: {file_path}")
        self.updateStatus(f"Data loaded from: {file_path}.")

    @QtCore.Slot(str)
    def onFinishedSavingData(self, file_path: str):
        """
        Slot called when test data is saved to a file.

        Args:
            file_path (str): The path to the saved data file.
        """
        logger.debug(f"[TesterWindow] Data saved to: {file_path}")
        self.updateStatus(f"Data saved to: {file_path}.")

    def show(self):
        """
        Show the main window.
        """
        logger.debug(f"[TesterWindow] Showing main window.")
        app = QtWidgets.QApplication.instance()
        if not app:
            logger.critical(f"[TesterWindow] No QCoreApplication instance found.")
            raise RuntimeError(
                "No QCoreApplication instance found. Ensure the application is initialized correctly."
            )
        self.setWindowTitle("Startup")
        return super().show()

    def updateStatus(self, message: str):
        """
        Update the status bar message in the UI.

        Args:
            message (str): The message to display.
        """
        logger.debug(f"[TesterWindow] Status update: {message}")
        _message = QtCore.QCoreApplication.translate("TesterWindow", message)
        self.ui.statusBar.showMessage(_message, 5000)

    def updateSubTitle(self, subTitle: str):
        """
        Update the window subtitle and the subtitle label in the UI.

        Args:
            subTitle (str): The subtitle to display.
        """
        logger.debug(f"[TesterWindow] Updating subtitle: {subTitle}")
        self.setWindowTitle(subTitle)
        self.ui.labelSubtitle.setText(subTitle)
