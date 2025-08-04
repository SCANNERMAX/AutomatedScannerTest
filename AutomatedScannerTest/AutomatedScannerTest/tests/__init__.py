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
import traceback

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
    QtCore.qDebug("[_test_list] Starting test class discovery.")
    from tester.tests import Test

    _test_folder = QtCore.QFileInfo(__file__).absolutePath()
    dir_obj = QtCore.QDir(_test_folder)
    py_files = [
        f
        for f in dir_obj.entryList(["*.py"], QtCore.QDir.Files)
        if not f.startswith("__")
    ]
    QtCore.qDebug("[_test_list] Python files found: %s" % py_files)
    _tests = []
    for _filename in py_files:
        _module_name = "tester.tests.%s" % _filename[:-3]
        try:
            QtCore.qDebug("[_test_list] Attempting to import module: %s" % _module_name)
            _module = importlib.import_module(_module_name)
        except Exception as e:
            QtCore.qWarning(
                "[_test_list] Could not import %s: %s\n%s"
                % (_module_name, e, traceback.format_exc())
            )
            continue
        found = (
            obj
            for _, obj in inspect.getmembers(_module, inspect.isclass)
            if issubclass(obj, Test) and obj is not Test
        )
        found_list = list(found)
        if found_list:
            QtCore.qDebug(
                "[_test_list] Discovered test classes in %s: %s"
                % (_module_name, [cls.__name__ for cls in found_list])
            )
        _tests.extend(found_list)
    QtCore.qDebug("[_test_list] Total discovered test classes: %d" % len(_tests))
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
        Initialize a Test instance.

        Args:
            name (str): The name of the test.
            cancel (CancelToken): Token to support test cancellation.
            devices (DeviceManager): Device manager for hardware interaction.
        Raises:
            RuntimeError: If not initialized within a TesterApp instance.
        """
        QtCore.qDebug(
            "[Test.__init__] Initializing Test instance with name='%s'" % name
        )
        super().__init__()
        app = QtCore.QCoreApplication.instance()
        if app is None or app.__class__.__name__ != "TesterApp":
            QtCore.qCritical(
                "[Test.__init__] Test class must be initialized within a TesterApp instance."
            )
            raise RuntimeError(
                "Test class must be initialized within a TesterApp instance."
            )
        self.__parameters = {}
        self.__settings = app.get_settings()
        self.__settings.settingsModified.connect(self.onSettingsModified)
        self.cancel = cancel
        self.devices = devices
        self.widgetTestMain = None
        self.resetParameters()
        self.Name = name
        QtCore.qDebug("[Test.__init__] Test instance '%s' initialized." % self.Name)

    @QtCore.Property(float, notify=durationChanged)
    def Duration(self):
        """
        Get the duration of the test in seconds.

        Returns:
            float: Duration in seconds.
        """
        QtCore.qDebug(
            "[Test.Duration] Getting Duration: %s"
            % self.__parameters.get("Duration", 0.0)
        )
        return self.__parameters.get("Duration", 0.0)

    @Duration.setter
    def Duration(self, value):
        """
        Set the duration of the test.

        Args:
            value (float): Duration in seconds.
        """
        old = self.__parameters.get("Duration", None)
        QtCore.qDebug(
            "[Test.Duration] Setting Duration from %s to %s for test '%s'."
            % (old, value, self.Name)
        )
        self.__parameters["Duration"] = value
        self.durationChanged.emit("%s sec" % value)

    @QtCore.Property(QtCore.QDateTime, notify=endTimeChanged)
    def EndTime(self):
        """
        Get the end time of the test.

        Returns:
            QDateTime: End time.
        """
        QtCore.qDebug(
            "[Test.EndTime] Getting EndTime: %s"
            % self.__parameters.get("EndTime", self.getCurrentTime())
        )
        return self.__parameters.get("EndTime", self.getCurrentTime())

    @EndTime.setter
    def EndTime(self, value):
        """
        Set the end time of the test.

        Args:
            value (QDateTime): End time.
        """
        old = self.__parameters.get("EndTime", None)
        QtCore.qDebug(
            "[Test.EndTime] Setting EndTime from %s to %s for test '%s'."
            % (old, value, self.Name)
        )
        self.__parameters["EndTime"] = value
        self.endTimeChanged.emit(
            value.toString("HH:mm:ss") if value and value.isValid() else ""
        )
        start = self.StartTime
        if start and value and start.isValid() and value.isValid():
            self.Duration = start.secsTo(value)
        else:
            self.Duration = 0.0

    @QtCore.Property(str, notify=nameChanged)
    def Name(self):
        """
        Get the name of the test.

        Returns:
            str: Test name.
        """
        QtCore.qDebug("[Test.Name] Getting Name: %s" % self.getParameter("Name", ""))
        return self.getParameter("Name", "")

    @Name.setter
    def Name(self, value):
        """
        Set the name of the test.

        Args:
            value (str): Test name.
        """
        QtCore.qDebug("[Test.Name] Setting Name to %s" % value)
        self.setParameter("Name", value)
        self.nameChanged.emit(value)

    @QtCore.Property(str, notify=serialNumberChanged)
    def SerialNumber(self):
        """
        Get the serial number associated with the test.

        Returns:
            str: Serial number.
        """
        QtCore.qDebug(
            "[Test.SerialNumber] Getting SerialNumber: %s"
            % self.__parameters.get("SerialNumber", "")
        )
        return self.__parameters.get("SerialNumber", "")

    @SerialNumber.setter
    def SerialNumber(self, value):
        """
        Set the serial number for the test.

        Args:
            value (str): Serial number.
        """
        QtCore.qDebug("[Test.SerialNumber] Setting SerialNumber to %s" % value)
        self.setParameter("SerialNumber", value)
        self.serialNumberChanged.emit(value)

    @QtCore.Property(QtCore.QDateTime, notify=startTimeChanged)
    def StartTime(self):
        """
        Get the start time of the test.

        Returns:
            QDateTime: Start time.
        """
        QtCore.qDebug(
            "[Test.StartTime] Getting StartTime: %s"
            % self.__parameters.get("StartTime", self.getCurrentTime())
        )
        return self.__parameters.get("StartTime", self.getCurrentTime())

    @StartTime.setter
    def StartTime(self, value):
        """
        Set the start time of the test.

        Args:
            value (QDateTime): Start time.
        """
        QtCore.qDebug("[Test.StartTime] Setting StartTime to %s" % value)
        self.setParameter("StartTime", value)
        self.startTimeChanged.emit(
            value.toString("HH:mm:ss") if value and value.isValid() else ""
        )

    @QtCore.Property(str, notify=statusChanged)
    def Status(self):
        """
        Get the status of the test.

        Returns:
            str: Status.
        """
        QtCore.qDebug(
            "[Test.Status] Getting Status: %s" % self.__parameters.get("Status", "")
        )
        return self.__parameters.get("Status", "")

    @Status.setter
    def Status(self, value):
        """
        Set the status of the test.

        Args:
            value (str): Status.
        """
        QtCore.qDebug("[Test.Status] Setting Status to %s" % value)
        self.setParameter("Status", value)
        self.statusChanged.emit(value)

    def getSetting(self, key: str, default=None):
        """
        Get a test-specific setting.

        Args:
            key (str): Setting key.
            default: Default value if not found.

        Returns:
            Any: Setting value.
        """
        QtCore.qDebug(
            "[Test.getSetting] Getting setting '%s' (default=%s) for test '%s'"
            % (key, default, self.Name)
        )
        return self.__settings.getSetting("Tests/%s" % self.Name, key, default)

    def setSetting(self, key: str, value):
        """
        Set a test-specific setting.

        Args:
            key (str): Setting key.
            value: Value to set.
        """
        QtCore.qDebug(
            "[Test.setSetting] Setting '%s' to '%s' for test '%s'"
            % (key, value, self.Name)
        )
        self.__settings.setSetting("Tests/%s" % self.Name, key, value)

    def onSettingsModified(self):
        """
        Slot called when settings are modified.
        """
        QtCore.qDebug(
            "[Test.onSettingsModified] Settings modified for test '%s'." % self.Name
        )

    def getParameter(self, key: str, default):
        """
        Get a parameter value.

        Args:
            key (str): Parameter key.
            default: Default value if not found.

        Returns:
            Any: Parameter value.
        """
        QtCore.qDebug(
            "[Test.getParameter] Getting parameter '%s' (default=%s)" % (key, default)
        )
        return self.__parameters.get(key, default)

    def setParameter(self, key: str, value):
        """
        Set a parameter value.

        Args:
            key (str): Parameter key.
            value: Value to set.
        """
        QtCore.qDebug(
            "[Test.setParameter] Setting parameter '%s' to '%s'" % (key, value)
        )
        self.__parameters[key] = value
        self.parameterChanged.emit(key, value)

    def getCurrentTime(self) -> QtCore.QDateTime:
        """
        Get the current date and time.

        Returns:
            QDateTime: Current date and time.
        """
        now = QtCore.QDateTime.currentDateTime()
        QtCore.qDebug(
            "[Test.getCurrentTime] Current time: %s"
            % now.toString("yyyy-MM-dd HH:mm:ss")
        )
        return now

    def cliPrintTest(self):
        """
        Print test information to the CLI.
        """
        QtCore.qDebug("[Test.cliPrintTest] Printing test info for '%s'" % self.Name)
        print("- %s:" % self.Name)
        if self.__doc__:
            print(
                "\n".join(
                    "    %s" % line.strip()
                    for line in self.__doc__.strip().splitlines()
                )
            )

    def setupUi(self, parent=None):
        """
        Set up the test UI.

        Args:
            parent: Parent widget.
        """
        QtCore.qDebug(
            "[Test.setupUi] Loading UI for test '%s'. Parent: %s" % (self.Name, parent)
        )
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
            Helper to add a QLabel to the UI and connect its text to a signal.

            Args:
                obj_name (str): Object name for the label.
                text (str): Initial text.
                signal (Signal): Signal to connect.

            Returns:
                QLabel: The created label.
            """
            QtCore.qDebug(
                "[Test.setupUi:add_label] Adding label '%s' with initial text '%s'"
                % (obj_name, text)
            )
            label = QtWidgets.QLabel(groupBox)
            label.setObjectName(obj_name)
            label.setText(str(text))
            signal.connect(label.setText)
            layoutParams.addWidget(label)
            return label

        self.labelTestName = add_label("labelTestName", self.Name, self.nameChanged)
        self.labelSerialNumber = add_label(
            "labelSerialNumber", self.SerialNumber, self.serialNumberChanged
        )
        self.labelStartTime = add_label(
            "labelStartTime", self.StartTime.toString("HH:mm:ss"), self.startTimeChanged
        )
        self.labelEndTime = add_label(
            "labelEndTime", self.EndTime.toString("HH:mm:ss"), self.endTimeChanged
        )
        self.labelDuration = add_label(
            "labelDuration", "%s sec" % self.Duration, self.durationChanged
        )
        self.labelStatus = add_label("labelStatus", self.Status, self.statusChanged)

        self.widgetTestData = QtWidgets.QWidget(parent)
        self.widgetTestData.setObjectName("widgetTestData")
        self.layoutTestData = QtWidgets.QVBoxLayout(self.widgetTestData)
        self.layoutTestData.setObjectName("layoutTestData")

    def onGenerateReport(self, report: TestReport):
        """
        Add test information to a report.

        Args:
            report (TestReport): The report object.
        """
        QtCore.qDebug("[Test.onGenerateReport] Adding test '%s' to report." % self.Name)
        start_time = self.StartTime
        end_time = self.EndTime
        report.startTest(
            self.Name,
            self.SerialNumber,
            (
                start_time.toString("HH:mm:ss")
                if start_time and start_time.isValid()
                else ""
            ),
            end_time.toString("HH:mm:ss") if end_time and end_time.isValid() else "",
            "%s sec" % self.Duration,
            self.Status,
        )

    def onLoadData(self, data: dict):
        """
        Load test data from a dictionary.

        Args:
            data (dict): Data to load.
        """
        QtCore.qDebug("[Test.onLoadData] Loading data: %s" % data)
        for key, value in data.items():
            if hasattr(type(self), key):
                try:
                    QtCore.qDebug(
                        "[Test.onLoadData] Setting attribute '%s' to '%s'"
                        % (key, value)
                    )
                    setattr(self, key, value)
                except Exception as e:
                    QtCore.qWarning(
                        "[Test.onLoadData] Failed to set attribute '%s': %s\n%s"
                        % (key, e, traceback.format_exc())
                    )
            else:
                QtCore.qDebug(
                    "[Test.onLoadData] Setting parameter '%s' to '%s'" % (key, value)
                )
                self.setParameter(key, value)

    def onSave(self) -> dict:
        """
        Save test parameters to a dictionary.

        Returns:
            dict: Parameters dictionary.
        """
        QtCore.qDebug("[Test.onSave] Saving parameters: %s" % self.__parameters)
        return dict(self.__parameters)

    def onStartTest(self, data_directory: str) -> bool:
        """
        Start the test process.

        Args:
            data_directory (str): Directory for test data.

        Returns:
            bool: True if test passed, False otherwise.
        """
        QtCore.qInfo(
            "[Test.onStartTest] Starting test '%s' in directory '%s'"
            % (self.Name, data_directory)
        )
        try:
            self.setDataDirectory(data_directory)
            self.StartTime = self.getCurrentTime()
            self.checkCancelled()
            QtCore.qDebug("[Test.onStartTest] Running setup for '%s'" % self.Name)
            self.setup()
            self.checkCancelled()
            QtCore.qDebug(
                "[Test.onStartTest] Running main test logic for '%s'" % self.Name
            )
            self.run()
            self.checkCancelled()
            QtCore.qDebug("[Test.onStartTest] Running teardown for '%s'" % self.Name)
            self.teardown()
            self.checkCancelled()
            QtCore.qDebug("[Test.onStartTest] Analyzing results for '%s'" % self.Name)
            result = self.analyzeResults()
            self.checkCancelled()
            self.Status = "Pass" if result else "Fail"
            QtCore.qInfo(
                "[Test.onStartTest] Test '%s' completed with status: %s"
                % (self.Name, self.Status)
            )
            return result
        except CancelledError:
            self.Status = "Cancelled"
            QtCore.qWarning("[Test.onStartTest] Test '%s' was cancelled." % self.Name)
            return False
        except Exception as e:
            self.Status = "Error"
            QtCore.qCritical(
                "[Test.onStartTest] Error during test '%s': %s\n%s"
                % (self.Name, e, traceback.format_exc())
            )
            return False
        finally:
            QtCore.qDebug(
                "[Test.onStartTest] Final teardown and setting EndTime for '%s'"
                % self.Name
            )
            self.teardown()
            self.EndTime = self.getCurrentTime()

    def resetParameters(self):
        """
        Reset all test parameters to their initial state.
        """
        QtCore.qDebug(
            "[Test.resetParameters] Resetting parameters for test '%s'" % self.Name
        )
        self.__parameters.clear()
        self.StartTime = QtCore.QDateTime()
        self.EndTime = QtCore.QDateTime()
        self.Status = "Idle"

    def checkCancelled(self):
        """
        Check if the test has been cancelled and raise CancelledError if so.

        Raises:
            CancelledError: If the test is cancelled.
        """
        QtCore.qDebug(
            "[Test.checkCancelled] Checking if test '%s' is cancelled" % self.Name
        )
        cancel = getattr(self.cancel, "isCancelled", None)
        if callable(cancel) and cancel():
            QtCore.qWarning(
                "[Test.checkCancelled] Test '%s' was cancelled." % self.Name
            )
            raise CancelledError("Test '%s' was cancelled." % self.Name)

    def setDataDirectory(self, data_directory: str):
        """
        Set the directory for storing test data.

        Args:
            data_directory (str): Base directory for test data.
        """
        QtCore.qDebug(
            "[Test.setDataDirectory] Setting data directory to '%s' for test '%s'"
            % (data_directory, self.Name)
        )
        dir_obj = QtCore.QDir(data_directory)
        if not dir_obj.exists(self.Name):
            QtCore.qDebug(
                "[Test.setDataDirectory] Creating directory '%s' in '%s'"
                % (self.Name, data_directory)
            )
            dir_obj.mkpath(self.Name)
        self.dataDirectory = dir_obj.filePath(self.Name)
        QtCore.qDebug(
            "[Test.setDataDirectory] Data directory set to '%s'" % self.dataDirectory
        )

    def setup(self):
        """
        Perform setup actions before running the test.
        """
        QtCore.qDebug("[Test.setup] Performing setup for test '%s'" % self.Name)
        setup_func = getattr(self.devices, "test_setup", None)
        if callable(setup_func):
            setup_func()
            QtCore.qDebug(
                "[Test.setup] Device setup completed for test '%s'" % self.Name
            )

    def run(self):
        """
        Main test logic. Should be overridden by subclasses.
        """
        QtCore.qDebug("[Test.run] Running main test logic for test '%s'" % self.Name)
        # To be overridden by subclasses

    def analyzeResults(self) -> bool:
        """
        Analyze test results.

        Returns:
            bool: True if test passed, False otherwise.
        """
        QtCore.qDebug(
            "[Test.analyzeResults] Analyzing results for test '%s'" % self.Name
        )
        return True

    def teardown(self):
        """
        Perform teardown actions after running the test.
        """
        QtCore.qDebug("[Test.teardown] Performing teardown for test '%s'" % self.Name)
        teardown_func = getattr(self.devices, "test_teardown", None)
        if callable(teardown_func):
            teardown_func()
            QtCore.qDebug(
                "[Test.teardown] Device teardown completed for test '%s'" % self.Name
            )