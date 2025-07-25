# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets, QtGui
import logging
from pathlib import Path
import re

import tester
from tester.manager.test_sequence import TestSequenceModel, TestWorker
from tester.gui.tester_ui import Ui_TesterWindow

# Pre-compile the serial number regex for efficiency
_SERIAL_RE = re.compile(r"^[A-Z]{2}[0-9]{6}$")


class TesterWindow(QtWidgets.QMainWindow):
    """
    Main Qt application window for the Automated Scanner Test GUI.
    Manages UI, user actions, and coordinates with the TestSequence model.
    """

    signalGenerateReport = QtCore.Signal(str)
    signalLoadData = QtCore.Signal(str)
    signalSaveData = QtCore.Signal(str)
    signalStartTest = QtCore.Signal(str, str, str)

    @property
    def LastDirectory(self) -> str:
        """
        Returns the last directory path used for file operations.

        Returns:
            str: The last directory path used.
        """
        return self.model._get_setting("LastDirectory")

    @LastDirectory.setter
    def LastDirectory(self, value: str):
        """
        Sets the last directory used for file operations.

        Args:
            value (str): The directory path to set.
        """
        self.model._set_setting("LastDirectory", value)

    def __init__(self, *args, **kwargs):
        """
        Initialize the TesterWindow, set up the UI, connect signals, and configure logging.
        """
        super().__init__(*args, **kwargs)

        # Setup model
        app = QtWidgets.QApplication.instance()
        model = TestSequenceModel(app.settings)

        # Setup UI
        self.ui = Ui_TesterWindow()
        self.ui.setupUi(self)
        self.ui.tableSequence.setModel(model)
        self.ui.tableSequence.setColumnWidth(0, 175)
        self.ui.tableSequence.setColumnWidth(1, 75)
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

        # Set up background worker for model updates
        self.worker = TestWorker(model)
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
        self._current_time_timer.timeout.connect(self._update_current_time)
        self._current_time_timer.start(1000)
        self._update_current_time()

    def _update_current_time(self):
        """
        Update the labelCurrentTime with the current time.
        """
        self.ui.labelCurrentTime.setText(
            QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        )

    @QtCore.Slot()
    def onAbout(self):
        """
        Show the About dialog with application information.
        """
        QtWidgets.QMessageBox.about(
            self,
            "About",
            f"{tester.__application__}\nVersion {tester.__version__}\nDeveloped by {tester.__company__}",
        )

    @QtCore.Slot()
    def onExit(self):
        """
        Handle the Exit action: stop the test and quit the application.
        """
        self.onStopTest()
        QtWidgets.QApplication.quit()

    @QtCore.Slot()
    def onOpen(self):
        """
        Handle the Open action: open a file dialog to select a test data file and load it.
        """
        QtCore.qInfo("Open menu clicked")
        file_path, ok = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open test data file",
            str(self.LastDirectory or ""),
            "Test Data files (*.past)",
        )
        if ok and file_path:
            self.LastDirectory = str(Path(file_path).parent)
            self.signalLoadData.emit(file_path)

    @QtCore.Slot()
    def onReport(self):
        """
        Handle the Report action: open a file dialog to select a location and generate a test report.
        """
        QtCore.qInfo("Generate Report menu clicked.")
        file_path, ok = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save test report file",
            str(self.LastDirectory or ""),
            "Test Report files (*.pdf)",
        )
        if ok and file_path:
            self.LastDirectory = str(Path(file_path).parent)
            self.signalGenerateReport.emit(file_path)

    @QtCore.Slot()
    def onSave(self):
        """
        Handle the Save action: open a file dialog to select a location and save the test data.
        """
        QtCore.qInfo("Save menu clicked.")
        file_path, ok = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save test data file",
            str(self.LastDirectory or ""),
            "Test Data files (*.past)",
        )
        if ok and file_path:
            self.LastDirectory = str(Path(file_path).parent)
            self.signalSaveData.emit(file_path)

    @QtCore.Slot()
    def onStartTest(self):
        """
        Handle the Start Test action: prompt for a serial number, validate it, and start the test.
        """
        QtCore.qInfo("Start test menu clicked.")
        _serial_number, _ok = QtWidgets.QInputDialog.getText(
            self, "Input", "Enter galvo serial number (q to quit):"
        )
        if not _ok or not _serial_number or _serial_number.strip().lower() == "q":
            return

        _serial_number = _serial_number.strip()
        if not _SERIAL_RE.fullmatch(_serial_number):
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Serial",
                "Serial number must be two uppercase letters followed by six digits.",
            )
            self._logger.error("Invalid serial number format.")
            return

        _model_name, _ok = QtWidgets.QInputDialog.getText(
            self, "Input", "Enter model name (e.g., 'Galvo-1234'):"
        )
        if not _ok or not _model_name:
            QtWidgets.QMessageBox.warning(
                self, "Invalid Model Name", "Model name cannot be empty."
            )
            self._logger.error("Model name cannot be empty.")
            return

        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(True)
        self.ui.actionReport.setEnabled(False)
        self.signalStartTest.emit(_serial_number, _model_name, "")

    @QtCore.Slot()
    def onStopTest(self):
        """
        Handle the Stop Test action: stop the current test and update UI actions.
        """
        QtCore.qInfo("Stop test menu clicked.")
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
            QtCore.qDebug(f"Table row selected: {row}.")
            self.model.loadUi(row, self.ui.widgetTest)
        else:
            QtCore.qDebug("No table row selected.")

    @QtCore.Slot(int)
    def onTestStarted(self, index: int):
        """
        Slot called when a test is started.

        Args:
            index (int): The index of the started test.
        """
        self.ui.tableSequence.selectRow(index)
        msg = f"Test {index + 1} started."
        self.ui.statusBar.showMessage(msg, 3000)
        QtCore.qInfo(msg)

    @QtCore.Slot(int, bool)
    def onTestFinished(self, index: int, result: bool):
        """
        Slot called when a test is finished.

        Args:
            index (int): The index of the finished test.
            result (bool): The result of the test (True for pass, False for fail).
        """
        msg = f"Test {index + 1} {'PASSED' if result else 'FAILED'}."
        self.ui.statusBar.showMessage(msg, 5000)
        QtCore.qInfo(msg)

    @QtCore.Slot()
    def onTestingComplete(self, result: bool):
        """
        Slot called when all tests are complete.

        Args:
            result (bool): The overall result of the test sequence.
        """
        QtCore.qInfo("All tests complete.")
        self.ui.actionStart.setEnabled(True)
        self.ui.actionStop.setEnabled(False)
        self.ui.actionReport.setEnabled(True)
        self.ui.statusBar.showMessage(msg, 5000)
        QtCore.qInfo(msg)

    @QtCore.Slot(str)
    def onFinishedGeneratingReport(self, file_path: str):
        """
        Slot called when the report generation is finished.
        Args:
            file_path (str): The path to the generated report file.
        """
        msg = f"Report generated: {file_path}"
        self.ui.statusBar.showMessage(msg, 5000)
        QtCore.qInfo(msg)

    @QtCore.Slot(str)
    def onFinishedLoadingData(self, file_path: str):
        """
        Slot called when the data loading is finished.
        Args:
            file_path (str): The path to the loaded data file.
        """
        msg = f"Data loaded from: {file_path}"
        self.ui.statusBar.showMessage(msg, 5000)
        QtCore.qInfo(msg)

    @QtCore.Slot(str)
    def onFinishedSavingData(self, file_path: str):
        """
        Slot called when the data saving is finished.
        Args:
            file_path (str): The path to the saved data file.
        """
        msg = f"Data saved to: {file_path}"
        self.ui.statusBar.showMessage(msg, 5000)
        QtCore.qInfo(msg)

    def show(self):
        """
        Show the main window and set up the status bar logging handler.

        Returns:
            None
        """
        self.setWindowTitle(tester.__application__)
        self.setWindowIcon(QtGui.QIcon(":/icons/icon.png"))

        class StatusBarHandler(logging.Handler):
            """
            Logging handler that updates the status bar with info messages.
            """

            def __init__(self, status_bar):
                super().__init__()
                self.status_bar = status_bar

            def emit(self, record):
                if record.levelno <= logging.INFO:
                    msg = self.format(record)
                    self.status_bar.showMessage(f"Status: {msg}")

        _status_bar_handler = StatusBarHandler(self.ui.statusBar)
        _status_bar_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(_status_bar_handler)

        return super().show()

    def showEvent(self, event):
        """
        Override showEvent to start the test if 'run' option is set.

        Args:
            event (QShowEvent): The show event.
        """
        super().showEvent(event)
        app = QtWidgets.QApplication.instance()
        if hasattr(app, "options") and app.options.isSet("run"):
            self.onStartTest()
