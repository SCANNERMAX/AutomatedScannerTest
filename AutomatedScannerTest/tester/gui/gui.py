# -*- coding: utf-8 -*-
from datetime import datetime
from PySide6 import QtCore, QtWidgets
import logging
import logging.handlers
from pathlib import Path
import re

import tester
from tester.manager.test_sequence import TestSequence
from tester.gui.tester_ui import Ui_TesterWindow


class TesterApp(QtWidgets.QApplication):
    """
    A custom QApplication subclass for the AutomatedScannerTest tester GUI.
    This class initializes the application with custom settings such as display name,
    organization, version, and logging. It also ensures the application quits when the
    last window is closed.
        *args: Additional positional arguments for QApplication.
        **kwargs: Additional keyword arguments for QApplication.
    Attributes:
        _logger (logging.Logger): Logger instance for the class.
        - Initializes a logger for the application.
    """

    def __init__(self, argv, *args, **kwargs):
        """
        Initializes the application with the provided command-line arguments and configuration.

        Args:
            argv (list): List of command-line arguments.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Side Effects:
            - Initializes the logger for the class.
            - Sets application display name, name, organization name, domain, and version.
            - Configures the application to quit when the last window is closed.
            - Logs debug messages for initialization and settings application.
        """
        super().__init__(argv, *args, **kwargs)
        self._logger = tester._get_class_logger(self.__class__)
        self._logger.debug("App initialized")
        self.applicationDisplayName = tester.__application__
        self.setApplicationName(tester.__application__)
        self.setOrganizationName(tester.__company__)
        self.setOrganizationDomain("pangolin.com")
        self.setApplicationVersion(tester.__version__)
        self.setQuitOnLastWindowClosed(True)
        self._logger.debug("App settings applied")


