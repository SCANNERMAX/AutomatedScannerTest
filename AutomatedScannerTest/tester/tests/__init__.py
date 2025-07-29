# -*- coding: utf-8 -*-
import inspect
from PySide6 import QtCore, QtWidgets
from datetime import datetime
from dateutil import tz
import importlib
import logging
import os
from pathlib import Path

import tester
from tester.manager.devices import DeviceManager
from tester.manager.report import TestReport


class CancelToken:
    """
    A simple token class to signal cancellation of an operation.

    Attributes
    ----------
    cancelled : bool
        Indicates whether the operation has been cancelled.
    """

    __slots__ = ("cancelled",)

    def __init__(self):
        """
        Initializes the CancelToken with cancelled set to False.
        """
        self.cancelled = False

    def cancel(self):
        """
        Sets the cancelled flag to True, indicating the operation should be cancelled.
        """
        self.cancelled = True

    def reset(self):
        """
        Resets the cancelled flag to False, allowing reuse of the token.
        """
        self.cancelled = False


def _test_list() -> list:
    """
    Discovers and returns a list of all test classes derived from the Test base class
    within the tester.tests package.

    Returns
    -------
    list
        A list of test class types derived from Test.
    """
    _tests = []
    _test_module = importlib.import_module(Test.__module__)
    _test_folder = os.path.dirname(_test_module.__file__)

    py_files = [f for f in os.listdir(_test_folder) if f.endswith(".py") and not f.startswith("__")]
    for _filename in py_files:
        _module_name = f"tester.tests.{_filename[:-3]}"
        try:
            _module = importlib.import_module(_module_name)
        except Exception as e:
            logging.warning(f"Could not import {_module_name}: {e}")
            continue

        # Use tuple unpacking and list comprehension for better performance
        _tests.extend(
            obj for _, obj in inspect.getmembers(_module, inspect.isclass)
            if issubclass(obj, Test) and obj is not Test
        )
    return _tests


