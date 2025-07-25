# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets, QtCharts
import time

import tester
from tester.devices.mso5000 import MSO5000
from tester.manager.devices import DeviceManager
import tester.tests


class BearingTest(tester.tests.Test):
    """
    Evaluates scanner rotational mechanics by sweeping at constant speed and measuring required current.
    Detects issues such as increased friction or mechanical resistance in bearings.
    """

    frictionDataChanged = QtCore.Signal(list)
    """Signal emitted when the friction data is updated."""

    def __init__(self, settings: QtCore.QSettings, cancel: tester.tests.CancelToken):
        """
        Initialize the BearingTest instance.

        Args:
            settings (QtCore.QSettings): The settings object for the test.
            cancel (tester.tests.CancelToken): The cancel token to allow test interruption.
        """
        super().__init__("Bearing Test", settings, cancel)

    def get_friction_data(self) -> list:
        """
        Get the current friction data.

        Returns:
            list: The list of (position, current) tuples representing friction data.
        """
        return self._get_parameter("FrictionData", [])

    def set_friction_data(self, value: list):
        """
        Set the friction data and emit the frictionDataChanged signal.

        Args:
            value (list): The new friction data as a list of (position, current) tuples.
        """
        self._set_parameter("FrictionData", value)
        self.frictionDataChanged.emit(value)

    FrictionData = QtCore.Property(list, get_friction_data, set_friction_data)
    """Qt Property for accessing and setting the friction data."""

    @tester._member_logger
    def analyze_results(self, serial_number: str):
        """
        Analyze the results of the bearing test for the given serial number.

        Args:
            serial_number (str): The serial number of the device under test.

        Returns:
            Any: The result of the analysis from the base class.
        """
        return super().analyze_results(serial_number)

    @tester._member_logger
    def load_ui(self, widget: QtWidgets.QWidget):
        """
        Load the test's user interface components into the provided widget, including the friction data plot.

        Args:
            widget (QtWidgets.QWidget): The parent widget to load UI components into.
        """
        super().load_ui(widget)

        chart = QtCharts.QChart()
        chart.setObjectName("chartFriction")
        line_series = QtCharts.QLineSeries()
        if self.FrictionData:
            line_series.replace(self.FrictionData)
        chart.addSeries(line_series)

        axis_x = QtCharts.QValueAxis()
        axis_x.setTitleText("Position (deg)")
        axis_x.setLabelFormat("%.2f")
        axis_x.setRange(-10, 10)
        chart.addAxis(axis_x, QtCore.Qt.AlignmentFlag.AlignBottom)
        line_series.attachAxis(axis_x)

        axis_y = QtCharts.QValueAxis()
        axis_y.setTitleText("Current (mA)")
        axis_y.setLabelFormat("%.2f")
        axis_y.setRange(-250, 250)
        chart.addAxis(axis_y, QtCore.Qt.AlignmentFlag.AlignLeft)
        line_series.attachAxis(axis_y)

        chart_view = QtCharts.QChartView(chart, self.widgetTestData)
        chart_view.setObjectName("chartViewFriction")
        chart_view.setWindowTitle("Friction Plot")
        chart_view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layoutTestData.addWidget(chart_view)

        self.frictionDataChanged.connect(line_series.replace)

        # Store references
        self.chartFriction = chart
        self.lineSeriesFriction = line_series
        self.axisX = axis_x
        self.axisY = axis_y
        self.chartViewFriction = chart_view

    @tester._member_logger
    def on_generate_report(self, report):
        """
        Generate a report section for the bearing test, including a friction plot.

        Args:
            report: The report object to which the plot will be added.
        """
        super().on_generate_report(report)
        report.plotXYData(
            self.FrictionData,
            "Friction Plot",
            "Position (deg)",
            "Current (mA)",
            str(self.figurePath.resolve()),
            xmin=-30,
            xmax=30,
            xTickCount=7,
            ymin=-400,
            ymax=400,
            yTickCount=9,
        )

    @tester._member_logger
    def on_save(self):
        """
        Save the friction data to a CSV file.

        Returns:
            Any: The result of the save operation from the base class.
        """
        try:
            with self.dataFilePath.open("w") as _handle:
                _handle.write("Time (ns),Position (deg),Torque Current (mA)\n")
                _handle.writelines(
                    f"{_time},{_data[0]},{_data[1]}\n"
                    for _time, _data in enumerate(self.FrictionData)
                )
        except Exception:
            pass
        return super().on_save()

    @tester._member_logger
    def run(self, serial_number: str, devices: DeviceManager):
        """
        Execute the bearing test, collecting position and current data from the connected devices.

        Args:
            serial_number (str): The serial number of the device under test.
            devices (DeviceManager): The device manager containing connected devices.
        """
        super().run(serial_number, devices)
        mso = devices.MSO5000
        mso.function_generator_state(1, True)
        mso.function_generator_state(2, True)
        mso.phase_align(2)
        mso.clear()
        mso.single()
        time.sleep(10)
        get_waveform = mso.get_waveform
        _positions_raw = get_waveform(
            source=MSO5000.Source.Channel2,
            mode=MSO5000.WaveformMode.Raw,
            format_=MSO5000.WaveformFormat.Ascii,
            stop=10000,
        )
        _currents_raw = get_waveform(
            source=MSO5000.Source.Channel3,
            mode=MSO5000.WaveformMode.Raw,
            format_=MSO5000.WaveformFormat.Ascii,
            stop=10000,
        )
        self.FrictionData = list(
            zip(
                (4.5 * x for x in _positions_raw),
                (100 * x for x in _currents_raw),
            )
        )
        mso.function_generator_state(1, False)
        mso.function_generator_state(2, False)

    @tester._member_logger
    def set_data_directory(self, root_directory):
        """
        Set the directory for saving test data and figures.

        Args:
            root_directory: The root directory where data and figures will be saved.
        """
        super().set_data_directory(root_directory)
        self.figurePath = self.dataDirectory / "friction_plot.png"
        self.dataFilePath = self.dataDirectory / "friction_plot_data.csv"

    @tester._member_logger
    def setup(self, serial_number: str, devices: DeviceManager):
        """
        Configure the devices and prepare the test environment for the bearing test.

        Args:
            serial_number (str): The serial number of the device under test.
            devices (DeviceManager): The device manager containing connected devices.
        """
        super().setup(serial_number, devices)
        mso = devices.MSO5000
        mso.acquire_settings(
            averages=16,
            memory_depth=MSO5000.MemoryDepth._10K,
            type_=MSO5000.AcquireType.Averages,
        )
        self.SampleRate = mso.get_sample_rate()
        mso.channel_settings(1, scale=2, display=True)
        mso.channel_settings(
            2, scale=2, display=True, bandwidth_limit=MSO5000.BandwidthLimit._20M
        )
        mso.channel_settings(
            3,
            scale=2,
            display=True,
            bandwidth_limit=MSO5000.BandwidthLimit._20M,
        )
        mso.timebase_settings(
            offset=2, scale=0.2, href_mode=MSO5000.HrefMode.Trigger
        )
        mso.trigger_edge(nreject=True)
        mso.function_generator_ramp(
            1,
            frequency=0.5,
            phase=270,
            amplitude=5,
            output_impedance=MSO5000.SourceOutputImpedance.Fifty,
        )
        mso.function_generator_square(
            2, frequency=0.5, phase=270, amplitude=5
        )
