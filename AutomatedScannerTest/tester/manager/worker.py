# -*- coding: utf-8 -*-
from PySide6 import QtCore
from datetime import datetime
import json

from tester.manager.report import TestReport
from tester.tests import _test_list


class TestWorker(QtCore.QObject):
    """
    Worker class to run tests in a separate thread.
    This allows the UI to remain responsive during test execution.

    Attributes:
        sequence: The TestSequenceModel instance to operate on.
        __logger: Logger instance for logging messages.
        __settings: Application settings object.
    """

    computerNameChanged = QtCore.Signal(str)
    durationChanged = QtCore.Signal(str)
    endTimeChanged = QtCore.Signal(str)
    finishedGeneratingReport = QtCore.Signal()
    finishedLoadingData = QtCore.Signal()
    finishedSavingData = QtCore.Signal()
    finishedTest = QtCore.Signal(int, str, bool)
    finishedTesting = QtCore.Signal(bool)
    modelNameChanged = QtCore.Signal(str)
    serialNumberChanged = QtCore.Signal(str)
    startTimeChanged = QtCore.Signal(str)
    startedTest = QtCore.Signal(int, str)
    statusChanged = QtCore.Signal(str)
    testerNameChanged = QtCore.Signal(str)

    def __init__(self, sequence):
        """
        Initialize the TestWorker.

        Args:
            sequence: The TestSequenceModel instance to operate on.
        Raises:
            RuntimeError: If the application instance is not a TesterApp.
        """
        super().__init__()
        app = QtCore.QCoreApplication.instance()
        if app.__class__.__name__ == "TesterApp":
            self.__logger = app.get_logger(self.__class__.__name__)
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
        else:
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        self.sequence = sequence

    def getComputerName(self) -> str:
        """
        Get the computer name from the sequence.

        Returns:
            str: The computer name.
        """
        return self.sequence.ComputerName

    def setComputerName(self, value: str):
        """
        Set the computer name in the sequence and emit the change signal.

        Args:
            value (str): The new computer name.
        """
        self.sequence.ComputerName = value
        self.computerNameChanged.emit(value)

    def getDuration(self) -> float:
        """
        Get the duration from the sequence.

        Returns:
            float: The duration.
        """
        return self.sequence.Duration

    def setDuration(self, value: float):
        """
        Set the duration in the sequence and emit the change signal.

        Args:
            value (float): The new duration.
        """
        self.sequence.Duration = value
        self.durationChanged.emit(f"{value} sec")

    def getEndTime(self) -> datetime:
        """
        Get the end time from the sequence.

        Returns:
            datetime: The end time.
        """
        return self.sequence.EndTime

    def setEndTime(self, value: datetime):
        """
        Set the end time in the sequence and emit the change signal.

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
        Get the model name from the sequence.

        Returns:
            str: The model name.
        """
        return self.sequence.ModelName

    def setModelName(self, value: str):
        """
        Set the model name in the sequence and emit the change signal.

        Args:
            value (str): The new model name.
        """
        self.sequence.ModelName = value
        self.modelNameChanged.emit(value)

    def getSerialNumber(self) -> str:
        """
        Get the serial number from the sequence.

        Returns:
            str: The serial number.
        """
        return self.sequence.SerialNumber

    def setSerialNumber(self, value: str):
        """
        Set the serial number in the sequence and emit the change signal.

        Args:
            value (str): The new serial number.
        """
        self.sequence.SerialNumber = value
        self.serialNumberChanged.emit(value)

    def getStartTime(self) -> datetime:
        """
        Get the start time from the sequence.

        Returns:
            datetime: The start time.
        """
        return self.sequence.StartTime

    def setStartTime(self, value: datetime):
        """
        Set the start time in the sequence and emit the change signal.

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
        Get the status from the sequence.

        Returns:
            str: The status.
        """
        return self.sequence.Status

    def setStatus(self, value: str):
        """
        Set the status in the sequence and emit the change signal.

        Args:
            value (str): The new status.
        """
        self.sequence.Status = value
        self.statusChanged.emit(value)

    def getTesterName(self) -> str:
        """
        Get the tester name from the sequence.

        Returns:
            str: The tester name.
        """
        return self.sequence.TesterName

    def setTesterName(self, value: str):
        """
        Set the tester name in the sequence and emit the change signal.

        Args:
            value (str): The new tester name.
        """
        self.sequence.TesterName = value
        self.testerNameChanged.emit(value)

    def resetTestData(self):
        """
        Reset all test data in the sequence to initial values.
        """
        self.Duration = 0
        self.EndTime = None
        self.ModelName = ""
        self.SerialNumber = ""
        self.StartTime = None
        self.Status = "Idle"
        self.sequence.Cancel.reset()
        self.sequence.resetTests()

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Update the worker settings when the application settings are modified.
        This includes updating the computer name and tester name.
        """
        self.__logger.debug("Settings modified, updating worker settings.")

    ComputerName = QtCore.Property(
        str, getComputerName, setComputerName, notify=computerNameChanged
    )
    Duration = QtCore.Property(float, getDuration, setDuration, notify=durationChanged)
    EndTime = QtCore.Property(datetime, getEndTime, setEndTime, notify=endTimeChanged)
    ModelName = QtCore.Property(
        str, getModelName, setModelName, notify=modelNameChanged
    )
    SerialNumber = QtCore.Property(
        str, getSerialNumber, setSerialNumber, notify=serialNumberChanged
    )
    StartTime = QtCore.Property(
        datetime, getStartTime, setStartTime, notify=startTimeChanged
    )
    Status = QtCore.Property(object, getStatus, setStatus, notify=statusChanged)
    TesterName = QtCore.Property(
        str, getTesterName, setTesterName, notify=testerNameChanged
    )

    @QtCore.Slot(str)
    def onGenerateReport(self, path: str = None):
        """
        Generate a PDF report for the test sequence.

        Args:
            path (str, optional): The path to save the report. If None, uses the default path.
        """
        _path = QtCore.QDir(path or self.sequence.PdfReportPath).absolutePath()
        parent_qdir = QtCore.QDir(_path).filePath("..")
        parent_dir = QtCore.QDir(parent_qdir)
        if not parent_dir.exists():
            parent_dir.mkpath(".")
        self.__logger.debug(f"Generating report at {_path}.")

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
            if getattr(_test, "Status", None) != "Skipped":
                _test.onGenerateReport(_report)

        _report.finish()
        self.finishedGeneratingReport.emit()

    @QtCore.Slot(str)
    def onLoadData(self, path: str):
        """
        Load test data from a JSON file and update the sequence.

        Args:
            path (str): The path to the JSON data file.
        """
        self.__logger.debug(f"Loading test data from file {path}.")
        file_obj = QtCore.QFile(path)
        if file_obj.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            data = bytes(file_obj.readAll()).decode()
            _data = json.loads(data)
            _tests_data = _data.pop("Tests", None)
            if _tests_data:
                _name_to_test = {t.Name: t for t in self.sequence.Tests}
                for _test_name, _test_data in _tests_data.items():
                    _test_obj = _name_to_test.get(_test_name)
                    if _test_obj:
                        _test_obj.onOpen(_test_data)
            for _key, _value in _data.items():
                self.sequence._set_parameter(_key, _value)
            file_obj.close()
        self.finishedLoadingData.emit()

    @QtCore.Slot(str)
    def onSaveData(self, path: str = None):
        """
        Save the current test data to a JSON file.

        Args:
            path (str, optional): The path to save the data. If None, uses the default path.
        """
        _data = self.sequence.Parameters.copy()
        _test_data = {t.Name: t.onSave() for t in self.sequence.Tests}
        _data["Tests"] = _test_data
        _path = QtCore.QDir(path or self.sequence.DataFilePath).absolutePath()
        self.__logger.debug(f"Saving test data to file {_path}.")

        def _json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        file_obj = QtCore.QFile(_path)
        if file_obj.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
            stream = QtCore.QTextStream(file_obj)
            json_str = json.dumps(_data, indent=4, default=_json_serial)
            stream << json_str
            file_obj.close()
        self.finishedSavingData.emit()

    @QtCore.Slot(str, str, str)
    def onStartTest(self, serial_number: str, model_name: str, test: str = None):
        """
        Start the test sequence for a given serial number and model name.

        Args:
            serial_number (str): The serial number for the test.
            model_name (str): The model name for the test.
            test (str, optional): The name of a specific test to run. If None, runs all tests.
        """
        self.__logger.debug(
            f"Executing tests for serial number {serial_number} and model name {model_name}."
        )
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
            self.startedTest.emit(_index, _test.Name)
            if getattr(_cancel, "cancelled", False):
                break
            if _test_name and _test.Name != _test_name:
                _test.Status = "Skipped"
                continue
            _test.setDataDirectory(_data_directory)
            result = _test.onStartTest(serial_number, self.sequence.Devices)
            _statuses.append(result)
            self.finishedTest.emit(_index, _test.Name, result)
        _final_status = all(_statuses) if _statuses else False
        if getattr(_cancel, "cancelled", False):
            self.Status = "Cancelled"
        else:
            if not _statuses:
                self.__logger.error(f"Test '{test}' not found.")
            else:
                self.Status = "Pass" if _final_status else "Fail"
        self.sequence.Devices.teardown()
        self.EndTime = self.sequence.getTime()
        self.Duration = (self.EndTime - self.StartTime).total_seconds()
        self.onSaveData()
        self.onGenerateReport()
        self.finishedTesting.emit(_final_status)

    @QtCore.Slot()
    def threadStarted(self):
        """
        Initialize the test sequence model with available tests when the worker thread starts.
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
