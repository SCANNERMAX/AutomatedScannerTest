# -*- coding: utf-8 -*-
"""
Test framework base classes and utilities for AutomatedScannerTest.

This module provides:
- CancelToken: a simple cancellation token for test interruption.
- Test: the base class for all tests, with parameter/state management, settings, and UI hooks.
- _test_list: a utility to discover all test classes in the tester.tests package.
"""

from PySide6 import QtCore, QtWidgets
import importlib
import inspect

from tester.manager.devices import DeviceManager
from tester.manager.report import TestReport


class CancelToken(QtCore.QObject):
    """
    A simple token class to signal cancellation of an operation.

    Signals
    -------
    cancelledChanged(bool)
        Emitted when the cancelled state changes.

    Properties
    ----------
    cancelled : bool
        Indicates whether the operation has been cancelled.
    """

    cancelledChanged = QtCore.Signal(bool)

    def __init__(self, parent=None):
        """
        Initialize the CancelToken.

        Parameters
        ----------
        parent : QObject, optional
            The parent QObject.
        """
        super().__init__(parent)
        self._cancelled = False
        QtCore.qDebug("CancelToken initialized with cancelled=False.")

    @QtCore.Property(bool, notify=cancelledChanged)
    def cancelled(self):
        """
        Get the cancelled state.

        Returns
        -------
        bool
            True if cancelled, False otherwise.
        """
        return self._cancelled

    @cancelled.setter
    def cancelled(self, value):
        """
        Set the cancelled state.

        Parameters
        ----------
        value : bool
            The new cancelled state.
        """
        if self._cancelled != value:
            QtCore.qInfo(f"CancelToken.cancelled changed from {self._cancelled} to {value}.")
            self._cancelled = value
            self.cancelledChanged.emit(self._cancelled)

    @QtCore.Slot()
    def cancel(self):
        """
        Set the cancelled state to True.
        """
        QtCore.qInfo("CancelToken.cancel() called.")
        self.cancelled = True

    @QtCore.Slot()
    def reset(self):
        """
        Reset the cancelled state to False.
        """
        QtCore.qInfo("CancelToken.reset() called.")
        self.cancelled = False


def _test_list() -> list:
    """
    Returns a list of all test classes derived from the Test base class
    within the tester.tests package.

    Returns
    -------
    list
        A list of test class types derived from Test.
    """
    QtCore.qDebug("Starting test class discovery in _test_list().")
    _test_module = importlib.import_module(Test.__module__)
    _test_folder = QtCore.QFileInfo(_test_module.__file__).absolutePath()
    dir_obj = QtCore.QDir(_test_folder)
    py_files = [f for f in dir_obj.entryList(["*.py"], QtCore.QDir.Files) if not f.startswith("__")]
    _tests = []
    for _filename in py_files:
        _module_name = f"tester.tests.{_filename[:-3]}"
        try:
            QtCore.qDebug(f"Attempting to import module: {_module_name}")
            _module = importlib.import_module(_module_name)
        except Exception as e:
            QtCore.qWarning(f"Could not import {_module_name}: {e}")
            continue
        found = [
            obj for _, obj in inspect.getmembers(_module, inspect.isclass)
            if issubclass(obj, Test) and obj is not Test
        ]
        if found:
            QtCore.qInfo(f"Discovered test classes in {_module_name}: {[cls.__name__ for cls in found]}")
        _tests += found
    QtCore.qDebug(f"Total discovered test classes: {len(_tests)}")
    return _tests


