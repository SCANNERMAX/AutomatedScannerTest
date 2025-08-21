# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets
import logging

from tester.manager.devices import DeviceManager
from tester.tests import CancelToken, _test_list

# Configure Python logging
logger = logging.getLogger(__name__)


class TestSequenceModel(QtCore.QAbstractTableModel):
    """
    Manages the execution, logging, and reporting of a sequence of hardware or software tests.

    This model provides a Qt-compatible interface for managing a list of test objects, their execution,
    result logging, report generation, and parameter management. It integrates with device management
    and supports both GUI and command-line workflows.
    """

    __parameters = {}
    __header = ("Test", "Status")
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
        logger.debug(
            f"[TestSequenceModel] __init__ called with cancel={cancel}, devices={devices}"
        )
        super().__init__()
        app = QtCore.QCoreApplication.instance()
        if not (app and hasattr(app, "addSettingsToObject")):
            logger.critical(
                f"[TestSequenceModel] TesterApp instance not found. Ensure the application is initialized correctly."
            )
            raise RuntimeError(
                "TesterApp instance not found. Ensure the application is initialized correctly."
            )
        app.addSettingsToObject(self)
        self.__cancel = cancel
        self.__devices = devices
        # Use list comprehension for faster test instantiation
        self.__tests = [test(self.__cancel, self.__devices) for test in _test_list()]

    @QtCore.Property(str)
    def ComputerName(self):
        """
        Get the computer name parameter.

        Returns:
            str: The computer name.
        """
        logger.debug(f"[TestSequenceModel] ComputerName getter called")
        return self.__parameters.get("ComputerName", "")

    @ComputerName.setter
    def ComputerName(self, value):
        """
        Set the computer name parameter.

        Args:
            value (str): The computer name.
        """
        logger.debug(
            f"[TestSequenceModel] ComputerName setter called with value={value}"
        )
        self.__parameters["ComputerName"] = value

    @QtCore.Property(float)
    def Duration(self):
        """
        Get the duration parameter.

        Returns:
            float: The duration value.
        """
        logger.debug(f"[TestSequenceModel] Duration getter called")
        return self.__parameters.get("Duration", 0.0)

    @Duration.setter
    def Duration(self, value):
        """
        Set the duration parameter.

        Args:
            value (float): The duration value.
        """
        logger.debug(f"[TestSequenceModel] Duration setter called with value={value}")
        self.__parameters["Duration"] = value

    @QtCore.Property(QtCore.QDateTime)
    def EndTime(self):
        """
        Get the end time parameter.

        Returns:
            QtCore.QDateTime: The end time.
        """
        logger.debug(f"[TestSequenceModel] EndTime getter called")
        val = self.__parameters.get("EndTime", None)
        return val if isinstance(val, QtCore.QDateTime) else QtCore.QDateTime()

    @EndTime.setter
    def EndTime(self, value):
        """
        Set the end time parameter.

        Args:
            value (QtCore.QDateTime): The end time.
        """
        logger.debug(f"[TestSequenceModel] EndTime setter called with value={value}")
        self.__parameters["EndTime"] = (
            value if isinstance(value, QtCore.QDateTime) else QtCore.QDateTime()
        )

    @QtCore.Property(str)
    def ModelName(self):
        """
        Get the model name parameter.

        Returns:
            str: The model name.
        """
        logger.debug(f"[TestSequenceModel] ModelName getter called")
        return self.__parameters.get("ModelName", "")

    @ModelName.setter
    def ModelName(self, value):
        """
        Set the model name parameter and propagate to all tests.

        Args:
            value (str): The model name.
        """
        logger.debug(f"[TestSequenceModel] ModelName setter called with value={value}")
        self.__parameters["ModelName"] = value
        # Use for loop without logging for performance
        for _test in self.__tests:
            _test.ModelName = value

    @QtCore.Property(str)
    def SerialNumber(self):
        """
        Get the serial number parameter.

        Returns:
            str: The serial number.
        """
        logger.debug(f"[TestSequenceModel] SerialNumber getter called")
        return self.__parameters.get("SerialNumber", "")

    @SerialNumber.setter
    def SerialNumber(self, value):
        """
        Set the serial number parameter and propagate to all tests.

        Args:
            value (str): The serial number.
        """
        logger.debug(
            f"[TestSequenceModel] SerialNumber setter called with value={value}"
        )
        self.__parameters["SerialNumber"] = value
        for _test in self.__tests:
            _test.SerialNumber = value

    @QtCore.Property(QtCore.QDateTime)
    def StartTime(self):
        """
        Get the start time parameter.

        Returns:
            QtCore.QDateTime: The start time.
        """
        logger.debug(f"[TestSequenceModel] StartTime getter called")
        val = self.__parameters.get("StartTime", None)
        return val if isinstance(val, QtCore.QDateTime) else QtCore.QDateTime()

    @StartTime.setter
    def StartTime(self, value):
        """
        Set the start time parameter.

        Args:
            value (QtCore.QDateTime): The start time.
        """
        logger.debug(f"[TestSequenceModel] StartTime setter called with value={value}")
        self.__parameters["StartTime"] = (
            value if isinstance(value, QtCore.QDateTime) else QtCore.QDateTime()
        )

    @QtCore.Property(str)
    def Status(self):
        """
        Get the status parameter.

        Returns:
            str: The status.
        """
        logger.debug(f"[TestSequenceModel] Status getter called")
        return self.__parameters.get("Status", "Idle")

    @Status.setter
    def Status(self, value):
        """
        Set the status parameter.

        Args:
            value (str): The status.
        """
        logger.debug(f"[TestSequenceModel] Status setter called with value={value}")
        self.__parameters["Status"] = value

    @QtCore.Property(str)
    def TesterName(self):
        """
        Get the tester name parameter.

        Returns:
            str: The tester name.
        """
        logger.debug(f"[TestSequenceModel] TesterName getter called")
        return self.__parameters.get("TesterName", "")

    @TesterName.setter
    def TesterName(self, value):
        """
        Set the tester name parameter.

        Args:
            value (str): The tester name.
        """
        logger.debug(f"[TestSequenceModel] TesterName setter called with value={value}")
        self.__parameters["TesterName"] = value

    # QtCore methods for the model
    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        Get the number of rows in the model.

        Args:
            parent (QtCore.QModelIndex): The parent index.

        Returns:
            int: Number of rows.
        """
        logger.debug(f"[TestSequenceModel] rowCount called")
        return len(self.__tests)

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        Get the number of columns in the model.

        Args:
            parent (QtCore.QModelIndex): The parent index.

        Returns:
            int: Number of columns.
        """
        logger.debug(f"[TestSequenceModel] columnCount called")
        return len(self.__header)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """
        Get the data for a given index and role.

        Args:
            index (QtCore.QModelIndex): The index.
            role (int): The role.

        Returns:
            Any: The data for the index and role.
        """
        logger.debug(f"[TestSequenceModel] data called with index={index}, role={role}")
        if not index.isValid():
            logger.warning(f"[TestSequenceModel] data: Invalid index")
            return None
        row, col = index.row(), index.column()
        if row >= len(self.__tests) or col >= len(self.__header):
            logger.warning(f"[TestSequenceModel] data: Index out of range")
            return None
        test = self.__tests[row]
        if role == QtCore.Qt.DisplayRole:
            logger.debug(
                f"[TestSequenceModel] data: Returning display value for row={row}, col={col}"
            )
            return test.Name if col == 0 else test.Status
        if role == QtCore.Qt.UserRole:
            logger.debug(
                f"[TestSequenceModel] data: Returning user role value for row={row}"
            )
            return test
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """
        Get the header data for a given section, orientation, and role.

        Args:
            section (int): The section.
            orientation (QtCore.Qt.Orientation): The orientation.
            role (int): The role.

        Returns:
            Any: The header data.
        """
        logger.debug(
            f"[TestSequenceModel] headerData called with section={section}, orientation={orientation}, role={role}"
        )
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.__header[section] if section < len(self.__header) else None
        return super().headerData(section, orientation, role)

    # Methods for managing the test sequence
    def extend(self, tests: list):
        """
        Extend the test list with additional tests.

        Args:
            tests (list): List of test objects to add.

        Raises:
            TypeError: If tests is not a list.
        """
        logger.debug(f"[TestSequenceModel] extend called with tests={tests}")
        if not isinstance(tests, list):
            logger.critical(f"[TestSequenceModel] Argument to extend is not a list")
            raise TypeError("tests must be a list")
        self.beginResetModel()
        self.__tests.extend(tests)
        self.endResetModel()
        logger.debug(f"[TestSequenceModel] Test list extended by {len(tests)} items.")

    def cliPrintTestList(self):
        """
        Print the list of available tests to the command line.
        """
        logger.debug(f"[TestSequenceModel] cliPrintTestList called")
        print("Available tests:")
        for test in self.__tests:
            test.cliPrintTest()
            print("\n")

    def onGenerateReport(self, report):
        """
        Generate a report for all non-skipped tests.

        Args:
            report: The report object to populate.
        """
        logger.debug(
            f"[TestSequenceModel] onGenerateReport called with report={report}"
        )
        for _test in self.__tests:
            if getattr(_test, "Status", None) != "Skipped":
                logger.debug(f"[TestSequenceModel] Generating report for test: {_test}")
                _test.onGenerateReport(report)

    def onLoadData(self, tests_data):
        """
        Load test data into the model.

        Args:
            tests_data (dict): Dictionary of test data keyed by test name.
        """
        logger.debug(
            f"[TestSequenceModel] onLoadData called with tests_data={tests_data}"
        )
        if tests_data:
            _name_to_test = {t.Name: t for t in self.__tests}
            for _test_name, _test_data in tests_data.items():
                _test_obj = _name_to_test.get(_test_name)
                if _test_obj:
                    logger.debug(
                        f"[TestSequenceModel] Loading data for test: {_test_name}"
                    )
                    _test_obj.onLoadData(_test_data)

    def onSaveData(self) -> dict:
        """
        Save the current model data.

        Returns:
            dict: Dictionary containing parameters and test data.
        """
        logger.debug(f"[TestSequenceModel] onSaveData called")
        _data = self.__parameters.copy()
        _data["Tests"] = {t.Name: t.onSaveData() for t in self.__tests}
        logger.debug(f"[TestSequenceModel] onSaveData returning: {_data}")
        return _data

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when settings are modified.
        """
        logger.debug(f"[TestSequenceModel] onSettingsModified called")

    def onStartTest(self, data_directory, test=None):
        """
        Start the test sequence, optionally for a specific test.

        Args:
            data_directory (str): Directory to store test data.
            test (str, optional): Name of a specific test to run.

        Returns:
            bool or None: True if all tests succeeded, False if any failed, None if cancelled or no tests run.
        """
        logger.debug(
            f"[TestSequenceModel] onStartTest called with data_directory={data_directory}, test={test}"
        )
        statuses = []
        cancel = getattr(self.__cancel, "cancelled", False)
        for index, _test in enumerate(self.__tests):
            logger.info(f"[TestSequenceModel] Starting {_test.Name} (index={index})")
            self.startedTest.emit(index, _test.Name)
            if cancel:
                logger.warning(
                    f"[TestSequenceModel] Testing cancelled before starting {_test.Name}"
                )
                _test.Status = "Skipped"
                continue
            if test and _test.Name != test:
                _test.Status = "Skipped"
                continue
            result = _test.onStartTest(data_directory)
            logger.info(f"[TestSequenceModel] {_test.Name} finished: result={result}")
            statuses.append(result)
            self.finishedTest.emit(index, _test.Name, result)
        if getattr(self.__cancel, "cancelled", False):
            logger.warning(f"[TestSequenceModel] Test sequence was cancelled.")
            return None
        elif not statuses:
            logger.warning(f"[TestSequenceModel] No tests were executed.")
            return None
        else:
            logger.info(
                f"[TestSequenceModel] All tests finished. Success={all(statuses)}"
            )
            return all(statuses)

    def resetTestData(self):
        """
        Reset parameters for all tests in the sequence.
        """
        logger.debug(f"[TestSequenceModel] resetTestData called")
        for test in self.__tests:
            logger.debug(f"[TestSequenceModel] Resetting parameters for test: {test}")
            test.resetParameters()
        logger.debug(f"[TestSequenceModel] All test parameters reset")

    def setupUi(self, parent=None):
        """
        Set up the UI for the test sequence in the given parent widget.

        Args:
            parent (QtWidgets.QStackedWidget, optional): The parent widget to set up.
        """
        logger.debug(f"[TestSequenceModel] setupUi called with parent={parent}")
        if isinstance(parent, QtWidgets.QStackedWidget):
            # Remove widgets efficiently
            for i in reversed(range(parent.count())):
                widget = parent.widget(i)
                parent.removeWidget(widget)
                widget.deleteLater()
            for test in self.__tests:
                logger.debug(f"[TestSequenceModel] Adding widget for test: {test}")
                widget = QtWidgets.QWidget(parent)
                parent.addWidget(widget)
                test.setupUi(widget)
        logger.debug(f"[TestSequenceModel] UI setup complete")
