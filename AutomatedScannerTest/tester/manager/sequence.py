# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets

from tester.manager.devices import DeviceManager
from tester.tests import CancelToken, _test_list


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

        Raises:
            RuntimeError: If there is no running QCoreApplication instance.
        """
        super().__init__()
        QtCore.qInfo("[TestSequenceModel] Initializing...")
        # Use AppLocalDataLocation and ensure app subdir exists
        app_instance = QtCore.QCoreApplication.instance()
        if app_instance is None or app_instance.__class__.__name__ != "TesterApp":
            QtCore.qCritical("[TestSequenceModel] TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        self.__settings = app_instance.get_settings()
        self.__settings.settingsModified.connect(self.onSettingsModified)
        self.onSettingsModified()
        QtCore.qInfo("[TestSequenceModel] Logger and settings initialized.")

        self.__parameters = {}
        self.__header = ("Test", "Status")
        self.__cancel = cancel
        self.__devices = devices
        self.__tests = []
        for test in _test_list():
            self.__tests.append(test(self.__cancel, self.__devices))
        QtCore.qInfo("[TestSequenceModel] Initialization complete.")

    # Qt Properties for the sequence parameters (using Qt types where possible)
    @QtCore.Property(str)
    def ComputerName(self):
        """
        Get or set the computer name for the test sequence.

        Returns:
            str: The computer name.
        """
        return self.__parameters.get("ComputerName", "")

    @ComputerName.setter
    def ComputerName(self, value):
        """
        Set the computer name for the test sequence.

        Args:
            value (str): The computer name.
        """
        self.__parameters["ComputerName"] = value

    @QtCore.Property(float)
    def Duration(self):
        """
        Get or set the duration of the test sequence in seconds.

        Returns:
            float: The duration in seconds.
        """
        return self.__parameters.get("Duration", 0.0)

    @Duration.setter
    def Duration(self, value):
        """
        Set the duration of the test sequence.

        Args:
            value (float): The duration in seconds.
        """
        self.__parameters["Duration"] = value

    @QtCore.Property(QtCore.QDateTime)
    def EndTime(self):
        """
        Get or set the end time of the test sequence.

        Returns:
            QtCore.QDateTime: The end time.
        """
        val = self.__parameters.get("EndTime", None)
        if isinstance(val, QtCore.QDateTime):
            return val
        return QtCore.QDateTime()

    @EndTime.setter
    def EndTime(self, value):
        """
        Set the end time of the test sequence.

        Args:
            value (QtCore.QDateTime): The end time.
        """
        self.__parameters["EndTime"] = value if isinstance(value, QtCore.QDateTime) else QtCore.QDateTime()

    @QtCore.Property(str)
    def ModelName(self):
        """
        Get or set the model name for the test sequence.

        Returns:
            str: The model name.
        """
        return self.__parameters.get("ModelName", "")

    @ModelName.setter
    def ModelName(self, value):
        """
        Set the model name for the test sequence.

        Args:
            value (str): The model name.
        """
        self.__parameters["ModelName"] = value
        for _test in self.__tests:
            _test.ModelName = value

    @QtCore.Property(str)
    def SerialNumber(self):
        """
        Get or set the serial number for the test sequence.

        Returns:
            str: The serial number.
        """
        return self.__parameters.get("SerialNumber", "")

    @SerialNumber.setter
    def SerialNumber(self, value):
        """
        Set the serial number for the test sequence.

        Args:
            value (str): The serial number.
        """
        self.__parameters["SerialNumber"] = value
        for _test in self.__tests:
            _test.SerialNumber = value

    @QtCore.Property(QtCore.QDateTime)
    def StartTime(self):
        """
        Get or set the start time of the test sequence.

        Returns:
            QtCore.QDateTime: The start time.
        """
        val = self.__parameters.get("StartTime", None)
        if isinstance(val, QtCore.QDateTime):
            return val
        return QtCore.QDateTime()

    @StartTime.setter
    def StartTime(self, value):
        """
        Set the start time of the test sequence.

        Args:
            value (QtCore.QDateTime): The start time.
        """
        self.__parameters["StartTime"] = value if isinstance(value, QtCore.QDateTime) else QtCore.QDateTime()

    @QtCore.Property(str)
    def Status(self):
        """
        Get or set the current status of the test sequence.

        Returns:
            str: The status.
        """
        return self.__parameters.get("Status", "Idle")

    @Status.setter
    def Status(self, value):
        """
        Set the current status of the test sequence.

        Args:
            value (str): The status.
        """
        self.__parameters["Status"] = value

    @QtCore.Property(str)
    def TesterName(self):
        """
        Get or set the tester name for the test sequence.

        Returns:
            str: The tester name.
        """
        return self.__parameters.get("TesterName", "")

    @TesterName.setter
    def TesterName(self, value):
        """
        Set the tester name for the test sequence.

        Args:
            value (str): The tester name.
        """
        self.__parameters["TesterName"] = value

    # QtCore methods for the model
    def rowCount(self, parent=QtCore.QModelIndex()):
        """
        Get the number of rows (tests) in the model.

        Args:
            parent (QModelIndex): The parent index (unused).

        Returns:
            int: The number of tests.
        """
        return len(self.__tests)

    def columnCount(self, parent=QtCore.QModelIndex()):
        """
        Get the number of columns in the model.

        Args:
            parent (QModelIndex): The parent index (unused).

        Returns:
            int: The number of columns (always 2: Test, Status).
        """
        return len(self.__header)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """
        Get the data for a given index and role.

        Args:
            index (QModelIndex): The model index.
            role (int): The Qt role.

        Returns:
            The data for the cell, or None.
        """
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if row >= len(self.__tests) or col >= len(self.__header):
            return None
        test = self.__tests[row]
        if role == QtCore.Qt.DisplayRole:
            return test.Name if col == 0 else test.Status
        if role == QtCore.Qt.UserRole:
            return test
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
            return self.__header[section] if section < len(self.__header) else None
        return super().headerData(section, orientation, role)

    # Methods for managing the test sequence
    def extend(self, tests: list):
        """
        Extend the list of tests with new test objects.

        Args:
            tests (list): A list of test objects to add.

        Raises:
            TypeError: If tests is not a list.
        """
        if not isinstance(tests, list):
            QtCore.qCritical("[TestSequenceModel] Argument to extend is not a list")
            raise TypeError("tests must be a list")
        self.__tests.extend(tests)
        self.layoutChanged.emit()
        QtCore.qInfo(f"[TestSequenceModel] Test list extended by {len(tests)} items.")

    def cliPrintTestList(self):
        """
        Print the list of available tests and their descriptions to the console.
        """
        QtCore.qInfo("[TestSequenceModel] Listing available tests.")
        print("Available tests:")
        for test in self.__tests:
            test.cliPrintTest()
            print("\n")

    def onGenerateReport(self, report):
        for _test in self.__tests:
            if getattr(_test, "Status", None) != "Skipped":
                _test.onGenerateReport(report)

    def onLoadData(self, tests_data):
        """
        Load test data from a dictionary into the model and its tests.
        """
        if tests_data:
            _name_to_test = {t.Name: t for t in self.__tests}
            for _test_name, _test_data in tests_data.items():
                _test_obj = _name_to_test.get(_test_name)
                if _test_obj:
                    _test_obj.onLoadData(_test_data)

    def onSaveData(self) -> dict:
        _data = self.__parameters.copy()
        _data["Tests"] = {t.Name: t.onSaveData() for t in self.__tests}
        return _data

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Read settings from the QSettings object and update parameters accordingly.

        This method is called when the settings are modified.
        """
        QtCore.qInfo("[TestSequenceModel] Reading settings")

    def onStartTest(self, data_directory, test=None):
        statuses = []
        for index, _test in enumerate(self.__tests):
            self.startedTest.emit(index, _test.Name)
            if getattr(self.__cancel, "cancelled", False):
                _test.Status = "Skipped"
                continue
            if test and _test.Name != test:
                _test.Status = "Skipped"
                continue
            result = _test.onStartTest(data_directory)
            statuses.append(result)
            self.finishedTest.emit(index, _test.Name, result)
        if self.__cancel.cancelled:
            QtCore.qWarning("[TestSequenceModel] Test sequence was cancelled.")
            return None
        elif statuses.count() == 0:
            QtCore.qWarning("[TestSequenceModel] No tests were executed.")
            return None
        else:
            return all(statuses) if statuses else False

    def resetTestData(self):
        """
        Reset the test data by clearing the parameters and cancel token.
        """
        QtCore.qInfo("[TestSequenceModel] Resetting test data")
        for test in self.__tests:
            test.resetParameters()
        QtCore.qInfo("[TestSequenceModel] All test parameters reset")

    def setupUi(self, parent=None):
        """
        Set up the user interface for the test sequence model.

        Args:
            parent (QWidget): The parent widget for the UI.
        """
        QtCore.qInfo("[TestSequenceModel] Setting up UI")
        if isinstance(parent, QtWidgets.QStackedWidget):
            parent.clear()
            for test in self.__tests:
                widget = QtWidgets.QWidget()
                parent.addWidget(widget)
                test.setupUi(widget)
        QtCore.qInfo("[TestSequenceModel] UI setup complete")
