# -*- coding: utf-8 -*-
from PySide6 import QtCore
import logging

from tester.manager.sequence import TestSequenceModel
from tester.manager.devices import DeviceManager
from tester.manager.report import TestReport
from tester.tests import _test_list

# Configure logging at the top of your file (customize as needed)
__logger = logging.getLogger(__name__)


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
        __logger.debug("__init__ called.")
        app_instance = QtCore.QCoreApplication.instance()
        if not (app_instance and app_instance.__class__.__name__ == "TesterApp"):
            __logger.critical(
                "TesterApp instance not found. Ensure the application is initialized correctly."
            )
            raise RuntimeError(
                "TesterApp instance not found. Ensure the application is initialized correctly."
            )
        self.__settings = app_instance.get_settings()
        self.__settings.settingsModified.connect(self.onSettingsModified)
        self.DataDirectory = self.__settings.getSetting(None, "DataDirectory", "")
        self.__cancel = cancel
        self.__devices = DeviceManager()
        self.__model = TestSequenceModel(self.__cancel, self.__devices)
        self.__model.startedTest.connect(self.modelStartedTest)
        self.__model.finishedTest.connect(self.modelFinishedTest)
        self.__timezone = QtCore.QTimeZone.systemTimeZone()

    @QtCore.Property(str, notify=computerNameChanged)
    def ComputerName(self):
        """
        Get the computer name used for the test.

        Returns:
            str: The computer name.
        """
        __logger.debug("Getting ComputerName property.")
        return self.__model.ComputerName

    @ComputerName.setter
    def ComputerName(self, value):
        """
        Set the computer name and emit the change signal.

        Args:
            value (str): The computer name.
        """
        __logger.debug(f"Setting ComputerName to '{value}'.")
        self.__model.ComputerName = value
        self.computerNameChanged.emit(value)

    @QtCore.Property(str)
    def DataFilePath(self) -> str:
        """
        Get the path to the JSON data file for the current run.

        Returns:
            str: The data file path.
        """
        __logger.debug("Getting DataFilePath property.")
        return QtCore.QDir(self.RunDataDirectory).filePath("data.json")

    @QtCore.Property(float, notify=durationChanged)
    def Duration(self):
        """
        Get the test duration in seconds.

        Returns:
            float: The test duration.
        """
        __logger.debug("Getting Duration property.")
        return self.__model.Duration

    @Duration.setter
    def Duration(self, value):
        """
        Set the test duration and emit the change signal.

        Args:
            value (float): The duration in seconds.
        """
        __logger.debug(f"Setting Duration to '{value}'.")
        self.__model.Duration = value
        self.durationChanged.emit(f"{value} sec")

    @QtCore.Property(QtCore.QDateTime, notify=endTimeChanged)
    def EndTime(self):
        """
        Get the end time of the test.

        Returns:
            QtCore.QDateTime: The end time.
        """
        __logger.debug("Getting EndTime property.")
        return self.__model.EndTime

    @EndTime.setter
    def EndTime(self, value):
        """
        Set the end time and emit the change signal. Updates duration.

        Args:
            value (QtCore.QDateTime): The end time.
        """
        __logger.debug(f"Setting EndTime to '{value.toString(QtCore.Qt.ISODate)}'.")
        self.__model.EndTime = value
        self.endTimeChanged.emit(
            value.toString("HH:mm:ss") if value and value.isValid() else ""
        )
        self.Duration = (
            self.StartTime.secsTo(value)
            if self.StartTime and value and self.StartTime.isValid() and value.isValid()
            else 0
        )

    @QtCore.Property(str, notify=modelNameChanged)
    def ModelName(self):
        """
        Get the model name for the test.

        Returns:
            str: The model name.
        """
        __logger.debug("Getting ModelName property.")
        return self.__model.ModelName

    @ModelName.setter
    def ModelName(self, value):
        """
        Set the model name and emit the change signal.

        Args:
            value (str): The model name.
        """
        __logger.debug(f"Setting ModelName to '{value}'.")
        self.__model.ModelName = value
        self.modelNameChanged.emit(value)

    @QtCore.Property(str)
    def PdfReportPath(self) -> str:
        """
        Get the path to the PDF report file for the current run.

        Returns:
            str: The PDF report file path.
        """
        __logger.debug("Getting PdfReportPath property.")
        return QtCore.QDir(self.RunDataDirectory).filePath("report.pdf")

    @QtCore.Property(str)
    def RunDataDirectory(self) -> str:
        """
        Get or create the directory for the current test run, based on serial number and start time.

        Returns:
            str: The run data directory.
        """
        __logger.debug("Getting RunDataDirectory property.")
        dir_path = QtCore.QDir(self.DataDirectory)
        serial = self.SerialNumber or "Unknown"
        dir_path.mkpath(serial)
        dir_path.cd(serial)
        start_time = self.StartTime
        dir_name = (
            start_time.toString("yyyyMMdd_HHmmss")
            if start_time and start_time.isValid()
            else "Unknown"
        )
        dir_path.mkpath(dir_name)
        dir_path.cd(dir_name)
        result = dir_path.absolutePath()
        __logger.info(f"RunDataDirectory resolved to '{result}'.")
        return result

    @QtCore.Property(str, notify=serialNumberChanged)
    def SerialNumber(self):
        """
        Get the serial number for the test.

        Returns:
            str: The serial number.
        """
        __logger.debug("Getting SerialNumber property.")
        return self.__model.SerialNumber

    @SerialNumber.setter
    def SerialNumber(self, value):
        """
        Set the serial number and emit the change signal.

        Args:
            value (str): The serial number.
        """
        __logger.debug(f"Setting SerialNumber to '{value}'.")
        self.__model.SerialNumber = value
        self.serialNumberChanged.emit(value)

    @QtCore.Property(QtCore.QDateTime, notify=startTimeChanged)
    def StartTime(self):
        """
        Get the start time of the test.

        Returns:
            QtCore.QDateTime: The start time.
        """
        __logger.debug("Getting StartTime property.")
        return self.__model.StartTime

    @StartTime.setter
    def StartTime(self, value):
        """
        Set the start time and emit the change signal.

        Args:
            value (QtCore.QDateTime): The start time.
        """
        __logger.debug(f"Setting StartTime to '{value.toString(QtCore.Qt.ISODate)}'.")
        self.__model.StartTime = value
        self.startTimeChanged.emit(
            value.toString("HH:mm:ss") if value and value.isValid() else ""
        )

    @QtCore.Property(str, notify=statusChanged)
    def Status(self):
        """
        Get the test status.

        Returns:
            str: The test status.
        """
        __logger.debug("Getting Status property.")
        return self.__model.Status

    @Status.setter
    def Status(self, value):
        """
        Set the test status and emit the change signal.

        Args:
            value (str): The test status.
        """
        __logger.debug(f"Setting Status to '{value}'.")
        self.__model.Status = value
        self.statusChanged.emit(value)

    @QtCore.Property(str, notify=testerNameChanged)
    def TesterName(self):
        """
        Get the tester name.

        Returns:
            str: The tester name.
        """
        __logger.debug("Getting TesterName property.")
        return self.__model.TesterName

    @TesterName.setter
    def TesterName(self, value):
        """
        Set the tester name and emit the change signal.

        Args:
            value (str): The tester name.
        """
        __logger.debug(f"Setting TesterName to '{value}'.")
        self.__model.TesterName = value
        self.testerNameChanged.emit(value)

    @QtCore.Slot(int, str)
    def modelStartedTest(self, test_id: int, test_name: str):
        """
        Slot called when a test starts in the model.

        Args:
            test_id (int): The ID of the test.
            test_name (str): The name of the test.
        """
        __logger.debug(f"Test started: ID={test_id}, Name={test_name}.")
        self.startedTest.emit(test_id, test_name)

    @QtCore.Slot(int, str, bool)
    def modelFinishedTest(self, test_id: int, test_name: str, status: bool):
        """
        Slot called when a test finishes in the model.

        Args:
            test_id (int): The ID of the test.
            test_name (str): The name of the test.
            status (bool): The status of the test (True for pass, False for fail).
        """
        __logger.debug(
            f"Test finished: ID={test_id}, Name={test_name}, Status={'Pass' if status else 'Fail'}."
        )
        self.finishedTest.emit(test_id, test_name, status)

    def getCurrentTime(self) -> QtCore.QDateTime:
        """
        Get the current local time in the configured timezone.

        Returns:
            QtCore.QDateTime: The current time.
        """
        now = QtCore.QDateTime.currentDateTime()
        if self.__timezone.isValid():
            now.setTimeZone(self.__timezone)
        __logger.debug(f"Current time is '{now.toString(QtCore.Qt.ISODate)}'.")
        return now

    def resetTestData(self):
        """
        Reset all test data and status to initial values.
        """
        __logger.debug("resetTestData called. Resetting all test data and status.")
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
        Set up the UI for the worker.

        Args:
            parent: The parent widget.
        """
        __logger.debug("setupUi called. Setting up UI for TestWorker.")
        parent.tableSequence.setModel(self.__model)
        self.__model.setupUi(parent.widgetTest)

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when settings are modified. Updates the data directory.
        """
        __logger.debug("onSettingsModified called. Updating worker settings.")
        self.DataDirectory = self.__settings.getSetting(
            None, "DataDirectory", self.DataDirectory
        )

    @QtCore.Slot(str)
    def onGenerateReport(self, path: str = None):
        """
        Generate a PDF report for the current test run.

        Args:
            path (str, optional): Path to save the report. If None, uses default.
        """
        __logger.debug(f"onGenerateReport called with path='{path}'.")
        file_path = path or self.PdfReportPath
        parent_dir = QtCore.QFileInfo(file_path).absolutePath()
        dir_obj = QtCore.QDir(parent_dir)
        if not dir_obj.exists():
            __logger.warning(
                f"Report parent directory '{parent_dir}' does not exist. Creating it."
            )
            dir_obj.mkpath(".")
        __logger.info(f"Generating report at '{file_path}'.")
        report = TestReport(file_path)
        start_time = self.StartTime
        end_time = self.EndTime
        report.titlePage(
            self.SerialNumber,
            self.ModelName,
            (
                start_time.toString("dddd, MMMM dd, yyyy")
                if start_time and start_time.isValid()
                else ""
            ),
            (
                start_time.toString("HH:mm:ss")
                if start_time and start_time.isValid()
                else ""
            ),
            end_time.toString("HH:mm:ss") if end_time and end_time.isValid() else "",
            f"{self.Duration} sec",
            self.TesterName,
            self.ComputerName,
            self.Status,
        )
        self.__model.onGenerateReport(report)
        report.finish()
        __logger.debug("Report generation finished.")
        self.finishedGeneratingReport.emit()

    @QtCore.Slot(str)
    def onLoadData(self, path: str):
        """
        Load test data from a JSON file.

        Args:
            path (str): Path to the data file.
        """
        __logger.debug(f"onLoadData called. Loading test data from file '{path}'.")
        file_obj = QtCore.QFile(path)
        if file_obj.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            doc = QtCore.QJsonDocument.fromJson(file_obj.readAll())
            if not doc.isObject():
                __logger.warning(f"File '{path}' does not contain a valid JSON object.")
                file_obj.close()
                self.finishedLoadingData.emit()
                return
            _data = doc.object().toVariantMap()
            _tests_data = _data.pop("Tests", None)
            self.__model.onLoadData(_tests_data)
            for _key, _value in _data.items():
                if hasattr(type(self), _key):
                    __logger.debug(f"Setting attribute '{_key}' from loaded data.")
                    setattr(self, _key, _value)
                else:
                    __logger.warning(f"Attribute '{_key}' not found in TestWorker.")
            file_obj.close()
        else:
            __logger.warning(f"Could not open file '{path}' for reading.")
        __logger.info(f"Loaded previous test data from '{path}'.")
        self.finishedLoadingData.emit()

    @QtCore.Slot(str)
    def onSaveData(self, path: str = None):
        """
        Save test data to a JSON file.

        Args:
            path (str, optional): Path to save the data. If None, uses default.
        """
        __logger.debug(f"onSaveData called with path='{path}'.")
        _data = self.__model.onSaveData()
        _path = path or self.DataFilePath
        __logger.info(f"Saving test data to file '{_path}'.")

        def _to_qvariant(obj):
            """
            Recursively convert objects to QVariant-compatible types.
            """
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
            __logger.debug(f"Test data saved to '{_path}'.")
        else:
            __logger.warning(f"Could not open file '{_path}' for writing.")
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
        __logger.debug(
            f"onStartTest called with serial_number='{serial_number}', model_name='{model_name}', test='{test}'."
        )
        self.resetTestData()
        self.SerialNumber = serial_number
        self.ModelName = model_name
        self.StartTime = self.getCurrentTime()
        self.Status = "Running"
        __logger.debug("Setting up devices for test.")
        self.__devices.setup()
        __logger.debug("Starting test sequence in model.")
        final_status = self.__model.onStartTest(self.RunDataDirectory, test=test)
        if getattr(self.__cancel, "cancelled", False):
            __logger.warning("Test was cancelled by user.")
            self.Status = "Cancelled"
        elif final_status is None:
            __logger.critical(f"Test '{test}' not found.")
        else:
            __logger.info(
                f"Test finished with status: {'Pass' if final_status else 'Fail'}."
            )
            self.Status = "Pass" if final_status else "Fail"
        __logger.debug("Tearing down devices after test.")
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
        __logger.debug("threadStarted called. Initializing test sequence model.")
        seq = self.__model
        if hasattr(seq, "beginResetModel"):
            __logger.debug("Calling beginResetModel on sequence.")
            seq.beginResetModel()
        if hasattr(seq, "Devices"):
            __logger.debug("Setting ComputerName and TesterName from Devices.")
            self.ComputerName = seq.Devices.ComputerName
            self.TesterName = seq.Devices.UserName
        tests = list(_test_list())
        if hasattr(seq, "beginInsertRows") and hasattr(seq, "endInsertRows"):
            __logger.debug(f"Inserting {len(tests)} tests into sequence model.")
            seq.beginInsertRows(QtCore.QModelIndex(), 0, len(tests) - 1)
            if hasattr(seq, "extend"):
                seq.extend(tests)
            seq.endInsertRows()
        if hasattr(seq, "endResetModel"):
            __logger.debug("Calling endResetModel on sequence.")
            seq.endResetModel()
        __logger.debug("Test sequence model initialized.")

    @QtCore.Slot()
    def run_cli(self):
        """
        Run the test sequence in CLI mode.
        Handles help, version, list, and exitcodes options. Prompts for serial/model if not provided.
        Supplies unique exit codes for each error type using an exit code map.
        """
        __logger.debug("run_cli called. Running CLI mode.")
        app_instance = QtCore.QCoreApplication.instance()
        if not (app_instance and app_instance.__class__.__name__ == "TesterApp"):
            __logger.critical(
                "TesterApp instance not found. Ensure the application is initialized correctly."
            )
            QtCore.QCoreApplication.exit(10)
            return

        exit_code_map = {
            KeyboardInterrupt: 2,
            FileNotFoundError: 20,
            PermissionError: 21,
            ValueError: 22,
            TypeError: 23,
            RuntimeError: 24,
            ImportError: 25,
            OSError: 26,
            Exception: 99,
        }
        exit_code_meanings = {
            0: "Success, help, version, or list shown",
            1: "Unknown/invalid usage",
            2: "User interrupt (KeyboardInterrupt)",
            10: "No TesterApp instance",
            11: "Error listing tests",
            12: "Test run error",
            20: "File not found",
            21: "Permission error",
            22: "Value error",
            23: "Type error",
            24: "Runtime error",
            25: "Import error",
            26: "OS error",
            99: "Generic/unknown exception",
        }

        options = app_instance.options

        def print_exit_codes():
            """
            Print the list of exit codes and their meanings.
            """
            print("\nExit codes and their meaning:")
            for code, meaning in sorted(exit_code_meanings.items()):
                print(f"  {code}: {meaning}")

        if options.isSet("help"):
            """
            Handle CLI help option.
            """
            __logger.debug("CLI help requested.")
            options.showHelp()
            print_exit_codes()
            QtCore.QCoreApplication.exit(0)
            return

        if options.isSet("version"):
            """
            Handle CLI version option.
            """
            __logger.debug("CLI version requested.")
            options.showVersion()
            QtCore.QCoreApplication.exit(0)
            return

        if options.isSet("exitcodes"):
            """
            Handle CLI exitcodes option.
            """
            __logger.debug("CLI exitcodes requested.")
            print_exit_codes()
            QtCore.QCoreApplication.exit(0)
            return

        if options.isSet("list"):
            """
            Handle CLI list option.
            """
            try:
                __logger.debug("CLI test list requested.")
                self.__model.cliPrintTestList()
                QtCore.QCoreApplication.exit(0)
            except Exception as e:
                __logger.critical(f"Error listing tests: {e}")
                code = exit_code_map.get(type(e), exit_code_map[Exception])
                QtCore.QCoreApplication.exit(code)
            return

        if options.isSet("run"):
            """
            Handle CLI run option.
            """
            try:
                __logger.debug("CLI test run requested.")
                serial = (
                    options.value("serial").strip()
                    if options.isSet("serial")
                    else input("Enter serial number: ").strip()
                )
                model = (
                    options.value("model").strip()
                    if options.isSet("model")
                    else input("Enter model name: ").strip()
                )
                test = options.value("test").strip() if options.isSet("test") else ""
                self.onStartTest(serial, model, test)
                QtCore.QCoreApplication.exit(0)
                return
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    __logger.warning("Test interrupted by user (KeyboardInterrupt).")
                else:
                    __logger.critical(f"Error running test: {e}")
                    options.showHelp()
                    print_exit_codes()
                code = exit_code_map.get(type(e), exit_code_map[Exception])
                QtCore.QCoreApplication.exit(code)
                return

        __logger.warning("Unknown or invalid CLI usage.")
        options.showHelp()
        print_exit_codes()
        QtCore.QCoreApplication.exit(1)
        return