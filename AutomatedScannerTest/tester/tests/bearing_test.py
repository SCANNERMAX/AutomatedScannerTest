# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets, QtCharts

import tester
from tester.devices.mso5000 import MSO5000
from tester.manager.devices import DeviceManager
import tester.tests


class BearingTest(tester.tests.Test):
    """
    Test for evaluating scanner bearing friction by sweeping and measuring current.

    This test sweeps the scanner across its field at a constant speed and measures
    the current required, detecting issues such as increased friction or mechanical
    resistance in the scanner's bearings.

    Attributes:
        FrictionData (list[QPointF]): List of (position, current) points.
        frictionDataChanged (Signal): Emitted when friction data is updated.
    """

    frictionDataChanged = QtCore.Signal(list)

    def __init__(self, cancel: tester.tests.CancelToken, devices: DeviceManager = None):
        """
        Initialize the BearingTest instance.

        Args:
            cancel (tester.tests.CancelToken): The cancel token to allow test interruption.
            devices (DeviceManager, optional): The device manager.
        """
        super().__init__(
            "Bearing Test", cancel, devices if devices is not None else DeviceManager()
        )
        QtCore.qInfo("BearingTest initialized.")

    @QtCore.Property(list, notify=frictionDataChanged)
    def FrictionData(self):
        """
        Get the current friction data.

        Returns:
            list: The list of (position, current) QPointF tuples.
        """
        return self.getParameter("FrictionData", [])

    @FrictionData.setter
    def FrictionData(self, value):
        """
        Set the friction data and emit the frictionDataChanged signal.

        Args:
            value (list): The new friction data as a list of QPointF tuples.
        """
        self.setParameter("FrictionData", value)
        self.frictionDataChanged.emit(value)

    def onSettingsModified(self):
        """
        Handle modifications to the test settings and update internal state.
        """
        super().onSettingsModified()
        s = self.getSetting
        self.readDelay = s("ReadDelay", 5)
        self.charttitle = s("ChartTitle", "Bearing Friction Plot")
        self.xtitle = s("PositionTitle", "Position (deg)")
        self.xmin = s("PositionMinimum", -30.0)
        self.xmax = s("PositionMaximum", 30.0)
        self.ytitle = s("TorqueCurrentTitle", "Torque Current (mA)")
        self.ymin = s("TorqueCurrentMinimum", -400.0)
        self.ymax = s("TorqueCurrentMaximum", 400.0)
        QtCore.qInfo(
            f"Settings modified: readDelay={self.readDelay}, charttitle={self.charttitle}, "
            f"xtitle={self.xtitle}, xmin={self.xmin}, xmax={self.xmax}, "
            f"ytitle={self.ytitle}, ymin={self.ymin}, ymax={self.ymax}"
        )

    def setupUi(self, widget: QtWidgets.QWidget):
        """
        Set up the user interface for the bearing test, including the chart for friction data.

        Args:
            widget (QtWidgets.QWidget): The parent widget to load UI components into.
        """
        QtCore.qInfo("Setting up UI for BearingTest.")
        super().setupUi(widget)
        chart = QtCharts.QChart()
        chart.setObjectName("chartFriction")
        line_series = QtCharts.QLineSeries()
        data = self.FrictionData
        if data:
            line_series.replace(data)
        chart.addSeries(line_series)

        axis_x = QtCharts.QValueAxis()
        axis_x.setTitleText(self.xtitle)
        axis_x.setLabelFormat("%.2f")
        axis_x.setRange(self.xmin, self.xmax)
        chart.addAxis(axis_x, QtCore.Qt.AlignmentFlag.AlignBottom)
        line_series.attachAxis(axis_x)

        axis_y = QtCharts.QValueAxis()
        axis_y.setTitleText(self.ytitle)
        axis_y.setLabelFormat("%.2f")
        axis_y.setRange(self.ymin, self.ymax)
        chart.addAxis(axis_y, QtCore.Qt.AlignmentFlag.AlignLeft)
        line_series.attachAxis(axis_y)

        chart_view = QtCharts.QChartView(chart, self.widgetTestData)
        chart_view.setObjectName("chartViewFriction")
        chart_view.setWindowTitle(self.charttitle)
        chart_view.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.layoutTestData.addWidget(chart_view)

        self.frictionDataChanged.connect(line_series.replace)

        self.chartFriction = chart
        self.lineSeriesFriction = line_series
        self.axisX = axis_x
        self.axisY = axis_y
        self.chartViewFriction = chart_view
        QtCore.qInfo("UI setup for BearingTest complete.")

    def onGenerateReport(self, report):
        """
        Generate a report section for the bearing test, including a friction plot.

        Args:
            report: The report object to which the plot will be added.
        """
        QtCore.qInfo("Generating report for BearingTest.")
        super().onGenerateReport(report)
        try:
            report.plotXYData(
                self.FrictionData,
                self.charttitle,
                self.xtitle,
                self.ytitle,
                getattr(self, "figurePath", ""),
                xmin=self.xmin,
                xmax=self.xmax,
                xTickCount=7,
                ymin=self.ymin,
                ymax=self.ymax,
                yTickCount=9,
            )
            QtCore.qInfo("Friction plot added to report.")
        except Exception as e:
            QtCore.qCritical(f"Failed to add friction plot to report: {e}")

    def onSaveData(self):
        """
        Save the friction data to a CSV file.

        Returns:
            Any: The result of the save operation from the base class.
        """
        QtCore.qInfo(f"Saving friction data to {getattr(self, 'dataFilePath', None)}")
        try:
            file = QtCore.QFile(getattr(self, "dataFilePath", ""))
            if file.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
                stream = QtCore.QTextStream(file)
                stream << f"Time (ns),{self.xtitle},{self.ytitle}\n"
                for _time, _data in enumerate(self.FrictionData):
                    if isinstance(_data, QtCore.QPointF):
                        stream << f"{_time},{_data.x()},{_data.y()}\n"
                    else:
                        stream << f"{_time},{_data[0]},{_data[1]}\n"
                file.close()
                QtCore.qInfo(
                    f"Friction data saved to {getattr(self, 'dataFilePath', None)}"
                )
            else:
                QtCore.qWarning(
                    f"Could not open file {getattr(self, 'dataFilePath', None)} for writing."
                )
        except Exception as e:
            QtCore.qCritical(f"Failed to save friction data: {e}")
        return super().onSaveData()

    def resetParameters(self):
        """
        Reset the test parameters and clear the friction data.
        """
        super().resetParameters()
        self.FrictionData = []

    def setDataDirectory(self, data_directory):
        """
        Set the directory for saving test data and figures.

        Args:
            data_directory (str): The root directory where data and figures will be saved.
        """
        QtCore.qInfo(f"Setting data directory for BearingTest: {data_directory}")
        super().setDataDirectory(data_directory)
        dir_obj = QtCore.QDir(self.dataDirectory)
        if not dir_obj.exists():
            dir_obj.mkpath(".")
        self.figurePath = dir_obj.filePath("friction_plot.png")
        self.dataFilePath = dir_obj.filePath("friction_plot_data.csv")
        QtCore.qInfo(f"Figure path set to: {self.figurePath}")
        QtCore.qInfo(f"Data file path set to: {self.dataFilePath}")

    def setup(self):
        """
        Configure the devices and prepare the test environment for the bearing test.
        """
        QtCore.qInfo(f"Setting up BearingTest for serial: {self.SerialNumber}")
        super().setup()
        MSO = self.devices.MSO5000
        MSO.acquire_settings(
            averages=16,
            memory_depth=MSO5000.MemoryDepth._10K,
            type_=MSO5000.AcquireType.Averages,
        )
        self.SampleRate = MSO.get_sample_rate()
        MSO.channel_settings(1, scale=2, display=True)
        MSO.channel_settings(
            2, scale=2, display=True, bandwidth_limit=MSO5000.BandwidthLimit._20M
        )
        MSO.channel_settings(
            3, scale=2, display=True, bandwidth_limit=MSO5000.BandwidthLimit._20M
        )
        MSO.timebase_settings(offset=2, scale=0.2, href_mode=MSO5000.HrefMode.Trigger)
        MSO.trigger_edge(nreject=True)
        MSO.function_generator_ramp(
            1,
            frequency=0.5,
            phase=270,
            amplitude=5,
            output_impedance=MSO5000.SourceOutputImpedance.Fifty,
        )
        MSO.function_generator_square(2, frequency=0.5, phase=270, amplitude=5)
        QtCore.qInfo("Device setup for BearingTest complete.")

    def run(self):
        """
        Execute the bearing test, collecting position and current data from the connected devices.
        """
        QtCore.qInfo(f"Running BearingTest for serial: {self.SerialNumber}")
        super().run()
        MSO = self.devices.MSO5000
        MSO.function_generator_state(1, True)
        MSO.function_generator_state(2, True)
        MSO.phase_align(2)
        MSO.clear()
        MSO.single()
        self.checkCancelled()
        for _ in range(int(self.readDelay)):
            self.checkCancelled()
            QtCore.QThread.msleep(1000)
        get_waveform = MSO.get_waveform
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
        self.checkCancelled()
        self.FrictionData = [
            QtCore.QPointF(4.5 * x, 100 * y)
            for x, y in zip(_positions_raw, _currents_raw)
        ]
        QtCore.qInfo(f"Collected {len(self.FrictionData)} friction data points.")
        MSO.function_generator_state(1, False)
        MSO.function_generator_state(2, False)

    def analyzeResults(self) -> bool:
        """
        Analyze the results of the bearing test.

        Returns:
            bool: The result of the analysis from the base class.
        """
        QtCore.qInfo(f"Analyzing results for serial: {self.SerialNumber}")
        result = super().analyzeResults()
        QtCore.qInfo(
            f"Analysis complete for serial: {self.SerialNumber}, result: {result}"
        )
        return result
