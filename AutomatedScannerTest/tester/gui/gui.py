# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets
import logging
from pathlib import Path
import re

import tester
from tester.manager.test_sequence import TestSequence
from tester.gui.tester_ui import Ui_TesterWindow


class TesterApp(QtWidgets.QApplication):
    """
    Custom QApplication for AutomatedScannerTest GUI.

    Sets up application metadata and logging for the AutomatedScannerTest application.
    """

    def __init__(self, argv, *args, **kwargs):
        """
        Initialize the TesterApp with application-specific settings and logging.

        Args:
            argv: List of command-line arguments.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(argv, *args, **kwargs)
        self._logger = tester._get_class_logger(self.__class__)
        self.setApplicationDisplayName(tester.__application__)
        self.setApplicationName(tester.__application__)
        self.setOrganizationName(tester.__company__)
        self.setOrganizationDomain("pangolin.com")
        self.setApplicationVersion(tester.__version__)
        self.setQuitOnLastWindowClosed(True)
        self._logger.debug("App initialized and settings applied")


class TesterWindow(QtWidgets.QMainWindow):
    """
    Main Qt application window for the Automated Scanner Test GUI.

    Manages the main window, UI setup, user actions, and coordinates with the TestSequence model.
    """

    @property
    def LastDirectory(self):
        """
        Get the last directory path used for file operations.

        Returns:
            str: The last directory path used.
        """
        return self.model._get_setting("LastDirectory")

    @LastDirectory.setter
    def LastDirectory(self, value: str):
        """
        Set the last directory used for file operations.

        Args:
            value (str): The directory path to set.
        """
        self.model._set_setting("LastDirectory", value)

    def __init__(self, *args, **kwargs):
        """
        Initialize the TesterWindow, set up the UI, connect signals, and configure logging.
        """
        super().__init__(*args, **kwargs)
        self._logger = tester._get_class_logger(self.__class__)

        # Setup model and UI
        self.model = TestSequence()
        self.ui = Ui_TesterWindow()
        self.ui.setupUi(self)
        self.ui.tableSequence.setModel(self.model)
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

        # Connect model signals
        self.model.computerNameChanged.connect(self.ui.labelComputerName.setText)
        self.model.durationChanged.connect(self.ui.labelDuration.setText)
        self.model.endTimeChanged.connect(self.ui.labelEndTime.setText)
        self.model.modelNameChanged.connect(self.ui.labelModelName.setText)
        self.model.serialNumberChanged.connect(self.ui.labelSerialNumber.setText)
        self.model.startTimeChanged.connect(self.ui.labelStartTime.setText)
        self.model.statusChanged.connect(self.ui.labelStatus.setText)
        self.model.testerNameChanged.connect(self.ui.labelTesterName.setText)
        self.model.testStarted.connect(self.ui.tableSequence.selectRow)

        # Status bar logging handler
        class StatusBarHandler(logging.Handler):
            """
            Logging handler that updates the status bar with info messages.
            """
            def __init__(self, status_bar):
                """
                Initialize the handler.

                Args:
                    status_bar (QStatusBar): The status bar to update.
                """
                super().__init__()
                self.status_bar = status_bar
            def emit(self, record):
                """
                Emit a log record to the status bar if the level is INFO or lower.

                Args:
                    record (LogRecord): The log record to emit.
                """
                if record.levelno <= logging.INFO:
                    msg = self.format(record)
                    self.status_bar.showMessage(f"Status: {msg}")

        _status_bar_handler = StatusBarHandler(self.ui.statusBar)
        _status_bar_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(_status_bar_handler)
        self._logger.info("Initializing TesterWindow")

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
        self._logger.info("Open menu clicked")
        file_path, ok = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open test data file", str(self.LastDirectory or ""), "Test Data files (*.past)"
        )
        if ok and file_path:
            self.LastDirectory = str(Path(file_path).parent)
            if self.model:
                self.model.on_open(file_path)
            else:
                self._logger.error("Model is not initialized.")

    @QtCore.Slot()
    def onSave(self):
        """
        Handle the Save action: open a file dialog to select a location and save the test data.
        """
        self._logger.info("Save menu clicked")
        file_path, ok = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save test data file", str(self.LastDirectory or ""), "Test Data files (*.past)"
        )
        if ok and file_path:
            self.LastDirectory = str(Path(file_path).parent)
            if self.model:
                self.model.on_save(file_path)
            else:
                self._logger.error("Model is not initialized.")

    @QtCore.Slot()
    def onStartTest(self):
        """
        Handle the Start Test action: prompt for a serial number, validate it, and start the test.
        """
        self._logger.info("Start test menu clicked")
        serial_number, ok = QtWidgets.QInputDialog.getText(
            self, "Input", "Enter galvo serial number (q to quit):"
        )
        if not ok or not serial_number or serial_number.strip().lower() == "q":
            return
        serial_number = serial_number.strip()
        if not re.fullmatch(r"[A-Z]{2}[0-9]{6}", serial_number):
            QtWidgets.QMessageBox.warning(
                self, "Invalid Serial",
                "Serial number must be two uppercase letters followed by six digits."
            )
            self._logger.error("Invalid serial number format.")
            return
        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(True)
        self.ui.actionReport.setEnabled(False)
        if self.model:
            self.model.on_start_test(serial_number)
        else:
            self._logger.error("Model is not initialized.")

    @QtCore.Slot()
    def onStopTest(self):
        """
        Handle the Stop Test action: stop the current test and update UI actions.
        """
        self._logger.info("Stop test menu clicked")
        if self.model:
            self.model.on_stop_test()
            self.ui.actionStart.setEnabled(True)
            self.ui.actionStop.setEnabled(False)
            self.ui.actionReport.setEnabled(True)
        else:
            self._logger.error("Model is not initialized.")

    @QtCore.Slot()
    def onReport(self):
        """
        Handle the Report action: open a file dialog to select a location and generate a test report.
        """
        self._logger.info("Generate Report menu clicked")
        file_path, ok = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save test report file",
            str(self.LastDirectory or ""),
            "Test Report files (*.pdf)",
        )
        if ok and file_path:
            self.LastDirectory = str(Path(file_path).parent)
            if self.model:
                self.model.on_generate_report(file_path)
            else:
                self._logger.error("Model is not initialized.")

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
            self._logger.debug(f"Table row selected: {row}")
            self.model.load_ui(row, self.ui.widgetTest)
        else:
            self._logger.debug("No table row selected.")
