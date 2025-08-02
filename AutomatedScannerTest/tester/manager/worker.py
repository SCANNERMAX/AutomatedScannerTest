# -*- coding: utf-8 -*-
from PySide6 import QtCore

from tester.manager.sequence import TestSequenceModel
from tester.manager.devices import DeviceManager
from tester.manager.report import TestReport
from tester.tests import _test_list


class TestWorker(QtCore.QObject):
    """
    Worker class to run tests in a separate thread.
    This allows the UI to remain responsive during test execution and supports CLI mode.
    Provides properties and signals for test status, data, and reporting.
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

    def __init__(self, cancel=None):
        """
        Initialize the TestWorker.

        Args:
            cancel: Optional cancel token for test interruption.
        Raises:
            RuntimeError: If TesterApp instance is not found.
        """
        super().__init__()
        app_instance = QtCore.QCoreApplication.instance()
        if app_instance is None or app_instance.__class__.__name__ != "TesterApp":
            QtCore.qCritical("TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        self.__settings = app_instance.get_settings()
        self.__settings.settingsModified.connect(self.onSettingsModified)
        self.onSettingsModified()
        self.__cancel = cancel
        self.__devices = DeviceManager()
        self.__model = TestSequenceModel(self.__cancel, self.__devices)
        self.__timezone = QtCore.QTimeZone.systemTimeZone()
        QtCore.qInfo("TestWorker initialized.")

    @QtCore.Property(str, notify=computerNameChanged)
    def ComputerName(self):
        """
        Get or set the computer name used for the test.

        Returns:
            str: The computer name.
        """
        return self.__model.ComputerName

    @ComputerName.setter
    def ComputerName(self, value):
        """
        Set the computer name and emit the change signal.

        Args:
            value (str): The computer name.
        """
        self.__model.ComputerName = value
        self.computerNameChanged.emit(value)

    @QtCore.Property(str)
    def DataFilePath(self) -> str:
        """
        Get the path to the JSON data file for the current run.

        Returns:
            str: The data file path.
        """
        return QtCore.QDir(self.RunDataDirectory).filePath("data.json")

    @QtCore.Property(float, notify=durationChanged)
    def Duration(self):
        """
        Get or set the test duration in seconds.

        Returns:
            float: The test duration.
        """
        return self.__model.Duration

    @Duration.setter
    def Duration(self, value):
        """
        Set the test duration and emit the change signal.

        Args:
            value (float): The duration in seconds.
        """
        self.__model.Duration = value
        self.durationChanged.emit(f"{value} sec")

    @QtCore.Property(QtCore.QDateTime, notify=endTimeChanged)
    def EndTime(self):
        """
        Get or set the end time of the test.

        Returns:
            QtCore.QDateTime: The end time.
        """
        return self.__model.EndTime

    @EndTime.setter
    def EndTime(self, value):
        """
        Set the end time and emit the change signal. Updates duration.

        Args:
            value (QtCore.QDateTime): The end time.
        """
        self.__model.EndTime = value
        self.endTimeChanged.emit(value.toString("HH:mm:ss") if value and value.isValid() else "")
        self.Duration = self.StartTime.secsTo(value) if self.StartTime and value and self.StartTime.isValid() and value.isValid() else 0

    @QtCore.Property(str, notify=modelNameChanged)
    def ModelName(self):
        """
        Get or set the model name for the test.

        Returns:
            str: The model name.
        """
        return self.__model.ModelName

    @ModelName.setter
    def ModelName(self, value):
        """
        Set the model name and emit the change signal.

        Args:
            value (str): The model name.
        """
        self.__model.ModelName = value
        self.modelNameChanged.emit(value)

    @QtCore.Property(str)
    def PdfReportPath(self) -> str:
        """
        Get the path to the PDF report file for the current run.

        Returns:
            str: The PDF report file path.
        """
        return QtCore.QDir(self.RunDataDirectory).filePath("report.pdf")

    @QtCore.Property(str)
    def RunDataDirectory(self) -> str:
        """
        Get or create the directory for the current test run, based on serial number and start time.

        Returns:
            str: The run data directory.
        """
        dir_path = QtCore.QDir(self.DataDirectory)
        serial = self.SerialNumber or "Unknown"
        dir_path.mkpath(serial)
        dir_path.cd(serial)
        dir_name = self.StartTime.toString("yyyyMMdd_HHmmss") if self.StartTime and self.StartTime.isValid() else "Unknown"
        dir_path.mkpath(dir_name)
        dir_path.cd(dir_name)
        return dir_path.absolutePath()

    @QtCore.Property(str, notify=serialNumberChanged)
    def SerialNumber(self):
        """
        Get or set the serial number for the test.

        Returns:
            str: The serial number.
        """
        return self.__model.SerialNumber

    @SerialNumber.setter
    def SerialNumber(self, value):
        """
        Set the serial number and emit the change signal.

        Args:
            value (str): The serial number.
        """
        self.__model.SerialNumber = value
        self.serialNumberChanged.emit(value)

    @QtCore.Property(QtCore.QDateTime, notify=startTimeChanged)
    def StartTime(self):
        """
        Get or set the start time of the test.

        Returns:
            QtCore.QDateTime: The start time.
        """
        return self.__model.StartTime

    @StartTime.setter
    def StartTime(self, value):
        """
        Set the start time and emit the change signal.

        Args:
            value (QtCore.QDateTime): The start time.
        """
        self.__model.StartTime = value
        self.startTimeChanged.emit(value.toString("HH:mm:ss") if value and value.isValid() else "")

    @QtCore.Property(str, notify=statusChanged)
    def Status(self):
        """
        Get or set the test status.

        Returns:
            str: The test status.
        """
        return self.__model.Status

    @Status.setter
    def Status(self, value):
        """
        Set the test status and emit the change signal.

        Args:
            value (str): The test status.
        """
        self.__model.Status = value
        self.statusChanged.emit(value)

    @QtCore.Property(str, notify=testerNameChanged)
    def TesterName(self):
        """
        Get or set the tester name.

        Returns:
            str: The tester name.
        """
        return self.__model.TesterName

    @TesterName.setter
    def TesterName(self, value):
        """
        Set the tester name and emit the change signal.

        Args:
            value (str): The tester name.
        """
        self.__model.TesterName = value
        self.testerNameChanged.emit(value)

    def getCurrentTime(self) -> QtCore.QDateTime:
        """
        Get the current local time in the configured timezone.

        Returns:
            QtCore.QDateTime: The current time.
        """
        now = QtCore.QDateTime.currentDateTime()
        if self.__timezone.isValid():
            now.setTimeZone(self.__timezone)
        return now

    def resetTestData(self):
        """
        Reset all test data and status to initial values.
        """
        self.SerialNumber = ""
        self.ModelName = ""
        self.StartTime = QtCore.QDateTime()
        self.EndTime = QtCore.QDateTime()
        self.Status = "Idle"
        if self.__cancel:
            self.__cancel.reset()
        self.__model.resetTestData()

    def setupUi(self, parent=None):
        """
        Set up the UI for the worker. This method can be overridden in subclasses.

        Args:
            parent: The parent widget.
        """
        QtCore.qInfo("[setupUi] Setting up UI for TestWorker.")
        parent.tableSequence.setModel(self.__model)
        self.__model.setupUi(parent.widgetTest)

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when settings are modified. Updates the data directory.
        """
        QtCore.qInfo("[onSettingsModified] Settings modified, updating worker settings.")
        data_directory = str(getattr(self, "DataDirectory", ""))
        self.DataDirectory = self.__settings.getSetting(None, "DataDirectory", data_directory)

    @QtCore.Slot(str)
    def onGenerateReport(self, path: str = None):
        """
        Generate a PDF report for the current test run.

        Args:
            path (str, optional): Path to save the report. If None, uses default.
        """
        qfile = QtCore.QFile(path or self.PdfReportPath)
        file_path = qfile.absolutePath()
        parent_dir = QtCore.QDir(qfile.filePath(".."))
        if not parent_dir.exists():
            parent_dir.mkpath(".")
        QtCore.qInfo(f"[onGenerateReport] Generating report at {file_path}.")
        report = TestReport(file_path)
        start_time = self.StartTime
        end_time = self.EndTime
        report.titlePage(
            self.SerialNumber,
            self.ModelName,
            start_time.toString("dddd, MMMM dd, yyyy") if start_time and start_time.isValid() else "",
            start_time.toString("HH:mm:ss") if start_time and start_time.isValid() else "",
            end_time.toString("HH:mm:ss") if end_time and end_time.isValid() else "",
            f"{self.Duration} sec",
            self.TesterName,
            self.ComputerName,
            self.Status,
        )
        self.__model.onGenerateReport(report)
        report.finish()
        QtCore.qInfo("[onGenerateReport] Report generation finished.")
        self.finishedGeneratingReport.emit()

    @QtCore.Slot(str)
    def onLoadData(self, path: str):
        """
        Load test data from a JSON file.

        Args:
            path (str): Path to the data file.
        """
        QtCore.qInfo(f"[onLoadData] Loading test data from file {path}.")
        file_obj = QtCore.QFile(path)
        if file_obj.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            doc = QtCore.QJsonDocument.fromJson(file_obj.readAll())
            if not doc.isObject():
                QtCore.qWarning(f"[onLoadData] File {path} does not contain a valid JSON object.")
                file_obj.close()
                self.finishedLoadingData.emit()
                return
            _data = doc.object().toVariantMap()
            _tests_data = _data.pop("Tests", None)
            self.__model.onLoadData(_tests_data)
            for _key, _value in _data.items():
                try:
                    setattr(self, _key, _value)
                except AttributeError:
                    QtCore.qWarning(f"[onLoadData] Attribute '{_key}' not found in TestSequenceModel.")
            file_obj.close()
        else:
            QtCore.qWarning(f"[onLoadData] Could not open file {path} for reading.")
        QtCore.qInfo("[onLoadData] Finished loading test data.")
        self.finishedLoadingData.emit()

    @QtCore.Slot(str)
    def onSaveData(self, path: str = None):
        """
        Save test data to a JSON file.

        Args:
            path (str, optional): Path to save the data. If None, uses default.
        """
        _data = self.__model.onSaveData()
        _path = QtCore.QDir(path or self.__model.DataFilePath).absolutePath()
        QtCore.qInfo(f"[onSaveData] Saving test data to file {_path}.")

        def _to_qvariant(obj):
            if isinstance(obj, dict):
                return {k: _to_qvariant(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_to_qvariant(v) for v in obj]
            if isinstance(obj, QtCore.QDateTime):
                return obj.toString(QtCore.Qt.ISODate)
            return obj

        qjson_obj = QtCore.QJsonObject.fromVariantMap(_to_qvariant(_data))
        doc = QtCore.QJsonDocument(qjson_obj)

        file_obj = QtCore.QFile(_path)
        if file_obj.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
            file_obj.write(doc.toJson(QtCore.QJsonDocument.Indented))
            file_obj.close()
            QtCore.qInfo(f"[onSaveData] Test data saved to {_path}.")
        else:
            QtCore.qWarning(f"[onSaveData] Could not open file {_path} for writing.")
        self.finishedSavingData.emit()

    @QtCore.Slot(str, str, str)
    def onStartTest(self, serial_number: str, model_name: str, test: str = None):
        """
        Start a test sequence.

        Args:
            serial_number (str): Serial number for the test.
            model_name (str): Model name for the test.
            test (str, optional): Specific test to run.
        """
        QtCore.qInfo(
            f"[onStartTest] Starting test sequence for serial number '{serial_number}', model '{model_name}', test='{test}'."
        )
        self.resetTestData()
        self.SerialNumber = serial_number
        self.ModelName = model_name
        self.StartTime = self.getCurrentTime()
        self.Status = "Running"
        self.__devices.setup()
        final_status = self.__model.onStartTest(self.RunDataDirectory, test)
        if getattr(self.__cancel, "cancelled", False):
            self.Status = "Cancelled"
        elif final_status is None:
            QtCore.qCritical(f"[onStartTest] Test '{test}' not found.")
        else:
            self.Status = "Pass" if final_status else "Fail"
        self.__devices.teardown()
        self.EndTime = self.getCurrentTime()
        self.onSaveData()
        self.onGenerateReport()
        self.finishedTesting.emit(final_status)

    @QtCore.Slot()
    def threadStarted(self):
        """
        Slot called when the worker thread starts. Initializes the test sequence model.
        """
        QtCore.qInfo("[threadStarted] TestWorker thread started. Initializing test sequence model.")
        seq = self.__model
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
        QtCore.qInfo("[threadStarted] Test sequence model initialized.")

    @QtCore.Slot()
    def run_cli(self):
        """
        Run the test sequence in CLI mode.
        Handles help, version, and list options. Prompts for serial/model if not provided.
        """
        app_instance = QtCore.QCoreApplication.instance()
        if app_instance is None or app_instance.__class__.__name__ != "TesterApp":
            QtCore.qCritical("TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")

        options = app_instance.options

        # Handle help option
        if options.isSet("help"):
            options.showHelp()
            QtCore.QCoreApplication.quit()
            return

        # Handle version option
        if options.isSet("version"):
            options.showVersion()
            QtCore.QCoreApplication.quit()
            return

        # Handle list option
        if options.isSet("list"):
            self.__model.cliPrintTestList()
            return

        serial = options.value("serial", "").strip()
        model = options.value("model", "").strip()
        if not serial:
            serial = input("Enter serial number: ").strip()
        if not model:
            model = input("Enter model name: ").strip()
        test = options.value("test", "").strip() if options.value("test") else None
        self.onStartTest(serial, model, test)

