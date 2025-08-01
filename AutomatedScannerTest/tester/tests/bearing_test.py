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

    def __init__(self, cancel: tester.tests.CancelToken):
        """
        Initialize the BearingTest instance.

        Args:
            cancel (tester.tests.CancelToken): The cancel token to allow test interruption.
        """
        super().__init__("Bearing Test", cancel)
        QtCore.qInfo("BearingTest initialized.")

    @QtCore.Property(list, notify=frictionDataChanged)
    def FrictionData(self):
        """
        Get the current friction data.

        Returns:
            list: The list of (position, current) QPointF tuples.
        """
        data = self.getParameter("FrictionData", [])
        if QtCore.QLoggingCategory.defaultCategory().isDebugEnabled():
            QtCore.qDebug(f"Accessed FrictionData: {len(data)} points")
        return data

    @FrictionData.setter
    def FrictionData(self, value):
        """
        Set the friction data and emit the frictionDataChanged signal.

        Args:
            value (list): The new friction data as a list of QPointF tuples.
        """
        if QtCore.QLoggingCategory.defaultCategory().isDebugEnabled():
            QtCore.qDebug(f"Setting FrictionData: {len(value)} points")
        self.setParameter("FrictionData", value)
        self.frictionDataChanged.emit(value)

    def analyzeResults(self, serial_number: str):
        """
        Analyze the results of the bearing test for the given serial number.

        Args:
            serial_number (str): The serial number of the device under test.

        Returns:
            Any: The result of the analysis from the base class.
        """
        QtCore.qInfo(f"Analyzing results for serial: {serial_number}")
        result = super().analyzeResults(serial_number)
        QtCore.qInfo(f"Analysis complete for serial: {serial_number}, result: {result}")
        return result

    def onSettingsModified(self):
        """
        Handle modifications to the test settings and update internal state.
        """
        super().onSettingsModified()
        self.readDelay = self.getSetting("ReadDelay", 5)
        self.charttitle = self.getSetting("ChartTitle", "Bearing Friction Plot")
        self.xtitle = self.getSetting("PositionTitle", "Position (deg)")
        self.xmin = self.getSetting("PositionMinimum", -30.0)
        self.xmax = self.getSetting("PositionMaximum", 30.0)
        self.ytitle = self.getSetting("TorqueCurrentTitle", "Torque Current (mA)")
        self.ymin = self.getSetting("TorqueCurrentMinimum", -400.0)
        self.ymax = self.getSetting("TorqueCurrentMaximum", 400.0)
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
            if QtCore.QLoggingCategory.defaultCategory().isDebugEnabled():
                QtCore.qDebug(f"Populating chart with {len(data)} FrictionData points")
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
        chart_view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
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
                str(self.figurePath),
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

    def onSave(self):
        """
        Save the friction data to a CSV file.

        Returns:
            Any: The result of the save operation from the base class.
        """
        QtCore.qInfo(f"Saving friction data to {getattr(self, 'dataFilePath', None)}")
        try:
            file = QtCore.QFile(self.dataFilePath)
            if file.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
                stream = QtCore.QTextStream(file)
                stream << f"Time (ns),{self.xtitle},{self.ytitle}\n"
                for _time, _data in enumerate(self.FrictionData):
                    if isinstance(_data, QtCore.QPointF):
                        stream << f"{_time},{_data.x()},{_data.y()}\n"
                    else:
                        stream << f"{_time},{_data[0]},{_data[1]}\n"
                file.close()
                QtCore.qInfo(f"Friction data saved to {self.dataFilePath}")
            else:
                QtCore.qWarning(f"Could not open file {self.dataFilePath} for writing.")
        except Exception as e:
            QtCore.qCritical(f"Failed to save friction data: {e}")
        return super().onSave()

    def resetParameters(self):
        """
        Reset the test parameters and clear the friction data.
        """
        if QtCore.QLoggingCategory.defaultCategory().isDebugEnabled():
            QtCore.qDebug("Resetting parameters for BearingTest.")
        super().resetParameters()
        self.FrictionData = []

    def run(self, serial_number: str, devices: DeviceManager):
        """
        Execute the bearing test, collecting position and current data from the connected devices.

        Args:
            serial_number (str): The serial number of the device under test.
            devices (DeviceManager): The device manager containing connected devices.
        """
        QtCore.qInfo(f"Running BearingTest for serial: {serial_number}")
        super().run(serial_number, devices)
        try:
            MSO = devices.MSO5000
            QtCore.qDebug("Enabling function generators and aligning phase.")
            MSO.function_generator_state(1, True)
            MSO.function_generator_state(2, True)
            MSO.phase_align(2)
            MSO.clear()
            MSO.single()
            QtCore.qDebug(f"Sleeping for readDelay: {self.readDelay}s using QtCore.QThread.msleep")
            QtCore.QThread.msleep(int(self.readDelay * 1000))
            get_waveform = MSO.get_waveform
            QtCore.qDebug("Acquiring position waveform.")
            _positions_raw = get_waveform(
                source=MSO5000.Source.Channel2,
                mode=MSO5000.WaveformMode.Raw,
                format_=MSO5000.WaveformFormat.Ascii,
                stop=10000,
            )
            QtCore.qDebug("Acquiring current waveform.")
            _currents_raw = get_waveform(
                source=MSO5000.Source.Channel3,
                mode=MSO5000.WaveformMode.Raw,
                format_=MSO5000.WaveformFormat.Ascii,
                stop=10000,
            )
            QtCore.qDebug("Processing and storing friction data.")
            self.FrictionData = [QtCore.QPointF(4.5 * x, 100 * y) for x, y in zip(_positions_raw, _currents_raw)]
            QtCore.qInfo(f"Collected {len(self.FrictionData)} friction data points.")
        except Exception as e:
            QtCore.qCritical(f"Error during BearingTest run: {e}")
        finally:
            try:
                MSO.function_generator_state(1, False)
                MSO.function_generator_state(2, False)
                QtCore.qDebug("Function generators disabled.")
            except Exception as e:
                QtCore.qWarning(f"Error disabling function generators: {e}")

    def setDataDirectory(self, root_directory):
        """
        Set the directory for saving test data and figures.

        Args:
            root_directory: The root directory where data and figures will be saved.
        """
        QtCore.qInfo(f"Setting data directory for BearingTest: {root_directory}")
        super().setDataDirectory(root_directory)
        dir_obj = QtCore.QDir(self.dataDirectory)
        if not dir_obj.exists():
            dir_obj.mkpath(".")
            QtCore.qDebug(f"Created data directory: {self.dataDirectory}")
        self.figurePath = dir_obj.filePath("friction_plot.png")
        self.dataFilePath = dir_obj.filePath("friction_plot_data.csv")
        QtCore.qInfo(f"Figure path set to: {self.figurePath}")
        QtCore.qInfo(f"Data file path set to: {self.dataFilePath}")

    def setup(self, serial_number: str, devices: DeviceManager):
        """
        Configure the devices and prepare the test environment for the bearing test.

        Args:
            serial_number (str): The serial number of the device under test.
            devices (DeviceManager): The device manager containing connected devices.
        """
        QtCore.qInfo(f"Setting up BearingTest for serial: {serial_number}")
        super().setup(serial_number, devices)
        try:
            MSO = devices.MSO5000
            MSO.acquire_settings(
                averages=16,
                memory_depth=MSO5000.MemoryDepth._10K,
                type_=MSO5000.AcquireType.Averages,
            )
            self.SampleRate = MSO.get_sample_rate()
            QtCore.qDebug(f"SampleRate set to: {self.SampleRate}")
            MSO.channel_settings(1, scale=2, display=True)
            MSO.channel_settings(
                2, scale=2, display=True, bandwidth_limit=MSO5000.BandwidthLimit._20M
            )
            MSO.channel_settings(
                3,
                scale=2,
                display=True,
                bandwidth_limit=MSO5000.BandwidthLimit._20M,
            )
            MSO.timebase_settings(
                offset=2, scale=0.2, href_mode=MSO5000.HrefMode.Trigger
            )
            MSO.trigger_edge(nreject=True)
            MSO.function_generator_ramp(
                1,
                frequency=0.5,
                phase=270,
                amplitude=5,
                output_impedance=MSO5000.SourceOutputImpedance.Fifty,
            )
            MSO.function_generator_square(
                2, frequency=0.5, phase=270, amplitude=5
            )
            QtCore.qInfo("Device setup for BearingTest complete.")
        except Exception as e:
            QtCore.qCritical(f"Error during BearingTest setup: {e}")
