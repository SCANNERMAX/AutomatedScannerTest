# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtGui, QtWidgets

from tester import CancelToken
from tester.gui.settings import SettingsDialog
from tester.gui.tester_ui import Ui_TesterWindow
from tester.manager.sequence import TestSequenceModel
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

        QtCore.qInfo("[TesterWindow] Initializing...")
        app = QtCore.QCoreApplication.instance()
        if app is not None and app.__class__.__name__ == "TesterApp":
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
            app.statusMessage.connect(self.updateStatus)
        else:
            QtCore.qCritical("[TesterWindow] TesterApp instance not found.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")

        self.__cancel = CancelToken()
        self.worker = TestWorker(self.__cancel)
        QtCore.qInfo("[TesterWindow] Model and worker initialized.")

        if getattr(app, "options", None) and app.options.isSet("gui"):
            self.ui = Ui_TesterWindow()
            self.ui.setupUi(self)
            self.ui.tableSequence.setColumnWidth(0, self.firstColumnWidth)
            self.ui.tableSequence.setColumnWidth(1, self.secondColumnWidth)
            self.ui.tableSequence.verticalHeader().setVisible(False)

            # Connect UI signals
            self.ui.actionAbout.triggered.connect(self.onAbout)
            self.ui.actionExit.triggered.connect(self.onExit)
            self.ui.actionOpen.triggered.connect(self.onOpen)
            self.ui.actionReport.triggered.connect(self.onReport)
            self.ui.actionSave.triggered.connect(self.onSave)
            self.ui.actionSettings.triggered.connect(self.onSettings)
            self.ui.actionStart.triggered.connect(self.onStartTest)
            self.ui.actionStop.triggered.connect(self.onStopTest)
            self.ui.tableSequence.selectionModel().selectionChanged.connect(
                self.on_tableSequence_selectionChanged
            )

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

            self.signalGenerateReport.connect(self.worker.onGenerateReport)
            self.signalLoadData.connect(self.worker.onLoadData)
            self.signalSaveData.connect(self.worker.onSaveData)
            self.signalStartTest.connect(self.worker.onStartTest)
            self.worker.setupUi(self.ui)
            self.worker.resetTestData()

            self.thread = QtCore.QThread()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.threadStarted)
            self.thread.start()

            # Timer to update current time label every second
            self._current_time_timer = QtCore.QTimer(self)
            self._current_time_timer.timeout.connect(self.updateCurrentTime)
            self._current_time_timer.start(1000)

            QtCore.qInfo("[TesterWindow] UI setup complete.")

    def updateCurrentTime(self):
        """
        Update the labelCurrentTime with the current time using the configured date/time format.
        """
        QtCore.qDebug("[TesterWindow] Updating current time label.")
        self.ui.labelCurrentTime.setText(
            QtCore.QDateTime.currentDateTime().toString(self.dateTimeFormat)
        )

    @QtCore.Property(str)
    def LastDirectory(self):
        """
        Property for the last directory used for file operations.

        Returns:
            str: The last directory path.
        """
        value = self.__settings.getSetting("GUI", "LastDirectory")
        QtCore.qDebug(f"[TesterWindow] Get LastDirectory: {value}")
        return value

    @LastDirectory.setter
    def LastDirectory(self, value):
        """
        Setter for the last directory used for file operations.

        Args:
            value (str): The directory path to set.
        """
        QtCore.qDebug(f"[TesterWindow] Set LastDirectory: {value}")
        self.__settings.setSetting("GUI", "LastDirectory", value)

    @QtCore.Slot()
    def onSettings(self):
        """
        Open the settings dialog for editing application settings.
        """
        QtCore.qInfo("[TesterWindow] Opening settings dialog.")
        _dialog = SettingsDialog(self.__settings)
        _dialog.setWindowTitle(QtCore.QCoreApplication.translate("TesterWindow", "Settings"))
        _dialog.setWindowIcon(QtGui.QIcon(":/rsc/Pangolin.ico"))
        if _dialog.exec() == QtWidgets.QDialog.Accepted:
            QtCore.qInfo("[TesterWindow] Settings dialog accepted.")
            self.onSettingsModified()
        else:
            QtCore.qInfo("[TesterWindow] Settings dialog canceled.")

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when application settings are modified.
        Updates UI properties from settings.
        """
        QtCore.qInfo("[TesterWindow] Settings modified, updating UI properties.")
        self.firstColumnWidth = self.__settings.getSetting("GUI", "FirstColumnWidth", 175)
        self.secondColumnWidth = self.__settings.getSetting("GUI", "SecondColumnWidth", 75)
        self.dateTimeFormat = self.__settings.getSetting("GUI", "DateTimeFormat", "yyyy-MM-dd HH:mm:ss")
        QtCore.qDebug(f"[TesterWindow] firstColumnWidth={self.firstColumnWidth}, secondColumnWidth={self.secondColumnWidth}, dateTimeFormat={self.dateTimeFormat}")

    @QtCore.Slot()
    def onAbout(self):
        """
        Show the About dialog with application information.
        """
        QtCore.qInfo("[TesterWindow] Showing About dialog.")
        _title = QtCore.QCoreApplication.translate("TesterWindow", "About")
        _version_string = QtCore.QCoreApplication.translate("TesterWindow", "Version")
        _company_string = QtCore.QCoreApplication.translate("TesterWindow", "Developed by")
        app = QtCore.QCoreApplication.instance()
        if not app:
            QtCore.qCritical("[TesterWindow] No QCoreApplication instance found.")
            raise RuntimeError("No QCoreApplication instance found. Ensure the application is initialized correctly.")
        _application = app.applicationName()
        _version = app.applicationVersion()
        _company = app.organizationName()
        QtWidgets.QMessageBox.about(
            self,
            _title,
            f"{_application}\n{_version_string} {_version}\n{_company_string} {_company}",
        )

    @QtCore.Slot()
    def onExit(self):
        """
        Handle the Exit action: stop the test and quit the application.
        """
        QtCore.qInfo("[TesterWindow] Exit menu clicked, stopping test and quitting application.")
        self.updateStatus("Exit menu clicked, stopping test and quitting application.")
        self.onStopTest()
        self.worker.stop()
        QtCore.QCoreApplication.quit()

    @QtCore.Slot()
    def onOpen(self):
        """
        Open a file dialog to select a test data file and load it.
        Updates the LastDirectory property and emits the signalLoadData signal.
        """
        QtCore.qInfo("[TesterWindow] Open menu clicked, opening file dialog for test data.")
        _caption = QtCore.QCoreApplication.translate("TesterWindow", "Open test data file")
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Data files")
        file_dialog = QtWidgets.QFileDialog(self, _caption, self.LastDirectory or "", f"{_filter} (*.past)")
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        if file_dialog.exec() == QtWidgets.QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            dir_path = QtCore.QFileInfo(file_path).absolutePath()
            QtCore.qInfo(f"[TesterWindow] File selected for loading: {file_path}")
            self.LastDirectory = dir_path
            self.updateStatus(f"Loading test data from file {file_path}.")
            self.signalLoadData.emit(file_path)
        else:
            QtCore.qInfo("[TesterWindow] Open file dialog canceled.")

    @QtCore.Slot()
    def onReport(self):
        """
        Open a file dialog to select a location and generate a test report.
        Updates the LastDirectory property and emits the signalGenerateReport signal.
        """
        QtCore.qInfo("[TesterWindow] Report menu clicked, opening file dialog for report generation.")
        _title = QtCore.QCoreApplication.translate("TesterWindow", "Save test report file")
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Report files")
        file_dialog = QtWidgets.QFileDialog(self, _title, self.LastDirectory or "", f"{_filter} (*.pdf)")
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        if file_dialog.exec() == QtWidgets.QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            dir_path = QtCore.QFileInfo(file_path).absolutePath()
            QtCore.qInfo(f"[TesterWindow] File selected for report: {file_path}")
            self.LastDirectory = dir_path
            self.updateStatus(f"Generating report to file {file_path}.")
            self.signalGenerateReport.emit(file_path)
        else:
            QtCore.qInfo("[TesterWindow] Report file dialog canceled.")

    @QtCore.Slot()
    def onSave(self):
        """
        Open a file dialog to select a location and save the test data.
        Updates the LastDirectory property and emits the signalSaveData signal.
        """
        QtCore.qInfo("[TesterWindow] Save menu clicked, opening file dialog for saving test data.")
        _title = QtCore.QCoreApplication.translate("TesterWindow", "Save test data file")
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Data files")
        file_dialog = QtWidgets.QFileDialog(self, _title, self.LastDirectory or "", f"{_filter} (*.past)")
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        if file_dialog.exec() == QtWidgets.QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            dir_path = QtCore.QFileInfo(file_path).absolutePath()
            QtCore.qInfo(f"[TesterWindow] File selected for saving: {file_path}")
            self.LastDirectory = dir_path
            self.updateStatus(f"Saving test data to file {file_path}.")
            self.signalSaveData.emit(file_path)
        else:
            QtCore.qInfo("[TesterWindow] Save file dialog canceled.")

    @QtCore.Slot()
    def onStartTest(self):
        """
        Prompt the user for a serial number and model name, validate them, and start the test.
        Emits the signalStartTest signal if valid input is provided.
        """
        QtCore.qInfo("[TesterWindow] Start test menu clicked, prompting for serial number and model name.")
        _title = QtCore.QCoreApplication.translate("TesterWindow", "Input Serial Number")
        _message = QtCore.QCoreApplication.translate("TesterWindow", "Enter galvo serial number (q to quit):")
        serial_dialog = QtWidgets.QInputDialog(self)
        serial_dialog.setWindowTitle(_title)
        serial_dialog.setLabelText(_message)
        serial_dialog.setInputMode(QtWidgets.QInputDialog.TextInput)
        if serial_dialog.exec() != QtWidgets.QDialog.Accepted:
            QtCore.qInfo("[TesterWindow] Serial number input canceled.")
            return
        _serial_number = serial_dialog.textValue().strip()
        QtCore.qDebug(f"[TesterWindow] Serial number entered: {_serial_number}")
        if not _serial_number or _serial_number.lower() == "q":
            QtCore.qInfo("[TesterWindow] Serial number input was empty or 'q'.")
            return
        if not _SERIAL_RE.match(_serial_number):
            _title = QtCore.QCoreApplication.translate("TesterWindow", "Invalid Serial Number")
            _message = QtCore.QCoreApplication.translate(
                "TesterWindow", "Serial number must be two uppercase letters followed by six digits."
            )
            QtWidgets.QMessageBox.warning(self, _title, _message)
            QtCore.qWarning("[TesterWindow] Invalid serial number format.")
            return

        _title = QtCore.QCoreApplication.translate("TesterWindow", "Input Model Name")
        _message = QtCore.QCoreApplication.translate("TesterWindow", "Enter model name:")
        model_dialog = QtWidgets.QInputDialog(self)
        model_dialog.setWindowTitle(_title)
        model_dialog.setLabelText(_message)
        model_dialog.setInputMode(QtWidgets.QInputDialog.TextInput)
        if model_dialog.exec() != QtWidgets.QDialog.Accepted:
            QtCore.qInfo("[TesterWindow] Model name input canceled.")
            return
        _model_name = model_dialog.textValue().strip()
        QtCore.qDebug(f"[TesterWindow] Model name entered: {_model_name}")
        if not _model_name:
            _title = QtCore.QCoreApplication.translate("TesterWindow", "Invalid Model Name")
            _message = QtCore.QCoreApplication.translate("TesterWindow", "Model name cannot be empty.")
            QtWidgets.QMessageBox.warning(self, _title, _message)
            QtCore.qWarning("[TesterWindow] Model name cannot be empty.")
            return

        QtCore.qInfo(f"[TesterWindow] Starting test for serial '{_serial_number}' and model '{_model_name}'.")
        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(True)
        self.ui.actionReport.setEnabled(False)
        self.signalStartTest.emit(_serial_number, _model_name, "")

    @QtCore.Slot()
    def onStopTest(self):
        """
        Stop the current test and update UI actions.
        """
        QtCore.qInfo("[TesterWindow] Stop test menu clicked, stopping the current test.")
        self.updateStatus("Stopping current test.")
        self.__cancel.cancel()
        self.ui.actionStart.setEnabled(True)
        self.ui.actionStop.setEnabled(False)
        self.ui.actionReport.setEnabled(True)

    @QtCore.Slot(object, object)
    def on_tableSequence_selectionChanged(self, selected, deselected):
        """
        Handle selection changes in the test sequence table and update the widgetTest index.

        Args:
            selected (QItemSelection): The newly selected items.
            deselected (QItemSelection): The previously selected items.
        """
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            QtCore.qDebug(f"[TesterWindow] Table row selected: {row}.")
            self.ui.widgetTest.setCurrentIndex(row)
        else:
            QtCore.qDebug("[TesterWindow] No table row selected.")
            self.ui.widgetTest.setCurrentIndex(-1)

    @QtCore.Slot(int, str)
    def onTestStarted(self, index: int, name: str):
        """
        Slot called when a test is started.

        Args:
            index (int): The index of the started test.
            name (str): The name of the started test.
        """
        QtCore.qInfo(f"[TesterWindow] Test started: index={index}, name={name}")
        self.ui.tableSequence.selectRow(index)
        self.updateStatus(f"Test {index + 1} {name} started.")

    @QtCore.Slot(int, str, bool)
    def onTestFinished(self, index: int, name: str, result: bool):
        """
        Slot called when a test is finished.

        Args:
            index (int): The index of the finished test.
            name (str): The name of the finished test.
            result (bool): The result of the test (True for pass, False for fail).
        """
        _status = "PASSED" if result else "FAILED"
        _message = f"Test {index + 1} {name} {_status}."
        QtCore.qInfo(f"[TesterWindow] Test finished: index={index}, name={name}, result={_status}")
        self.updateStatus(_message)

    @QtCore.Slot(bool)
    def onTestingComplete(self, result: bool):
        """
        Slot called when all tests are complete.

        Args:
            result (bool): The overall result of the test sequence.
        """
        _status = "Pass" if result else "Fail"
        QtCore.qInfo(f"[TesterWindow] All tests complete. Status: {_status}")
        self.updateStatus(f"All tests complete with status {_status}.")
        self.ui.actionStart.setEnabled(True)
        self.ui.actionStop.setEnabled(False)
        self.ui.actionReport.setEnabled(True)

    @QtCore.Slot(str)
    def onFinishedGeneratingReport(self, file_path: str):
        """
        Slot called when the report generation is finished.

        Args:
            file_path (str): The path to the generated report file.
        """
        QtCore.qInfo(f"[TesterWindow] Report generated: {file_path}")
        self.updateStatus(f"Report generated: {file_path}.")

    @QtCore.Slot(str)
    def onFinishedLoadingData(self, file_path: str):
        """
        Slot called when the data loading is finished.

        Args:
            file_path (str): The path to the loaded data file.
        """
        QtCore.qInfo(f"[TesterWindow] Data loaded from: {file_path}")
        self.updateStatus(f"Data loaded from: {file_path}.")

    @QtCore.Slot(str)
    def onFinishedSavingData(self, file_path: str):
        """
        Slot called when the data saving is finished.

        Args:
            file_path (str): The path to the saved data file.
        """
        QtCore.qInfo(f"[TesterWindow] Data saved to: {file_path}")
        self.updateStatus(f"Data saved to: {file_path}.")

    def show(self):
        """
        Show the main window and set the window title to 'Startup'.

        Returns:
            None
        """
        QtCore.qInfo("[TesterWindow] Showing main window.")
        app = QtWidgets.QApplication.instance()
        if not app:
            QtCore.qCritical("[TesterWindow] No QCoreApplication instance found.")
            raise RuntimeError("No QCoreApplication instance found. Ensure the application is initialized correctly.")
        self.setWindowTitle("Startup")
        return super().show()

    def updateStatus(self, message: str):
        """
        Update the status bar with a message.

        Args:
            message (str): The message to display in the status bar.
        """
        QtCore.qInfo(f"[TesterWindow] Status update: {message}")
        _message = QtCore.QCoreApplication.translate("TesterWindow", message)
        self.ui.statusBar.showMessage(_message, 5000)

    def updateSubTitle(self, subTitle: str):
        """
        Update the window title and subtitle label.

        Args:
            subTitle (str): The subtitle to set.
        """
        QtCore.qInfo(f"[TesterWindow] Updating subtitle: {subTitle}")
        self.setWindowTitle(subTitle)
        self.ui.labelSubtitle.setText(subTitle)
