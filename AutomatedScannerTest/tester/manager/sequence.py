# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets

from tester.app import __application__
from tester.manager.devices import DeviceManager
from tester.tests import CancelToken, _test_list


class TestSequenceModel(QtCore.QAbstractTableModel):
    """
    Manages the execution, logging, and reporting of a sequence of hardware or software tests.

    This model provides a Qt-compatible interface for managing a list of test objects, their execution,
    result logging, report generation, and parameter management. It integrates with device management
    and supports both GUI and command-line workflows.
    """

    def __init__(self):
        """
        Initialize the TestSequenceModel, set up logging, device manager, test list, and default parameters.

        Raises:
            RuntimeError: If there is no running QCoreApplication instance.
        """
        super().__init__()
        QtCore.qInfo("[TestSequenceModel] Initializing...")
        # Use AppLocalDataLocation and ensure app subdir exists
        base_dir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppLocalDataLocation)
        app_dir = QtCore.QDir(base_dir)
        app_dir.mkpath(__application__)
        self._data_directory = app_dir.filePath(__application__)

        app_instance = QtCore.QCoreApplication.instance()
        if app_instance is not None and app_instance.__class__.__name__ == "TesterApp":
            self.__settings = app_instance.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
            QtCore.qInfo("[TestSequenceModel] Logger and settings initialized.")
        else:
            QtCore.qCritical("[TestSequenceModel] TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")

        self.__timezone = QtCore.QTimeZone.systemTimeZone()
        self.__cancel = CancelToken()
        self.__parameters = {}
        self.__devices = DeviceManager()
        self.__tests = list(_test_list())
        self.__headers = ("Test", "Status")
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

    @property
    def Cancel(self):
        """
        Get the cancel token for the test sequence.

        Returns:
            CancelToken: The cancel token instance.
        """
        return self.__cancel

    @QtCore.Property(str)
    def DataDirectory(self) -> str:
        """
        Get or set the base data directory for storing test data.

        Returns:
            str: The data directory path.
        """
        return self._data_directory

    @DataDirectory.setter
    def DataDirectory(self, value):
        """
        Set the base data directory for storing test data.

        Args:
            value (str): The new data directory path.
        """
        QtCore.qDebug(f"[TestSequenceModel] Setting DataDirectory: {value}")
        self._data_directory = QtCore.QDir(str(value)).absolutePath()

    @QtCore.Property(str)
    def DataFilePath(self) -> str:
        """
        Get the path to the JSON data file for the current run.

        Returns:
            str: The data file path.
        """
        return QtCore.QDir(self.RunDataDirectory).filePath("data.json")

    @property
    def Devices(self):
        """
        Get the device manager instance.

        Returns:
            DeviceManager: The device manager.
        """
        return self.__devices

    @property
    def Parameters(self):
        """
        Get the current parameters of the test sequence.

        Returns:
            dict: The parameters dictionary.
        """
        return self.__parameters

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
        serial = self.SerialNumber
        start_time = self.StartTime
        dir_path = QtCore.QDir(self.DataDirectory)
        if serial and start_time and start_time.isValid():
            subdir = f"{serial}/{start_time.toString('yyyyMMdd_HHmmss')}"
        else:
            subdir = "Unknown/Unknown"
        dir_path.mkpath(subdir)
        return dir_path.filePath(subdir)

    @property
    def Tests(self):
        """
        Get the list of available tests.

        Returns:
            list: The list of test objects.
        """
        return self.__tests

    def getTime(self) -> QtCore.QDateTime:
        """
        Get the current local time in the configured timezone.

        Returns:
            QtCore.QDateTime: The current time.
        """
        now = QtCore.QDateTime.currentDateTime()
        if self.__timezone.isValid():
            now.setTimeZone(self.__timezone)
        return now

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Read settings from the QSettings object and update parameters accordingly.

        This method is called when the settings are modified.
        """
        QtCore.qInfo("[TestSequenceModel] Reading settings")
        _data_directory = str(self.DataDirectory)
        _data_directory = self.__settings.getSetting("Tests", "DataDirectory", _data_directory)
        self.DataDirectory = _data_directory

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
        return len(self.__headers)

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
        if row >= len(self.__tests) or col >= len(self.__headers):
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
            return self.__headers[section] if section < len(self.__headers) else None
        return super().headerData(section, orientation, role)

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

    def printTestList(self):
        """
        Print the list of available tests and their descriptions to the console.
        """
        QtCore.qInfo("[TestSequenceModel] Listing available tests.")
        print("Available tests:")
        for test in self.__tests:
            print(f"- {test.Name}:")
            if test.__doc__:
                print("\n".join(f"    {line.strip()}" for line in test.__doc__.strip().splitlines()))

    def resetTests(self):
        """
        Reset the test data by clearing the parameters and cancel token.
        """
        QtCore.qInfo("[TestSequenceModel] Resetting test data")
        for test in self.__tests:
            test.resetParameters()
        QtCore.qInfo("[TestSequenceModel] All test parameters reset")

    def setupDevices(self):
        """
        Set up the devices required for the test sequence.
        """
        QtCore.qInfo("[TestSequenceModel] Setting up devices")
        self.__devices.setup()
        QtCore.qInfo("[TestSequenceModel] Devices setup complete")

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

