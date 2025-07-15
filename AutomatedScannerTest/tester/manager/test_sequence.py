from PySide6 import QtCore, QtWidgets
from datetime import datetime
from dateutil import tz
import json
import logging
import logging.handlers
from pathlib import Path

import tester
from tester.manager.devices import DeviceManager
from tester.manager.report import TestReport
from tester.tests import _test_list, Test, CancelToken


class TestSequence(QtCore.QAbstractTableModel):
    """
    TestSequence manages the execution, logging, and reporting of a sequence of hardware or software tests.
    This class is responsible for:
    - Initializing test environment, logging, and device management.
    - Discovering and instantiating all available Test subclasses dynamically.
    - Managing test parameters and settings, including data directories, serial numbers, model names, and tester information.
    - Providing properties for accessing and modifying test metadata (e.g., StartTime, EndTime, Duration, Status).
    - Handling command-line options for test execution.
    - Running tests, collecting results, and updating status.
    - Generating PDF reports summarizing test results.
    - Saving and loading test data to and from JSON files.
    - Printing available tests and their descriptions.
    - Supporting cancellation and cleanup of test runs.
    Attributes:
        DataDirectory (Path): The root directory for storing test data.
        RunDataDirectory (Path): The directory for the current test run.
        DataFilePath (Path): The path to the JSON file storing test data.
        PdfReportPath (Path): The path to the generated PDF report.
        SerialNumber (str): The serial number of the device under test.
        ModelName (str): The model name of the device under test.
        TesterName (str): The name of the tester.
        StartTime (datetime): The start time of the test sequence.
        EndTime (datetime): The end time of the test sequence.
        Duration (float): The duration of the test sequence in seconds.
        Status (bool): The overall pass/fail status of the test sequence.
        StatusText (str): Human-readable status ("Pass", "Fail", or "Incomplete").
    Methods:
        command_line(app): Parse and return command-line options for test execution.
        get_test(index): Retrieve a test instance by index.
        on_generate_report(path=None, test=None): Generate a PDF report for the test sequence or a specific test.
        on_open(path): Load test data from a JSON file.
        on_save(path=None): Save test data to a JSON file.
        on_start_test(serial_number, model_name="", test=None): Execute the test sequence or a specific test.
        on_stop_test(): Cancel the running test sequence.
        print_test_list(): Print the list of available tests and their descriptions.
        test_count(): Return the number of available tests.
        test_name(index=-1): Return the name(s) of the test(s).
        test_status(index=-1): Return the status text(s) of the test(s).
    """

    def __init__(self):
        """
        Initializes the manager class by setting up logging, application settings, timezone, cancellation token, data storage, and device management.
        Dynamically discovers and instantiates all subclasses of the `Test` class found in the `tester.tests` package.
        Attributes initialized:
            __logger: Logger instance for the class.
            __settings: Application settings loaded from an INI file using QtCore.QSettings.
            __timezone: Local timezone information.
            __cancel: Cancellation token for managing test interruptions.
            __data: Dictionary for storing runtime data.
            __devices: DeviceManager instance for handling connected devices.
            __tests: List of instantiated Test subclasses discovered in the `tester.tests` package.
        Raises:
            Logs a warning if any test module cannot be imported.
        """
        super().__init__()
        self.__logger = tester._get_class_logger(self.__class__)
        self.__settings = QtCore.QSettings(
            QtCore.QSettings.Format.IniFormat,
            QtCore.QSettings.Scope.SystemScope,
            tester.__company__,
            tester.__application__,
            self,
        )
        self._start_logging(self.DataDirectory)
        logging.root.setLevel(logging.DEBUG)
        self.__timezone = tz.tzlocal()
        self.__cancel = CancelToken()
        self.__parameters = {}
        self.__devices = DeviceManager(self.__settings)
        self.__tests = []
        for _test in _test_list():
            self.addTest(_test(self.__settings, self.__cancel))
        self.reset_test_data()
        self.ComputerName = self.__devices.ComputerName
        self.TesterName = self.__devices.UserName

    @tester._member_logger
    def _start_logging(self, log_path: Path = None):
        """
        Starts logging to a rotating file handler with a timestamped log file name.

        If a log path is provided, creates a log file in that directory with the current date and time in its name.
        Configures the logging system to use a rotating file handler with a maximum file size of 5 MB and up to 7 backup files.
        Sets the log message format to include the timestamp, logger name, log level, and message.
        Logs an informational message indicating the start of logging and the log file location.

        Args:
            log_path (Path, optional): The directory where the log file will be created. Defaults to None.

        Raises:
            TypeError: If log_path is not a Path object when provided.
        """
        log_file = log_path / datetime.today().strftime("log_%Y%m%d_%H%M%S.log")
        _log_file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=(1048576 * 5), backupCount=7
        )
        _formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        _log_file_handler.setFormatter(_formatter)
        logging.root.addHandler(_log_file_handler)
        self.__logger.info(f"Logging started at {log_file}")

    computerNameChanged = QtCore.Signal(str)

    def get_computer_name(self) -> str:
        """
        Retrieves the computer name from the parameters.

        Returns:
            str: The value of the "ComputerName" parameter if it exists, otherwise an empty string.
        """
        return self._get_parameter("ComputerName", "")

    def set_computer_name(self, value: str):
        """
        Sets the computer name parameter and emits a signal indicating the change.

        Args:
            value (str): The new computer name to set.

        Emits:
            computerNameChanges (str): Signal emitted with the new computer name.
        """
        self._set_parameter("ComputerName", value)
        self.computerNameChanged.emit(value)

    ComputerName = QtCore.Property(str, get_computer_name, set_computer_name)

    durationChanged = QtCore.Signal(str)

    def get_duration(self) -> float:
        """
        Returns the duration parameter value.

        Retrieves the value of the "Duration" parameter. If the parameter is not set,
        returns 0.0 by default.

        Returns:
            float: The value of the "Duration" parameter, or 0.0 if not set.
        """
        return self._get_parameter("Duration", 0.0)

    def set_duration(self, value: float):
        """
        Sets the duration parameter for the test sequence.

        Args:
            value (float): The duration value to set, in seconds.
        """
        self._set_parameter("Duration", value)
        self.durationChanged.emit(f"{value} sec")

    Duration = QtCore.Property(float, get_duration, set_duration)

    endTimeChanged = QtCore.Signal(str)

    def get_end_time(self) -> datetime:
        """
        Returns the end time parameter.

        Retrieves the value of the "EndTime" parameter. If the parameter is not set, it returns the current time as a default.

        Returns:
            datetime: The end time value.
        """
        return self._get_parameter("EndTime", self._get_time())

    def set_end_time(self, value: datetime):
        """
        Sets the end time parameter for the sequence.

        Args:
            value (datetime): The end time to set.
        """
        self._set_parameter("EndTime", value)
        try:
            self.endTimeChanged.emit(value.strftime("%H:%M:%S"))
        except:
            self.endTimeChanged.emit("")

    EndTime = QtCore.Property(datetime, get_end_time, set_end_time)

    modelNameChanged = QtCore.Signal(str)

    def get_model_name(self) -> str:
        """
        Returns the model name parameter.

        Returns:
            str: The value of the "ModelName" parameter, or an empty string if not set.
        """
        return self._get_parameter("ModelName", "")

    def set_model_name(self, value: str):
        """
        Sets the model name parameter.

        Args:
            value (str): The name of the model to set.
        """
        self._set_parameter("ModelName", value)
        try:
            self.modelNameChanged.emit(value.strftime("%H:%M:%S"))
        except:
            self.modelNameChanged.emit("")

    ModelName = QtCore.Property(str, get_model_name, set_model_name)

    serialNumberChanged = QtCore.Signal(str)

    def get_serial_number(self) -> str:
        """
        Retrieves the serial number parameter.

        Returns:
            str: The serial number as a string. Returns an empty string if not set.
        """
        return self._get_parameter("SerialNumber", "")

    def set_serial_number(self, value: str):
        """
        Sets the serial number parameter.

        Args:
            value (str): The serial number to set.
        """
        self._set_parameter("SerialNumber", value)

    SerialNumber = QtCore.Property(str, get_serial_number, set_serial_number)

    startTimeChanged = QtCore.Signal(str)

    def get_start_time(self) -> datetime:
        """
        Returns the start time parameter.

        If the "StartTime" parameter is not set, returns the current time.

        Returns:
            datetime: The start time as a datetime object.
        """
        return self._get_parameter("StartTime", self._get_time())

    def set_start_time(self, value: datetime):
        """
        Sets the start time parameter.

        Args:
            value (datetime): The start time to be set.
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
        Retrieves the current status parameter.

        Returns:
            The value of the "Status" parameter, or None if not set.
        """
        return self._get_parameter("Status", "Idle")

    def set_status(self, value: str):
        """
        Sets the 'Status' parameter to the specified value.

        Args:
            value: The value to set for the 'Status' parameter.
        """
        self._set_parameter("Status", value)
        self.statusChanged.emit(value)

    Status = QtCore.Property(object, get_status, set_status)

    testerNameChanged = QtCore.Signal(str)

    def get_tester_name(self) -> str:
        """
        Returns the name of the tester.

        This method retrieves the tester's name by first attempting to get the "TesterName" parameter.
        If the parameter is not set, it falls back to using the current user's name.

        Returns:
            str: The name of the tester.
        """
        return self._get_parameter("TesterName", "")

    def set_tester_name(self, value: str):
        """
        Sets the name of the tester.

        Args:
            value (str): The name to assign to the tester.
        """
        self._set_parameter("TesterName", value)
        self.testerNameChanged.emit(value)

    TesterName = QtCore.Property(str, get_tester_name, set_tester_name)

    @property
    def DataDirectory(self) -> Path:
        """
        Returns the resolved path to the data directory, creating it if it does not exist.

        This method retrieves the data directory path from the settings using the key "DataDirectory".
        If the setting is not found, it defaults to "C:/Test Data/{tester.__application__}". The method
        ensures that the directory exists by creating it (including any necessary parent directories)
        if it does not already exist, and then returns the resolved Path object.

        Returns:
            Path: The resolved and ensured data directory path.
        """
        _data_path = self._get_setting(
            "DataDirectory", f"C:/Test Data/{tester.__application__}"
        )
        _data_directory = Path(_data_path).resolve()
        _data_directory.mkdir(parents=True, exist_ok=True)
        return _data_directory

    @DataDirectory.setter
    def DataDirectory(self, value: Path):
        """
        Updates the data directory to a new location.

        If the new directory is different from the current one, this method:
        - Logs the directory change.
        - Shuts down the current logging system and removes any RotatingFileHandler handlers.
        - Moves all files from the old data directory to the new one, preserving the directory structure.
        - Restarts logging in the new directory.
        - Updates the internal setting for the data directory.

        Args:
            value (Path): The new path for the data directory.
        """
        _old = self.DataDirectory
        if value.resolve() == _old.resolve():
            return
        self.__logger.info(
            f"Moving data directory from {self.DataDirectory} to {value}"
        )
        logging.shutdown()
        for _handler in logging.root.handlers[:]:
            if isinstance(_handler, logging.handlers.RotatingFileHandler):
                _handler.close()
                logging.root.removeHandler(_handler)
        for _dirpath, _dirnames, _filenames in _old.walk():
            for _item in _filenames:
                _old_file = Path(_dirpath) / _item
                _new_file = value / _old_file.relative_to(_old)
                if not _new_file.parent.exists():
                    _new_file.parent.mkdir(parents=True, exist_ok=True)
                if not _new_file.exists():
                    _old_file.rename(_new_file)
        self._start_logging(value)
        self._set_setting("DataDirectory", str(value))

    @property
    def DataFilePath(self) -> Path:
        """
        Returns the full path to the 'data.json' file located in the run data directory.

        Returns:
            Path: The path object representing the location of 'data.json' within the run data directory.
        """
        return self.RunDataDirectory / "data.json"

    @property
    def PdfReportPath(self) -> Path:
        """
        Returns the file path to the PDF report within the run data directory.

        Returns:
            Path: The full path to the "report.pdf" file located in the run data directory.
        """
        return self.RunDataDirectory / "report.pdf"

    @property
    def RunDataDirectory(self) -> Path:
        """
        Creates and returns the directory path for storing run data.

        The directory is constructed using the base data directory, the serial number,
        and the start time formatted as 'YYYYMMDD_HHMMSS'. If the directory does not exist,
        it is created along with any necessary parent directories.

        Returns:
            Path: The path to the created (or existing) run data directory.
        """
        _dir = (
            self.DataDirectory
            / self.SerialNumber
            / self.StartTime.strftime("%Y%m%d_%H%M%S")
        )
        _dir.mkdir(parents=True, exist_ok=True)
        return _dir

    parameterChanged = QtCore.Signal(str, object)

    def _get_parameter(self, key: str, default=None):
        """
        Retrieve the value associated with the given key from the internal data dictionary.
        If the key does not exist, set it to the provided default value and return the default.

        Args:
            key (str): The key to look up in the internal data dictionary.
            default (Any, optional): The value to set and return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the key, or the default value if the key was not present.
        """
        if key in self.__parameters:
            return self.__parameters[key]
        else:
            self._set_parameter(key, default)
            return default

    def _set_parameter(self, key: str, value):
        """
        Sets the value of a parameter in the internal data dictionary.

        Args:
            key (str): The key identifying the parameter to set.
            value: The value to assign to the parameter.

        """
        self.__parameters[key] = value
        self.parameterChanged.emit(key, value)

    def _get_setting(self, key: str, default=None):
        """
        Retrieve the value associated with the given key from the settings.

        If the key exists in the settings, its value is returned. If the key does not exist,
        the default value is set for the key and returned.

        Args:
            key (str): The key to look up in the settings.
            default (Any, optional): The value to set and return if the key does not exist. Defaults to None.

        Returns:
            Any: The value associated with the key, or the default value if the key was not present.
        """
        if self.__settings.contains(key):
            return self.__settings.value(key)
        else:
            self._set_setting(key, default)
            return default

    def _set_setting(self, key: str, value):
        """
        Sets a configuration setting by assigning the specified value to the given key.

        Args:
            key (str): The name of the setting to update.
            value: The value to assign to the setting.

        Returns:
            None
        """
        self.__settings.setValue(key, value)

    def _get_time(self) -> datetime:
        """
        Returns the current date and time in the configured timezone.

        Returns:
            datetime: The current datetime object localized to the instance's timezone.
        """
        return datetime.now(self.__timezone)

    def rowCount(self, parent=None):
        """
        Returns the number of rows in the model.

        Args:
            parent (QModelIndex, optional): The parent index. Defaults to None.

        Returns:
            int: The number of rows (tests) in the model.
        """
        return len(self.__tests)

    def columnCount(self, parent=None):
        """
        Returns the number of columns for the model.

        Args:
            parent (QModelIndex, optional): The parent index. Defaults to None.

        Returns:
            int: The number of columns in the model (always 2).
        """
        return 2

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """
        Returns the data associated with the specified index and role in the model.

        Args:
            index (QModelIndex): The index of the item in the model.
            role (int, optional): The role for which the data is requested. Defaults to QtCore.Qt.DisplayRole.

        Returns:
            Any: The data for the given index and role. Returns the test's name if the first column is selected,
                 the test's status text if the second column is selected, the test object itself for UserRole,
                 or None if the index is invalid or the role is unrecognized.
        """
        if not index.isValid() or index.row() >= len(self.__tests):
            return None
        if role == QtCore.Qt.DisplayRole:
            _test = self.__tests[index.row()]
            if index.column() >= 2:
                return None
            if index.column() == 0:
                return _test.Name
            elif index.column() == 1:
                return _test.Status
        elif role == QtCore.Qt.UserRole:
            return self.__tests[index.row()]
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """
        Returns the header data for a given section and orientation.

        Parameters:
            section (int): The index of the header section.
            orientation (Qt.Orientation): The orientation (horizontal or vertical) of the header.
            role (int, optional): The display role for which the data is requested. Defaults to QtCore.Qt.DisplayRole.

        Returns:
            Any: The header data for the specified section and orientation if the role is DisplayRole and orientation is Horizontal; otherwise, delegates to the superclass implementation.
        """
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            if section == 0:
                return "Test"
            elif section == 1:
                return "Status"
        return super().headerData(section, orientation, role)

    @tester._member_logger
    def addTest(self, test: Test):
        """
        Adds a test to the end of the test list and emits the appropriate signals.

        Args:
            test (Test): The test instance to add.
        """
        row = len(self.__tests)
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.__tests.append(test)
        test.nameChanged.connect(
            lambda: self.dataChanged.emit(
                self.index(row, 0), self.index(row, 0), [QtCore.Qt.DisplayRole]
            )
        )
        test.statusChanged.connect(
            lambda: self.dataChanged.emit(
                self.index(row, 1), self.index(row, 1), [QtCore.Qt.DisplayRole]
            )
        )
        self.endInsertRows()
        self.layoutChanged.emit()

    @tester._member_logger
    def get_command_line_parser(self, app: QtWidgets.QApplication):
        """
        Configures and processes command-line options for the application using Qt's QCommandLineParser.

        Args:
            app (QtWidgets.QApplication): The QApplication instance required for processing command-line options.

        Returns:
            QtCore.QCommandLineParser: The configured command-line parser after processing the application's arguments.

        Command-line options added:
            -d, --directory <directory> : Set the data directory (default: self.DataDirectory)
            -s, --serial <serial>       : The serial number on which to test (default: self.SerialNumber)
            -m, --model <model>         : The model number on which to test (default: self.ModelName)
            -t, --test <test>           : The test to run
            -l, --list                  : List the available tests
            -r, --run                   : Run the tests
            --help                      : Show help information
            --version                   : Show version information
        """
        _options = QtCore.QCommandLineParser()
        _context = _options.__class__.__name__
        _options.setApplicationDescription(tester.__doc__)
        _options.addOption(
            QtCore.QCommandLineOption(
                ["d", "directory"],
                QtCore.QCoreApplication.translate(_context, "Set the data directory."),
                "directory",
                str(self.DataDirectory),
            )
        )
        _options.addOption(
            QtCore.QCommandLineOption(
                ["s", "serial"],
                QtCore.QCoreApplication.translate(
                    _context, "The serial number on which to test."
                ),
                "serial",
                self.SerialNumber,
            )
        )
        _options.addOption(
            QtCore.QCommandLineOption(
                ["m", "model"],
                QtCore.QCoreApplication.translate(
                    _context, "The model number on which to test."
                ),
                "model",
                self.ModelName,
            )
        )
        _options.addOption(
            QtCore.QCommandLineOption(
                ["t", "test"],
                QtCore.QCoreApplication.translate(_context, "The test to run."),
                "test",
                None,
            )
        )
        _options.addOption(
            QtCore.QCommandLineOption(
                ["l", "list"],
                QtCore.QCoreApplication.translate(
                    _context, "List the available tests."
                ),
            )
        )
        _options.addOption(
            QtCore.QCommandLineOption(
                ["r", "run"],
                QtCore.QCoreApplication.translate(_context, "Run the tests."),
            )
        )
        _options.addHelpOption()
        _options.addVersionOption()
        _options.process(app)
        return _options

    @tester._member_logger
    def load_ui(self, index: int, container: QtWidgets.QWidget):
        """
        Loads the UI for the test at the specified index into the provided container widget.

        This method first releases the UI of any previously loaded test. If the index is valid,
        it loads the UI for the test at the given index into the container and updates the
        current UI reference. If the index is invalid, it clears the current UI reference.

        Args:
            index (int): The index of the test whose UI should be loaded.
            container (QtWidgets.QWidget): The widget container where the test UI will be loaded.

        Returns:
            None
        """
        prev_ui = getattr(self, "_currentui", None)
        if prev_ui is not None:
            prev_ui.release_ui()
        if 0 <= index < len(self.__tests):
            current_ui = self.__tests[index]
            self._currentui = current_ui
            current_ui.load_ui(container)
        else:
            self._currentui = None

    @tester._member_logger
    def on_generate_report(self, path: str = None, test: str = None):
        """
        Generates a PDF report for the test sequence.

        If a specific test name is provided, generates a report section for that test only.
        Otherwise, generates report sections for all tests in the sequence.

        Args:
            path (str, optional): The file path where the PDF report will be saved. If not provided, uses the default report path.
            test (str, optional): The name of a specific test to generate a report for. If not provided, includes all tests.

        Returns:
            None

        Logs:
            - Info message when report generation starts.
            - Error message if a specified test is not found.
        """
        _path = path or str(self.PdfReportPath.resolve())
        _parent = Path(_path).parent
        if not _parent.exists():
            _parent.mkdir(parents=True, exist_ok=True)
        self.__logger.info(f"Generating report at {_path}")

        # Begin generating a PDF document at _path
        _report = TestReport(_path)
        _start_time = self.StartTime
        _end_time = self.EndTime
        _report.titlePage(
            self.SerialNumber,
            self.ModelName,
            _start_time.strftime("%A, %B %d, %Y") if _start_time else "",
            _start_time.strftime("%H:%M:%S") if _start_time else "",
            _end_time.strftime("%H:%M:%S") if _end_time else "",
            f"{self.Duration} sec",
            self.TesterName,
            self.ComputerName,
            self.Status,
        )

        # Each test can append its own report section
        if test is None:
            for _test in self.__tests:
                _test.on_generate_report(_report)
        else:
            # Use a dict for O(1) lookup if many tests
            _test_map = {t.Name: t for t in self.__tests}
            _selected_test = _test_map.get(test)
            if _selected_test:
                _selected_test.on_generate_report(_report)
            else:
                self.__logger.error(f"Test '{test}' not found.")
                return

        _report.finish()

    @tester._member_logger
    def on_open(self, path: str):
        """
        Opens a JSON file at the specified path and loads its contents.
        Iterates through the key-value pairs in the JSON data:
        - If the key is "Tests", it matches test names in self.__tests and
          calls their on_open method with the corresponding data.
        - For all other keys, stores the value in self.__data.

        Args:
            path (str): The file path to the JSON file to open.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        with open(path, "r") as _file:
            _data = json.load(_file)
            for _key, _value in _data:
                if _key == "Tests":
                    for _test in self.__tests:
                        if _test.Name in _value:
                            _test.on_open(_value[_test.Name])
                else:
                    self._set_parameter(_key, _value)

    @tester._member_logger
    def on_save(self, path: str = None):
        """
        Saves the current test sequence data to a JSON file.
        Serializes the internal data, including all contained tests, and writes
        it to the specified file path.
        If no path is provided, uses the default data file path. Handles
        serialization of datetime objects.
        Args:
            path (str, optional): The file path to save the data to. If None,
                                  uses the default data file path.
        Raises:
            TypeError: If an object that is not serializable is encountered
                       during JSON serialization.
        """
        _data = self.__parameters
        _test_data = {}
        for _test in self.__tests:
            _test_data[_test.Name] = _test.on_save()
        _data["Tests"] = _test_data
        if path is None:
            _path = str(self.DataFilePath.resolve())
        else:
            _path = path

        def _json_serial(object):
            if isinstance(object, datetime):
                return object.isoformat()
            raise TypeError(f"Type {type(object)} not serializable")

        with open(_path, "w") as _file:
            json.dump(_data, _file, indent=4, default=_json_serial)

    testStarted = QtCore.Signal(int)

    @tester._member_logger
    def on_start_test(self, serial_number: str, model_name: str = "", test: str = None):
        """
        Executes the test sequence for a given serial number and model name.

        This method initializes the test environment, resets test states, sets up devices,
        and runs either all tests or a specified test. It manages test timing, status tracking,
        and handles cancellation requests. After execution, it tears down devices, calculates
        duration, updates the overall status, saves results, and generates a report.

        Args:
            serial_number (str): The serial number of the device under test.
            model_name (str, optional): The model name of the device. Defaults to "".
            test (str, optional): The name of a specific test to run. If None, all tests are run. Defaults to None.

        Returns:
            None
        """
        self.__logger.info(f"Executing tests for serial number {serial_number}")
        self.reset_test_data()
        self.SerialNumber = serial_number
        self.ModelName = model_name
        self.StartTime = datetime.now(self.__timezone)
        self.Status = "Running"
        self.__devices.setup()
        _data_directory = self.RunDataDirectory
        _statuses = []
        for _index, _test in enumerate(self.__tests):
            if self.__cancel.cancelled:
                break
            if test and _test.Name != test:
                continue
            self.testStarted.emit(_index)
            _test.set_data_directory(_data_directory)
            _status = _test.on_start_test(serial_number, self.__devices)
            _statuses.append(_status)
        if self.__cancel.cancelled:
            self.Status = "Cancelled"
        else:
            if len(_statuses) == 0:
                self.__logger.error(f"Test '{test}' not found.")
            else:
                if all(_statuses):
                    self.Status = "Pass"
                else:
                    self.Status = "Fail"
        self.__devices.teardown()
        self.EndTime = datetime.now(self.__timezone)
        self.Duration = (self.EndTime - self.StartTime).total_seconds()
        self.on_save()
        self.on_generate_report(test=test)

    @tester._member_logger
    def on_stop_test(self):
        """
        Handles the stop test event by triggering the cancellation process.

        This method calls the `cancel` method of the `__cancel` attribute to stop the ongoing test sequence.
        """
        self.__cancel.cancel()

    @tester._member_logger
    def print_test_list(self):
        """
        Prints the list of available tests along with their docstrings.

        This method iterates over all tests stored in the `self.__tests` attribute,
        printing each test's name followed by its docstring, line by line, with indentation.
        """
        print("Available tests:")
        for test in self.__tests:
            print(f"- {test.Name}:")
            for line in test.__doc__.strip().splitlines():
                print(f"    {line.strip()}")

    @tester._member_logger
    def reset_test_data(self):
        """
        Resets the test sequence data and all contained tests to their initial state.

        This method performs the following actions:
        - Sets the Duration to 0.
        - Sets EndTime and StartTime to None.
        - Clears ModelName and SerialNumber.
        - Sets Status to "Idle".
        - Resets the cancellation token.
        - Calls the reset method on each test in the sequence.

        This ensures that all test parameters and statuses are cleared, preparing the sequence for a new test run.
        """
        self.Duration = 0
        self.EndTime = None
        self.ModelName = ""
        self.SerialNumber = ""
        self.StartTime = None
        self.Status = "Idle"
        self.__cancel.reset()
        # Use list comprehension for faster iteration and potential future extension
        [_test.reset() for _test in self.__tests]
