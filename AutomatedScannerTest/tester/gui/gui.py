# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtGui, QtWidgets
from pathlib import Path
import re

from tester.gui.tester_ui import Ui_TesterWindow
from tester.manager.sequence import TestSequenceModel
from tester.manager.worker import TestWorker

# Pre-compile the serial number regex for efficiency
_SERIAL_RE = re.compile(r"^[A-Z]{2}[0-9]{6}$")


class TesterWindow(QtCore.QMainWindow):
    """
    Main Qt application window for the Automated Scanner Test GUI.
    Manages UI, user actions, and coordinates with the TestSequence model.
    """

    signalGenerateReport = QtCore.Signal(str)
    signalLoadData = QtCore.Signal(str)
    signalSaveData = QtCore.Signal(str)
    signalStartTest = QtCore.Signal(str, str, str)

    def __init__(self, *args, **kwargs):
        """
        Initialize the TesterWindow, set up the UI, connect signals, and configure logging.
        """
        super().__init__(*args, **kwargs)

        # Setup model
        app = QtCore.QCoreApplication.instance()
        if app and hasattr(app, "get_logger") and hasattr(app, "get_settings"):
            self.__logger = app.get_logger(self.__class__.__name__)
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
        else:
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        model = TestSequenceModel()
        self.worker = TestWorker(model)

        if app.options.isSet("gui"):
            # Setup UI
            self.ui = Ui_TesterWindow()
            self.ui.setupUi(self)
            self.ui.tableSequence.setModel(model)
            self.ui.tableSequence.setColumnWidth(0, self.firstColumnWidth)
            self.ui.tableSequence.setColumnWidth(1, self.secondColumnWidth)
            self.ui.tableSequence.verticalHeader().setVisible(False)

            # Connect UI signals
            self.ui.actionAbout.triggered.connect(self.onAbout)
            self.ui.actionExit.triggered.connect(self.onExit)
            self.ui.actionOpen.triggered.connect(self.onOpen)
            self.ui.actionReport.triggered.connect(self.onReport)
            self.ui.actionSave.triggered.connect(self.onSave)
            self.ui.actionStart.triggered.connect(self.onStartTest)
            self.ui.actionStop.triggered.connect(self.onStopTest)
            self.ui.tableSequence.selectionModel().selectionChanged.connect(
                self.on_tableSequence_selectionChanged
            )

            # Use a mapping to reduce repetitive code for label connections
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
            self.thread = QtCore.QThread()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.threadStarted)
            self.thread.start()

            # Timer to update current time label every second
            self._current_time_timer = QtCore.QTimer(self)
            self._current_time_timer.timeout.connect(self.updateCurrentTime)
            self._current_time_timer.start(1000)
            self.updateCurrentTime()

            model.setupUi(self.ui.widgetTest)
            model.statusChanged.connect(self.updateStatus)

    def updateCurrentTime(self):
        """
        Update the labelCurrentTime with the current time.
        """
        self.ui.labelCurrentTime.setText(
            QtCore.QDateTime.currentDateTime().toString(self.dateTimeFormat)
        )

    def getLastDirectory(self) -> Path:
        """
        Get the last directory used for file operations.
        Returns:
            str: The last directory path.
        """
        self.__logger.debug("Retrieving last directory from settings.")
        return self.__settings.value("LastDirectory", str(Path.home()))

    def setLastDirectory(self, path: Path):
        """
        Set the last directory used for file operations.
        Args:
            path (Path): The new last directory path.
        """
        self.__logger.debug(f"Setting last directory to: {path}")
        self.__settings.setValue("LastDirectory", str(path))
        self.__settings.sync()

    LastDirectory = QtCore.Property(Path, getLastDirectory, setLastDirectory, doc="Last directory used for file operations.")

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when settings are modified.
        """
        self.__logger.debug("Settings modified, updating UI properties.")
        self.__settings.beginGroup(self.__class__.__name__)
        self.firstColumnWidth = self.__settings.value("FirstColumnWidth", 175, int)
        self.secondColumnWidth = self.__settings.value("SecondColumnWidth", 75, int)
        self.dateTimeFormat = self.__settings.value("DateTimeFormat", "yyyy-MM-dd HH:mm:ss", str)
        self.__settings.setValue("FirstColumnWidth", self.firstColumnWidth)
        self.__settings.setValue("SecondColumnWidth", self.secondColumnWidth)
        self.__settings.setValue("DateTimeFormat", self.dateTimeFormat)
        self.__settings.endGroup()
        self.__settings.sync()

    @QtCore.Slot()
    def onAbout(self):
        """
        Show the About dialog with application information.
        """
        self.__logger.debug("About menu clicked, displaying about dialog.")
        _title = QtCore.QCoreApplication.translate("TesterWindow", "About")
        _version = QtCore.QCoreApplication.translate("TesterWindow", "Version")
        _company = QtCore.QCoreApplication.translate("TesterWindow", "Developed by")
        QtWidgets.QMessageBox.about(
            self,
            _title,
            f"{tester.__application__}\n{_version} {tester.__version__}\n{_company} {tester.__company__}",
        )

    @QtCore.Slot()
    def onExit(self):
        """
        Handle the Exit action: stop the test and quit the application.
        """
        self.updateStatus("Exit menu clicked, stopping test and quitting application.")
        self.onStopTest()
        QtCore.QCoreApplication.quit()

    @QtCore.Slot()
    def onOpen(self):
        """
        Handle the Open action: open a file dialog to select a test data file and load it.
        """
        self.__logger.debug("Open menu clicked, opening file dialog for test data.")
        _caption = QtCore.QCoreApplication.translate("TesterWindow", "Open test data file")
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Data files")
        file_path, ok = QtWidgets.QFileDialog.getOpenFileName(
            self,
            _caption,
            str(self.LastDirectory or ""),
            f"{_filter} (*.past)",
        )
        if ok and file_path:
            self.LastDirectory = str(Path(file_path).parent)
            self.updateStatus(f"Loading test data from file {file_path}.")
            self.signalLoadData.emit(file_path)

    @QtCore.Slot()
    def onReport(self):
        """
        Handle the Report action: open a file dialog to select a location and generate a test report.
        """
        self.__logger.debug("Report menu clicked, opening file dialog for report generation.")
        _title = QtCore.QCoreApplication.translate("TesterWindow", "Save test report file")
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Report files")
        file_path, ok = QtWidgets.QFileDialog.getSaveFileName(
            self,
            _title,
            str(self.LastDirectory or ""),
            f"{_filter} (*.pdf)",
        )
        if ok and file_path:
            self.LastDirectory = str(Path(file_path).parent)
            self.updateStatus(f"Generating report to file {file_path}.")
            self.signalGenerateReport.emit(file_path)

    @QtCore.Slot()
    def onSave(self):
        """
        Handle the Save action: open a file dialog to select a location and save the test data.
        """
        self.__logger.debug("Save menu clicked, opening file dialog for saving test data.")
        _title = QtCore.QCoreApplication.translate("TesterWindow", "Save test data file")
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Data files")
        file_path, ok = QtWidgets.QFileDialog.getSaveFileName(
            self,
            _title,
            str(self.LastDirectory or ""),
            f"{_filter} (*.past)",
        )
        if ok and file_path:
            self.LastDirectory = str(Path(file_path).parent)
            self.updateStatus(f"Saving test data to file {file_path}.")
            self.signalSaveData.emit(file_path)

    @QtCore.Slot()
    def onStartTest(self):
        """
        Handle the Start Test action: prompt for a serial number, validate it, and start the test.
        """
        self.__logger.debug("Start test menu clicked, prompting for serial number and model name.")
        _title = QtCore.QCoreApplication.translate("TesterWindow", "Input Serial Number")
        _message = QtCore.QCoreApplication.translate("TesterWindow", "Enter galvo serial number (q to quit):")
        _serial_number, _ok = QtWidgets.QInputDialog.getText(self, _title, _message)
        if not _ok or not _serial_number or _serial_number.strip().lower() == "q":
            return
        _serial_number = _serial_number.strip()
        if not _SERIAL_RE.fullmatch(_serial_number):
            _title = QtCore.QCoreApplication.translate("TesterWindow", "Invalid Serial Number")
            _message = QtCore.QCoreApplication.translate("TesterWindow", "Serial number must be two uppercase letters followed by six digits.")
            QtWidgets.QMessageBox.warning(self, _title, _message)
            self.__logger.warning("Invalid serial number format.")

        _title = QtCore.QCoreApplication.translate("TesterWindow", "Input Model Name")
        _message = QtCore.QCoreApplication.translate("TesterWindow", "Enter model name:")
        _model_name, _ok = QtWidgets.QInputDialog.getText(self, _title, _message)
        if not _ok or not _model_name:
            _title = QtCore.QCoreApplication.translate("TesterWindow", "Invalid Model Name")
            _message = QtCore.QCoreApplication.translate("TesterWindow", "Model name cannot be empty.")
            QtWidgets.QMessageBox.warning(self, _title, _message)
            self._logger.warning("Model name cannot be empty.")

        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(True)
        self.ui.actionReport.setEnabled(False)
        self.signalStartTest.emit(_serial_number, _model_name, "")

    @QtCore.Slot()
    def onStopTest(self):
        """
        Handle the Stop Test action: stop the current test and update UI actions.
        """
        self.__logger.debug("Stop test menu clicked, stopping the current test.")
        self.updateStatus("Stopping current test.")
        if hasattr(self.model, "on_stop_test"):
            self.model.on_stop_test()
        self.ui.actionStart.setEnabled(True)
        self.ui.actionStop.setEnabled(False)
        self.ui.actionReport.setEnabled(True)

    @QtCore.Slot(object, object)
    def on_tableSequence_selectionChanged(self, selected, deselected):
        """
        Handle selection changes in the test sequence table.

        Args:
            selected (QItemSelection): The newly selected items.
            deselected (QItemSelection): The previously selected items.
        """
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            self.__logger.debug(f"Table row selected: {row}.")
            self.ui.widgetTest.setCurrentIndex(row)
        else:
            self.__logger.debug("No table row selected.")
            self.ui.widgetTest.setCurrentIndex(-1)

    @QtCore.Slot(int, str)
    def onTestStarted(self, index: int, name: str):
        """
        Slot called when a test is started.

        Args:
            index (int): The index of the started test.
        """
        self.ui.tableSequence.selectRow(index)
        self.updateStatus(f"Test {index + 1} {name} started.")

    @QtCore.Slot(int, str, bool)
    def onTestFinished(self, index: int, name: str, result: bool):
        """
        Slot called when a test is finished.

        Args:
            index (int): The index of the finished test.
            result (bool): The result of the test (True for pass, False for fail).
        """
        _status = "PASSED" if result else "FAILED"
        _message = f"Test {index + 1} {name} {_status}."
        self.updateStatus(_message)

    @QtCore.Slot(bool)
    def onTestingComplete(self, result: bool):
        """
        Slot called when all tests are complete.

        Args:
            result (bool): The overall result of the test sequence.
        """
        _status = "Pass" if result else "Fail"
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
        self.updateStatus(f"Report generated: {file_path}.")

    @QtCore.Slot(str)
    def onFinishedLoadingData(self, file_path: str):
        """
        Slot called when the data loading is finished.
        Args:
            file_path (str): The path to the loaded data file.
        """
        self.updateStatus(f"Data loaded from: {file_path}.")

    @QtCore.Slot(str)
    def onFinishedSavingData(self, file_path: str):
        """
        Slot called when the data saving is finished.
        Args:
            file_path (str): The path to the saved data file.
        """
        self.updateStatus(f"Data saved to: {file_path}.")

    def show(self):
        """
        Show the main window and set up the status bar logging handler.

        Returns:
            None
        """
        self.setWindowTitle(tester.__application__)
        self.setWindowIcon(QtGui.QIcon(":/icons/icon.png"))
        return super().show()

    def showEvent(self, event):
        """
        Override showEvent to start the test if 'run' option is set.

        Args:
            event (QShowEvent): The show event.
        """
        super().showEvent(event)
        app = TesterApp.instance()
        if hasattr(app, "options") and app.options.isSet("run"):
            self.onStartTest()

    @QtCore.Slot(str)
    def updateStatus(self, message: str):
        """
        Update the status bar with a message.
        Args:
            message (str): The message to display in the status bar.
        """
        self.__logger.info(message)
        _message = QtCore.QCoreApplication.translate("TesterWindow", message)
        self.ui.statusBar.showMessage(_message, 5000)
