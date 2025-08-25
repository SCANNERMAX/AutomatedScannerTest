# -*- coding: utf-8 -*-
"""
Test framework base classes and utilities for AutomatedScannerTest.

This module provides:
- CancelToken: a simple cancellation token for test interruption.
- Test: the base class for all tests, with parameter/state management, settings, and UI hooks.
- _test_list: a utility to discover all test classes in the tester.tests package.
"""

from PySide6 import QtCore, QtWidgets
from asyncio import CancelledError
import logging

from tester import CancelToken
from tester.manager.devices import DeviceManager
from tester.manager.report import TestReportGenerator

logger = logging.getLogger(__name__)


class Test(QtCore.QObject):
    """
    Base model class for all tests in the AutomatedScannerTest framework.
    Provides core interface and state management for test execution, parameter handling,
    UI integration, and reporting.

    Signals:
        durationChanged(str): Emitted when the duration changes.
        endTimeChanged(str): Emitted when the end time changes.
        nameChanged(str): Emitted when the name changes.
        serialNumberChanged(str): Emitted when the serial number changes.
        startTimeChanged(str): Emitted when the start time changes.
        statusChanged(str): Emitted when the status changes.
        parameterChanged(str, object): Emitted when a parameter changes.

    Properties:
        Duration (float): The duration of the test in seconds.
        EndTime (QDateTime): The end time of the test.
        Name (str): The name of the test.
        SerialNumber (str): The serial number associated with the test.
        StartTime (QDateTime): The start time of the test.
        Status (str): The status of the test.
    """

    durationChanged = QtCore.Signal(str)
    endTimeChanged = QtCore.Signal(str)
    modelNameChanged = QtCore.Signal(str)
    nameChanged = QtCore.Signal(str)
    parameterChanged = QtCore.Signal(str, object)
    serialNumberChanged = QtCore.Signal(str)
    startTimeChanged = QtCore.Signal(str)
    statusChanged = QtCore.Signal(str)

    def __init__(self, name: str, cancel: CancelToken, devices: DeviceManager):
        logger.debug(f"[Test] Initializing Test instance with name: {name}")
        super().__init__()
        self._parameters = {}
        self.resetTestData()
        self.Name = name
        app = QtCore.QCoreApplication.instance()
        if not (app and hasattr(app, "addSettingsToObject")):
            logger.critical(
                f"[Test] Test class must be initialized within a TesterApp instance."
            )
            raise RuntimeError(
                f"Test class must be initialized within a TesterApp instance."
            )
        app.addSettingsToObject(self)
        self.cancel = cancel
        self.devices = devices
        self.widgetTestData = None
        logger.debug(f"[Test] Instance initialized.")

    def __repr__(self):
        return f"<Test: {self.Name}>"

    def __str__(self):
        return f"Test: {self.Name}\n{self.__doc__ if self.__doc__ else 'No description provided.'}"

    @QtCore.Property(float, notify=durationChanged)
    def Duration(self):
        """
        Get the test duration in seconds.

        Returns:
            float: The duration of the test in seconds.
        """
        return self.getParameter("Duration", 0.0)

    @Duration.setter
    def Duration(self, value):
        """
        Set the test duration and emit the durationChanged signal.

        Args:
            value (float): The duration in seconds.
        """
        self.setParameter("Duration", value)
        self.durationChanged.emit(f"{value} sec")

    @QtCore.Property(QtCore.QDateTime, notify=endTimeChanged)
    def EndTime(self):
        """
        Get the end time of the test.

        Returns:
            QDateTime: The end time of the test.
        """
        return self.getParameter("EndTime", self.getCurrentTime())

    @EndTime.setter
    def EndTime(self, value):
        """
        Set the end time of the test and emit the endTimeChanged signal.

        Args:
            value (QDateTime): The end time.
        """
        if not isinstance(value, QtCore.QDateTime):
            logger.error(f"[Test] EndTime must be a QDateTime instance.")
            raise ValueError("EndTime must be a QDateTime instance.")
        self.setParameter("EndTime", value)
        valueString = (
            value.toString("HH:mm:ss") if value and value.isValid() else "Not Set"
        )
        self.endTimeChanged.emit(valueString)
        self.Duration = self.StartTime.secsTo(value)

    @QtCore.Property(str, notify=modelNameChanged)
    def ModelName(self):
        """
        Get the model name associated with the test.
        Returns:
            str: The model name.
        """
        return self.getParameter("ModelName", "")

    @ModelName.setter
    def ModelName(self, value):
        """
        Set the model name and emit the modelNameChanged signal.
        Args:
            value (str): The model name.
        """
        self.setParameter("ModelName", value)
        self.modelNameChanged.emit(value)

    @QtCore.Property(str, notify=nameChanged)
    def Name(self):
        """
        Get the name of the test.

        Returns:
            str: The test name.
        """
        return self.getParameter("Name", "")

    @Name.setter
    def Name(self, value):
        """
        Set the name of the test and emit the nameChanged signal.

        Args:
            value (str): The test name.
        """
        self.setParameter("Name", value)
        self.nameChanged.emit(value)

    @QtCore.Property(str, notify=serialNumberChanged)
    def SerialNumber(self):
        """
        Get the serial number associated with the test.

        Returns:
            str: The serial number.
        """
        return self.getParameter("SerialNumber", "")

    @SerialNumber.setter
    def SerialNumber(self, value):
        """
        Set the serial number and emit the serialNumberChanged signal.

        Args:
            value (str): The serial number.
        """
        self.setParameter("SerialNumber", value)
        self.serialNumberChanged.emit(value)

    @QtCore.Property(QtCore.QDateTime, notify=startTimeChanged)
    def StartTime(self):
        """
        Get the start time of the test.

        Returns:
            QDateTime: The start time of the test.
        """
        return self.getParameter("StartTime", self.getCurrentTime())

    @StartTime.setter
    def StartTime(self, value):
        """
        Set the start time of the test and emit the startTimeChanged signal.

        Args:
            value (QDateTime): The start time.
        """
        if not isinstance(value, QtCore.QDateTime):
            logger.error(f"[Test] StartTime must be a QDateTime instance.")
            raise ValueError("StartTime must be a QDateTime instance.")
        self.setParameter("StartTime", value)
        valueString = (
            value.toString("HH:mm:ss") if value and value.isValid() else "Not Set"
        )
        self.startTimeChanged.emit(valueString)

    @QtCore.Property(str, notify=statusChanged)
    def Status(self):
        """
        Get the status of the test.

        Returns:
            str: The test status.
        """
        return self.getParameter("Status", "")

    @Status.setter
    def Status(self, value):
        """
        Set the status of the test and emit the statusChanged signal.

        Args:
            value (str): The test status.
        """
        self.setParameter("Status", value)
        self.statusChanged.emit(value)

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Handle settings modifications by updating the test as needed.
        """
        logger.debug(f"[Test] Settings modified.")

    def getParameter(self, key: str, default):
        """
        Get a parameter value by key, or return the default if not present.

        Args:
            key (str): The parameter key.
            default (any): The default value if not present.

        Returns:
            any: The parameter value.
        """
        value = self._parameters.get(key, default)
        logger.debug(f'[Test] Retrieved parameter "{key}": {value}')
        return value

    def setParameter(self, key: str, value):
        """
        Set a parameter value and emit the parameterChanged signal.

        Args:
            key (str): The parameter key.
            value (any): The value to set.
        """
        logger.debug(f'[Test] Setting parameter "{key}" to: {value}')
        self._parameters[key] = value
        self.parameterChanged.emit(key, value)

    def getCurrentTime(self) -> QtCore.QDateTime:
        """
        Get the current local time as a QDateTime in the system's current time zone.

        Returns:
            QDateTime: The current local time.
        """
        now = QtCore.QDateTime.currentDateTime()
        now.setTimeZone(QtCore.QTimeZone.systemTimeZone())
        return now

    def cliPrintTest(self):
        """
        Print the test name and docstring to the console.
        """
        logger.debug(f"[Test] cliPrintTest called")
        print(f"- {self.Name}:")
        if self.__doc__:
            print(
                "\n".join(
                    f"    {line.strip()}" for line in self.__doc__.strip().splitlines()
                )
            )

    def setupReportGenerator(self, reportGenerator: TestReportGenerator) -> None:
        """
        Configure the provided TestReportGenerator with this test's parameters.
        Args:
            reportGenerator (TestReportGenerator): The report generator to configure.
        """
        logger.debug(f"[Test] Setting up report generator.")
        if not isinstance(reportGenerator, TestReportGenerator):
            logger.error(
                f"[Test] reportGenerator must be a TestReportGenerator instance."
            )
            raise ValueError("reportGenerator must be a TestReportGenerator instance.")
        self.durationChanged.connect(
            lambda value: reportGenerator.onTestInfoChanged(
                self.Name, "Duration", value
            )
        )
        self.endTimeChanged.connect(
            lambda value: reportGenerator.onTestInfoChanged(self.Name, "EndTime", value)
        )
        self.modelNameChanged.connect(
            lambda value: reportGenerator.onTestInfoChanged(
                self.Name, "ModelName", value
            )
        )
        self.serialNumberChanged.connect(
            lambda value: reportGenerator.onTestInfoChanged(
                self.Name, "SerialNumber", value
            )
        )
        self.startTimeChanged.connect(
            lambda value: reportGenerator.onTestInfoChanged(
                self.Name, "StartTime", value
            )
        )
        self.statusChanged.connect(
            lambda value: reportGenerator.onTestInfoChanged(self.Name, "Status", value)
        )

    def setupUi(self, parent=None):
        """
        Load the test UI into the provided widget.

        Args:
            parent (QtWidgets.QWidget): The parent widget for the test UI.
        """
        logger.debug("[Test] Loading UI.")
        if not isinstance(parent, QtWidgets.QWidget):
            logger.critical("[Test] Parent must be a QWidget instance.")
            raise ValueError("Parent must be a QWidget instance.")
        cname = self.__class__.__name__
        parent.setObjectName(f"widget{cname}")
        layout = QtWidgets.QHBoxLayout(parent)
        layout.setObjectName(f"layout{cname}")
        parent.setLayout(layout)

        # Left panel with test parameters
        groupBoxWidget = QtWidgets.QGroupBox(parent)
        groupBoxWidget.setObjectName(f"groupBox{cname}")
        groupBoxWidget.setCheckable(False)
        groupBoxWidget.setFixedWidth(150)
        groupBoxWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
        )
        groupBoxLayout = QtWidgets.QVBoxLayout(groupBoxWidget)
        groupBoxLayout.setObjectName(f"layout{cname}Params")
        groupBoxLayout.setContentsMargins(5, 5, 5, 5)
        groupBoxWidget.setLayout(groupBoxLayout)
        layout.addWidget(groupBoxWidget)

        # Predefine label info to avoid repeated code
        label_info = [
            ("Name", self.Name, self.nameChanged),
            ("Serial Number", self.SerialNumber, self.serialNumberChanged),
            ("Start Time", self.StartTime.toString("HH:mm:ss"), self.startTimeChanged),
            ("End Time", self.EndTime.toString("HH:mm:ss"), self.endTimeChanged),
            ("Duration", self.Duration, self.durationChanged),
            ("Status", self.Status, self.statusChanged),
        ]

        def add_label(name, text, signal):
            label_name = f"label{cname}{name}".replace(" ", "")
            param_label = QtWidgets.QLabel(groupBoxWidget)
            param_label.setObjectName(f"{label_name}Title")
            param_label.setText(f"<b>{name}</b>")
            param_label.setTextFormat(QtCore.Qt.RichText)
            groupBoxLayout.addWidget(param_label)
            label = QtWidgets.QLabel(groupBoxWidget)
            label.setObjectName(label_name)
            label.setText(str(text))
            label.setFixedWidth(300)
            signal.connect(label.setText)
            groupBoxLayout.addWidget(label)
            return label

        # Use a loop to add labels efficiently
        (
            self.labelTestName,
            self.labelSerialNumber,
            self.labelStartTime,
            self.labelEndTime,
            self.labelDuration,
            self.labelStatus,
        ) = [add_label(*info) for info in label_info]

        # Add an expanding spacer at the bottom
        spacer_widget = QtWidgets.QWidget(groupBoxWidget)
        spacer_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        groupBoxLayout.addWidget(spacer_widget)

        self.widgetTestData = QtWidgets.QWidget(parent)
        self.widgetTestData.setObjectName(f"widget{cname}Data")
        self.widgetTestData.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        layout.addWidget(self.widgetTestData)

    def onLoadData(self, data: dict):
        """
        Load parameters from a dictionary into the test.

        Args:
            data (dict): The parameter dictionary to load.
        """
        logger.debug(f"[Test] Loading data: {data}")
        keys = []
        for key, value in data.items():
            keys.append(key)
        keys.reverse()
        for key in keys:
            try:
                setattr(self, key, data[key])
                logger.debug(f'[Test] Set attribute "{key}" to "{data[key]}"')
            except AttributeError:
                logger.warning(f'[Test] Attribute "{key}" not found')

    def onSaveData(self) -> dict:
        """
        Return a dictionary of the current test parameters.

        Returns:
            dict: The current parameters.
        """
        logger.debug(f"[Test] Saving parameters: {self._parameters}")
        return dict(self._parameters)

    def onStartTest(self, data_directory: str) -> bool:
        """
        Run the full test sequence: setup, run, teardown, and analysis.

        Returns:
            bool: True if the test and analysis succeed, False otherwise.
        """
        logger.debug(f'[Test] Starting in directory "{data_directory}"')
        try:
            self.setDataDirectory(data_directory)
            self.StartTime = self.getCurrentTime()
            self.checkCancelled()
            logger.info(f'[Test] Beginning device setup for test "{self.Name}"')
            self.setup()
            self.checkCancelled()
            logger.info(f'[Test] Beginning execution for test "{self.Name}"')
            self.run()
            self.checkCancelled()
            logger.info(f'[Test] Analyzing collected data for test "{self.Name}"')
            result = self.analyzeResults()
            self.checkCancelled()
            self.Status = "Pass" if result else "Fail"
            logger.info(
                f'[Test] Test "{self.Name}" completed with status: {self.Status}'
            )
            return result
        except CancelledError:
            self.Status = "Cancelled"
            logger.warning(f'[Test] Test "{self.Name}" was cancelled.')
            return False
        except Exception as e:
            self.Status = "Error"
            logger.critical(f'[Test] Exception in test "{self.Name}": {e}')
            return False
        finally:
            logger.info(f'[Test] Beginning teardown for test "{self.Name}"')
            self.teardown()
            self.EndTime = self.getCurrentTime()

    def resetTestData(self):
        """
        Reset the test state and parameters to their initial values.
        """
        logger.debug(f"[Test] Resetting parameters")
        self.SerialNumber = ""
        self.ModelName = ""
        self.StartTime = QtCore.QDateTime()
        self.EndTime = QtCore.QDateTime()
        self.Status = "Not Started"

    def checkCancelled(self):
        """
        Check if the test has been cancelled and raise CancelledError if so.

        Raises:
            CancelledError: If the test has been cancelled.
        """
        if hasattr(self.cancel, "isCancelled") and self.cancel.isCancelled():
            logger.warning(f"[Test] Detected cancellation.")
            raise CancelledError(f'Test "{self.Name}" was cancelled.')

    def setDataDirectory(self, data_directory: str):
        """
        Set the data directory for the test.

        Args:
            data_directory (str): The path to the data directory.
        """
        logger.debug(f'[Test] Setting data directory to "{data_directory}"')
        dir_obj = QtCore.QDir(data_directory)
        test_dir_path = dir_obj.filePath(self.Name)
        test_dir = QtCore.QDir(test_dir_path)
        if not test_dir.exists("."):
            logger.debug(f'Creating directory "{self.Name}" in "{data_directory}"')
            dir_obj.mkpath(self.Name)
        self.dataDirectory = test_dir_path

    def setup(self):
        """
        Perform setup actions before running the test.
        """
        logger.debug(f"[Test] Running setup")
        if hasattr(self.devices, "test_setup"):
            self.devices.test_setup()

    def run(self):
        """
        Execute the main test logic. Should be overridden by subclasses.
        """
        logger.debug(f"[Test] Running main test logic")

    def analyzeResults(self) -> bool:
        """
        Analyze the test results and update the end time, duration, and status.

        Returns:
            bool: True if analysis is successful.
        """
        logger.debug(f"[Test] Analyzing results")
        return True

    def teardown(self):
        """
        Perform teardown actions after running the test.
        """
        logger.debug(f"[Test] Running teardown")
        if hasattr(self.devices, "test_teardown"):
            self.devices.test_teardown()
