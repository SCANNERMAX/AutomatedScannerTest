#-*- coding: utf-8 -*-
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
    Manages the execution, logging, and reporting of a sequence of hardware or software tests.

    Provides a Qt model for test management, including test execution, result logging,
    report generation, and parameter management. Integrates with device management and supports
    both GUI and command-line workflows.
    """

    computerNameChanged = QtCore.Signal(str)
    """Signal emitted when the computer name changes."""
    durationChanged = QtCore.Signal(str)
    """Signal emitted when the test duration changes."""
    endTimeChanged = QtCore.Signal(str)
    """Signal emitted when the end time changes."""
    modelNameChanged = QtCore.Signal(str)
    """Signal emitted when the model name changes."""
    serialNumberChanged = QtCore.Signal(str)
    """Signal emitted when the serial number changes."""
    startTimeChanged = QtCore.Signal(str)
    """Signal emitted when the start time changes."""
    statusChanged = QtCore.Signal(str)
    """Signal emitted when the test status changes."""
    testerNameChanged = QtCore.Signal(str)
    """Signal emitted when the tester name changes."""
    parameterChanged = QtCore.Signal(str, object)
    """Signal emitted when any parameter changes."""
    testStarted = QtCore.Signal(int)
    """Signal emitted when a test is started (by index)."""

    def __init__(self):
        """
        Initialize the TestSequence, set up logging, device manager, test list, and default parameters.
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
        self.__timezone = tz.tzlocal()
        self.__cancel = CancelToken()
        self.__parameters = {}
        self.__devices = DeviceManager(self.__settings)
        self.__tests = []
        self._currentui = None
        self._init_tests()
        self.reset_test_data()
        self.ComputerName = self.__devices.ComputerName
        self.TesterName = self.__devices.UserName
        self._start_logging(self.DataDirectory)
        logging.root.setLevel(logging.DEBUG)

    @tester._member_logger
    def _init_tests(self):
        """
        Initialize the list of tests using the test list factory.
        """
        settings = self.__settings
        cancel = self.__cancel
        for _test in _test_list():
            self.addTest(_test(settings, cancel))

    @tester._member_logger
    def _start_logging(self, log_path: Path = None):
        """
        Start logging to a rotating file handler in the specified log path.

        Args:
            log_path (Path): Directory where log files will be stored.
        """
        log_file = log_path / datetime.today().strftime("log_%Y%m%d_%H%M%S.log")
        handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5 * 1048576, backupCount=7
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logging.root.addHandler(handler)
        self.__logger.info(f"Logging started at {log_file}")

    def get_computer_name(self) -> str:
        """
        Get the current computer name.

        Returns:
            str: The computer name.
        """
        return self._get_parameter("ComputerName", "")

    def set_computer_name(self, value: str):
        """
        Set the computer name and emit the change signal.

        Args:
            value (str): The new computer name.
        """
        self._set_parameter("ComputerName", value)
        self.computerNameChanged.emit(value)

    ComputerName = QtCore.Property(str, get_computer_name, set_computer_name)

    def get_duration(self) -> float:
        """
        Get the test duration.

        Returns:
            float: The duration in seconds.
        """
        return self._get_parameter("Duration", 0.0)

    def set_duration(self, value: float):
        """
        Set the test duration and emit the change signal.

        Args:
            value (float): The new duration in seconds.
        """
        self._set_parameter("Duration", value)
        self.durationChanged.emit(f"{value} sec")

    Duration = QtCore.Property(float, get_duration, set_duration)

    def get_end_time(self) -> datetime:
        """
        Get the end time of the test sequence.

        Returns:
            datetime: The end time.
        """
        return self._get_parameter("EndTime", self._get_time())

    def set_end_time(self, value: datetime):
        """
        Set the end time and emit the change signal.

        Args:
            value (datetime): The new end time.
        """
        self._set_parameter("EndTime", value)
        try:
            self.endTimeChanged.emit(value.strftime("%H:%M:%S"))
        except Exception:
            self.endTimeChanged.emit("")

    EndTime = QtCore.Property(datetime, get_end_time, set_end_time)

    def get_model_name(self) -> str:
        """
        Get the model name.

        Returns:
            str: The model name.
        """
        return self._get_parameter("ModelName", "")

    def set_model_name(self, value: str):
        """
        Set the model name and emit the change signal.

        Args:
            value (str): The new model name.
        """
        self._set_parameter("ModelName", value)
        self.modelNameChanged.emit(value)

    ModelName = QtCore.Property(str, get_model_name, set_model_name)

    def get_serial_number(self) -> str:
        """
        Get the serial number.

        Returns:
            str: The serial number.
        """
        return self._get_parameter("SerialNumber", "")

    def set_serial_number(self, value: str):
        """
        Set the serial number and emit the change signal.

        Args:
            value (str): The new serial number.
        """
        self._set_parameter("SerialNumber", value)
        self.serialNumberChanged.emit(value)

    SerialNumber = QtCore.Property(str, get_serial_number, set_serial_number)

    def get_start_time(self) -> datetime:
        """
        Get the start time of the test sequence.

        Returns:
            datetime: The start time.
        """
        return self._get_parameter("StartTime", self._get_time())

    def set_start_time(self, value: datetime):
        """
        Set the start time and emit the change signal.

        Args:
            value (datetime): The new start time.
        """
        self._set_parameter("StartTime", value)
        try:
            self.startTimeChanged.emit(value.strftime("%H:%M:%S"))
        except Exception:
            self.startTimeChanged.emit("")

    StartTime = QtCore.Property(datetime, get_start_time, set_start_time)

    def get_status(self) -> str:
        """
        Get the current status of the test sequence.

        Returns:
            str: The status string.
        """
        return self._get_parameter("Status", "Idle")

    def set_status(self, value: str):
        """
        Set the status and emit the change signal.

        Args:
            value (str): The new status.
        """
        self._set_parameter("Status", value)
        self.statusChanged.emit(value)

    Status = QtCore.Property(str, get_status, set_status)

    def get_tester_name(self) -> str:
        """
        Get the tester's name.

        Returns:
            str: The tester's name.
        """
        return self._get_parameter("TesterName", "")

    def set_tester_name(self, value: str):
        """
        Set the tester's name and emit the change signal.

        Args:
            value (str): The new tester name.
        """
        self._set_parameter("TesterName", value)
        self.testerNameChanged.emit(value)

    TesterName = QtCore.Property(str, get_tester_name, set_tester_name)

    @property
    def DataDirectory(self) -> Path:
        """
        Get or create the root data directory for test results.

        Returns:
            Path: The data directory path.
        """
        _data_path = self._get_setting(
            "DataDirectory", f"C:/Test Data/{tester.__application__}"
        )
        _data_directory = Path(_data_path).resolve()
        if not _data_directory.exists():
            _data_directory.mkdir(parents=True, exist_ok=True)
        return _data_directory

    @DataDirectory.setter
    def DataDirectory(self, value: Path):
        """
        Set the data directory, move existing files, and restart logging.

        Args:
            value (Path): The new data directory path.
        """
        _old = self.DataDirectory
        new_value = value.resolve()
        if new_value == _old.resolve():
            return
        self.__logger.info(f"Moving data directory from {_old} to {value}")
        logging.shutdown()
        for handler in list(logging.root.handlers):
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.close()
                logging.root.removeHandler(handler)
        for _old_file in _old.rglob('*'):
            if _old_file.is_file():
                _new_file = new_value / _old_file.relative_to(_old)
                _new_file.parent.mkdir(parents=True, exist_ok=True)
                if not _new_file.exists():
                    _old_file.rename(_new_file)
        self._start_logging(new_value)
        self._set_setting("DataDirectory", str(new_value))

    @property
    def DataFilePath(self) -> Path:
        """
        Get the path to the JSON data file for the current run.

        Returns:
            Path: The data file path.
        """
        return self.RunDataDirectory / "data.json"

    @property
    def PdfReportPath(self) -> Path:
        """
        Get the path to the PDF report file for the current run.

        Returns:
            Path: The PDF report file path.
        """
        return self.RunDataDirectory / "report.pdf"

    @property
    def RunDataDirectory(self) -> Path:
        """
        Get or create the directory for the current test run, based on serial number and start time.

        Returns:
            Path: The run data directory.
        """
        data_dir = self.DataDirectory
        serial = self.SerialNumber
        start_time = self.StartTime
        if not serial or not start_time:
            _dir = data_dir / "Unknown" / "Unknown"
        else:
            _dir = data_dir / serial / start_time.strftime("%Y%m%d_%H%M%S")
        if not _dir.exists():
            _dir.mkdir(parents=True, exist_ok=True)
        return _dir

    def _get_parameter(self, key: str, default=None):
        """
        Get a parameter value.

        Args:
            key (str): The parameter key.
            default: The default value if not set.

        Returns:
            The parameter value or default.
        """
        return self.__parameters.get(key, default)

    def _set_parameter(self, key: str, value):
        """
        Set a parameter value and emit the parameterChanged signal.

        Args:
            key (str): The parameter key.
            value: The value to set.
        """
        self.__parameters[key] = value
        self.parameterChanged.emit(key, value)

    def _get_setting(self, key: str, default=None):
        """
        Get a persistent setting from QSettings.

        Args:
            key (str): The setting key.
            default: The default value if not set.

        Returns:
            The setting value or default.
        """
        if self.__settings.contains(key):
            return self.__settings.value(key)
        self._set_setting(key, default)
        return default

    def _set_setting(self, key: str, value):
        """
        Set a persistent setting in QSettings.

        Args:
            key (str): The setting key.
            value: The value to set.
        """
        self.__settings.setValue(key, value)

    def _get_time(self) -> datetime:
        """
        Get the current local time.

        Returns:
            datetime: The current time in the configured timezone.
        """
        return datetime.now(self.__timezone)

    def rowCount(self, parent=None):
        """
        Get the number of rows (tests) in the model.

        Args:
            parent: Not used.

        Returns:
            int: The number of tests.
        """
        return len(self.__tests)

    def columnCount(self, parent=None):
        """
        Get the number of columns in the model.

        Args:
            parent: Not used.

        Returns:
            int: The number of columns (always 2: Test, Status).
        """
        return 2

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """
        Get the data for a given index and role.

        Args:
            index (QModelIndex): The model index.
            role (int): The Qt role.

        Returns:
            The data for the cell, or None.
        """
        row = index.row()
        col = index.column()
        if not index.isValid() or row >= len(self.__tests) or col >= 2:
            return None
        _test = self.__tests[row]
        if role == QtCore.Qt.DisplayRole:
            return _test.Name if col == 0 else _test.Status
        elif role == QtCore.Qt.UserRole:
            return _test
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """
        Get the header data for the table.

        Args:
            section (int): The section index.
            orientation (Qt.Orientation): The orientation.
            role (int): The Qt role.

        Returns:
            The header label or None.
        """
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return ("Test", "Status")[section] if section in (0, 1) else None
        return super().headerData(section, orientation, role)

    @tester._member_logger
    def addTest(self, test: Test):
        """
        Add a test to the sequence and connect its signals for UI updates.

        Args:
            test (Test): The test instance to add.
        """
        row = len(self.__tests)
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.__tests.append(test)
        self.endInsertRows()
        self.layoutChanged.emit()

    def _emit_data_changed(self, row, col):
        """
        Emit the dataChanged signal for a specific cell.

        Args:
            row (int): The row index.
            col (int): The column index.
        """
        self.dataChanged.emit(
            self.index(row, col), self.index(row, col), [QtCore.Qt.DisplayRole]
        )

    @tester._member_logger
    def get_command_line_parser(self, app: QtWidgets.QApplication):
        """
        Create and process a QCommandLineParser for command-line options.

        Args:
            app (QApplication): The application instance.

        Returns:
            QCommandLineParser: The configured parser.
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
        Load the UI for the test at the given index into the provided container.

        Args:
            index (int): The test index.
            container (QWidget): The container widget.
        """
        prev_ui = self._currentui
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
        Generate a PDF report for the test sequence or a specific test.

        Args:
            path (str, optional): The output path for the report.
            test (str, optional): The name of a specific test to report.
        """
        _path = path or str(self.PdfReportPath.resolve())
        _parent = Path(_path).parent
        if not _parent.exists():
            _parent.mkdir(parents=True, exist_ok=True)
        self.__logger.info(f"Generating report at {_path}")

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

        if not test:
            for _test in self.__tests:
                _test.on_generate_report(_report)
        else:
            _selected_test = next((t for t in self.__tests if t.Name == test), None)
            if _selected_test:
                _selected_test.on_generate_report(_report)
            else:
                self.__logger.error(f"Test '{test}' not found.")
                return

        _report.finish()

    @tester._member_logger
    def on_open(self, path: str):
        """
        Load test sequence data and test results from a JSON file.

        Args:
            path (str): The path to the JSON file.
        """
        with open(path, "r") as _file:
            _data = json.load(_file)
            tests_data = _data.pop("Tests", None)
            if tests_data:
                name_to_test = {t.Name: t for t in self.__tests}
                for test_name, test_data in tests_data.items():
                    test_obj = name_to_test.get(test_name)
                    if test_obj:
                        test_obj.on_open(test_data)
            for _key, _value in _data.items():
                self._set_parameter(_key, _value)

    @tester._member_logger
    def on_save(self, path: str = None):
        """
        Save the current test sequence data and test results to a JSON file.

        Args:
            path (str, optional): The path to save the file. Defaults to DataFilePath.
        """
        _data = dict(self.__parameters)
        _test_data = {t.Name: t.on_save() for t in self.__tests}
        _data["Tests"] = _test_data
        _path = str(self.DataFilePath.resolve()) if path is None else path

        def _json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(_path, "w") as _file:
            json.dump(_data, _file, indent=4, default=_json_serial)

    @tester._member_logger
    def on_start_test(self, serial_number: str, model_name: str = "", test: str = None):
        """
        Start the test sequence or a specific test.

        Args:
            serial_number (str): The serial number for the test run.
            model_name (str, optional): The model name.
            test (str, optional): The name of a specific test to run.
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
        test_name = test
        cancel = self.__cancel
        for _index, _test in enumerate(self.__tests):
            if cancel.cancelled:
                break
            if test_name and _test.Name != test_name:
                continue
            self.testStarted.emit(_index)
            _test.set_data_directory(_data_directory)
            _statuses.append(_test.on_start_test(serial_number, self.__devices))
        if cancel.cancelled:
            self.Status = "Cancelled"
        else:
            if not _statuses:
                self.__logger.error(f"Test '{test}' not found.")
            else:
                self.Status = "Pass" if all(_statuses) else "Fail"
        self.__devices.teardown()
        self.EndTime = datetime.now(self.__timezone)
        self.Duration = (self.EndTime - self.StartTime).total_seconds()
        self.on_save()
        self.on_generate_report(test=test)

    @tester._member_logger
    def on_stop_test(self):
        """
        Request cancellation of the running test sequence.
        """
        self.__cancel.cancel()

    @tester._member_logger
    def print_test_list(self):
        """
        Print the list of available tests and their descriptions to the console.
        """
        print("Available tests:")
        for test in self.__tests:
            print(f"- {test.Name}:")
            if test.__doc__:
                for line in test.__doc__.strip().splitlines():
                    print(f"    {line.strip()}")

    @tester._member_logger
    def reset_test_data(self):
        """
        Reset all test parameters and test states to their initial values.
        """
        self.Duration = 0
        self.EndTime = None
        self.ModelName = ""
        self.SerialNumber = ""
        self.StartTime = None
        self.Status = "Idle"
        self.__cancel.reset()
        for _test in self.__tests:
            _test.reset()