class Test(QtCore.QObject):
    """
    Base model class for all tests in the AutomatedScannerTest framework.
    Provides core interface and state management for test execution, parameter handling,
    UI integration, and reporting.

    Signals
    -------
    durationChanged(str)
        Emitted when the duration changes.
    endTimeChanged(str)
        Emitted when the end time changes.
    nameChanged(str)
        Emitted when the name changes.
    serialNumberChanged(str)
        Emitted when the serial number changes.
    startTimeChanged(str)
        Emitted when the start time changes.
    statusChanged(str)
        Emitted when the status changes.
    parameterChanged(str, object)
        Emitted when a parameter changes.

    Properties
    ----------
    Duration : float
        The duration of the test in seconds.
    EndTime : QDateTime
        The end time of the test.
    Name : str
        The name of the test.
    SerialNumber : str
        The serial number associated with the test.
    StartTime : QDateTime
        The start time of the test.
    Status : str
        The status of the test.
    """

    durationChanged = QtCore.Signal(str)
    endTimeChanged = QtCore.Signal(str)
    nameChanged = QtCore.Signal(str)
    serialNumberChanged = QtCore.Signal(str)
    startTimeChanged = QtCore.Signal(str)
    statusChanged = QtCore.Signal(str)
    parameterChanged = QtCore.Signal(str, object)

    def __init__(self, name: str, cancel: CancelToken):
        """
        Initialize the Test instance.

        Parameters
        ----------
        name : str
            The name of the test.
        cancel : CancelToken
            The cancellation token for test interruption.

        Raises
        ------
        RuntimeError
            If not initialized within a TesterApp instance.
        """
        super().__init__()
        app = QtCore.QCoreApplication.instance()
        if app is not None and app.__class__.__name__ == "TesterApp":
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
        else:
            QtCore.qCritical("Test class must be initialized within a TesterApp instance.")
            raise RuntimeError("Test class must be initialized within a TesterApp instance.")
        self.__parameters = {}
        self.widgetTestMain = None
        self._cancel = cancel
        self.Name = name
        self.resetParameters()
        QtCore.qInfo(f"Test instance '{self.Name}' initialized.")

    @QtCore.Property(float, notify=durationChanged)
    def Duration(self):
        """
        Get the test duration in seconds.

        Returns
        -------
        float
            The duration of the test in seconds.
        """
        return self.__parameters.get("Duration", 0.0)

    @Duration.setter
    def Duration(self, value):
        """
        Set the test duration and emit the durationChanged signal.

        Parameters
        ----------
        value : float
            The duration in seconds.
        """
        old = self.__parameters.get("Duration", None)
        self.__parameters["Duration"] = value
        QtCore.qDebug(f"Duration changed from {old} to {value} for test '{self.Name}'.")
        self.durationChanged.emit(f"{value} sec")

    @QtCore.Property(QtCore.QDateTime, notify=endTimeChanged)
    def EndTime(self):
        """
        Get the end time of the test.

        Returns
        -------
        QDateTime
            The end time of the test.
        """
        return self.__parameters.get("EndTime", self.getTime())

    @EndTime.setter
    def EndTime(self, value):
        """
        Set the end time of the test and emit the endTimeChanged signal.

        Parameters
        ----------
        value : QDateTime
            The end time.
        """
        old = self.__parameters.get("EndTime", None)
        self.__parameters["EndTime"] = value
        QtCore.qDebug(f"EndTime changed from {old} to {value} for test '{self.Name}'.")
        self.endTimeChanged.emit(value.toString("HH:mm:ss") if value and value.isValid() else "")

    @QtCore.Property(str, notify=nameChanged)
    def Name(self):
        """
        Get the name of the test.

        Returns
        -------
        str
            The test name.
        """
        return self.__parameters.get("Name", "")

    @Name.setter
    def Name(self, value):
        """
        Set the name of the test and emit the nameChanged signal.

        Parameters
        ----------
        value : str
            The test name.
        """
        old = self.__parameters.get("Name", None)
        self.__parameters["Name"] = value
        QtCore.qDebug(f"Name changed from {old} to {value}.")
        self.nameChanged.emit(value)

    @QtCore.Property(str, notify=serialNumberChanged)
    def SerialNumber(self):
        """
        Get the serial number associated with the test.

        Returns
        -------
        str
            The serial number.
        """
        return self.__parameters.get("SerialNumber", "")

    @SerialNumber.setter
    def SerialNumber(self, value):
        """
        Set the serial number and emit the serialNumberChanged signal.

        Parameters
        ----------
        value : str
            The serial number.
        """
        old = self.__parameters.get("SerialNumber", None)
        self.__parameters["SerialNumber"] = value
        QtCore.qDebug(f"SerialNumber changed from {old} to {value} for test '{self.Name}'.")
        self.serialNumberChanged.emit(value)

    @QtCore.Property(QtCore.QDateTime, notify=startTimeChanged)
    def StartTime(self):
        """
        Get the start time of the test.

        Returns
        -------
        QDateTime
            The start time of the test.
        """
        return self.__parameters.get("StartTime", self.getTime())

    @StartTime.setter
    def StartTime(self, value):
        """
        Set the start time of the test and emit the startTimeChanged signal.

        Parameters
        ----------
        value : QDateTime
            The start time.
        """
        old = self.__parameters.get("StartTime", None)
        self.__parameters["StartTime"] = value
        QtCore.qDebug(f"StartTime changed from {old} to {value} for test '{self.Name}'.")
        self.startTimeChanged.emit(value.toString("HH:mm:ss") if value and value.isValid() else "")

    @QtCore.Property(str, notify=statusChanged)
    def Status(self):
        """
        Get the status of the test.

        Returns
        -------
        str
            The test status.
        """
        return self.__parameters.get("Status", "")

    @Status.setter
    def Status(self, value):
        """
        Set the status of the test and emit the statusChanged signal.

        Parameters
        ----------
        value : str
            The test status.
        """
        old = self.__parameters.get("Status", None)
        self.__parameters["Status"] = value
        QtCore.qDebug(f"Status changed from {old} to {value} for test '{self.Name}'.")
        self.statusChanged.emit(value)

    def getSetting(self, key: str, default=None):
        """
        Get a persistent setting value for this test, or set it to default if not present.

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
        QtCore.qDebug(f"Getting setting '{key}' for test '{self.Name}' with default '{default}'")
        return self.__settings.getSetting(f"Tests/{self.Name}", key, default)

    def setSetting(self, key: str, value):
        """
        Set a persistent setting value for this test.

        Parameters
        ----------
        key : str
            The setting key.
        value : any
            The value to set.
        """
        QtCore.qDebug(f"Setting '{key}' to '{value}' for test '{self.Name}'")
        self.__settings.setSetting(f"Tests/{self.Name}", key, value)

    def onSettingsModified(self):
        """
        Handle settings modifications by updating the test as needed.
        """
        QtCore.qInfo(f"Settings modified for test '{self.Name}'.")

    def getParameter(self, key: str, default):
        """
        Get a parameter value by key, or return the default if not present.

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
        value = self.__parameters.get(key, default)
        QtCore.qDebug(f"getParameter: key='{key}', value='{value}', default='{default}' for test '{self.Name}'.")
        return value

    def setParameter(self, key: str, value):
        """
        Set a parameter value and emit the parameterChanged signal.

        Parameters
        ----------
        key : str
            The parameter key.
        value : any
            The value to set.
        """
        old = self.__parameters.get(key, None)
        self.__parameters[key] = value
        QtCore.qDebug(f"Parameter '{key}' changed from '{old}' to '{value}' for test '{self.Name}'.")
        self.parameterChanged.emit(key, value)

    def getTime(self) -> QtCore.QDateTime:
        """
        Get the current local time as a QDateTime in the system's current time zone.

        Returns
        -------
        QDateTime
            The current local time.
        """
        now = QtCore.QDateTime.currentDateTime()
        QtCore.qDebug(f"getTime() called, returning {now.toString(QtCore.Qt.ISODate)} for test '{self.Name}'.")
        return now

    def analyzeResults(self, serial_number: str) -> bool:
        """
        Analyze the test results and update the end time, duration, and status.

        Parameters
        ----------
        serial_number : str
            The serial number of the device under test.

        Returns
        -------
        bool
            True if analysis is successful.
        """
        QtCore.qInfo(f"Analyzing results for test '{self.Name}', serial '{serial_number}'.")
        self.EndTime = self.getTime()
        self.Duration = self.StartTime.secsTo(self.EndTime)
        self.Status = "Pass"
        QtCore.qInfo(f"Test '{self.Name}' analysis complete: Duration={self.Duration}, Status={self.Status}.")
        return True

    def setupUi(self, widget: QtWidgets.QWidget):
        """
        Load the test UI into the provided widget.

        Parameters
        ----------
        widget : QtWidgets.QWidget
            The parent widget for the test UI.
        """
        QtCore.qInfo(f"Loading UI for test '{self.Name}'.")
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
            QtCore.qDebug(f"UI label '{obj_name}' initialized with text '{text}'.")
            return label

        self.labelTestName = add_label("labelTestName", self.Name, self.nameChanged)
        self.labelSerialNumber = add_label("labelSerialNumber", self.SerialNumber, self.serialNumberChanged)
        self.labelStartTime = add_label("labelStartTime", self.StartTime.toString("HH:mm:ss"), self.startTimeChanged)
        self.labelEndTime = add_label("labelEndTime", self.EndTime.toString("HH:mm:ss"), self.endTimeChanged)
        self.labelDuration = add_label("labelDuration", self.Duration, self.durationChanged)
        self.labelStatus = add_label("labelStatus", self.Status, self.statusChanged)

        self.widgetTestData = QtWidgets.QWidget(widget)
        self.widgetTestData.setObjectName("widgetTestData")
        self.layoutTestData = QtWidgets.QVBoxLayout(self.widgetTestData)
        self.layoutTestData.setObjectName("layoutTestData")
        QtCore.qInfo(f"UI for test '{self.Name}' loaded.")

    def onGenerateReport(self, report: TestReport):
        """
        Add this test's results to the provided report.

        Parameters
        ----------
        report : TestReport
            The report object to which the test results are added.
        """
        QtCore.qInfo(f"Adding test report for '{self.Name}'.")
        report.startTest(
            self.Name,
            self.SerialNumber,
            self.StartTime.toString("HH:mm:ss") if self.StartTime and self.StartTime.isValid() else "",
            self.EndTime.toString("HH:mm:ss") if self.EndTime and self.EndTime.isValid() else "",
            f"{self.Duration} sec",
            self.Status,
        )
        QtCore.qDebug(f"Report generated for test '{self.Name}'.")

    def onOpen(self, data: dict):
        """
        Load parameters from a dictionary into the test.

        Parameters
        ----------
        data : dict
            The parameter dictionary to load.
        """
        QtCore.qInfo(f"Loading parameters for test '{self.Name}': {data}")
        self.__parameters.update(data)

    def onSave(self):
        """
        Return a dictionary of the current test parameters.

        Returns
        -------
        dict
            The current parameters.
        """
        QtCore.qInfo(f"Saving parameters for test '{self.Name}'.")
        return dict(self.__parameters)

    def onStartTest(self, serial_number: str, devices: DeviceManager) -> bool:
        """
        Run the full test sequence: setup, run, teardown, and analysis.

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
        QtCore.qInfo(
            f"Starting test '{self.Name}' for serial '{serial_number}' on station '{devices.ComputerName}'."
        )
        self.setup(serial_number, devices)
        self.run(serial_number, devices)
        self.teardown(devices)
        result = self.analyzeResults(serial_number)
        QtCore.qInfo(f"Test '{self.Name}' completed for serial '{serial_number}' with result: {result}.")
        return result

    def resetParameters(self):
        """
        Reset the test state and parameters to their initial values.
        """
        QtCore.qDebug(f"Resetting parameters for test '{self.Name}'.")
        self.__parameters.clear()
        self.SerialNumber = ""
        self.StartTime = QtCore.QDateTime()
        self.EndTime = QtCore.QDateTime()
        self.Duration = 0.0
        self.Status = ""

    def run(self, serial_number: str, devices: DeviceManager):
        """
        Execute the main test logic. Should be overridden by subclasses.

        Parameters
        ----------
        serial_number : str
            The serial number of the device under test.
        devices : DeviceManager
            The device manager for hardware interaction.
        """
        QtCore.qInfo(
            f"Running test '{self.Name}' for serial '{serial_number}' on station '{devices.ComputerName}'."
        )

    def setDataDirectory(self, root_directory: str):
        """
        Set the data directory for this test, creating it if necessary.

        Parameters
        ----------
        root_directory : str
            The root directory under which the test's data directory will be created.
        """
        dir_obj = QtCore.QDir(root_directory)
        if not dir_obj.exists(self.Name):
            dir_obj.mkpath(self.Name)
        self.dataDirectory = dir_obj.filePath(self.Name)
        QtCore.qInfo(f"Data directory for test '{self.Name}' set to '{self.dataDirectory}'.")

    def setup(self, serial_number: str, devices: DeviceManager):
        """
        Perform setup actions before running the test.

        Parameters
        ----------
        serial_number : str
            The serial number of the device under test.
        devices : DeviceManager
            The device manager for hardware interaction.
        """
        QtCore.qInfo(f"Setting up test '{self.Name}' for serial '{serial_number}'.")
        self.SerialNumber = serial_number
        self.StartTime = self.getTime()
        devices.test_setup()

    def teardown(self, devices: DeviceManager):
        """
        Perform teardown actions after running the test.

        Parameters
        ----------
        devices : DeviceManager
            The device manager for hardware interaction.
        """
        QtCore.qInfo(f"Tearing down test '{self.Name}'.")
        devices.test_teardown()
