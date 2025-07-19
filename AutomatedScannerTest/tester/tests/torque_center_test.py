# -*- coding: utf-8 -*-
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
        TorqueCenter (float): The calculated torque center value.
        chartTorqueCenter: Reference to the QtCharts.QChart object for plotting.
        lineSeriesTorqueCenter: Reference to the QtCharts.QLineSeries object for plotting.
        axisX: Reference to the X axis of the chart.
        axisY: Reference to the Y axis of the chart.
        chartViewTorqueCenter: Reference to the QtCharts.QChartView object.
        widgetTorqueCenter: Reference to the widget displaying the torque center value.
        layoutTorqueCenter: Reference to the layout for the torque center widget.
        labelTorqueCenterName: Reference to the label for the torque center.
        textBoxTorqueCenter: Reference to the text box displaying the torque center value.
        figurePath: Path to the saved plot image.
        dataFilePath: Path to the saved CSV data file.
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
    """
    Signal emitted when the torque data changes.

    Args:
        list: The new torque data.
    """

    def get_torque_data(self) -> list:
        """
        Retrieves the torque data from the underlying data source.

        Returns:
            list: A list containing the torque data as (offset, RMS current) tuples.
        """
        return self._get_parameter("TorqueData", [])

    def set_torque_data(self, value: list):
        """
        Sets the torque data value.

        Args:
            value (list): The value to set for the torque data.
        """
        self._set_parameter("TorqueData", value)
        self.torqueDataChanged.emit(value)

    TorqueData = QtCore.Property(list, get_torque_data, set_torque_data)
    """
    Qt Property for accessing and setting the torque data.
    """

    torqueCenterChanged = QtCore.Signal(float)
    """
    Signal emitted when the torque center value changes.

    Args:
        float: The new torque center value.
    """

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
    """
    Qt Property for accessing and setting the torque center value.
    """

    @tester._member_logger
    def analyze_results(self, serial_number: str):
        """
        Analyzes the test results for a given serial number.

        This method determines the torque center by finding the offset with the minimum RMS current.
        If the absolute value of the torque center is less than 1, the test passes; otherwise, it fails.

        Args:
            serial_number (str): The serial number of the device under test.

        Returns:
            bool: True if the test passes, False otherwise.
        """
        super().analyze_results(serial_number)
        if self.TorqueData:
            _minimum = min(self.TorqueData, key=lambda x: x[1])
            self.TorqueCenter = _minimum[0]
        else:
            self.TorqueCenter = 0.0
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
            layout = widget.layout()
            if layout is None:
                layout = QtWidgets.QVBoxLayout(widget)
                widget.setLayout(layout)
            layout.addWidget(chart_view)

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
        text_box_torque_center = QtWidgets.QLineEdit("{:.2f}".format(self.TorqueCenter), widget_torque_center)
        text_box_torque_center.setObjectName("textBoxTorqueCenter")
        text_box_torque_center.setEnabled(False)
        self.torqueCenterChanged.connect(lambda value: text_box_torque_center.setText("{:.2f}".format(value)))
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

        This method writes a header line for the "Torque Center Plot" and adds a plot of the torque data to the report.
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
        Saves torque data to a CSV file if the data directory attribute exists.

        The method writes a header row followed by time-indexed position and torque current data
        from the `TorqueData` attribute to the file specified by `dataFilePath`. Each row
        contains the time (as an index in nanoseconds), position in degrees, and torque current in mA.
        After saving, it calls the superclass's `on_save` method and returns its result.

        Returns:
            The result of the superclass's `on_save` method.
        """
        try:
            with self.dataFilePath.open("w") as _handle:
                _handle.write("Time (ns),Position (deg),Torque Current (mA)\n")
                lines = [f"{_time},{_data[0]},{_data[1]}\n" for _time, _data in enumerate(self.TorqueData)]
                _handle.writelines(lines)
        except Exception:
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
            - Enables the function generator on channel 1 of the MSO5000.
            - Runs the MSO5000.
            - Iterates through 51 offset values, setting the source offset on channel 1 for each iteration.
            - For each offset, measures the RMS value and stores the offset-RMS pair.
            - Stores the collected data in self.TorqueData.
            - Disables the function generator on channel 1 after the test.
        """
        super().run(serial_number, devices)
        mso = devices.MSO5000
        mso.function_generator_state(1, True)
        mso.run()
        _data = []
        offsets = [i / 10 for i in range(-25, 26)]
        for _offset in offsets:
            mso.set_source_offset(1, _offset)
            time.sleep(0.2)
            try:
                _rms = mso.get_measure_item(
                    MSO5000.Measurement.VoltageRms, MSO5000.Source.Channel2
                )
                _data.append((_offset * 4.5, _rms * 100))
            except Exception:
                pass
        self.TorqueData = _data
        mso.function_generator_state(1, False)

    @tester._member_logger
    def setup(self, serial_number, devices):
        """
        Sets up the test environment for the torque center test using the provided serial number and devices.

        This method configures the MSO5000 oscilloscope and its function generator with specific settings.

        Args:
            serial_number (str): The serial number of the device under test.
            devices: An object containing device interfaces, including MSO5000.

        Returns:
            None
        """
        super().setup(serial_number, devices)
        mso = devices.MSO5000
        mso.timebase_settings(
            offset=2, scale=0.02, href_mode=MSO5000.HrefMode.Trigger
        )
        mso.function_generator_sinusoid(
            1,
            frequency=5,
            amplitude=0.5,
            output_impedance=MSO5000.SourceOutputImpedance.Fifty,
        )
        mso.channel_settings(
            1,
            display=False,
        )
        mso.channel_settings(
            2,
            scale=2,
            display=True,
            bandwidth_limit=MSO5000.BandwidthLimit._20M,
        )
        mso.set_measure_item(
            MSO5000.Measurement.VoltageRms, MSO5000.Source.Channel2
        )

    @tester._member_logger
    def set_data_directory(self, root_directory):
        """
        Sets the root directory for data storage and updates internal paths for figure and data files.

        Args:
            root_directory (str or Path): The root directory where data should be stored.

        Side Effects:
            Updates self.dataDirectory, self.figurePath, and self.dataFilePath with new paths based on the provided root directory.
        """
        super().set_data_directory(root_directory)
        self.figurePath = self.dataDirectory / "torque_plot.png"
        self.dataFilePath = self.dataDirectory / "torque_center_data.csv"

    @tester._member_logger
    def teardown(self, devices):
        """
        Tears down the test environment and performs any necessary cleanup.

        Args:
            devices: An object containing device interfaces.

        Returns:
            None
        """
        super().teardown(devices)
