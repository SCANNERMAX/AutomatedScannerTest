# -*- coding: utf-8 -*-
from PySide6 import QtCore
import logging

from tester import CancelToken
from tester.manager.sequence import TestSequenceModel
from tester.manager.devices import DeviceManager
from tester.manager.report import TestReport

logger = logging.getLogger(__name__)


class TestWorker(QtCore.QObject):
    """
    Worker class to run tests in a separate thread.
    This allows the UI to remain responsive during test execution and supports CLI mode.
    Provides properties and signals for test status, data, and reporting.
    """

    computerNameSignal = QtCore.Signal(str)
    durationSignal = QtCore.Signal(str)
    endTimeSignal = QtCore.Signal(str)
    reportFinishedSignal = QtCore.Signal()
    openFinishedSignal = QtCore.Signal()
    savingFinishedSignal = QtCore.Signal()
    testFinishedSignal = QtCore.Signal(int, str, bool)
    testingFinishedSignal = QtCore.Signal(bool)
    modelNameSignal = QtCore.Signal(str)
    serialNumberSignal = QtCore.Signal(str)
    startTimeSignal = QtCore.Signal(str)
    testStartedSignal = QtCore.Signal(int, str)
    statusSignal = QtCore.Signal(str)
    testerNameSignal = QtCore.Signal(str)
    closeSignal = QtCore.Signal()

    def __init__(self):
        """
        Initialize the TestWorker instance, setting up connections, device manager,
        test sequence model, and timezone.
        Raises:
            RuntimeError: If TesterApp instance is not found.
        """
        super().__init__()
        logger.debug("[TestWorker] __init__ called.")
        app = QtCore.QCoreApplication.instance()
        if not (app and hasattr(app, "addSettingsToObject")):
            logger.critical(
                "[TestWorker] TesterApp instance not found. Ensure the application is initialized correctly."
            )
            raise RuntimeError(
                "TesterApp instance not found. Ensure the application is initialized correctly."
            )
        app.addSettingsToObject(self)
        self.cancel = CancelToken()
        self.devices = DeviceManager()
        self.model = TestSequenceModel(self.cancel, self.devices)
        self.model.startedTest.connect(self.onModelStartedTest)
        self.model.finishedTest.connect(self.onModelFinishedTest)
        self.timeZone = QtCore.QTimeZone.systemTimeZone()
        self.exitCode = 0
        self.running = False
        self.resetTestData()

    @QtCore.Property(str, notify=computerNameSignal)
    def ComputerName(self):
        """
        Get the computer name used for the test.

        Returns:
            str: The computer name.
        """
        logger.debug("[TestWorker] Getting ComputerName property.")
        return self.model.ComputerName

    @ComputerName.setter
    def ComputerName(self, value):
        """
        Set the computer name and emit the change signal.

        Args:
            value (str): The computer name.
        """
        logger.debug(f"[TestWorker] Setting ComputerName to '{value}'.")
        self.model.ComputerName = value
        self.computerNameSignal.emit(value)

    @QtCore.Property(str)
    def DataFilePath(self) -> str:
        """
        Get the path to the JSON data file for the current run.

        Returns:
            str: The data file path.
        """
        logger.debug("[TestWorker] Getting DataFilePath property.")
        return QtCore.QDir(self.RunDataDirectory).filePath("data.json")

    @QtCore.Property(float, notify=durationSignal)
    def Duration(self):
        """
        Get the test duration in seconds.

        Returns:
            float: The test duration.
        """
        logger.debug("[TestWorker] Getting Duration property.")
        return self.model.Duration

    @Duration.setter
    def Duration(self, value):
        """
        Set the test duration and emit the change signal.

        Args:
            value (float): The duration in seconds.
        """
        logger.debug(f"[TestWorker] Setting Duration to '{value}'.")
        self.model.Duration = value
        self.durationSignal.emit(f"{value} sec")

    @QtCore.Property(QtCore.QDateTime, notify=endTimeSignal)
    def EndTime(self):
        """
        Get the end time of the test.

        Returns:
            QtCore.QDateTime: The end time.
        """
        logger.debug("[TestWorker] Getting EndTime property.")
        return self.model.EndTime

    @EndTime.setter
    def EndTime(self, value):
        """
        Set the end time and emit the change signal. Updates duration.

        Args:
            value (QtCore.QDateTime): The end time.
        """
        logger.debug(
            f"[TestWorker] Setting EndTime to '{value.toString(QtCore.Qt.ISODate)}'."
        )
        self.model.EndTime = value
        self.endTimeSignal.emit(
            value.toString("HH:mm:ss") if value and value.isValid() else ""
        )
        self.Duration = (
            self.StartTime.secsTo(value)
            if self.StartTime and value and self.StartTime.isValid() and value.isValid()
            else 0
        )

    @QtCore.Property(str, notify=modelNameSignal)
    def ModelName(self):
        """
        Get the model name for the test.

        Returns:
            str: The model name.
        """
        logger.debug("[TestWorker] Getting ModelName property.")
        return self.model.ModelName

    @ModelName.setter
    def ModelName(self, value):
        """
        Set the model name and emit the change signal.

        Args:
            value (str): The model name.
        """
        logger.debug(f"[TestWorker] Setting ModelName to '{value}'.")
        self.model.ModelName = value
        self.modelNameSignal.emit(value)

    @QtCore.Property(str)
    def PdfReportPath(self) -> str:
        """
        Get the path to the PDF report file for the current run.

        Returns:
            str: The PDF report file path.
        """
        logger.debug("[TestWorker] Getting PdfReportPath property.")
        return QtCore.QDir(self.RunDataDirectory).filePath("report.pdf")

    @QtCore.Property(str)
    def RunDataDirectory(self) -> str:
        """
        Get or create the directory for the current test run, based on serial number and start time.

        Returns:
            str: The run data directory.
        """
        logger.debug("[TestWorker] Getting RunDataDirectory property.")
        dir_path = QtCore.QDir(self.DataDirectory)
        serial = self.SerialNumber or "Unknown"
        if not dir_path.exists(serial):
            dir_path.mkpath(serial)
        dir_path.cd(serial)
        start_time = self.StartTime
        dir_name = (
            start_time.toString("yyyyMMdd_HHmmss")
            if start_time and start_time.isValid()
            else "Unknown"
        )
        if not dir_path.exists(dir_name):
            dir_path.mkpath(dir_name)
        dir_path.cd(dir_name)
        result = dir_path.absolutePath()
        logger.info(f"[TestWorker] RunDataDirectory resolved to '{result}'.")
        return result

    @QtCore.Property(str, notify=serialNumberSignal)
    def SerialNumber(self):
        """
        Get the serial number for the test.

        Returns:
            str: The serial number.
        """
        logger.debug("[TestWorker] Getting SerialNumber property.")
        return self.model.SerialNumber

    @SerialNumber.setter
    def SerialNumber(self, value):
        """
        Set the serial number and emit the change signal.

        Args:
            value (str): The serial number.
        """
        logger.debug(f"[TestWorker] Setting SerialNumber to '{value}'.")
        self.model.SerialNumber = value
        self.serialNumberSignal.emit(value)

    @QtCore.Property(QtCore.QDateTime, notify=startTimeSignal)
    def StartTime(self):
        """
        Get the start time of the test.

        Returns:
            QtCore.QDateTime: The start time.
        """
        logger.debug("[TestWorker] Getting StartTime property.")
        return self.model.StartTime

    @StartTime.setter
    def StartTime(self, value):
        """
        Set the start time and emit the change signal.

        Args:
            value (QtCore.QDateTime): The start time.
        """
        logger.debug(
            f"[TestWorker] Setting StartTime to '{value.toString(QtCore.Qt.ISODate)}'."
        )
        self.model.StartTime = value
        self.startTimeSignal.emit(
            value.toString("HH:mm:ss") if value and value.isValid() else ""
        )

    @QtCore.Property(str, notify=statusSignal)
    def Status(self):
        """
        Get the test status.

        Returns:
            str: The test status.
        """
        logger.debug("[TestWorker] Getting Status property.")
        return self.model.Status

    @Status.setter
    def Status(self, value):
        """
        Set the test status and emit the change signal.

        Args:
            value (str): The test status.
        """
        logger.debug(f"[TestWorker] Setting Status to '{value}'.")
        self.model.Status = value
        self.statusSignal.emit(value)

    @QtCore.Property(str, notify=testerNameSignal)
    def TesterName(self):
        """
        Get the tester name.

        Returns:
            str: The tester name.
        """
        logger.debug("[TestWorker] Getting TesterName property.")
        return self.model.TesterName

    @TesterName.setter
    def TesterName(self, value):
        """
        Set the tester name and emit the change signal.

        Args:
            value (str): The tester name.
        """
        logger.debug(f"[TestWorker] Setting TesterName to '{value}'.")
        self.model.TesterName = value
        self.testerNameSignal.emit(value)

    def getCurrentTime(self) -> QtCore.QDateTime:
        """
        Get the current local time in the configured timezone.

        Returns:
            QtCore.QDateTime: The current time.
        """
        now = QtCore.QDateTime.currentDateTime()
        if self.timeZone.isValid():
            now = now.toTimeZone(self.timeZone)
        logger.debug(
            f"[TestWorker] Current time is '{now.toString(QtCore.Qt.ISODate)}'."
        )
        return now

    def resetTestData(self):
        """
        Reset all test data and status to initial values.
        """
        logger.debug(
            "[TestWorker] resetTestData called. Resetting all test data and status."
        )
        self.SerialNumber = ""
        self.ModelName = ""
        self.StartTime = QtCore.QDateTime()
        self.EndTime = QtCore.QDateTime()
        self.Status = "Idle"
        if self.cancel:
            self.cancel.reset()
        self.model.resetTestData()

    def setupUi(self, parent=None):
        """
        Set up the UI for the worker.

        Args:
            parent: The parent widget.
        """
        logger.debug("[TestWorker] setupUi called. Setting up UI for TestWorker.")
        if (
            parent is not None
            and hasattr(parent, "tableSequence")
            and hasattr(parent, "stackedWidgetTest")
        ):
            parent.tableSequence.setModel(self.model)
            self.model.setupUi(parent.stackedWidgetTest)
        else:
            logger.warning(
                "[TestWorker] setupUi: parent is None or missing required attributes."
            )

    @QtCore.Slot()
    def onStopWorker(self):
        """
        Slot called when the application is exiting. Cleans up resources.
        """
        logger.debug("[TestWorker] onExit called. Cleaning up resources.")
        if self.running:
            logger.info(
                "[TestWorker] Worker is running. Stopping tests and cleaning up."
            )
            self.model.onStopTest()
            while self.running:
                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents, 100)
        self.closeSignal.emit()

    @QtCore.Slot(str)
    def onGenerateReport(self, path: str = None):
        """
        Generate a PDF report for the current test run.

        Args:
            path (str, optional): Path to save the report. If None, uses default.
        """
        self.running = True
        logger.debug(f"[TestWorker] onGenerateReport called with path='{path}'.")
        file_path = path or self.PdfReportPath
        parent_dir = QtCore.QFileInfo(file_path).absolutePath()
        dir_obj = QtCore.QDir(parent_dir)
        if not dir_obj.exists():
            logger.warning(
                f"[TestWorker] Report parent directory '{parent_dir}' does not exist. Creating it."
            )
            dir_obj.mkpath(".")
        logger.info(f"[TestWorker] Generating report at '{file_path}'.")
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
        self.model.onGenerateReport(report)
        report.finish()
        logger.debug("[TestWorker] Report generation finished.")
        self.running = False
        self.reportFinishedSignal.emit()

    @QtCore.Slot(str)
    def onLoadData(self, path: str):
        """
        Load test data from a JSON file.

        Args:
            path (str): Path to the data file.
        """
        self.running = True
        logger.debug(f"[TestWorker] onLoadData called. Loading test data from file '{path}'.")

        def _from_qvariant(obj):
            """
            Recursively convert QVariant-compatible types back to Python/Qt types.
            Handles dict, list, QDateTime strings, and QPoint dicts.
            """
            if isinstance(obj, dict):
                # Handle QPoint
                if set(obj.keys()) == {"x", "y"}:
                    return QtCore.QPoint(obj["x"], obj["y"])
                return {k: _from_qvariant(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_from_qvariant(v) for v in obj]
            if isinstance(obj, str):
                # Try to parse QDateTime from ISO string
                dt = QtCore.QDateTime.fromString(obj, QtCore.Qt.ISODate)
                if dt.isValid():
                    return dt
            return obj

        file_obj = QtCore.QFile(path)
        if file_obj.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            data_bytes = file_obj.readAll()
            file_obj.close()
            doc = QtCore.QJsonDocument.fromJson(data_bytes)
            if not doc.isNull():
                variant_data = doc.toVariant()
                loaded_data = _from_qvariant(variant_data)
                keys = list(loaded_data.keys())
                keys.reverse()
                for key in keys:
                    value = loaded_data[key]
                    if hasattr(self, key):
                        setattr(self, key, value)
                if hasattr(self.model, "onLoadData"):
                    self.model.onLoadData(loaded_data["Tests"], self.RunDataDirectory)
                logger.debug(f"[TestWorker] Test data loaded from '{path}'.")
                
            else:
                logger.warning(f"[TestWorker] Could not parse JSON from '{path}'.")
        else:
            logger.warning(f"[TestWorker] Could not open file '{path}' for reading.")
        self.onSaveData()
        self.onGenerateReport()
        self.running = False
        self.openFinishedSignal.emit()

    @QtCore.Slot(int, str, bool)
    def onModelFinishedTest(self, test_id: int, test_name: str, status: bool):
        """
        Slot called when a test finishes in the model.

        Args:
            test_id (int): The ID of the test.
            test_name (str): The name of the test.
            status (bool): The status of the test (True for pass, False for fail).
        """
        logger.info(
            f"[TestWorker] Finished test #{test_id + 1} -- {test_name}, Status={'Pass' if status else 'Fail'}."
        )
        self.testFinishedSignal.emit(test_id, test_name, status)

    @QtCore.Slot(int, str)
    def onModelStartedTest(self, test_id: int, test_name: str):
        """
        Slot called when a test starts in the model.

        Args:
            test_id (int): The ID of the test.
            test_name (str): The name of the test.
        """
        logger.info(f"[TestWorker] Started test #{test_id + 1} -- {test_name}.")
        self.testStartedSignal.emit(test_id, test_name)

    @QtCore.Slot()
    def onRunCli(self):
        """
        Run the test sequence in CLI mode.
        Handles help, version, list, and exitcodes options. Prompts for serial/model if not provided.
        Supplies unique exit codes for each error type using an exit code map.
        """
        logger.debug("[TestWorker] run_cli called. Running CLI mode.")
        app_instance = QtCore.QCoreApplication.instance()
        if not (app_instance and app_instance.__class__.__name__ == "TesterApp"):
            logger.critical(
                "[TestWorker] TesterApp instance not found. Ensure the application is initialized correctly."
            )
            self.exitCode = 10
            self.closeSignal.emit()
            return

        self.ComputerName = self.devices.ComputerName
        self.TesterName = self.devices.UserName

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
            logger.debug("[TestWorker] CLI help requested.")
            options.showHelp()
            print_exit_codes()
            self.exitCode = 0
            self.onStopWorker()
            return

        if options.isSet("version"):
            logger.debug("[TestWorker] CLI version requested.")
            options.showVersion()
            self.exitCode = 0
            self.onStopWorker()
            return

        if options.isSet("exitcodes"):
            logger.debug("[TestWorker] CLI exitcodes requested.")
            print_exit_codes()
            self.exitCode = 0
            self.onStopWorker()
            return

        if options.isSet("list"):
            try:
                logger.debug("[TestWorker] CLI test list requested.")
                self.model.cliPrintTestList()
                self.exitCode = 0
                self.onStopWorker()
            except Exception as e:
                logger.critical(f"[TestWorker] Error listing tests: {e}")
                code = exit_code_map.get(type(e), exit_code_map[Exception])
                self.exitCode = code
                self.onStopWorker()
            return

        if options.isSet("run"):
            try:
                logger.debug("[TestWorker] CLI test run requested.")
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
                self.exitCode = 0
                self.onStopWorker()
                return
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    logger.warning(
                        "[TestWorker] Test interrupted by user (KeyboardInterrupt)."
                    )
                else:
                    logger.critical(f"[TestWorker] Error running test: {e}")
                    options.showHelp()
                    print_exit_codes()
                code = exit_code_map.get(type(e), exit_code_map[Exception])
                self.exitCode = code
                self.onStopWorker()
                return

        logger.warning("[TestWorker] Unknown or invalid CLI usage.")
        options.showHelp()
        print_exit_codes()
        self.exitCode = 1  # Unknown/invalid usage
        self.onStopWorker()
        return

    @QtCore.Slot()
    def onRunGui(self):
        """
        Slot called when the worker thread starts. Initializes the test sequence model.
        """
        logger.debug(
            "[TestWorker] threadStarted called. Initializing test sequence model."
        )

    @QtCore.Slot(str, str)
    def onSaveData(self, path: str = None):
        """
        Save test data to a JSON file.

        Args:
            path (str, optional): Path to save the data. If None, uses default.
        """
        self.running = True
        logger.debug(f"[TestWorker] onSaveData called with path='{path}'.")
        _data = self.model.onSaveData()
        _path = path or self.DataFilePath
        logger.info(f"[TestWorker] Saving test data to file '{_path}'.")

        def _to_qvariant(obj):
            """
            Recursively convert objects to QVariant-compatible types.
            Handles dict, list, QDateTime, QPoint, and tuples.
            Ensures QDateTime is saved in UTC.
            """
            if isinstance(obj, dict):
                return {k: _to_qvariant(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_to_qvariant(v) for v in obj]
            if isinstance(obj, tuple):
                return [_to_qvariant(v) for v in obj]
            if hasattr(QtCore, "QPoint") and isinstance(obj, QtCore.QPoint):
                return {"x": obj.x(), "y": obj.y()}
            if isinstance(obj, QtCore.QDateTime):
                # Convert to UTC before saving
                utc_dt = obj.toUTC() if obj.isValid() else obj
                return utc_dt.toString(QtCore.Qt.ISODate)
            return obj

        qjson_obj = QtCore.QJsonDocument.fromVariant(_to_qvariant(_data))
        doc = QtCore.QJsonDocument(qjson_obj)

        file_obj = QtCore.QFile(_path)
        if file_obj.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
            file_obj.write(doc.toJson(QtCore.QJsonDocument.Indented))
            file_obj.close()
            logger.debug(f"[TestWorker] Test data saved to '{_path}'.")
        else:
            logger.warning(f"[TestWorker] Could not open file '{_path}' for writing.")
        self.running = False
        self.savingFinishedSignal.emit()

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when settings are modified. Updates the data directory.
        """
        logger.debug(
            "[TestWorker] onSettingsModified called. Updating worker settings."
        )
        dataDirectory = getattr(self, "DataDirectory", "")
        self.DataDirectory = self.settings.getSetting(
            None, "DataDirectory", dataDirectory
        )

    @QtCore.Slot(str, str, str)
    def onStartTest(self, serial_number: str, model_name: str, test: str = None):
        """
        Start a test sequence.

        Args:
            serial_number (str): Serial number for the test.
            model_name (str): Model name for the test.
            test (str, optional): Specific test to run.
        """
        self.running = True
        logger.debug(
            f"[TestWorker] onStartTest called with serial_number='{serial_number}', "
            f"model_name='{model_name}', test='{test}'."
        )
        self.resetTestData()
        self.SerialNumber = serial_number
        self.ModelName = model_name
        self.StartTime = self.getCurrentTime()
        self.Status = "Running"
        logger.info("[TestWorker] Setting up devices for tests.")
        self.devices.setup()
        logger.debug(f"[TestWorker] Starting test sequence for {serial_number}.")
        final_status = self.model.onStartTest(self.RunDataDirectory, test=test)
        if getattr(self.cancel, "cancelled", False):
            logger.warning("[TestWorker] Test was cancelled by user.")
            self.Status = "Cancelled"
        elif final_status is None:
            logger.critical(f"[TestWorker] Test '{test}' not found.")
        else:
            logger.info(
                f"[TestWorker] Tests finished with status: {'Pass' if final_status else 'Fail'}."
            )
            self.Status = "Pass" if final_status else "Fail"
        logger.info("[TestWorker] Tearing down devices after tests.")
        self.devices.teardown()
        self.EndTime = self.getCurrentTime()
        self.onSaveData()
        self.onGenerateReport()
        self.running = False
        self.testingFinishedSignal.emit(final_status)


def moveWorkerToThread(worker, interval_ms=100, run_cli=False):
    """
    Moves the worker to a new QThread and starts a QTimer in that thread
    to periodically process Qt events. Calls either onRunCli or onRunGui
    on the worker when the thread starts, based on the run_cli parameter.

    Args:
        worker (TestWorker): The worker instance to move.
        interval_ms (int): Timer interval in milliseconds.
        run_cli (bool): If True, call onRunCli; otherwise, call onRunGui.
    Returns:
        QThread: The thread running the worker.
    """
    thread = QtCore.QThread()
    worker.moveToThread(thread)

    # Timer to process events in the worker's thread
    timer = QtCore.QTimer()
    timer.setInterval(interval_ms)
    timer.moveToThread(thread)
    timer.timeout.connect(QtCore.QCoreApplication.processEvents)

    # Ensure timer stops and thread quits when worker signals close
    worker.closeSignal.connect(timer.stop)
    worker.closeSignal.connect(thread.quit)
    worker.closeSignal.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    # Start timer and call the appropriate method when thread starts
    def start_timer_and_method():
        timer.start()
        if run_cli:
            if hasattr(worker, "onRunCli") and callable(worker.onRunCli):
                worker.onRunCli()
        else:
            if hasattr(worker, "onRunGui") and callable(worker.onRunGui):
                worker.onRunGui()
    thread.started.connect(start_timer_and_method)

    thread.start()
    return thread
