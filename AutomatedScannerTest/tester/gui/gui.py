# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtGui, QtWidgets
import logging

__logger = logging.getLogger(__name__)

from tester import CancelToken
from tester.gui.settings import SettingsDialog
from tester.gui.tester_ui import Ui_TesterWindow
from tester.manager.worker import TestWorker

_SERIAL_RE = QtCore.QRegularExpression(r"^[A-Z]{2}[0-9]{6}$")


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

        __logger.debug("Initializing TesterWindow...")
        app = QtCore.QCoreApplication.instance()
        if app is not None and app.__class__.__name__ == "TesterApp":
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
            app.statusMessage.connect(self.updateStatus)
            __logger.debug("Connected to TesterApp instance and settings.")
        else:
            __logger.critical("TesterApp instance not found.")
            raise RuntimeError(
                "TesterApp instance not found. Ensure the application is initialized correctly."
            )

        self.__cancel = CancelToken()
        self.worker = TestWorker(self.__cancel)
        __logger.debug("TestWorker initialized.")

        if getattr(app, "options", None) and app.options.isSet("gui"):
            self.ui = Ui_TesterWindow()
            self.ui.setupUi(self)
            __logger.debug("UI setup complete.")
            self.ui.tableSequence.setColumnWidth(0, self.firstColumnWidth)
            self.ui.tableSequence.setColumnWidth(1, self.secondColumnWidth)
            self.ui.tableSequence.verticalHeader().setVisible(False)

            # Connect UI signals
            for action, slot in [
                (self.ui.actionAbout, self.onAbout),
                (self.ui.actionExit, self.onExit),
                (self.ui.actionOpen, self.onOpen),
                (self.ui.actionReport, self.onReport),
                (self.ui.actionSave, self.onSave),
                (self.ui.actionSettings, self.onSettings),
                (self.ui.actionStart, self.onStartTest),
                (self.ui.actionStop, self.onStopTest),
            ]:
                action.triggered.connect(slot)
                __logger.debug(
                    f"Connected UI action {action.objectName()} to slot {slot.__name__}."
                )
            self.ui.tableSequence.selectionModel().selectionChanged.connect(
                self.on_tableSequence_selectionChanged
            )
            __logger.debug("Connected tableSequence selection model.")

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
                signal.connect(slot, QtCore.Qt.QueuedConnection)
                __logger.debug(
                    f"Connected worker signal {signal} to slot {getattr(slot, '__name__', str(slot))}."
                )

            self.signalGenerateReport.connect(self.worker.onGenerateReport)
            self.signalLoadData.connect(self.worker.onLoadData)
            self.signalSaveData.connect(self.worker.onSaveData)
            self.signalStartTest.connect(self.worker.onStartTest)
            __logger.debug("Connected custom signals to worker slots.")

            self.worker.setupUi(self.ui)
            self.worker.resetTestData()
            __logger.debug("Worker UI setup and test data reset.")

            self.thread = QtCore.QThread(self)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.threadStarted)
            self.thread.start()
            __logger.debug("Worker moved to thread and thread started.")

            # Timer to update current time label every second
            self._current_time_timer = QtCore.QTimer(self)
            self._current_time_timer.timeout.connect(self.updateCurrentTime)
            self._current_time_timer.start(1000)
            __logger.debug("Current time timer started.")

    def updateCurrentTime(self):
        """
        Update the current time label in the UI with the current date and time.
        """
        __logger.debug("Updating current time label.")
        current_time = QtCore.QDateTime.currentDateTime().toString(self.dateTimeFormat)
        __logger.debug(f"Current time updated: {current_time}")
        self.ui.labelCurrentTime.setText(current_time)

    @QtCore.Property(str)
    def LastDirectory(self):
        """
        Property for the last directory used for file operations.

        Returns:
            str: The last directory path.
        """
        value = self.__settings.getSetting("GUI", "LastDirectory")
        __logger.debug(f"Get LastDirectory: {value}")
        return value

    @LastDirectory.setter
    def LastDirectory(self, value):
        """
        Setter for the last directory used for file operations.

        Args:
            value (str): The directory path to set.
        """
        __logger.debug(f"Set LastDirectory: {value}")
        self.__settings.setSetting("GUI", "LastDirectory", value)

    @QtCore.Slot()
    def onSettings(self):
        """
        Slot to open the settings dialog and apply changes if accepted.
        """
        __logger.debug("Opening settings dialog.")
        _dialog = SettingsDialog(self.__settings)
        _dialog.setWindowTitle(
            QtCore.QCoreApplication.translate("TesterWindow", "Settings")
        )
        _dialog.setWindowIcon(QtGui.QIcon(":/rsc/Pangolin.ico"))
        result = _dialog.exec()
        __logger.debug(f"Settings dialog result: {result}")
        if result == QtWidgets.QDialog.Accepted:
            __logger.debug("Settings dialog accepted.")
            self.onSettingsModified()
        else:
            __logger.debug("Settings dialog canceled.")

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when settings are modified. Updates UI properties accordingly.
        """
        __logger.debug("Settings modified, updating UI properties.")
        self.firstColumnWidth = int(
            self.__settings.getSetting("GUI", "FirstColumnWidth", 175)
        )
        self.secondColumnWidth = int(
            self.__settings.getSetting("GUI", "SecondColumnWidth", 75)
        )
        self.dateTimeFormat = str(
            self.__settings.getSetting("GUI", "DateTimeFormat", "yyyy-MM-dd HH:mm:ss")
        )
        __logger.debug(
            f"firstColumnWidth={self.firstColumnWidth}, secondColumnWidth={self.secondColumnWidth}, dateTimeFormat={self.dateTimeFormat}"
        )

    @QtCore.Slot()
    def onAbout(self):
        """
        Slot to show the About dialog with application information.
        """
        __logger.debug("Showing About dialog.")
        _title = QtCore.QCoreApplication.translate("TesterWindow", "About")
        _version_string = QtCore.QCoreApplication.translate("TesterWindow", "Version")
        _company_string = QtCore.QCoreApplication.translate(
            "TesterWindow", "Developed by"
        )
        app = QtCore.QCoreApplication.instance()
        if not app:
            __logger.critical("No QCoreApplication instance found.")
            raise RuntimeError(
                "No QCoreApplication instance found. Ensure the application is initialized correctly."
            )
        _application = app.applicationName()
        _version = app.applicationVersion()
        _company = app.organizationName()
        __logger.debug(f"About info: {_application}, {_version}, {_company}")
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
        __logger.debug("Exit menu clicked, stopping test and quitting application.")
        self.updateStatus("Exit menu clicked, stopping test and quitting application.")
        self.onStopTest()
        self.worker.stop()
        QtCore.QCoreApplication.quit()

    @QtCore.Slot()
    def onOpen(self):
        """
        Slot to open a file dialog for loading test data from a file.
        """
        __logger.debug("Open menu clicked, opening file dialog for test data.")
        _caption = QtCore.QCoreApplication.translate(
            "TesterWindow", "Open test data file"
        )
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Data files")
        file_dialog = QtWidgets.QFileDialog(
            self, _caption, self.LastDirectory or "", f"{_filter} (*.past)"
        )
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        result = file_dialog.exec()
        __logger.debug(f"Open file dialog result: {result}")
        if result == QtWidgets.QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            dir_path = QtCore.QFileInfo(file_path).absolutePath()
            __logger.debug(f"File selected for loading: {file_path}")
            self.LastDirectory = dir_path
            self.updateStatus(f"Loading test data from file {file_path}.")
            self.signalLoadData.emit(file_path)
        else:
            __logger.debug("Open file dialog canceled.")

    @QtCore.Slot()
    def onReport(self):
        """
        Slot to open a file dialog for saving a test report.
        """
        __logger.debug("Report menu clicked, opening file dialog for report generation.")
        _title = QtCore.QCoreApplication.translate(
            "TesterWindow", "Save test report file"
        )
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Report files")
        file_dialog = QtWidgets.QFileDialog(
            self, _title, self.LastDirectory or "", f"{_filter} (*.pdf)"
        )
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        result = file_dialog.exec()
        __logger.debug(f"Report file dialog result: {result}")
        if result == QtWidgets.QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            dir_path = QtCore.QFileInfo(file_path).absolutePath()
            __logger.debug(f"File selected for report: {file_path}")
            self.LastDirectory = dir_path
            self.updateStatus(f"Generating report to file {file_path}.")
            self.signalGenerateReport.emit(file_path)
        else:
            __logger.debug("Report file dialog canceled.")

    @QtCore.Slot()
    def onSave(self):
        """
        Slot to open a file dialog for saving test data to a file.
        """
        __logger.debug("Save menu clicked, opening file dialog for saving test data.")
        _title = QtCore.QCoreApplication.translate(
            "TesterWindow", "Save test data file"
        )
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Data files")
        file_dialog = QtWidgets.QFileDialog(
            self, _title, self.LastDirectory or "", f"{_filter} (*.past)"
        )
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        result = file_dialog.exec()
        __logger.debug(f"Save file dialog result: {result}")
        if result == QtWidgets.QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            dir_path = QtCore.QFileInfo(file_path).absolutePath()
            __logger.debug(f"File selected for saving: {file_path}")
            self.LastDirectory = dir_path
            self.updateStatus(f"Saving test data to file {file_path}.")
            self.signalSaveData.emit(file_path)
        else:
            __logger.debug("Save file dialog canceled.")

    @QtCore.Slot()
    def onStartTest(self):
        """
        Slot to prompt for serial number and model name, validate input, and start the test.
        """
        __logger.debug(
            "Start test menu clicked, prompting for serial number and model name."
        )
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
        __logger.debug(f"Serial number dialog result: {result}")
        if result != QtWidgets.QDialog.Accepted:
            __logger.debug("Serial number input canceled.")
            return
        _serial_number = serial_dialog.textValue().strip()
        __logger.debug(f"Serial number entered: {_serial_number}")
        if not _serial_number or _serial_number.lower() == "q":
            __logger.debug("Serial number input was empty or 'q'.")
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
            __logger.warning("Invalid serial number format.")
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
        __logger.debug(f"Model name dialog result: {result}")
        if result != QtWidgets.QDialog.Accepted:
            __logger.debug("Model name input canceled.")
            return
        _model_name = model_dialog.textValue().strip()
        __logger.debug(f"Model name entered: {_model_name}")
        if not _model_name:
            _title = QtCore.QCoreApplication.translate(
                "TesterWindow", "Invalid Model Name"
            )
            _message = QtCore.QCoreApplication.translate(
                "TesterWindow", "Model name cannot be empty."
            )
            QtWidgets.QMessageBox.warning(self, _title, _message)
            __logger.warning("Model name cannot be empty.")
            return

        __logger.debug(
            f"Starting test for serial '{_serial_number}' and model '{_model_name}'."
        )
        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(True)
        self.ui.actionReport.setEnabled(False)
        self.signalStartTest.emit(_serial_number, _model_name, "")

    @QtCore.Slot()
    def onStopTest(self):
        """
        Slot to stop the current test and update UI actions.
        """
        __logger.debug("Stop test menu clicked, stopping the current test.")
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
            __logger.debug(f"Table row selected: {row}.")
            self.ui.widgetTest.setCurrentIndex(row)
        else:
            __logger.debug("No table row selected.")
            self.ui.widgetTest.setCurrentIndex(-1)

    @QtCore.Slot(int, str)
    def onTestStarted(self, index: int, name: str):
        """
        Slot called when a test is started.

        Args:
            index (int): The index of the test.
            name (str): The name of the test.
        """
        __logger.debug(f"Test started: index={index}, name={name}")
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
        __logger.debug(f"Test finished: index={index}, name={name}, result={_status}")
        self.updateStatus(f"Test {index + 1} {name} {_status}.")

    @QtCore.Slot(bool)
    def onTestingComplete(self, result: bool):
        """
        Slot called when all tests are complete.

        Args:
            result (bool): The overall result (True for pass, False for fail).
        """
        _status = "Pass" if result else "Fail"
        __logger.debug(f"All tests complete. Status: {_status}")
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
        __logger.debug(f"Report generated: {file_path}")
        self.updateStatus(f"Report generated: {file_path}.")

    @QtCore.Slot(str)
    def onFinishedLoadingData(self, file_path: str):
        """
        Slot called when test data is loaded from a file.

        Args:
            file_path (str): The path to the loaded data file.
        """
        __logger.debug(f"Data loaded from: {file_path}")
        self.updateStatus(f"Data loaded from: {file_path}.")

    @QtCore.Slot(str)
    def onFinishedSavingData(self, file_path: str):
        """
        Slot called when test data is saved to a file.

        Args:
            file_path (str): The path to the saved data file.
        """
        __logger.debug(f"Data saved to: {file_path}")
        self.updateStatus(f"Data saved to: {file_path}.")

    def show(self):
        """
        Show the main window.
        """
        __logger.debug("Showing main window.")
        app = QtWidgets.QApplication.instance()
        if not app:
            __logger.critical("No QCoreApplication instance found.")
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
        __logger.debug(f"Status update: {message}")
        _message = QtCore.QCoreApplication.translate("TesterWindow", message)
        self.ui.statusBar.showMessage(_message, 5000)

    def updateSubTitle(self, subTitle: str):
        """
        Update the window subtitle and the subtitle label in the UI.

        Args:
            subTitle (str): The subtitle to display.
        """
        __logger.debug(f"Updating subtitle: {subTitle}")
        self.setWindowTitle(subTitle)
        self.ui.labelSubtitle.setText(subTitle)
