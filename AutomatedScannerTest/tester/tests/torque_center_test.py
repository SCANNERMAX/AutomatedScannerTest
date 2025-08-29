# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets, QtCharts
import time

import tester
from tester.devices.mso5000 import MSO5000
import tester.tests


class TorqueCenterTest(tester.tests.Test):
    """
    Performs a torque center analysis on a scanner device by applying a sinusoidal signal with varying offsets
    and measuring the resulting RMS current. Determines the torque center as the offset with minimum RMS current.
    """

    torqueDataChanged = QtCore.Signal(list)
    """Signal emitted when the torque data changes."""

    torqueCenterChanged = QtCore.Signal(float)
    """Signal emitted when the torque center value changes."""

    def __init__(self, settings: QtCore.QSettings, cancel: tester.tests.CancelToken):
        """
        Initialize the TorqueCenterTest.

        Args:
            settings (QtCore.QSettings): The application settings object.
            cancel (tester.tests.CancelToken): Token to signal cancellation of the test.
        """
        super().__init__("Torque Center Test", settings, cancel)

    def get_torque_data(self) -> list:
        """
        Get the torque data.

        Returns:
            list: The torque data as a list of (offset, RMS current) tuples.
        """
        return self._get_parameter("TorqueData", [])

    def set_torque_data(self, value: list):
        """
        Set the torque data and emit the torqueDataChanged signal.

        Args:
            value (list): The new torque data.
        """
        self._set_parameter("TorqueData", value)
        self.torqueDataChanged.emit(value)

    TorqueData = QtCore.Property(list, get_torque_data, set_torque_data)
    """Qt Property for accessing and setting the torque data."""

    def get_torque_center(self) -> float:
        """
        Get the torque center value.

        Returns:
            float: The torque center value.
        """
        return self._get_parameter("TorqueCenter", 0.0)

    def set_torque_center(self, value: float):
        """
        Set the torque center value and emit the torqueCenterChanged signal.

        Args:
            value (float): The new torque center value.
        """
        self._set_parameter("TorqueCenter", value)
        self.torqueCenterChanged.emit(value)

    TorqueCenter = QtCore.Property(float, get_torque_center, set_torque_center)
    """Qt Property for accessing and setting the torque center value."""

    @tester._member_logger
    def analyze_results(self, serial_number: str):
        """
        Analyze the test results for a given serial number.

        Determines the torque center by finding a local minimum of RMS current near zero offset.
        Sets the test status to "Pass" if the absolute value of the torque center is less than 1, otherwise "Fail".

        Args:
            serial_number (str): The serial number of the device under test.

        Returns:
            bool: True if the test passes, False otherwise.
        """
        super().analyze_results(serial_number)
        data = self.TorqueData
        torque_center = 0.0

        if data:
            # Find indices where offset is near zero (within +/-2 deg)
            candidates = [(i, offset, rms) for i, (offset, rms) in enumerate(data) if abs(offset) <= 2]
            local_min_index = None

            # Check for local minimum in candidates
            for idx, offset, rms in candidates:
                prev_rms = data[idx - 1][1] if idx > 0 else float('inf')
                next_rms = data[idx + 1][1] if idx < len(data) - 1 else float('inf')
                if rms < prev_rms and rms < next_rms:
                    local_min_index = idx
                    break

            if local_min_index is not None:
                torque_center = data[local_min_index][0]
            else:
                # Fallback: use global minimum
                torque_center = min(data, key=lambda x: x[1])[0]
        self.TorqueCenter = torque_center
        self.Status = "Pass" if abs(self.TorqueCenter) < 1 else "Fail"
        return self.Status == "Pass"

    @tester._member_logger
    def load_ui(self, widget: QtWidgets.QWidget):
        """
        Initialize and configure the UI components for displaying the torque center plot and value.

        Args:
            widget (QtWidgets.QWidget): The parent widget to which the UI components will be added.
        """
        super().load_ui(widget)

        # Torque Center Plot
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

        layout_test_data = getattr(self, "layoutTestData", None)
        if layout_test_data is not None:
            layout_test_data.addWidget(chart_view)
        else:
            layout = widget.layout() or QtWidgets.QVBoxLayout(widget)
            if widget.layout() is None:
                widget.setLayout(layout)
            layout.addWidget(chart_view)

        self.torqueDataChanged.connect(line_series.replace)

        # Store references
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
        text_box_torque_center = QtWidgets.QLineEdit(f"{self.TorqueCenter:.2f}", widget_torque_center)
        text_box_torque_center.setObjectName("textBoxTorqueCenter")
        text_box_torque_center.setEnabled(False)
        self.torqueCenterChanged.connect(lambda value: text_box_torque_center.setText(f"{value:.2f}"))
        layout_torque_center.addWidget(text_box_torque_center)

        if layout_test_data is not None:
            layout_test_data.addWidget(widget_torque_center)
        else:
            widget.layout().addWidget(widget_torque_center)

        self.widgetTorqueCenter = widget_torque_center
        self.layoutTorqueCenter = layout_torque_center
        self.labelTorqueCenterName = label_torque_center_name
        self.textBoxTorqueCenter = text_box_torque_center

    @tester._member_logger
    def on_generate_report(self, report):
        """
        Generate a report section specific to the torque center test.

        Adds a plot of the torque data and writes the torque center value to the report.

        Args:
            report: An object responsible for report generation, expected to have writeLine and plotXYData methods.
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
        report.writeLine(f"Torque Center: {self.TorqueCenter:.2f} deg")

    @tester._member_logger
    def on_save(self):
        """
        Save torque data to a CSV file if the data directory attribute exists.

        Writes a header row followed by time-indexed position and torque current data
        from the TorqueData attribute to the file specified by dataFilePath.

        Returns:
            The result of the superclass's on_save method.
        """
        try:
            with self.dataFilePath.open("w") as _handle:
                _handle.write("Time (ns),Position (deg),Torque Current (mA)\n")
                _handle.writelines(
                    f"{_time},{_data[0]},{_data[1]}\n" for _time, _data in enumerate(self.TorqueData)
                )
        except Exception:
            pass
        return super().on_save()

    @tester._member_logger
    def run(self, serial_number, devices):
        """
        Run the torque center test by iteratively adjusting the source offset and collecting RMS measurements.

        Args:
            serial_number (str): The serial number of the device under test.
            devices (object): An object providing access to connected devices, including the MSO5000.
        """
        super().run(serial_number, devices)
        mso = devices.MSO5000
        mso.function_generator_state(1, True)
        mso.run()
        _data = []
        offsets = [i / 10 for i in range(-25, 26)]
        for _offset in offsets:
            mso.set_source_offset(1, _offset)
            time.sleep(0.04)
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
        Set up the test environment for the torque center test using the provided serial number and devices.

        Configures the MSO5000 oscilloscope and its function generator with specific settings.

        Args:
            serial_number (str): The serial number of the device under test.
            devices: An object containing device interfaces, including MSO5000.
        """
        super().setup(serial_number, devices)
        mso = devices.MSO5000
        mso.timebase_settings(
            offset=2, scale=0.02, href_mode=MSO5000.HrefMode.Trigger
        )
        mso.function_generator_sinusoid(
            1,
            frequency=10,
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
        Set the root directory for data storage and update internal paths for figure and data files.

        Args:
            root_directory (str or Path): The root directory where data should be stored.
        """
        super().set_data_directory(root_directory)
        self.figurePath = self.dataDirectory / "torque_plot.png"
        self.dataFilePath = self.dataDirectory / "torque_center_data.csv"

    @tester._member_logger
    def teardown(self, devices):
        """
        Tear down the test environment and perform any necessary cleanup.

        Args:
            devices: An object containing device interfaces.
        """
        super().teardown(devices)
