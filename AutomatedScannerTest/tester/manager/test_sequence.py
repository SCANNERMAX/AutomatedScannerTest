# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets
from datetime import datetime
from dateutil import tz
import json
from pathlib import Path

import tester
from tester.manager.devices import DeviceManager
from tester.manager.report import TestReport
from tester.tests import _test_list, CancelToken


class TestSequenceModel(QtCore.QAbstractTableModel):
    """
    TestSequenceModel manages the execution, logging, and reporting of a sequence of hardware or software tests.

    This class provides a Qt model for test management, including test execution, result logging,
    report generation, and parameter management. It integrates with device management and supports
    both GUI and command-line workflows.
    """

    def __init__(self, settings: QtCore.QSettings):
        """
        Initialize the TestSequenceModel, set up logging, device manager, test list, and default parameters.

        Args:
            settings (QtCore.QSettings): The application settings object.
        """
        super().__init__()
        self.__settings = settings
        self.__timezone = tz.tzlocal()
        self.__cancel = CancelToken()
        self.__parameters = {}
        self.__devices = DeviceManager(self.__settings)
        self.__tests = []
        self.__currentui = None

    ComputerName = QtCore.Property(
        str,
        fget=lambda self: self._get_parameter("ComputerName", ""),
        fset=lambda self, value: self._set_parameter("ComputerName", value),
    )
    Duration = QtCore.Property(
        float,
        fget=lambda self: self._get_parameter("Duration", 0.0),
        fset=lambda self, value: self._set_parameter("Duration", value),
    )
    EndTime = QtCore.Property(
        datetime,
        fget=lambda self: self._get_parameter("EndTime", self._get_time()),
        fset=lambda self, value: self._set_parameter("EndTime", value),
    )
    ModelName = QtCore.Property(
        str,
        fget=lambda self: self._get_parameter("ModelName", ""),
        fset=lambda self, value: self._set_parameter("ModelName", value),
    )
    SerialNumber = QtCore.Property(
        str,
        fget=lambda self: self._get_parameter("SerialNumber", ""),
        fset=lambda self, value: self._set_parameter("SerialNumber", value),
    )
    StartTime = QtCore.Property(
        datetime,
        fget=lambda self: self._get_parameter("StartTime", self._get_time()),
        fset=lambda self, value: self._set_parameter("StartTime", value),
    )
    Status = QtCore.Property(
        str,
        fget=lambda self: self._get_parameter("Status", "Idle"),
        fset=lambda self, value: self._set_parameter("Status", value),
    )
    TesterName = QtCore.Property(
        str,
        fget=lambda self: self._get_parameter("TesterName", ""),
        fset=lambda self, value: self._set_parameter("TesterName", value),
    )

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
        Set a parameter value.

        Args:
            key (str): The parameter key.
            value: The value to set.
        """
        self.__parameters[key] = value

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

    def _get_time(self):
        """
        Get the current local time in the configured timezone.

        Returns:
            datetime: The current time.
        """
        return datetime.now(self.__timezone)

    def getTime(self) -> datetime:
        """
        Get the current local time in the configured timezone.

        Returns:
            datetime: The current time.
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
        _row = index.row()
        _col = index.column()
        if not index.isValid() or _row >= len(self.__tests) or _col >= 2:
            return None
        _test = self.__tests[_row]
        if role == QtCore.Qt.DisplayRole:
            return _test.Name if _col == 0 else _test.Status
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

    def extend(self, tests: list):
        """
        Extend the list of tests with new test objects.

        Args:
            tests (list): A list of test objects to add.
        """
        if not isinstance(tests, list):
            raise TypeError("tests must be a list")
        self.__tests.extend(tests)
        self.layoutChanged.emit()

    @tester._member_logger
    def loadUi(self, index: int, container: QtWidgets.QWidget):
        """
        Load the UI for the test at the given index into the provided container.

        Args:
            index (int): The test index.
            container (QWidget): The container widget.
        """
        prev_ui = self.__currentui
        if prev_ui is not None:
            prev_ui.release_ui()
        if 0 <= index < len(self.__tests):
            current_ui = self.__tests[index]
            self.__currentui = current_ui
            current_ui.load_ui(container)
        else:
            self.__currentui = None

    @tester._member_logger
    def printTestList(self):
        """
        Print the list of available tests and their descriptions to the console.
        """
        print("Available tests:")
        for test in self.__tests:
            print(f"- {test.Name}:")
            if test.__doc__:
                print(
                    "\n".join(
                        f"    {line.strip()}"
                        for line in test.__doc__.strip().splitlines()
                    )
                )

    @property
    def Tests(self):
        """
        Get the list of available tests.

        Returns:
            list: The list of test objects.
        """
        return self.__tests

    @tester._member_logger
    def setupDevices(self):
        """
        Set up the devices required for the test sequence.
        """
        self.__devices.setup()

    @property
    def Parameters(self):
        """
        Get the current parameters of the test sequence.

        Returns:
            dict: A dictionary of parameter names and values.
        """
        return self.__parameters

    @property
    def Cancel(self):
        """
        Get the cancel token for the test sequence.

        Returns:
            CancelToken: The cancel token.
        """
        return self.__cancel

    @property
    def Devices(self):
        """
        Get the device manager.

        Returns:
            DeviceManager: The device manager instance.
        """
        return self.__devices