class Test(QtCore.QObject):
    """
    Base model class for all tests in the AutomatedScannerTest framework.

    This class provides the core interface and state management for test execution,
    parameter handling, UI integration, and reporting.

    Parameters
    ----------
    name : str
        The name of the test.
    settings : QtCore.QSettings
        The settings object for persistent storage.
    cancel : CancelToken
        The cancellation token for test interruption.

    Attributes
    ----------
    parameterChanged : QtCore.Signal
        Signal emitted when a parameter changes.
    durationChanged : QtCore.Signal
        Signal emitted when the duration changes.
    endTimeChanged : QtCore.Signal
        Signal emitted when the end time changes.
    nameChanged : QtCore.Signal
        Signal emitted when the name changes.
    serialNumberChanged : QtCore.Signal
        Signal emitted when the serial number changes.
    startTimeChanged : QtCore.Signal
        Signal emitted when the start time changes.
    statusChanged : QtCore.Signal
        Signal emitted when the status changes.
    """

    def __init__(self, name: str, settings: QtCore.QSettings, cancel: CancelToken):
        """
        Initializes the Test instance with the given name, settings, and cancel token.

        Parameters
        ----------
        name : str
            The name of the test.
        settings : QtCore.QSettings
            The settings object for persistent storage.
        cancel : CancelToken
            The cancellation token for test interruption.
        """
        super().__init__()
        app = QtCore.QCoreApplication.instance()
        if app.__class__.__name__ == "TesterApp":
            self.logger = app.get_logger(self.__class__.__name__)
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
        self.__timezone = tz.tzlocal()
        self.__settings = settings
        self.__parameters = {}
        self.widgetTestMain = None
        self._cancel = cancel
        self.Name = name
        self.resetParameters()

    def onSettingsModified(self):
        """
        Handles settings modifications by updating the timezone if necessary.
        This method is called when the settings are modified.
        """
        self.logger.debug(f"Settings modified, updating {self.Name}.")

    def getDuration(self) -> float:
        """
        Gets the test duration in seconds.

        Returns
        -------
        float
            The duration of the test in seconds.
        """
        return self.getParameter("Duration", 0.0)

    def setDuration(self, value: float):
        """
        Sets the test duration and emits the durationChanged signal.

        Parameters
        ----------
        value : float
            The duration in seconds.
        """
        self.setParameter("Duration", value)
        self.durationChanged.emit(f"{value} sec")

    Duration = QtCore.Property(float, getDuration, setDuration)

    def getEndTime(self) -> datetime:
        """
        Gets the end time of the test.

        Returns
        -------
        datetime
            The end time of the test.
        """
        return self.getParameter("EndTime", self.getTime())

    def setEndTime(self, value: datetime):
        """
        Sets the end time of the test and emits the endTimeChanged signal.

        Parameters
        ----------
        value : datetime
            The end time.
        """
        self.setParameter("EndTime", value)
        self.endTimeChanged.emit(value.strftime("%H:%M:%S") if value else "")

    EndTime = QtCore.Property(datetime, getEndTime, setEndTime)

    def getName(self) -> str:
        """
        Gets the name of the test.

        Returns
        -------
        str
            The test name.
        """
        return self.getParameter("Name", "")

    def setName(self, value: str):
        """
        Sets the name of the test and emits the nameChanged signal.

        Parameters
        ----------
        value : str
            The test name.
        """
        self.setParameter("Name", value)
        self.nameChanged.emit(value)

    Name = QtCore.Property(str, getName, setName)

    def getSerialNumber(self) -> str:
        """
        Gets the serial number associated with the test.

        Returns
        -------
        str
            The serial number.
        """
        return self.getParameter("SerialNumber", "")

    def setSerialNumber(self, value: str):
        """
        Sets the serial number and emits the serialNumberChanged signal.

        Parameters
        ----------
        value : str
            The serial number.
        """
        self.setParameter("SerialNumber", value)
        self.serialNumberChanged.emit(value)

    SerialNumber = QtCore.Property(str, getSerialNumber, setSerialNumber)

    def getStartTime(self) -> datetime:
        """
        Gets the start time of the test.

        Returns
        -------
        datetime
            The start time of the test.
        """
        return self.getParameter("StartTime", self.getTime())

    def setStartTime(self, value: datetime):
        """
        Sets the start time of the test and emits the startTimeChanged signal.

        Parameters
        ----------
        value : datetime
            The start time.
        """
        self.setParameter("StartTime", value)
        self.startTimeChanged.emit(value.strftime("%H:%M:%S") if value else "")

    StartTime = QtCore.Property(datetime, getStartTime, setStartTime)

    def getStatus(self) -> str:
        """
        Gets the status of the test.

        Returns
        -------
        str
            The test status.
        """
        return self.getParameter("Status", None)

    def setStatus(self, value: str):
        """
        Sets the status of the test and emits the statusChanged signal.

        Parameters
        ----------
        value : str
            The test status.
        """
        self.setParameter("Status", value)
        self.statusChanged.emit(value)

    Status = QtCore.Property(str, getStatus, setStatus)

    def getParameter(self, key: str, default):
        """
        Gets a parameter value by key, or sets it to default if not present.

        Parameters
        ----------
        key : str
            The parameter key.
        default : any
            The default value if the key is not present.

        Returns
        -------
        any
            The parameter value.
        """
        # Use dict.setdefault for atomic get-or-set
        return self.__parameters.setdefault(key, default)

    def setParameter(self, key: str, value):
        """
        Sets a parameter value and emits the parameterChanged signal.

        Parameters
        ----------
        key : str
            The parameter key.
        value : any
            The value to set.
        """
        self.__parameters[key] = value
        self.parameterChanged.emit(key, value)

    def getSetting(self, key: str, default):
        """
        Gets a persistent setting value for this test, or sets it to default if not present.

        Parameters
        ----------
        key : str
            The setting key.
        default : any
            The default value if the key is not present.

        Returns
        -------
        any
            The setting value.
        """
        self.__settings.beginGroup(self.Name)
        try:
            if self.__settings.contains(key):
                return self.__settings.value(key)
            self.__settings.setValue(key, default)
            return default
        finally:
            self.__settings.endGroup()

    def setSetting(self, key: str, value):
        """
        Sets a persistent setting value for this test.

        Parameters
        ----------
        key : str
            The setting key.
        value : any
            The value to set.
        """
        self.__settings.beginGroup(self.Name)
        try:
            self.__settings.setValue(key, value)
        finally:
            self.__settings.endGroup()

    def getTime(self) -> datetime:
        """
        Gets the current local time in the configured timezone.

        Returns
        -------
        datetime
            The current local time.
        """
        return datetime.now(self.__timezone)

    @tester._member_logger
    def analyzeResults(self, serial_number: str) -> bool:
        """
        Analyzes the test results and updates the end time, duration, and status.

        Parameters
        ----------
        serial_number : str
            The serial number of the device under test.

        Returns
        -------
        bool
            True if analysis is successful.
        """
        self.logger.info(f"Analyzing {self.Name} results for {serial_number}...")
        self.EndTime = self.getTime()
        self.Duration = (self.EndTime - self.StartTime).total_seconds()
        self.Status = "Pass"
        return True

    @tester._member_logger
    def setupUi(self, widget: QtWidgets.QWidget):
        """
        Loads the test UI into the provided widget.

        Parameters
        ----------
        widget : QtWidgets.QWidget
            The parent widget for the test UI.
        """
        self.logger.info(f"Loading UI for test {self.Name}...")
        self.widgetTestMain = widget

        layoutTestMain = QtWidgets.QHBoxLayout(widget)
        layoutTestMain.setObjectName("layoutTestMain")
        layoutTestMain.setContentsMargins(0, 0, 0, 0)

        groupBox = QtWidgets.QGroupBox(widget)
        groupBox.setObjectName("groupBoxTestParameters")
        groupBox.setAutoFillBackground(True)
        groupBox.setCheckable(False)
        layoutTestMain.addWidget(groupBox)

        layoutParams = QtWidgets.QVBoxLayout(groupBox)
        layoutParams.setObjectName("layoutTestParameters")

        def add_label(obj_name, text, signal):
            """
            Helper to add a QLabel to the layout and connect it to a signal.

            Parameters
            ----------
            obj_name : str
                The object name for the label.
            text : any
                The initial text for the label.
            signal : QtCore.Signal
                The signal to connect for updating the label text.

            Returns
            -------
            QtWidgets.QLabel
                The created label.
            """
            label = QtWidgets.QLabel(groupBox)
            label.setObjectName(obj_name)
            label.setText(str(text))
            signal.connect(label.setText)
            layoutParams.addWidget(label)
            return label

        self.labelTestName = add_label("labelTestName", self.Name, self.nameChanged)
        self.labelSerialNumber = add_label("labelSerialNumber", self.SerialNumber, self.serialNumberChanged)
        self.labelStartTime = add_label("labelStartTime", self.StartTime, self.startTimeChanged)
        self.labelEndTime = add_label("labelEndTime", self.EndTime, self.endTimeChanged)
        self.labelDuration = add_label("labelDuration", self.Duration, self.durationChanged)
        self.labelStatus = add_label("labelStatus", self.Status, self.statusChanged)

        self.widgetTestData = QtWidgets.QWidget(widget)
        self.widgetTestData.setObjectName("widgetTestData")
        self.layoutTestData = QtWidgets.QVBoxLayout(self.widgetTestData)
        self.layoutTestData.setObjectName("layoutTestData")

    @tester._member_logger
    def onGenerateReport(self, report: TestReport):
        """
        Adds this test's results to the provided report.

        Parameters
        ----------
        report : TestReport
            The report object to which the test results are added.
        """
        self.logger.info(f"Adding test report for {self.Name}...")
        report.startTest(
            self.Name,
            self.SerialNumber,
            self.StartTime.strftime("%H:%M:%S"),
            self.EndTime.strftime("%H:%M:%S"),
            f"{self.Duration} sec",
            self.Status,
        )

    @tester._member_logger
    def onOpen(self, data: dict):
        """
        Loads parameters from a dictionary into the test.

        Parameters
        ----------
        data : dict
            The parameter dictionary to load.
        """
        self.logger.info(f"Adding parameters for {self.Name} with dict: {data}")
        for _key, _value in data.items():
            self.setParameter(_key, _value)

    @tester._member_logger
    def onSave(self):
        """
        Returns a dictionary of the current test parameters.

        Returns
        -------
        dict
            The current parameters.
        """
        self.logger.info(f"Saving parameters for {self.Name}...")
        return dict(self.__parameters)

    @tester._member_logger
    def onStartTest(self, serial_number: str, devices: DeviceManager) -> bool:
        """
        Runs the full test sequence: setup, run, teardown, and analysis.

        Parameters
        ----------
        serial_number : str
            The serial number of the device under test.
        devices : DeviceManager
            The device manager for hardware interaction.

        Returns
        -------
        bool
            True if the test and analysis succeed.
        """
        self.logger.info(
            f"Starting {self.Name} for {serial_number} on station {devices.ComputerName}..."
        )
        self.setup(serial_number, devices)
        self.run(serial_number, devices)
        self.teardown(devices)
        return self.analyzeResults(serial_number)

    @tester._member_logger
    def resetParameters(self):
        """
        Resets the test state and parameters to their initial values.
        """
        self.SerialNumber = None
        self.StartTime = None
        self.EndTime = None
        self.Duration = None
        self.Status = None

    @tester._member_logger
    def run(self, serial_number: str, devices: DeviceManager):
        """
        Executes the main test logic. Should be overridden by subclasses.

        Parameters
        ----------
        serial_number : str
            The serial number of the device under test.
        devices : DeviceManager
            The device manager for hardware interaction.
        """
        self.logger.info(
            f"Running {self.Name} for {serial_number} on station {devices.ComputerName}..."
        )

    @tester._member_logger
    def setDataDirectory(self, root_directory: Path):
        """
        Sets the data directory for this test, creating it if necessary.

        Parameters
        ----------
        root_directory : Path
            The root directory under which the test's data directory will be created.
        """
        self.dataDirectory = root_directory / self.Name
        self.dataDirectory.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Data directory for {self.Name} set to {self.dataDirectory}")

    @tester._member_logger
    def setup(self, serial_number: str, devices: DeviceManager):
        """
        Performs setup actions before running the test.

        Parameters
        ----------
        serial_number : str
            The serial number of the device under test.
        devices : DeviceManager
            The device manager for hardware interaction.
        """
        self.logger.info(f"Setup {self.Name} for {serial_number}...")
        self.SerialNumber = serial_number
        self.StartTime = self.getTime()
        devices.test_setup()

    @tester._member_logger
    def teardown(self, devices: DeviceManager):
        """
        Performs teardown actions after running the test.

        Parameters
        ----------
        devices : DeviceManager
            The device manager for hardware interaction.
        """
        self.logger.info(f"Tearing down setup for {self.Name}...")
        devices.test_teardown()
