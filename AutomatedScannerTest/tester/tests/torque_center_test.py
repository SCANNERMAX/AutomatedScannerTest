# -*- utf-8 -*-
from PySide6 import QtCore, QtWidgets, QtCharts
import time

import tester
from tester.devices.mso5000 import MSO5000
import tester.tests


class TorqueCenterTest(tester.tests.Test):
    """
    TorqueCenterTest performs a torque center analysis on a scanner device by applying a sinusoidal signal with varying offsets and measuring the resulting RMS current. The test is designed to determine the torque center, which is expected to correspond to a zero crossing in the measured current.
    Attributes:
        TorqueData (list): Stores the measured torque data as a list of (offset, RMS current) tuples.
    Methods:
        __init__(settings, cancel):
            Initializes the TorqueCenterTest with the provided settings and cancel token.
        analyze_results(serial_number):
            Analyzes the test results for the given serial number.
        load_ui(widget):
            Loads and configures the user interface for displaying the torque data plot.
        on_generate_report(report):
            Adds the torque center plot and related data to the test report.
        on_save():
            Saves the torque data to a CSV file in the data directory.
        run_test(serial_number, devices):
            Executes the torque center test by varying the signal offset, collecting RMS current data, and storing the results.
        setup_test(serial_number, devices):
            Configures the measurement devices and function generators for the test.
        set_data_directory(root_directory):
            Sets the directory for saving test data and figures.
    """

    def __init__(self, settings: QtCore.QSettings, cancel: tester.tests.CancelToken):
        """
        Initialize the Torque Center Test model.

        Args:
            settings (QtCore.QSettings): The application settings object.
            cancel (tester.tests.CancelToken): Token to signal cancellation of the test.

        """
        super().__init__("Torque Center Test", settings, cancel)

    torqueDataChanged = QtCore.Signal(list)

    def get_torque_data(self) -> list:
        """
        Retrieves the torque data from the underlying data source.

        Returns:
            list: A list containing the torque data.
        """
        return self._get_parameter("TorqueData", list())

    def set_torque_data(self, value: list):
        """
        Sets the torque data value.

        Args:
            value: The value to set for the torque data.
        """
        self._set_parameter("TorqueData", value)
        self.torqueDataChanged.emit(value)

    TorqueData = QtCore.Property(list, get_torque_data, set_torque_data)

    torqueCenterChanged = QtCore.Signal(float)

    def get_torque_center(self) -> float:
        """
        Retrieves the torque center value from the underlying data source.
        Returns:
            float: The torque center value.
        """
        return self._get_parameter("TorqueCenter", 0.0)

    def set_torque_center(self, value: float):
        """
        Sets the torque center value.
        Args:
            value (float): The value to set for the torque center.
        """
        self._set_parameter("TorqueCenter", value)
        self.torqueCenterChanged.emit(value)

    TorqueCenter = QtCore.Property(float, get_torque_center, set_torque_center)

    @tester._member_logger
    def analyze_results(self, serial_number: str):
        """
        Analyzes the test results for a given serial number.

        Overrides the base class implementation to perform additional analysis
        specific to this test. Calls the superclass's analyze_results method.

        Args:
            serial_number (str): The serial number of the device under test.
        """
        super().analyze_results(serial_number)
        _minimum = (None, float("inf"))
        for _data in self.TorqueData:
            if _data[1] < _minimum[1]:
                _minimum = _data
        self.TorqueCenter = _minimum[0]
        if abs(self.TorqueCenter) < 1:
            self.Status = "Pass"
            return True
        else:
            self.Status = "Fail"
            return False

    @tester._member_logger
    def load_ui(self, widget: QtWidgets.QWidget):
        """
        Initializes and configures the UI components for displaying the torque center plot and value.

        Args:
            widget (QtWidgets.QWidget): The parent widget to which the UI components will be added.

        Process:
            - Creates a QtCharts.QChart for the torque center plot.
            - Adds a QtCharts.QLineSeries to display the torque data.
            - Configures X and Y axes for position and RMS current.
            - Embeds the chart in a QtCharts.QChartView and adds it to the layout.
            - Connects the torqueDataChanged signal to update the plot.
            - Displays the torque center value in a disabled QLineEdit.
            - Connects the torqueCenterChanged signal to update the displayed value.
            - Stores references to UI components for later use.

        Returns:
            None
        """
        super().load_ui(widget)

        # Torque Center Plot #####################################################
        chart = QtCharts.QChart()
        chart.setObjectName("chartTorqueCenter")
        line_series = QtCharts.QLineSeries()
        line_series.setObjectName("lineSeriesTorqueCenter")
        line_series.replace(self.TorqueData)
        chart.addSeries(line_series)

        # X Axis
        axis_x = QtCharts.QValueAxis()
        axis_x.setTitleText("Position (deg)")
        axis_x.setLabelFormat("%.2f")
        axis_x.setRange(-10, 10)
        chart.addAxis(axis_x, QtCore.Qt.AlignmentFlag.AlignBottom)
        line_series.attachAxis(axis_x)

        # Y Axis
        axis_y = QtCharts.QValueAxis()
        axis_y.setTitleText("RMS Current (mA)")
        axis_y.setLabelFormat("%.2f")
        axis_y.setRange(-250, 250)
        chart.addAxis(axis_y, QtCore.Qt.AlignmentFlag.AlignLeft)
        line_series.attachAxis(axis_y)

        # Chart View
        chart_view = QtCharts.QChartView(chart, widget)
        chart_view.setObjectName("chartViewTorqueCenter")
        chart_view.setWindowTitle("Torque Center Plot")
        chart_view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # Use getattr for layoutTestData to avoid repeated hasattr checks
        layout_test_data = getattr(self, "layoutTestData", None)
        if layout_test_data is not None:
            layout_test_data.addWidget(chart_view)
        else:
            layout = widget.layout() or QtWidgets.QVBoxLayout(widget)
            layout.addWidget(chart_view)
            widget.setLayout(layout)

        self.torqueDataChanged.connect(line_series.replace)

        # Store references for later use if needed
        self.chartTorqueCenter = chart
        self.lineSeriesTorqueCenter = line_series
        self.axisX = axis_x
        self.axisY = axis_y
        self.chartViewTorqueCenter = chart_view

        # Display the torque center
        widget_torque_center = QtWidgets.QWidget(widget)
        widget_torque_center.setObjectName("widgetTorqueCenter")
        layout_torque_center = QtWidgets.QHBoxLayout(widget_torque_center)
        label_torque_center_name = QtWidgets.QLabel("Torque Center: ", widget_torque_center)
        label_torque_center_name.setObjectName("labelTorqueCenterName")
        layout_torque_center.addWidget(label_torque_center_name)
        text_box_torque_center = QtWidgets.QLineEdit(str(self.TorqueCenter), widget_torque_center)
        text_box_torque_center.setObjectName("textBoxTorqueCenter")
        text_box_torque_center.setEnabled(False)
        self.torqueCenterChanged.connect(text_box_torque_center.setText)
        layout_torque_center.addWidget(text_box_torque_center)

        if layout_test_data is not None:
            layout_test_data.addWidget(widget_torque_center)
        else:
            widget.layout().addWidget(widget_torque_center)

        # Store references
        self.widgetTorqueCenter = widget_torque_center
        self.layoutTorqueCenter = layout_torque_center
        self.labelTorqueCenterName = label_torque_center_name
        self.textBoxTorqueCenter = text_box_torque_center

    @tester._member_logger
    def on_generate_report(self, report):
        """
        Handles the generation of a report section specific to the torque center test.

        This method writes a header line for the "Torque Center Plot" and adds a plot of the friction data to the report.
        It calls the parent class's on_generate_report method to ensure any base functionality is preserved.

        Args:
            report: An object responsible for report generation, expected to have writeLine and plotXYData methods.

        Returns:
            None
        """
        super().on_generate_report(report)
        report.plotXYData(
            self.TorqueData,
            "Torque Center Plot",
            "Position (deg)",
            "Current (mA)",
            str(self.figurePath.resolve()),
            ymin=0,
            ymax=500,
            yTickCount=8,
        )
        report.writeLine("Torque Center: {:.2f} deg".format(self.TorqueCenter))

    @tester._member_logger
    def on_save(self):
        """
        Saves friction data to a CSV file if the data directory attribute exists.

        The method writes a header row followed by time-indexed position and torque current data
        from the `FrictionData` attribute to the file specified by `__data_file_path`. Each row
        contains the time (as an index in nanoseconds), position in degrees, and torque current in mA.
        After saving, it calls the superclass's `on_save` method and returns its result.

        Returns:
            The result of the superclass's `on_save` method.
        """
        try:
            with self.dataFilePath.open("w") as _handle:
                _handle.write("Time (ns),Position (deg),Torque Current (mA)\n")
                for _time, _data in enumerate(self.TorqueData):
                    _handle.write(f"{_time},{_data[0]},{_data[1]}\n")
        except:
            pass
        return super().on_save()

    @tester._member_logger
    def run(self, serial_number, devices):
        """
        Runs the torque center test by iteratively adjusting the source offset and collecting RMS measurements.

        Args:
            serial_number (str): The serial number of the device under test.
            devices (object): An object providing access to connected devices, including the MSO5000.

        Process:
            - Enables the function generator on channels 1 and 2 of the MSO5000.
            - Runs the MSO5000.
            - Iterates through 101 offset values, setting the source offset on channel 1 for each iteration.
            - For each offset, measures the RMS value and stores the offset-RMS pair.
            - Stores the collected data in self.TorqueData.
            - Disables the function generator on channels 1 and 2 after the test.
        """
        super().run(serial_number, devices)
        devices.MSO5000.function_generator_state(1, True)
        devices.MSO5000.run()
        _data = []
        for _iteration in range(-25, 26):
            _offset = _iteration / 10
            devices.MSO5000.set_source_offset(1, _offset)
            time.sleep(0.2)
            try:
                _rms = devices.MSO5000.get_measure_item(
                    MSO5000.Measurement.VoltageRms, MSO5000.Source.Channel2
                )
                _data.append((_offset * 4.5, _rms * 100))
            except:
                pass
        self.TorqueData = _data
        devices.MSO5000.function_generator_state(1, False)

    @tester._member_logger
    def setup(self, serial_number, devices):
        """
        Sets up the test environment for the torque center test using the provided serial number and devices.

        This method configures the MSO5000 oscilloscope and its function generator with specific settings:
        - Sets acquisition settings with averaging and memory depth.
        - Retrieves and stores the sample rate.
        - Configures channels 1, 2, and 3 with specified scale, display, and bandwidth limit options.
        - Sets the timebase with offset, scale, and trigger reference mode.
        - Configures trigger timeout and edge trigger.
        - Sets up function generator outputs:
            - Channel 1: sinusoidal waveform with specified frequency, amplitude, output impedance, and offset.
            - Channel 2: square waveform with specified frequency and amplitude.

        Args:
            serial_number (str): The serial number of the device under test.
            devices: An object containing device interfaces, including MSO5000.

        Returns:
            None
        """
        super().setup(serial_number, devices)
        devices.MSO5000.timebase_settings(
            offset=2, scale=0.02, href_mode=MSO5000.HrefMode.Trigger
        )
        devices.MSO5000.function_generator_sinusoid(
            1,
            frequency=5,
            amplitude=0.5,
            output_impedance=MSO5000.SourceOutputImpedance.Fifty,
        )
        devices.MSO5000.channel_settings(
            1,
            display=False,
        )
        devices.MSO5000.channel_settings(
            2,
            scale=2,
            display=True,
            bandwidth_limit=MSO5000.BandwidthLimit._20M,
        )
        devices.MSO5000.set_measure_item(
            MSO5000.Measurement.VoltageRms, MSO5000.Source.Channel2
        )

    @tester._member_logger
    def set_data_directory(self, root_directory):
        """
        Sets the root directory for data storage and updates internal paths for figure and data files.

        Args:
            root_directory (str or Path): The root directory where data should be stored.

        Side Effects:
            Updates self._data_directory, self.__figure_path, and self.__data_file_path with new paths based on the provided root directory.
        """
        super().set_data_directory(root_directory)
        self.figurePath = self.dataDirectory / "torque_plot.png"
        self.dataFilePath = self.dataDirectory / "torque_center_data.csv"

    @tester._member_logger
    def teardown(self, devices):
        super().teardown(devices)
