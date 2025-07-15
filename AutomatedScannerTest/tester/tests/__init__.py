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
    Attributes:
        cancelled (bool): Indicates whether the token has been cancelled.
    Methods:
        cancel():
            Sets the token as cancelled.
        reset():
            Resets the token to not cancelled.
    """

    def __init__(self):
        """
        Initializes the instance and sets the 'cancelled' attribute to False.
        """
        self.cancelled = False

    def cancel(self):
        """
        Marks the current operation as cancelled by setting the 'cancelled' attribute to True.
        """
        self.cancelled = True

    def reset(self):
        """
        Resets the object's state by setting the 'cancelled' attribute to False.
        """
        self.cancelled = False


def _test_list() -> list:
    """
    Discovers and returns a list of all test classes derived from the Test base class
    within the tester.tests package.

    This function dynamically imports all Python modules in the tests directory (excluding
    dunder files), then inspects each module for classes that inherit from Test (excluding
    the Test base class itself). All discovered test classes are appended to the returned list.

    Returns:
        list: A list of test class objects that are subclasses of Test.
    """
    _tests = []
    _test_module = importlib.import_module(Test.__module__)
    _test_folder = os.path.dirname(_test_module.__file__)

    py_files = [
        f
        for f in os.listdir(_test_folder)
        if f.endswith(".py") and not f.startswith("__")
    ]
    for _filename in py_files:
        _module_name = f"tester.tests.{_filename[:-3]}"
        try:
            _module = importlib.import_module(_module_name)
        except Exception as e:
            logging.warning(f"Could not import {_module_name}: {e}")
            continue

        # Use a generator expression for faster filtering
        for _obj in (
            obj
            for _, obj in inspect.getmembers(_module, inspect.isclass)
            if issubclass(obj, Test) and obj is not Test
        ):
            _tests.append(_obj)
    return _tests


class Test(QtCore.QObject):
    """
    Test is a base model class for all tests in the AutomatedScannerTest framework.
    This class provides a structure for managing test data, settings, and UI integration,
    as well as methods for running, analyzing, and reporting test results. It uses Qt's
    signal/slot mechanism to notify about data changes and interacts with QSettings for
    persistent configuration.
    Attributes:
        dataChanged (QtCore.Signal): Signal emitted when test data changes.
        Name (str): Name of the test.
        SerialNumber (str): Serial number associated with the test.
        StartTime (datetime): Start time of the test.
        EndTime (datetime): End time of the test.
        Duration (float): Duration of the test in seconds.
        Status (bool): Pass/fail status of the test.
        StatusText (str): Human-readable status ("Incomplete", "Pass", "Fail").
    Methods:
        analyze_results(serial_number): Analyze the results of the test.
        load_ui(widget): Display the test model in the given widget.
        on_generate_report(report): Append the report of the test.
        on_start_test(serial_number, devices): Execute the test for the scanner model.
        on_open(data): Open the test model and set the data from the dictionary.
        on_save(): Save the test model data to a dictionary.
        release_ui(): Release the UI of the test model.
        reset_test(): Reset the test data to initial state.
        run_test(serial_number, devices): Run the test for the scanner model.
        set_data_directory(root_directory): Set the data directory for the test model.
        setup_test(serial_number, devices): Setup the test for the scanner model.
    Internal Methods:
        _get_data(key, default): Get a parameter value from the internal data dictionary.
        _set_data(key, value): Set a parameter value in the internal data dictionary.
        _get_setting(key, default): Get a setting value from QSettings.
        _set_setting(key, value): Set a setting value in QSettings.
        _get_time(): Get the current time in the local timezone.
    Signals:
        dataChanged(str, object): Emitted when a data property changes.
    """

    def __init__(self, name: str, settings: QtCore.QSettings, cancel: CancelToken):
        """
        Initialize the test model.

        Args:
            name (str): The name of the test.
            settings (QtCore.QSettings): The application settings object.
            cancel (CancelToken): Token used to signal cancellation of the test.

        Attributes:
            _logger: Logger instance for the class.
            __timezone: Local timezone information.
            __settings: Reference to the provided settings object.
            __data: Dictionary to store test data.
            _widget: Widget associated with the test (if any).
            _cancel: Reference to the cancellation token.
            Name: Name of the test.
        """
        super().__init__()
        self._logger = tester._get_class_logger(self.__class__)
        self.__timezone = tz.tzlocal()
        self.__settings = settings
        self.__parameters = {}
        self.widgetTestMain = None
        self._cancel = cancel
        self.Name = name
        self.reset()

    durationChanged = QtCore.Signal(str)

    def get_duration(self) -> float:
        """
        Returns the duration value.

        Retrieves the value associated with the "Duration" key from the underlying data source.
        If the key is not present, returns 0.0 by default.

        Returns:
            float: The duration value, or 0.0 if not found.
        """
        return self._get_parameter("Duration", 0.0)

    def set_duration(self, value: float):
        """
        Sets the duration value.

        Args:
            value (float): The duration to set.
        """
        self._set_parameter("Duration", value)
        self.durationChanged.emit(f"{value} sec")

    Duration = QtCore.Property(float, get_duration, set_duration)

    endTimeChanged = QtCore.Signal(str)

    def get_end_time(self) -> datetime:
        """
        Returns the end time of the current operation.

        Retrieves the value associated with the "EndTime" key from the internal data source.
        If the value is not present, it defaults to the current time.

        Returns:
            datetime: The end time as a datetime object.
        """
        return self._get_parameter("EndTime", self._get_time())

    def set_end_time(self, value: datetime):
        """
        Sets the end time for the current operation.

        Args:
            value (datetime): The datetime value to set as the end time.
        """
        self._set_parameter("EndTime", value)
        try:
            self.endTimeChanged.emit(value.strftime("%H:%M:%S"))
        except:
            self.endTimeChanged.emit("")

    EndTime = QtCore.Property(datetime, get_end_time, set_end_time)

    nameChanged = QtCore.Signal(str)

    def get_name(self) -> str:
        """
        Returns the name associated with the current instance.

        Returns:
            str: The value of the "Name" data field, or an empty string if not found.
        """
        return self._get_parameter("Name", "")

    def set_name(self, value: str):
        """
        Sets the name value for the current instance.

        Args:
            value (str): The name to be set.
        """
        self._set_parameter("Name", value)
        self.nameChanged.emit(value)

    Name = QtCore.Property(str, get_name, set_name)

    serialNumberChanged = QtCore.Signal(str)

    def get_serial_number(self) -> str:
        """
        Retrieves the serial number.

        Returns:
            str: The serial number as a string. Returns an empty string if not available.
        """
        return self._get_parameter("SerialNumber", "")

    def set_serial_number(self, value: str):
        """
        Sets the serial number for the object.

        Args:
            value (str): The serial number to assign.
        """
        self._set_parameter("SerialNumber", value)
        self.serialNumberChanged.emit(value)

    SerialNumber = QtCore.Property(str, get_serial_number, set_serial_number)

    startTimeChanged = QtCore.Signal(str)

    def get_start_time(self) -> datetime:
        """
        Gets the start time.

        Returns:
            datetime: The start time retrieved from the data source, or the current time if not available.
        """
        return self._get_parameter("StartTime", self._get_time())

    def set_start_time(self, value: datetime):
        """
        Sets the start time for the test.

        Args:
            value (datetime): The datetime value to set as the start time.
        """
        self._set_parameter("StartTime", value)
        try:
            self.startTimeChanged.emit(value.strftime("%H:%M:%S"))
        except:
            self.startTimeChanged.emit("")

    StartTime = QtCore.Property(datetime, get_start_time, set_start_time)

    statusChanged = QtCore.Signal(str)

    def get_status(self) -> str:
        """
        Retrieves the status information.

        Returns:
            The value associated with the "Status" key, or None if not found.
        """
        return self._get_parameter("Status", None)

    def set_status(self, value: str):
        """
        Sets the status value for the current instance.

        Args:
            value: The status value to be set. The expected type and valid values depend on the implementation context.

        Returns:
            None
        """
        self._set_parameter("Status", value)
        self.statusChanged.emit(value)

    Status = QtCore.Property(str, get_status, set_status)

    parameterChanged = QtCore.Signal(str, object)

    def _get_parameter(self, key: str, default):
        """
        Retrieve the value associated with the given key from the internal settings dictionary.
        If the key does not exist, set it to the provided default value and return the default.

        Args:
            key (str): The key to look up in the settings dictionary.
            default: The value to return and set if the key is not present.

        Returns:
            The value associated with the key if it exists, otherwise the default value.
        """
        _value = default
        if key in self.__parameters:
            _value = self.__parameters[key]
        else:
            self._set_parameter(default)
        return _value

    def _set_parameter(self, key: str, value):
        """
        Sets the value for a given key in the internal data dictionary and emits a signal indicating that the data has changed.

        Args:
            key (str): The key under which the value will be stored.
            value: The value to associate with the specified key.

        Emits:
            dataChanged (str, Any): Signal emitted with the key and value when the data is updated.
        """
        self.__parameters[key] = value
        self.parameterChanged.emit(key, value)

    def _get_setting(self, key: str, default):
        """
        Retrieve a setting value from the settings dictionary for the current group.

        If the specified key exists, its value is returned. Otherwise, the default value is set and returned.

        Args:
            key (str): The key of the setting to retrieve.
            default: The default value to use if the key does not exist.

        Returns:
            The value associated with the key, or the default value if the key is not found.
        """
        _value = default
        self.__settings.beginGroup(self.Name)
        if self.__settings.contains(key):
            _value = self.__settings.value(key)
        else:
            self.__settings.setValue(key, _value)
        self.__settings.endGroup()
        return _value

    def _set_setting(self, key: str, value):
        """
        Sets a configuration value for the current object's settings group.

        Args:
            key (str): The name of the setting to set.
            value: The value to assign to the setting.

        This method begins a settings group using the object's `Name` attribute,
        sets the specified key to the given value, and then ends the group.
        """
        self.__settings.beginGroup(self.Name)
        self.__settings.setValue(key, value)
        self.__settings.endGroup()

    def _get_time(self) -> datetime:
        """
        Returns the current date and time in the instance's configured timezone.

        Returns:
            datetime: The current datetime object localized to self.__timezone.
        """
        return datetime.now(self.__timezone)

    @tester._member_logger
    def analyze_results(self, serial_number: str) -> bool:
        """
        Analyzes the test results for a given serial number.

        Logs the analysis process, records the end time, calculates the duration of the test,
        and sets the test status to passed by default.

        Args:
            serial_number (str): The serial number of the device or test subject being analyzed.
        """
        self._logger.info(f"Analyzing {self.Name} results for {serial_number}...")
        self.EndTime = self._get_time()
        self.Duration = (self.EndTime - self.StartTime).total_seconds()
        self.Status = "Pass"  # Assume the test passed by default
        return True

    @tester._member_logger
    def load_ui(self, widget: QtWidgets.QWidget):
        """
        Loads the provided QWidget as the UI for this test instance.

        This method sets up the main UI layout for the test, including a horizontal layout
        containing a group box for test parameters and a separate widget for test data.
        It creates labels for key test properties (name, serial number, start/end time, duration, status),
        connects their update signals, and adds them to the layout. The test data widget is also initialized
        with its own vertical layout for further customization by subclasses.

        Args:
            widget (QtWidgets.QWidget): The widget instance to be loaded as the UI.

        Side Effects:
            - Sets self.widgetTestMain to the provided widget.
            - Initializes and arranges UI elements for test parameters and data.
            - Connects property change signals to corresponding labels for live updates.
        """
        self._logger.info(f"Loading UI for test {self.Name}...")
        self.widgetTestMain = widget

        # Horizontal layout for the main test widget
        layoutTestMain = QtWidgets.QHBoxLayout(widget)
        layoutTestMain.setObjectName("layoutTestMain")
        layoutTestMain.setContentsMargins(0, 0, 0, 0)

        # Group box for test parameters
        groupBox = QtWidgets.QGroupBox(widget)
        groupBox.setObjectName("groupBoxTestParameters")
        groupBox.setAutoFillBackground(True)
        groupBox.setCheckable(False)
        layoutTestMain.addWidget(groupBox)

        # Vertical layout for parameters
        layoutParams = QtWidgets.QVBoxLayout(groupBox)
        layoutParams.setObjectName("layoutTestParameters")

        # Helper to create label, set text, connect signal, and add to layout
        def add_label(obj_name, text, signal):
            """
            Helper function to create a QLabel, set its text, connect a signal for updates,
            and add it to the provided layout.

            Args:
                obj_name (str): Object name for the label.
                text (Any): Initial text to display.
                signal (QtCore.Signal): Signal to connect for updating the label text.

            Returns:
                QtWidgets.QLabel: The created label widget.
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

        # Test Data widget and layout
        self.widgetTestData = QtWidgets.QWidget(widget)
        self.widgetTestData.setObjectName("widgetTestData")
        self.layoutTestData = QtWidgets.QVBoxLayout(self.widgetTestData)
        self.layoutTestData.setObjectName("layoutTestData")

    @tester._member_logger
    def on_generate_report(self, report: TestReport):
        """
        Adds information about the current test to the provided TestReport.
        This method logs the action and then appends the test's details, such as name, serial number,
        start and end times, duration, and status, to the report.
        Args:
            report (TestReport): The report object to which the test information will be added.
        """
        self._logger.info(f"Adding test report for {self.Name}...")

        # Add the test name to the top of the page
        report.startTest(
            self.Name,
            self.SerialNumber,
            self.StartTime.strftime("%H:%M:%S"),
            self.EndTime.strftime("%H:%M:%S"),
            f"{self.Duration} sec",
            self.Status,
        )

    @tester._member_logger
    def on_open(self, data: dict):
        """
        Handles the event when new data is opened for the test.

        Logs the addition of data for the current test and updates the internal data dictionary
        with the provided key-value pairs.

        Args:
            data (dict): A dictionary containing data to be added to the test.
        """
        self._logger.info(f"Adding parameters for {self.Name} with dict: {data}")
        for _key, _value in data.items():
            self._set_parameter(_key, _value)

    @tester._member_logger
    def on_save(self):
        """
        Saves the current test data.

        Logs an informational message indicating that data for the current test is being saved,
        and returns a dictionary containing the test's data.

        Returns:
            dict: A dictionary containing the test's data.
        """
        self._logger.info(f"Saving parameters for {self.Name}...")
        return dict(self.__parameters)

    @tester._member_logger
    def on_start_test(self, serial_number: str, devices: DeviceManager) -> bool:
        """
        Starts the test process for a given device serial number and device manager.

        Logs the start of the test, performs setup, runs the test, analyzes the results,
        and returns the current status.

        Args:
            serial_number (str): The serial number of the device under test.
            devices (DeviceManager): The device manager instance containing device and station information.

        Returns:
            Status: The current status after running and analyzing the test.
        """
        self._logger.info(
            f"Starting {self.Name} for {serial_number} on station {devices.ComputerName}..."
        )
        self.setup(serial_number, devices)
        self.run(serial_number, devices)
        self.teardown(devices)
        return self.analyze_results(serial_number)

    @tester._member_logger
    def release_ui(self):
        """
        Releases the UI resources associated with this instance.

        This method logs the release action, iterates through all child widgets of the main widget,
        schedules them for deletion, and then sets the main widget reference to None to free resources.
        """
        self._logger.info(f"Releasing UI for {self.Name}...")
        if self.widgetTestMain:
            for widget in self.widgetTestMain.findChildren(QtWidgets.QWidget):
                widget.deleteLater()
            self.widgetTestMain = None

    @tester._member_logger
    def reset(self):
        """
        Resets the test attributes to their initial state.

        Sets SerialNumber, StartTime, EndTime, Duration, and Status to None.
        This method is typically used to clear previous test data before starting a new test.
        """
        self.SerialNumber = None
        self.StartTime = None
        self.EndTime = None
        self.Duration = None
        self.Status = None

    @tester._member_logger
    def run(self, serial_number: str, devices: DeviceManager):
        """
        Run the test for the specified scanner model.

        Args:
            serial_number (str): The serial number of the scanner to test.
            devices (DeviceManager): The device manager instance containing device information.

        Logs:
            Information about the test run, including the serial number and station name.
        """
        self._logger.info(
            f"Running {self.Name} for {serial_number} on station {devices.ComputerName}..."
        )

    @tester._member_logger
    def set_data_directory(self, root_directory: Path):
        """
        Sets the data directory for the test instance.

        This method creates a subdirectory within the specified root directory,
        named after the test's Name attribute. If the directory does not exist,
        it is created along with any necessary parent directories. The method
        also logs the path to the newly set data directory.

        Args:
            root_directory (Path): The root directory under which the data directory will be created.
        """
        self.dataDirectory = root_directory / self.Name
        self.dataDirectory.mkdir(parents=True, exist_ok=True)
        self._logger.info(f"Data directory for {self.Name} set to {self.dataDirectory}")

    @tester._member_logger
    def setup(self, serial_number: str, devices: DeviceManager):
        """
        Initializes the test setup by storing the serial number, recording the start time, and performing device setup.

        Args:
            serial_number (str): The serial number of the device under test.
            devices (DeviceManager): The device manager instance used to set up devices for testing.

        Side Effects:
            Sets the SerialNumber and StartTime attributes on the instance.
            Calls the test_setup method on the devices manager.
        """
        self._logger.info(f"Setup {self.Name} for {serial_number}...")
        self.SerialNumber = serial_number
        self.StartTime = self._get_time()
        devices.test_setup()

    @tester._member_logger
    def teardown(self, devices: DeviceManager):
        """
        Tears down the test setup for the current test instance.

        This method logs the teardown action and calls the test_teardown method
        on the provided DeviceManager instance to perform any necessary cleanup
        after the test has completed.

        Args:
            devices (DeviceManager): The device manager instance used to teardown devices after testing.

        Side Effects:
            Calls the test_teardown method on the devices manager.
        """
        self._logger.info(f"Tearing down setup for {self.Name}...")
        devices.test_teardown()