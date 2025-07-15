# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets, QtCharts
import time

import tester
from tester.devices.mso5000 import MSO5000
from tester.manager.devices import DeviceManager
import tester.tests


class BearingTest(tester.tests.Test):
    """
    BearingTest is a test class for evaluating the rotational mechanics of a scanner by sweeping it across the field at a constant speed and measuring the current required. The test is designed to detect issues such as increased friction or mechanical resistance in the scanner's bearings.
    Attributes:
        FrictionData (list): Stores the measured friction data as a list of (position, current) tuples.
    Methods:
        __init__(settings, cancel):
            Initializes the BearingTest instance with the provided settings and cancel token.
        analyze_results(serial_number):
            Analyzes the results of the bearing test for the given serial number.
        load_ui(widget):
            Loads the test's user interface components into the provided widget, including the friction data plot.
        on_generate_report(report):
            Generates a report section for the bearing test, including a friction plot.
        on_save():
            Saves the friction data to a CSV file.
        run_test(serial_number, devices):
            Executes the bearing test, collecting position and current data from the connected devices.
        set_data_directory(root_directory):
            Sets the directory for saving test data and figures.
        setup_test(serial_number, devices):
            Configures the devices and prepares the test environment for the bearing test.
    """

    def __init__(self, settings: QtCore.QSettings, cancel: tester.tests.CancelToken):
        """
        Initialize the bearing test model.

        Args:
            settings (QtCore.QSettings): The application settings to use for the test.
            cancel (tester.tests.CancelToken): A token to signal cancellation of the test.
        """
        super().__init__("Bearing Test", settings, cancel)

    frictionDataChanged = QtCore.Signal(list)

    def get_friction_data(self) -> list:
        """
        Retrieves the friction data for the bearing test.

        Returns:
            list: A list containing the friction data values.
        """
        return self._get_parameter("FrictionData", [])

    def set_friction_data(self, value: list):
        """
        Sets the friction data for the tester and updates the corresponding plot.

        Parameters:
            value: The new friction data to be set. The expected type depends on the implementation of _set_data.

        Side Effects:
            Updates the internal friction data and refreshes the plot to reflect the new data.
        """
        self._set_parameter("FrictionData", value)
        self.frictionDataChanged.emit(value)

    FrictionData = QtCore.Property(list, get_friction_data, set_friction_data)

    @tester._member_logger
    def analyze_results(self, serial_number: str):
        """
        Analyzes the test results for a given serial number.

        Overrides the parent class's analyze_results method to perform additional analysis
        specific to this class, if needed.

        Args:
            serial_number (str): The serial number of the item whose results are to be analyzed.

        Returns:
            None
        """
        return super().analyze_results(serial_number)

    @tester._member_logger
    def load_ui(self, widget: QtWidgets.QWidget):
        """
        Initializes and configures the UI components for displaying a friction plot.

        This method sets up a QChart with a QLineSeries to visualize the friction data,
        configures the X and Y axes for position and current, and embeds the chart in the
        provided widget. It also connects the frictionDataChanged signal to update the plot
        when new data is available.

        Args:
            widget (QtWidgets.QWidget): The parent widget to which the UI elements are added.

        Side Effects:
            - Adds a chart view to the test data layout.
            - Stores references to chart components for later use.
            - Connects the friction data change signal to update the plot.
        """
        super().load_ui(widget)

        # Friction Plot #####################################################
        chart = QtCharts.QChart()
        chart.setObjectName("chartFriction")
        line_series = QtCharts.QLineSeries()
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

        # Store references for later use if needed
        self.chartFriction = chart
        self.lineSeriesFriction = line_series
        self.axisX = axis_x
        self.axisY = axis_y
        self.chartViewFriction = chart_view

    @tester._member_logger
    def on_generate_report(self, report):
        """
        Generates and appends a friction plot to the provided report.

        This method overrides the parent class's on_generate_report method.
        It writes a section header for the friction plot and adds an XY plot of the bearing data
        to the report, using the stored friction data and figure path.

        Args:
            report: The report object to which the friction plot and header will be added.
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
        Saves friction test data to a CSV file if the data file path attribute exists.

        The method writes a header followed by rows containing time (in nanoseconds),
        position (in degrees), and torque current (in mA) for each entry in FrictionData.
        Returns the result of the superclass's on_save method.
        """
        try:
            with self.dataFilePath.open("w") as _handle:
                _handle.write("Time (ns),Position (deg),Torque Current (mA)\n")
                for _time, _data in enumerate(self.FrictionData):
                    _handle.write(f"{_time},{_data[0]},{_data[1]}\n")
        except:
            pass
        return super().on_save()

    @tester._member_logger
    def run(self, serial_number: str, devices: DeviceManager):
        """
        Run the test for the bearing using the specified serial number and device manager.

        This method performs the following steps:
        1. Calls the parent class's `run_test` method.
        2. Enables the function generators on channels 1 and 2.
        3. Aligns the phase on channel 2.
        4. Clears and arms the oscilloscope for a single acquisition.
        5. Waits for 10 seconds to allow data acquisition.
        6. Retrieves waveform data from channel 2 (positions) and channel 3 (currents), scaling the values appropriately.
        7. Zips the position and current data into `self.FrictionData`.
        8. Disables the function generators on channels 1 and 2.

        Args:
            serial_number (str): The serial number of the device under test.
            devices (DeviceManager): The device manager instance providing access to test equipment.

        Side Effects:
            Updates `self.FrictionData` with a list of (position, current) tuples.
            Controls the state of the function generators and oscilloscope via the `devices` manager.
        """
        super().run(serial_number, devices)
        devices.MSO5000.function_generator_state(1, True)
        devices.MSO5000.function_generator_state(2, True)
        devices.MSO5000.phase_align(2)
        devices.MSO5000.clear()
        devices.MSO5000.single()
        time.sleep(10)
        _positions = [
            4.5 * x
            for x in devices.MSO5000.get_waveform(
                source=MSO5000.Source.Channel2,
                mode=MSO5000.WaveformMode.Raw,
                format_=MSO5000.WaveformFormat.Ascii,
                stop=10000,
            )
        ]
        _currents = [
            100 * x
            for x in devices.MSO5000.get_waveform(
                source=MSO5000.Source.Channel3,
                mode=MSO5000.WaveformMode.Raw,
                format_=MSO5000.WaveformFormat.Ascii,
                stop=10000,
            )
        ]
        self.FrictionData = list(zip(_positions, _currents))
        devices.MSO5000.function_generator_state(1, False)
        devices.MSO5000.function_generator_state(2, False)

    @tester._member_logger
    def set_data_directory(self, root_directory):
        """
        Sets the data directory for the test and initializes paths for output files.

        Args:
            root_directory (str or Path): The root directory where data should be stored.

        Side Effects:
            - Calls the parent class's set_data_directory method.
            - Sets self.__figure_path to the path for saving the friction plot image.
            - Sets self.__data_file_path to the path for saving the friction plot data as a CSV file.
        """
        super().set_data_directory(root_directory)
        self.figurePath = self.dataDirectory / "friction_plot.png"
        self.dataFilePath = self.dataDirectory / "friction_plot_data.csv"

    @tester._member_logger
    def setup(self, serial_number: str, devices: DeviceManager):
        """
        Configures the test environment for a bearing test using the provided serial number and device manager.

        This method sets up the MSO5000 oscilloscope and function generator with specific acquisition, channel, timebase, and trigger settings. It also configures two function generator outputs.

        Args:
            serial_number (str): The serial number of the device under test.
            devices (DeviceManager): The device manager instance providing access to test instruments.

        Raises:
            Any exceptions raised by the underlying device configuration methods.
        """
        super().setup(serial_number, devices)
        devices.MSO5000.acquire_settings(
            averages=16,
            memory_depth=MSO5000.MemoryDepth._10K,
            type_=MSO5000.AcquireType.Averages,
        )
        self.SampleRate = devices.MSO5000.get_sample_rate()
        devices.MSO5000.channel_settings(1, scale=2, display=True)
        devices.MSO5000.channel_settings(
            2, scale=2, display=True, bandwidth_limit=MSO5000.BandwidthLimit._20M
        )
        devices.MSO5000.channel_settings(
            3,
            scale=2,
            display=True,
            bandwidth_limit=MSO5000.BandwidthLimit._20M,
        )
        devices.MSO5000.timebase_settings(
            offset=2, scale=0.2, href_mode=MSO5000.HrefMode.Trigger
        )
        devices.MSO5000.trigger_edge(nreject=True)
        devices.MSO5000.function_generator_ramp(
            1,
            frequency=0.5,
            phase=270,
            amplitude=5,
            output_impedance=MSO5000.SourceOutputImpedance.Fifty,
        )
        devices.MSO5000.function_generator_square(
            2, frequency=0.5, phase=270, amplitude=5
        )