class TestWorker(QtCore.QObject):
    """
    Worker class to run tests in a separate thread.
    This allows the UI to remain responsive during test execution.
    """

    computerNameChanged = QtCore.Signal(str)
    durationChanged = QtCore.Signal(str)
    endTimeChanged = QtCore.Signal(str)
    finishedGeneratingReport = QtCore.Signal()
    finishedLoadingData = QtCore.Signal()
    finishedSavingData = QtCore.Signal()
    finishedTest = QtCore.Signal(int, bool)
    finishedTesting = QtCore.Signal(bool)
    modelNameChanged = QtCore.Signal(str)
    serialNumberChanged = QtCore.Signal(str)
    startTimeChanged = QtCore.Signal(str)
    startedTest = QtCore.Signal(int)
    statusChanged = QtCore.Signal(str)
    testerNameChanged = QtCore.Signal(str)

    def __init__(self, sequence: TestSequenceModel):
        """
        Initialize the TestWorker.

        Args:
            sequence (TestSequenceModel): The test sequence model to operate on.
        """
        super().__init__()
        self.sequence = sequence

    def getComputerName(self) -> str:
        """
        Get the current computer name.

        Returns:
            str: The computer name.
        """
        return self.sequence.ComputerName

    def setComputerName(self, value: str):
        """
        Set the computer name and emit the change signal.

        Args:
            value (str): The new computer name.
        """
        self.sequence.ComputerName = value
        self.computerNameChanged.emit(value)

    def getDuration(self) -> float:
        """
        Get the test duration.

        Returns:
            float: The duration in seconds.
        """
        return self.sequence.Duration

    def setDuration(self, value: float):
        """
        Set the test duration and emit the change signal.

        Args:
            value (float): The new duration in seconds.
        """
        self.sequence.Duration = value
        self.durationChanged.emit(f"{value} sec")

    def getEndTime(self) -> datetime:
        """
        Get the end time of the test sequence.

        Returns:
            datetime: The end time.
        """
        return self.sequence.EndTime

    def setEndTime(self, value: datetime):
        """
        Set the end time and emit the change signal.

        Args:
            value (datetime): The new end time.
        """
        self.sequence.EndTime = value
        try:
            self.endTimeChanged.emit(value.strftime("%H:%M:%S"))
        except Exception:
            self.endTimeChanged.emit("")

    def getModelName(self) -> str:
        """
        Get the model name.

        Returns:
            str: The model name.
        """
        return self.sequence.ModelName

    def setModelName(self, value: str):
        """
        Set the model name and emit the change signal.

        Args:
            value (str): The new model name.
        """
        self.sequence.ModelName = value
        self.modelNameChanged.emit(value)

    def getSerialNumber(self) -> str:
        """
        Get the serial number.

        Returns:
            str: The serial number.
        """
        return self.sequence.SerialNumber

    def setSerialNumber(self, value: str):
        """
        Set the serial number and emit the change signal.

        Args:
            value (str): The new serial number.
        """
        self.sequence.SerialNumber = value
        self.serialNumberChanged.emit(value)

    def getStartTime(self) -> datetime:
        """
        Get the start time of the test sequence.

        Returns:
            datetime: The start time.
        """
        return self.sequence.StartTime

    def setStartTime(self, value: datetime):
        """
        Set the start time and emit the change signal.

        Args:
            value (datetime): The new start time.
        """
        self.sequence.StartTime = value
        try:
            self.startTimeChanged.emit(value.strftime("%H:%M:%S"))
        except Exception:
            self.startTimeChanged.emit("")

    def getStatus(self) -> str:
        """
        Get the current status of the test sequence.

        Returns:
            str: The status string.
        """
        return self.sequence.Status

    def setStatus(self, value: str):
        """
        Set the status and emit the change signal.

        Args:
            value (str): The new status.
        """
        self.sequence.Status = value
        self.statusChanged.emit(value)

    def getTesterName(self) -> str:
        """
        Get the tester's name.

        Returns:
            str: The tester's name.
        """
        return self.sequence.TesterName

    def setTesterName(self, value: str):
        """
        Set the tester's name and emit the change signal.

        Args:
            value (str): The new tester name.
        """
        self.sequence.TesterName = value
        self.testerNameChanged.emit(value)

    def resetTestData(self):
        """
        Reset all test parameters and test states to their initial values.
        """
        QtCore.qInfo("Resetting test data")
        self.Duration = 0
        self.EndTime = None
        self.ModelName = ""
        self.SerialNumber = ""
        self.StartTime = None
        self.Status = "Idle"
        self.sequence.Cancel.reset()
        for _test in self.sequence.Tests:
            _test.reset()

    ComputerName = QtCore.Property(str, getComputerName, setComputerName)
    Duration = QtCore.Property(float, getDuration, setDuration)
    EndTime = QtCore.Property(datetime, getEndTime, setEndTime)
    ModelName = QtCore.Property(str, getModelName, setModelName)
    SerialNumber = QtCore.Property(str, getSerialNumber, setSerialNumber)
    StartTime = QtCore.Property(datetime, getStartTime, setStartTime)
    Status = QtCore.Property(object, getStatus, setStatus)
    TesterName = QtCore.Property(str, getTesterName, setTesterName)

    @QtCore.Slot(str)
    def onGenerateReport(self, path: str = None):
        """
        Generate a PDF report for the test sequence or a specific test.

        Args:
            path (str, optional): The output path for the report.
        """
        _path = path or str(self.sequence.PdfReportPath.resolve())
        _parent = Path(_path).parent
        if not _parent.exists():
            _parent.mkdir(parents=True, exist_ok=True)
        QtCore.qInfo(f"Generating report at {_path}")

        _report = TestReport(_path)
        _startTime = self.StartTime
        _endTime = self.EndTime
        _report.titlePage(
            self.SerialNumber,
            self.ModelName,
            _startTime.strftime("%A, %B %d, %Y") if _startTime else "",
            _startTime.strftime("%H:%M:%S") if _startTime else "",
            _endTime.strftime("%H:%M:%S") if _endTime else "",
            f"{self.Duration} sec",
            self.TesterName,
            self.ComputerName,
            self.Status,
        )

        for _test in self.sequence.Tests:
            if _test.Status != "Skipped":
                _test.on_generate_report(_report)

        _report.finish()
        self.finishedGeneratingReport.emit()

    @QtCore.Slot(str)
    def onLoadData(self, path: str):
        """
        Load test sequence data and test results from a JSON file.

        Args:
            path (str): The path to the JSON file.
        """
        QtCore.qInfo(f"Loading test data from file {path}")
        with open(path, "r") as _file:
            _data = json.load(_file)
            _tests_data = _data.pop("Tests", None)
            if _tests_data:
                _name_to_test = {t.Name: t for t in self.sequence.Tests}
                for _test_name, _test_data in _tests_data.items():
                    _test_obj = _name_to_test.get(_test_name)
                    if _test_obj:
                        _test_obj.on_open(_test_data)
            for _key, _value in _data.items():
                self.sequence._set_parameter(_key, _value)
        self.finishedLoadingData.emit()

    @QtCore.Slot(str)
    def onSaveData(self, path: str = None):
        """
        Save the current test sequence data and test results to a JSON file.

        Args:
            path (str, optional): The path to save the file. Defaults to DataFilePath.
        """
        QtCore.qInfo("Saving test data to file")
        _data = self.sequence.Parameters.copy()
        _test_data = {t.Name: t.on_save() for t in self.sequence.Tests}
        _data["Tests"] = _test_data
        _path = str(self.sequence.DataFilePath.resolve()) if path is None else path

        def _json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(_path, "w") as _file:
            json.dump(_data, _file, indent=4, default=_json_serial)
        self.finishedSavingData.emit()

    @QtCore.Slot(str, str, str)
    def onStartTest(self, serial_number: str, model_name: str, test: str = None):
        """
        Start the test sequence or a specific test.

        Args:
            serial_number (str): The serial number for the test run.
            model_name (str): The model name.
            test (str, optional): The name of a specific test to run.
        """
        QtCore.qInfo(f"Executing tests for serial number {serial_number}.")
        self.resetTestData()
        self.SerialNumber = serial_number
        self.ModelName = model_name
        self.StartTime = self.sequence.getTime()
        self.Status = "Running"
        self.sequence.setupDevices()
        _data_directory = self.sequence.RunDataDirectory
        _statuses = []
        _test_name = test
        _cancel = self.sequence.Cancel
        for _index, _test in enumerate(self.sequence.Tests):
            self.startedTest.emit(_index)
            if _cancel.cancelled:
                break
            if _test_name and _test.Name != _test_name:
                _test.Status = "Skipped"
                continue
            _test.set_data_directory(_data_directory)
            result = _test.on_start_test(serial_number, self.sequence.Devices)
            _statuses.append(result)
            self.finishedTest.emit(_index, result)
        _final_status = all(_statuses) if _statuses else False
        if _cancel.cancelled:
            self.Status = "Cancelled"
        else:
            if not _statuses:
                logger = getattr(self.sequence, "logger", None)
                if logger:
                    logger.error(f"Test '{test}' not found.")
            else:
                self.Status = "Pass" if _final_status else "Fail"
        self.sequence.Devices.teardown()
        self.EndTime = datetime.now(self.sequence._timezone)
        self.Duration = (self.EndTime - self.StartTime).total_seconds()
        self.onSaveData()
        self.onGenerateReport()
        self.finishedTesting.emit(_final_status)

    @QtCore.Slot()
    def threadStarted(self):
        """
        Initialize the test sequence, setting up the model and connecting signals.
        Loads the available tests and populates the model.
        """
        seq = self.sequence
        if hasattr(seq, "beginResetModel"):
            seq.beginResetModel()
        if hasattr(seq, "Devices"):
            self.ComputerName = seq.Devices.ComputerName
            self.TesterName = seq.Devices.UserName
        tests = list(_test_list())
        if hasattr(seq, "beginInsertRows") and hasattr(seq, "endInsertRows"):
            seq.beginInsertRows(QtCore.QModelIndex(), 0, len(tests) - 1)
            if hasattr(seq, "extend"):
                seq.extend(tests)
            seq.endInsertRows()
        if hasattr(seq, "endResetModel"):
            seq.endResetModel()

