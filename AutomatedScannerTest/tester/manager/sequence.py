# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets
from datetime import datetime

from tester.app import __application__
from tester.manager.devices import DeviceManager
from tester.tests import CancelToken, _test_list

try:
    from dateutil import tz
except ImportError:
    tz = None


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
        # Use AppLocalDataLocation and ensure app subdir exists
        base_dir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppLocalDataLocation)
        app_dir = QtCore.QDir(base_dir)
        app_dir.mkpath(__application__)
        self._data_directory = app_dir.filePath(__application__)

        app_instance = QtCore.QCoreApplication.instance()
        if app_instance is not None and app_instance.__class__.__name__ == "TesterApp":
            self.__logger = app_instance.get_logger(self.__class__.__name__)
            self.__settings = app_instance.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
        else:
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        self.__timezone = tz.tzlocal() if tz else None
        self.__cancel = CancelToken()
        self.__parameters = {}
        self.__devices = DeviceManager()
        self.__tests = _test_list()
        self.__headers = ("Test", "Status")

    # Properties for the sequence parameters
    ComputerName = QtCore.Property(
        str,
        lambda self: self.__parameters.get("ComputerName", ""),
        lambda self, value: self.__parameters.__setitem__("ComputerName", value),
        doc="The name of the computer running the test sequence."
    )
    Duration = QtCore.Property(
        float,
        lambda self: self.__parameters.get("Duration", 0.0),
        lambda self, value: self.__parameters.__setitem__("Duration", value),
        doc="The duration of the test sequence in seconds."
    )
    EndTime = QtCore.Property(
        datetime,
        lambda self: self.__parameters.get("EndTime", None),
        lambda self, value: self.__parameters.__setitem__("EndTime", value),
        doc="The end time of the test sequence."
    )
    ModelName = QtCore.Property(
        str,
        lambda self: self.__parameters.get("ModelName", ""),
        lambda self, value: self.__parameters.__setitem__("ModelName", value),
        doc="The model name for the test sequence."
    )
    SerialNumber = QtCore.Property(
        str,
        lambda self: self.__parameters.get("SerialNumber", ""),
        lambda self, value: self.__parameters.__setitem__("SerialNumber", value),
        doc="The serial number for the test sequence."
    )
    StartTime = QtCore.Property(
        datetime,
        lambda self: self.__parameters.get("StartTime", None),
        lambda self, value: self.__parameters.__setitem__("StartTime", value),
        doc="The start time of the test sequence."
    )
    Status = QtCore.Property(
        str,
        lambda self: self.__parameters.get("Status", "Idle"),
        lambda self, value: self.__parameters.__setitem__("Status", value),
        doc="The current status of the test sequence."
    )
    TesterName = QtCore.Property(
        str,
        lambda self: self.__parameters.get("TesterName", ""),
        lambda self, value: self.__parameters.__setitem__("TesterName", value),
        doc="The name of the tester running the sequence."
    )

    @property
    def Cancel(self):
        """
        Get the cancel token for the test sequence.

        Returns:
            CancelToken: The cancel token instance.
        """
        return self.__cancel

    @property
    def DataDirectory(self) -> str:
        """
        Get the base data directory for storing test data.

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
        self.__logger.debug("Setting DataDirectory: %s", value)
        self._data_directory = QtCore.QDir(str(value)).absolutePath()

    @property
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

    @property
    def PdfReportPath(self) -> str:
        """
        Get the path to the PDF report file for the current run.

        Returns:
            str: The PDF report file path.
        """
        return QtCore.QDir(self.RunDataDirectory).filePath("report.pdf")

    @property
    def RunDataDirectory(self) -> str:
        """
        Get or create the directory for the current test run, based on serial number and start time.

        Returns:
            str: The run data directory.
        """
        serial = self.SerialNumber
        start_time = self.StartTime
        dir_path = QtCore.QDir(self.DataDirectory)
        subdir = f"{serial}/{start_time.strftime('%Y%m%d_%H%M%S')}" if serial and start_time else "Unknown/Unknown"
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

    def getTime(self) -> datetime:
        """
        Get the current local time in the configured timezone.

        Returns:
            datetime: The current time.
        """
        return datetime.now(self.__timezone) if self.__timezone else datetime.now()

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Read settings from the QSettings object and update parameters accordingly.

        This method is called when the settings are modified.
        """
        self.__logger.debug("Reading settings")
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
            raise TypeError("tests must be a list")
        self.__tests.extend(tests)
        self.layoutChanged.emit()

    
    def printTestList(self):
        """
        Print the list of available tests and their descriptions to the console.
        """
        self.__logger.info("Listing available tests.")
        print("Available tests:")
        for test in self.__tests:
            print(f"- {test.Name}:")
            if test.__doc__:
                print("\n".join(f"    {line.strip()}" for line in test.__doc__.strip().splitlines()))

    def resetTests(self):
        """
        Reset the test data by clearing the parameters and cancel token.
        """
        self.__logger.debug("Resetting test data")
        for test in self.__tests:
            test.resetParameters()

    
    def setupDevices(self):
        """
        Set up the devices required for the test sequence.
        """
        self.__devices.setup()

    
    def setupUi(self, parent=None):
        """
        Set up the user interface for the test sequence model.

        Args:
            parent (QWidget): The parent widget for the UI.
        """
        self.__logger.debug("Setting up UI")
        if isinstance(parent, QtWidgets.QStackedWidget):
            parent.clear()
            for test in self.__tests:
                widget = QtWidgets.QWidget()
                parent.addWidget(widget)
                test.setupUi(widget)

