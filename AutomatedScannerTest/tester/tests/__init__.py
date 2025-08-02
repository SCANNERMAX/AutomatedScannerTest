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
import importlib
import inspect

from tester import CancelToken
from tester.manager.devices import DeviceManager
from tester.manager.report import TestReport


def _test_list() -> list:
    """
    Discover and return all test classes derived from the Test base class
    within the AutomatedScannerTest.tester.tests package.

    Returns:
        list: List of test class types derived from Test.
    """
    QtCore.qDebug("Starting test class discovery in _test_list().")
    from tester.tests import Test
    _test_folder = QtCore.QFileInfo(__file__).absolutePath()
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
        found = [obj for _, obj in inspect.getmembers(_module, inspect.isclass)
                 if issubclass(obj, Test) and obj is not Test]
        if found:
            QtCore.qInfo(f"Discovered test classes in {_module_name}: {[cls.__name__ for cls in found]}")
        _tests.extend(found)
    QtCore.qDebug(f"Total discovered test classes: {len(_tests)}")
    return _tests


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
    nameChanged = QtCore.Signal(str)
    serialNumberChanged = QtCore.Signal(str)
    startTimeChanged = QtCore.Signal(str)
    statusChanged = QtCore.Signal(str)
    parameterChanged = QtCore.Signal(str, object)

    def __init__(self, name: str, cancel: CancelToken, devices: DeviceManager):
        """
        Initialize the Test instance.

        Args:
            name (str): The name of the test.
            cancel (CancelToken): The cancellation token for test interruption.
            devices (DeviceManager): The device manager for hardware interaction.

        Raises:
            RuntimeError: If not initialized within a TesterApp instance.
        """
        super().__init__()
        app = QtCore.QCoreApplication.instance()
        if app is None or app.__class__.__name__ != "TesterApp":
            QtCore.qCritical("Test class must be initialized within a TesterApp instance.")
            raise RuntimeError("Test class must be initialized within a TesterApp instance.")
        self._settings = app.get_settings()
        self._settings.settingsModified.connect(self.onSettingsModified)
        self.onSettingsModified()
        self.cancel = cancel
        self.devices = devices
        self.widgetTestMain = None
        self.Name = name
        self._parameters = {}
        self.resetParameters()
        QtCore.qInfo(f"Test instance '{self.Name}' initialized.")

    @QtCore.Property(float, notify=durationChanged)
    def Duration(self):
        """
        Get the test duration in seconds.

        Returns:
            float: The duration of the test in seconds.
        """
        return self._parameter.get("Duration", 0.0)

    @Duration.setter
    def Duration(self, value):
        """
        Set the test duration and emit the durationChanged signal.

        Args:
            value (float): The duration in seconds.
        """
        old = self._parameter.get("Duration", None)
        self._parameters["Duration"] = value
        QtCore.qDebug(f"Duration changed from {old} to {value} for test '{self.Name}'.")
        self.durationChanged.emit(f"{value} sec")

    @QtCore.Property(QtCore.QDateTime, notify=endTimeChanged)
    def EndTime(self):
        """
        Get the end time of the test.

        Returns:
            QDateTime: The end time of the test.
        """
        return self._parameter.get("EndTime", self.getCurrentTime())

    @EndTime.setter
    def EndTime(self, value):
        """
        Set the end time of the test and emit the endTimeChanged signal.

        Args:
            value (QDateTime): The end time.
        """
        old = self._parameter.get("EndTime", None)
        self._parameters["EndTime"] = value
        QtCore.qDebug(f"EndTime changed from {old} to {value} for test '{self.Name}'.")
        self.endTimeChanged.emit(value.toString("HH:mm:ss") if value and value.isValid() else "")
        self.Duration = self.StartTime.secsTo(value)

    @QtCore.Property(str, notify=nameChanged)
    def Name(self):
        """
        Get the name of the test.

        Returns:
            str: The test name.
        """
        return self._parameter.get("Name", "")

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
        return self._parameter.get("SerialNumber", "")

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
        return self._parameter.get("StartTime", self.getCurrentTime())

    @StartTime.setter
    def StartTime(self, value):
        """
        Set the start time of the test and emit the startTimeChanged signal.

        Args:
            value (QDateTime): The start time.
        """
        self.setParameter("StartTime", value)
        self.startTimeChanged.emit(value.toString("HH:mm:ss") if value and value.isValid() else "")

    @QtCore.Property(str, notify=statusChanged)
    def Status(self):
        """
        Get the status of the test.

        Returns:
            str: The test status.
        """
        return self._parameter.get("Status", "")

    @Status.setter
    def Status(self, value):
        """
        Set the status of the test and emit the statusChanged signal.

        Args:
            value (str): The test status.
        """
        self.setParameter("Status", value)
        self.statusChanged.emit(value)

    def getSetting(self, key: str, default=None):
        """
        Get a persistent setting value for this test, or set it to default if not present.

        Args:
            key (str): The setting key.
            default (any): The default value if the key is not present.

        Returns:
            any: The setting value.
        """
        return self._settings.getSetting(f"Tests/{self.Name}", key, default)

    def setSetting(self, key: str, value):
        """
        Set a persistent setting value for this test.

        Args:
            key (str): The setting key.
            value (any): The value to set.
        """
        self._settings.setSetting(f"Tests/{self.Name}", key, value)

    def onSettingsModified(self):
        """
        Handle settings modifications by updating the test as needed.
        """
        QtCore.qInfo(f"Settings modified for test '{self.Name}'.")

    def getParameter(self, key: str, default):
        """
        Get a parameter value by key, or return the default if not present.

        Args:
            key (str): The parameter key.
            default (any): The default value if the key is not present.

        Returns:
            any: The parameter value.
        """
        return self._parameter.get(key, default)

    def setParameter(self, key: str, value):
        """
        Set a parameter value and emit the parameterChanged signal.

        Args:
            key (str): The parameter key.
            value (any): The value to set.
        """
        self._parameters[key] = value
        self.parameterChanged.emit(key, value)

    def getCurrentTime(self) -> QtCore.QDateTime:
        """
        Get the current local time as a QDateTime in the system's current time zone.

        Returns:
            QDateTime: The current local time.
        """
        now = QtCore.QDateTime.currentDateTime()
        return now

    def cliPrintTest(self):
        """
        Print the test name and docstring to the console.
        """
        print(f"- {self.Name}:")
        if self.__doc__:
            print("\n".join(f"    {line.strip()}" for line in self.__doc__.strip().splitlines()))

    def setupUi(self, parent=None):
        """
        Load the test UI into the provided widget.

        Args:
            parent (QtWidgets.QWidget): The parent widget for the test UI.
        """
        QtCore.qInfo(f"Loading UI for test '{self.Name}'.")
        self.widgetTestMain = parent

        layoutTestMain = QtWidgets.QHBoxLayout(parent)
        layoutTestMain.setObjectName("layoutTestMain")
        layoutTestMain.setContentsMargins(0, 0, 0, 0)

        groupBox = QtWidgets.QGroupBox(parent)
        groupBox.setObjectName("groupBoxTestParameters")
        groupBox.setAutoFillBackground(True)
        groupBox.setCheckable(False)
        layoutTestMain.addWidget(groupBox)

        layoutParams = QtWidgets.QVBoxLayout(groupBox)
        layoutParams.setObjectName("layoutTestParameters")

        def add_label(obj_name, text, signal):
            """
            Helper to add a QLabel to the layout and connect it to a signal.

            Args:
                obj_name (str): The object name for the label.
                text (any): The initial text for the label.
                signal (QtCore.Signal): The signal to connect for updating the label text.

            Returns:
                QtWidgets.QLabel: The created label.
            """
            label = QtWidgets.QLabel(groupBox)
            label.setObjectName(obj_name)
            label.setText(str(text))
            signal.connect(label.setText)
            layoutParams.addWidget(label)
            return label

        self.labelTestName = add_label("labelTestName", self.Name, self.nameChanged)
        self.labelSerialNumber = add_label("labelSerialNumber", self.SerialNumber, self.serialNumberChanged)
        self.labelStartTime = add_label("labelStartTime", self.StartTime.toString("HH:mm:ss"), self.startTimeChanged)
        self.labelEndTime = add_label("labelEndTime", self.EndTime.toString("HH:mm:ss"), self.endTimeChanged)
        self.labelDuration = add_label("labelDuration", self.Duration, self.durationChanged)
        self.labelStatus = add_label("labelStatus", self.Status, self.statusChanged)

        self.widgetTestData = QtWidgets.QWidget(parent)
        self.widgetTestData.setObjectName("widgetTestData")
        self.layoutTestData = QtWidgets.QVBoxLayout(self.widgetTestData)
        self.layoutTestData.setObjectName("layoutTestData")

    def onGenerateReport(self, report: TestReport):
        """
        Add this test's results to the provided report.

        Args:
            report (TestReport): The report object to which the test results are added.
        """
        report.startTest(
            self.Name,
            self.SerialNumber,
            self.StartTime.toString("HH:mm:ss") if self.StartTime and self.StartTime.isValid() else "",
            self.EndTime.toString("HH:mm:ss") if self.EndTime and self.EndTime.isValid() else "",
            f"{self.Duration} sec",
            self.Status,
        )

    def onLoadData(self, data: dict):
        """
        Load parameters from a dictionary into the test.

        Args:
            data (dict): The parameter dictionary to load.
        """
        for key, value in data.items():
            try:
                setattr(self, key, value)
            except AttributeError:
                pass

    def onSave(self) -> dict:
        """
        Return a dictionary of the current test parameters.

        Returns:
            dict: The current parameters.
        """
        return dict(self._parameters)

    def onStartTest(self) -> bool:
        """
        Run the full test sequence: setup, run, teardown, and analysis.

        Returns:
            bool: True if the test and analysis succeed, False otherwise.
        """
        try:
            self.StartTime = self.getCurrentTime()
            self.checkCancelled()
            self.setup()
            self.checkCancelled()
            self.run()
            self.checkCancelled()
            self.teardown()
            self.checkCancelled()
            result = self.analyzeResults()
            self.checkCancelled()
            self.Status = "Pass" if result else "Fail"
            return result
        except CancelledError:
            self.Status = "Cancelled"
            return False
        except Exception:
            self.Status = "Error"
            return False
        finally:
            self.teardown()
            self.EndTime = self.getCurrentTime()

    def resetParameters(self):
        """
        Reset the test state and parameters to their initial values.
        """
        self._parameters.clear()
        self.StartTime = QtCore.QDateTime()
        self.EndTime = QtCore.QDateTime()
        self.Status = "Idle"

    def checkCancelled(self):
        """
        Check if the test has been cancelled and raise CancelledError if so.

        Raises:
            CancelledError: If the test has been cancelled.
        """
        if hasattr(self.cancel, "isCancelled") and self.cancel.isCancelled():
            raise CancelledError(f"Test '{self.Name}' was cancelled.")

    def setDataDirectory(self, data_directory: str):
        """
        Set the data directory for the test.

        Args:
            data_directory (str): The path to the data directory.
        """
        dir_obj = QtCore.QDir(data_directory)
        if not dir_obj.exists(self.Name):
            dir_obj.mkpath(self.Name)
        self.dataDirectory = dir_obj.filePath(self.Name)

    def setup(self):
        """
        Perform setup actions before running the test.
        """
        if hasattr(self.devices, "test_setup"):
            self.devices.test_setup()

    def run(self):
        """
        Execute the main test logic. Should be overridden by subclasses.
        """
        pass

    def analyzeResults(self) -> bool:
        """
        Analyze the test results and update the end time, duration, and status.

        Returns:
            bool: True if analysis is successful.
        """
        return True

    def teardown(self):
        """
        Perform teardown actions after running the test.
        """
        if hasattr(self.devices, "test_teardown"):
            self.devices.test_teardown()