class TesterWindow(QtWidgets.QMainWindow):
    """
    TesterWindow is the main Qt application window for the Automated Scanner Test GUI.
    This class is responsible for initializing and managing the graphical user interface,
    including setting up UI components, handling user actions, and coordinating with the
    underlying data model (TestSequence). It provides menu actions for opening, saving,
    and reporting test data, as well as starting and stopping tests. The class also
    integrates a custom logging handler to display status messages in the application's
    status bar.
    Attributes:
        ui (Ui_TesterWindow): The UI object containing all widgets and actions.
        __model (TestSequence): The data model managing test sequences and settings.
        __logger (logging.Logger): Logger instance for the class.
    Properties:
        LastDirectory (str): Gets or sets the last directory used for file operations.
    Methods:
        __init__(*args, **kwargs): Initializes the main window, UI, model, and logging.
        on_about(): Displays an 'About' dialog with application information.
        on_open(): Handles the 'Open' action, allowing the user to select and load a test data file.
        on_save(): Handles the 'Save' action, allowing the user to specify a file path to save test data.
        on_start_test(): Handles the 'Start Test' action, prompting for and validating a serial number, then starting the test.
        on_stop_test(): Handles the 'Stop Test' action, stopping the current test and updating the UI.
        on_generate_report(): Handles the 'Generate Report' action, prompting for a file path and generating a test report.
    """

    @property
    def LastDirectory(self):
        """
        Returns the last directory path used for file operations.

        Retrieves the value associated with the "LastDirectory" setting from the model.

        Returns:
            str: The path of the last directory used.
        """
        return self.model.get_setting("LastDirectory")

    @LastDirectory.setter
    def LastDirectory(self, value: str):
        """
        Sets the last directory used for file operations.

        Args:
            value (str): The path to the last directory used.
        """
        self.model.set_settings("LastDirectory", value)

    def __init__(self, *args, **kwargs):
        """
        Initialize the main window for the tester GUI.
        This constructor sets up the main window, including the UI components, table model, column widths, and visibility of headers.
        It also configures a custom logging handler to display info-level log messages in the status bar, and connects UI actions
        (such as About, Open, Save, Start, Stop, and Report) to their respective handler methods.
        Args:
            *args: Variable length argument list for the parent class.
            **kwargs: Arbitrary keyword arguments for the parent class.
        """
        super().__init__(*args, **kwargs)
        self._logger = tester._get_class_logger(self.__class__)

        # Setup model
        self.model = TestSequence()

        # Setup the user interface
        self.ui = Ui_TesterWindow()
        self.ui.setupUi(self)
        self.ui.tableSequence.setModel(self.model)
        self.ui.tableSequence.setColumnWidth(0, 175)
        self.ui.tableSequence.setColumnWidth(1, 75)
        self.ui.tableSequence.verticalHeader().setVisible(False)

        # Connect to ui signals

        # Connect to ui signals
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

        # Connect to model signals
        self.model.computerNameChanged.connect(self.ui.labelComputerName.setText)
        self.model.durationChanged.connect(self.ui.labelDuration.setText)
        self.model.endTimeChanged.connect(self.ui.labelEndTime.setText)
        self.model.modelNameChanged.connect(self.ui.labelModelName.setText)
        self.model.serialNumberChanged.connect(self.ui.labelSerialNumber.setText)
        self.model.startTimeChanged.connect(self.ui.labelStartTime.setText)
        self.model.statusChanged.connect(self.ui.labelStatus.setText)
        self.model.testerNameChanged.connect(self.ui.labelTesterName.setText)
        self.model.testStarted.connect(self.ui.tableSequence.selectRow)

        # Add a logging handler to update the status bar with info messages
        class StatusBarHandler(logging.Handler):
            """Custom logging handler to update the status bar with info messages."""

            def __init__(self, status_bar):
                """Initialize the handler with the status bar."""
                super().__init__()
                self.status_bar = status_bar

            def emit(self, record):
                """Emit a log record to the status bar."""
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
        Displays an 'About' dialog box with application name, version, and company information.
        """
        QtWidgets.QMessageBox.about(
            self,
            "About",
            f"{tester.__application__}\nVersion {tester.__version__}\nDeveloped by {tester.__company__}",
        )

    @QtCore.Slot()
    def onExit(self):
        self.onStopTest()

    @QtCore.Slot()
    def onOpen(self):
        """
        Handles the 'Open' menu action by displaying a file dialog for the user to select a test data file.
        If a file is selected, updates the last accessed directory and delegates the file opening to the model.
        Logs actions and errors appropriately.
        """
        self._logger.info("Open menu clicked")
        file_path, ok = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open test data file", self.LastDirectory, "Test Data files (*.past)"
        )
        if ok and file_path:
            self.LastDirectory = Path(file_path).parent
            if not self.model:
                self._logger.error("Model is not initialized.")
                return
            self.model.on_open(file_path)

    @QtCore.Slot()
    def onSave(self):
        """
        Handles the Save menu action by opening a file dialog for the user to specify a file path to save test data.
        If a valid file path is selected, updates the last used directory and delegates the save operation to the model.
        Logs actions and errors appropriately.
        """
        self._logger.info("Save menu clicked")
        file_path, ok = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save test data file", self.LastDirectory, "Test Data files (*.past)"
        )
        if ok and file_path:
            self.LastDirectory = Path(file_path).parent
            if not self.model:
                self._logger.error("Model is not initialized.")
                return
            self.model.on_save(file_path)

    @QtCore.Slot()
    def onStartTest(self):
        """
        Handles the 'Start Test' menu action by prompting the user for a galvo serial number,
        validating its format, updating the UI state, and initiating the test process via the model.
        Steps:
        1. Prompts the user to enter a galvo serial number using an input dialog.
        2. Validates the serial number format (must match two uppercase letters followed by six digits).
        3. Updates the UI to reflect the test state (enables/disables relevant actions).
        4. Logs errors and exits early if the input is invalid or the model is uninitialized.
        5. Calls the model's `on_start_test` method with the validated serial number.
        """
        self._logger.info("Start test menu clicked")
        serial_number, ok = QtWidgets.QInputDialog.getText(
            self, "Input", "Enter galvo serial number (q to quit):"
        )
        if not ok or not serial_number:
            return  # User cancelled or entered nothing

        if not re.match(r"^[A-Z]{2}[0-9]{6}$", serial_number):
            self._logger.error("Invalid serial number format.")
            return

        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(True)
        self.ui.actionReport.setEnabled(False)
        if not self.model:
            self._logger.error("Model is not initialized.")
            return
        self.model.on_start_test(serial_number)

    @QtCore.Slot()
    def onStopTest(self):
        """
        Handles the Stop Test menu action by logging the event, checking if the model is initialized,
        invoking the model's stop test method, and updating the UI actions' enabled states accordingly.
        """
        self._logger.info("Stop test menu clicked")
        if not self.model:
            self._logger.error("Model is not initialized.")
            return
        self.model.on_stop_test()
        self.ui.actionStart.setEnabled(True)
        self.ui.actionStop.setEnabled(False)
        self.ui.actionReport.setEnabled(True)

    @QtCore.Slot()
    def onReport(self):
        """
        Handles the 'Generate Report' menu action by prompting the user to select a file path for saving a test report.
        If a valid file path is selected and the model is initialized, it triggers the report generation process.
        Logs actions and errors appropriately.
        """
        self._logger.info("Generate Report menu clicked")
        file_path, ok = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save test report file",
            self.LastDirectory,
            "Test Report files (*.pdf)",
        )
        if ok and file_path:
            self.LastDirectory = Path(file_path).parent
            if not self.model:
                self._logger.error("Model is not initialized.")
                return
            self.model.on_generate_report(file_path)

    @QtCore.Slot(object, object)
    def on_tableSequence_selectionChanged(self, selected, deselected):
        """
        Handles the selection change in the tableSequence view.
        Updates the UI or model based on the newly selected row(s).
        Args:
            selected (QItemSelection): Newly selected indexes.
            deselected (QItemSelection): Previously selected indexes.
        """
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            self._logger.debug(f"Table row selected: {row}")
            # Optionally, update UI or model with the selected row
            # Example: self.model.set_current_row(row)
            self.__model.load_ui(row, self.ui.widgetTest)
        else:
            self._logger.debug("No table row selected.")
