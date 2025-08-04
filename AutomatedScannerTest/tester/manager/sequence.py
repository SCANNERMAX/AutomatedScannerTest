# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets
import logging

from tester.manager.devices import DeviceManager
from tester.tests import CancelToken, _test_list

# Configure Python logging
__logger = logging.getLogger(__name__)

class TestSequenceModel(QtCore.QAbstractTableModel):
    """
    Manages the execution, logging, and reporting of a sequence of hardware or software tests.

    This model provides a Qt-compatible interface for managing a list of test objects, their execution,
    result logging, report generation, and parameter management. It integrates with device management
    and supports both GUI and command-line workflows.
    """
    startedTest = QtCore.Signal(int, str)
    finishedTest = QtCore.Signal(int, str, bool)

    def __init__(self, cancel: CancelToken, devices: DeviceManager):
        """
        Initialize the TestSequenceModel, set up logging, device manager, test list, and default parameters.

        Args:
            cancel (CancelToken): Token to signal cancellation of test execution.
            devices (DeviceManager): Device manager for hardware/software test dependencies.

        Raises:
            RuntimeError: If there is no running QCoreApplication instance.
        """
        __logger.debug(f"__init__ called with cancel={cancel}, devices={devices}")
        super().__init__()
        app_instance = QtCore.QCoreApplication.instance()
        if app_instance is None or app_instance.__class__.__name__ != "TesterApp":
            __logger.critical("TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        self.__settings = app_instance.get_settings()
        self.__settings.settingsModified.connect(self.onSettingsModified)
        self.onSettingsModified()
        self.__parameters = {}
        self.__header = ("Test", "Status")
        self.__cancel = cancel
        self.__devices = devices
        self.__tests = []
        for test in _test_list():
            __logger.debug(f"Adding test: {test}")
            self.__tests.append(test(self.__cancel, self.__devices))
        __logger.debug("Initialization complete.")

    # Qt Properties for the sequence parameters (using Qt types where possible)
    @QtCore.Property(str)
    def ComputerName(self):
        __logger.debug("ComputerName getter called")
        return self.__parameters.get("ComputerName", "")

    @ComputerName.setter
    def ComputerName(self, value):
        __logger.debug(f"ComputerName setter called with value={value}")
        self.__parameters["ComputerName"] = value

    @QtCore.Property(float)
    def Duration(self):
        __logger.debug("Duration getter called")
        return self.__parameters.get("Duration", 0.0)

    @Duration.setter
    def Duration(self, value):
        __logger.debug(f"Duration setter called with value={value}")
        self.__parameters["Duration"] = value

    @QtCore.Property(QtCore.QDateTime)
    def EndTime(self):
        __logger.debug("EndTime getter called")
        val = self.__parameters.get("EndTime", None)
        if isinstance(val, QtCore.QDateTime):
            return val
        return QtCore.QDateTime()

    @EndTime.setter
    def EndTime(self, value):
        __logger.debug(f"EndTime setter called with value={value}")
        self.__parameters["EndTime"] = value if isinstance(value, QtCore.QDateTime) else QtCore.QDateTime()

    @QtCore.Property(str)
    def ModelName(self):
        __logger.debug("ModelName getter called")
        return self.__parameters.get("ModelName", "")

    @ModelName.setter
    def ModelName(self, value):
        __logger.debug(f"ModelName setter called with value={value}")
        self.__parameters["ModelName"] = value
        for _test in self.__tests:
            __logger.debug(f"Setting ModelName for test: {_test}")
            _test.ModelName = value

    @QtCore.Property(str)
    def SerialNumber(self):
        __logger.debug("SerialNumber getter called")
        return self.__parameters.get("SerialNumber", "")

    @SerialNumber.setter
    def SerialNumber(self, value):
        __logger.debug(f"SerialNumber setter called with value={value}")
        self.__parameters["SerialNumber"] = value
        for _test in self.__tests:
            __logger.debug(f"Setting SerialNumber for test: {_test}")
            _test.SerialNumber = value

    @QtCore.Property(QtCore.QDateTime)
    def StartTime(self):
        __logger.debug("StartTime getter called")
        val = self.__parameters.get("StartTime", None)
        if isinstance(val, QtCore.QDateTime):
            return val
        return QtCore.QDateTime()

    @StartTime.setter
    def StartTime(self, value):
        __logger.debug(f"StartTime setter called with value={value}")
        self.__parameters["StartTime"] = value if isinstance(value, QtCore.QDateTime) else QtCore.QDateTime()

    @QtCore.Property(str)
    def Status(self):
        __logger.debug("Status getter called")
        return self.__parameters.get("Status", "Idle")

    @Status.setter
    def Status(self, value):
        __logger.debug(f"Status setter called with value={value}")
        self.__parameters["Status"] = value

    @QtCore.Property(str)
    def TesterName(self):
        __logger.debug("TesterName getter called")
        return self.__parameters.get("TesterName", "")

    @TesterName.setter
    def TesterName(self, value):
        __logger.debug(f"TesterName setter called with value={value}")
        self.__parameters["TesterName"] = value

    # QtCore methods for the model
    def rowCount(self, parent=QtCore.QModelIndex()):
        __logger.debug("rowCount called")
        return len(self.__tests)

    def columnCount(self, parent=QtCore.QModelIndex()):
        __logger.debug("columnCount called")
        return len(self.__header)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        __logger.debug(f"data called with index={index}, role={role}")
        if not index.isValid():
            __logger.warning("data: Invalid index")
            return None
        row, col = index.row(), index.column()
        if row >= len(self.__tests) or col >= len(self.__header):
            __logger.warning("data: Index out of range")
            return None
        test = self.__tests[row]
        if role == QtCore.Qt.DisplayRole:
            __logger.debug(f"data: Returning display value for row={row}, col={col}")
            return test.Name if col == 0 else test.Status
        if role == QtCore.Qt.UserRole:
            __logger.debug(f"data: Returning user role value for row={row}")
            return test
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        __logger.debug(f"headerData called with section={section}, orientation={orientation}, role={role}")
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.__header[section] if section < len(self.__header) else None
        return super().headerData(section, orientation, role)

    # Methods for managing the test sequence
    def extend(self, tests: list):
        __logger.debug(f"extend called with tests={tests}")
        if not isinstance(tests, list):
            __logger.critical("Argument to extend is not a list")
            raise TypeError("tests must be a list")
        self.__tests.extend(tests)
        self.layoutChanged.emit()
        __logger.debug(f"Test list extended by {len(tests)} items.")

    def cliPrintTestList(self):
        __logger.debug("cliPrintTestList called")
        print("Available tests:")
        for test in self.__tests:
            __logger.debug(f"Printing test: {test}")
            test.cliPrintTest()
            print("\n")

    def onGenerateReport(self, report):
        __logger.debug(f"onGenerateReport called with report={report}")
        for _test in self.__tests:
            if getattr(_test, "Status", None) != "Skipped":
                __logger.debug(f"Generating report for test: {_test}")
                _test.onGenerateReport(report)

    def onLoadData(self, tests_data):
        __logger.debug(f"onLoadData called with tests_data={tests_data}")
        if tests_data:
            _name_to_test = {t.Name: t for t in self.__tests}
            for _test_name, _test_data in tests_data.items():
                _test_obj = _name_to_test.get(_test_name)
                if _test_obj:
                    __logger.debug(f"Loading data for test: {_test_name}")
                    _test_obj.onLoadData(_test_data)

    def onSaveData(self) -> dict:
        __logger.debug("onSaveData called")
        _data = self.__parameters.copy()
        _data["Tests"] = {t.Name: t.onSaveData() for t in self.__tests}
        __logger.debug(f"onSaveData returning: {_data}")
        return _data

    @QtCore.Slot()
    def onSettingsModified(self):
        __logger.debug("onSettingsModified called")

    def onStartTest(self, data_directory, test=None):
        __logger.debug(f"onStartTest called with data_directory={data_directory}, test={test}")
        statuses = []
        for index, _test in enumerate(self.__tests):
            __logger.info(f"Starting {_test.Name} (index={index})")
            self.startedTest.emit(index, _test.Name)
            if getattr(self.__cancel, "cancelled", False):
                __logger.warning(f"Testing cancelled before starting {_test.Name}")
                _test.Status = "Skipped"
                continue
            if test and _test.Name != test:
                __logger.info(f"Skipping {_test.Name}")
                _test.Status = "Skipped"
                continue
            result = _test.onStartTest(data_directory)
            __logger.info(f"{_test.Name} finished: result={result}")
            statuses.append(result)
            self.finishedTest.emit(index, _test.Name, result)
        if self.__cancel.cancelled:
            __logger.warning("Test sequence was cancelled.")
            return None
        elif len(statuses) == 0:
            __logger.warning("No tests were executed.")
            return None
        else:
            __logger.info(f"All tests finished. Success={all(statuses) if statuses else False}")
            return all(statuses) if statuses else False

    def resetTestData(self):
        __logger.debug("resetTestData called")
        for test in self.__tests:
            __logger.debug(f"Resetting parameters for test: {test}")
            test.resetParameters()
        __logger.debug("All test parameters reset")

    def setupUi(self, parent=None):
        __logger.debug(f"setupUi called with parent={parent}")
        if isinstance(parent, QtWidgets.QStackedWidget):
            __logger.debug("Clearing parent QStackedWidget")
            parent.clear()
            for test in self.__tests:
                __logger.debug(f"Adding widget for test: {test}")
                widget = QtWidgets.QWidget()
                parent.addWidget(widget)
                test.setupUi(widget)
        __logger.debug("UI setup complete")
