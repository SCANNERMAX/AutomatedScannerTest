# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets, QtCharts
import logging
import traceback

from tester.tests import CancelToken, Test
from tester.devices.enums import (
    MemoryDepth,
    AcquireType,
    BandwidthLimit,
    HrefMode,
    SourceOutputImpedance,
    Source,
    TriggerCoupling,
    WaveformMode,
    WaveformFormat,
)
from tester.manager.devices import DeviceManager

logger = logging.getLogger(__name__)


class BearingTest(Test):
    """
    Test for evaluating scanner bearing friction by sweeping and measuring current.

    Attributes:
        FrictionData (list[tuple]): List of (position, current) tuples.
        frictionDataChanged (Signal): Emitted when friction data is updated.
    """

    frictionDataChanged = QtCore.Signal(list)

    def __init__(self, cancel: CancelToken, devices: DeviceManager = None):
        """
        Initialize the BearingTest instance.

        Args:
            cancel (CancelToken): Token to allow test interruption.
            devices (DeviceManager, optional): Device manager for hardware access.
        """
        logger.debug(
            f"[BearingTest] Initializing BearingTest with cancel={cancel}, devices={devices}"
        )
        try:
            super().__init__(
                "Bearing Test",
                cancel,
                devices if devices is not None else DeviceManager(),
            )
        except Exception as e:
            logger.critical(
                f"[BearingTest] Exception in __init__: {e}\n{traceback.format_exc()}"
            )

    @QtCore.Property(list, notify=frictionDataChanged)
    def FrictionData(self):
        """
        Get the current friction data.

        Returns:
            list: The list of (position, current) tuples.
        """
        return self.getParameter("FrictionData", [])

    @FrictionData.setter
    def FrictionData(self, value):
        """
        Set the friction data and emit the frictionDataChanged signal.

        Args:
            value (list): The new friction data as a list of (position, current) tuples.
        """
        self.setParameter("FrictionData", value)
        self.frictionDataChanged.emit(value)

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Handle modifications to the test settings and update internal state.
        """
        logger.debug("[BearingTest] onSettingsModified called")
        super().onSettingsModified()
        s = self.getSetting
        self.readDelay = s("ReadDelay", 10)
        self.charttitle = s("ChartTitle", "Bearing Friction Plot")
        self.xtitle = s("PositionTitle", "Position (deg)")
        self.xmin = s("PositionMinimum", -30.0)
        self.xmax = s("PositionMaximum", 30.0)
        self.ytitle = s("TorqueCurrentTitle", "Torque Current (mA)")
        self.ymin = s("TorqueCurrentMinimum", -400.0)
        self.ymax = s("TorqueCurrentMaximum", 400.0)

    def setupUi(self, widget: QtWidgets.QWidget):
        """
        Set up the user interface for the bearing test, including the chart for friction data.

        Args:
            widget (QtWidgets.QWidget): The parent widget to load UI components into.
        """
        logger.debug("[BearingTest] setupUi called")
        super().setupUi(widget)

        # Set a vertical layout for the test data widget
        layoutBearingTestData = QtWidgets.QVBoxLayout(self.widgetTestData)
        layoutBearingTestData.setObjectName("layoutBearingTestData")
        self.widgetTestData.setLayout(layoutBearingTestData)

        # Create and configure the chart for friction data
        chartBearingTest = QtCharts.QChart()
        chartBearingTest.setObjectName("chartBearingTest")
        chartBearingTest.setTitle(self.charttitle)
        chartBearingTest.legend().hide()

        # Create the line series and populate it with initial data
        lineSeriesFrictionPlot = QtCharts.QLineSeries()
        lineSeriesFrictionPlot.setName("Friction Data")
        lineSeriesFrictionPlot.setObjectName("lineSeriesFrictionPlot")
        chartBearingTest.addSeries(lineSeriesFrictionPlot)

        xAxis = QtCharts.QValueAxis()
        xAxis.setTitleText(self.xtitle)
        xAxis.setLabelFormat("%.2f")
        xAxis.setRange(self.xmin, self.xmax)
        chartBearingTest.addAxis(xAxis, QtCore.Qt.AlignmentFlag.AlignBottom)
        lineSeriesFrictionPlot.attachAxis(xAxis)

        yAxis = QtCharts.QValueAxis()
        yAxis.setTitleText(self.ytitle)
        yAxis.setLabelFormat("%.2f")
        yAxis.setRange(self.ymin, self.ymax)
        chartBearingTest.addAxis(yAxis, QtCore.Qt.AlignmentFlag.AlignLeft)
        lineSeriesFrictionPlot.attachAxis(yAxis)

        chartViewBearingTest = QtCharts.QChartView(
            chartBearingTest, self.widgetTestData
        )
        chartViewBearingTest.setObjectName("bearingTestChartView")
        chartViewBearingTest.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        layoutBearingTestData.addWidget(chartViewBearingTest)

        # Use a local function to avoid recreating lambda on every signal emission
        def updateFrictionChart(data):
            """
            Update the chart with new friction data.

            Args:
                data (list): List of (position, current) tuples.
            """
            lineSeriesFrictionPlot.replace([QtCore.QPointF(x, y) for x, y in data])

        updateFrictionChart(self.FrictionData)
        self.frictionDataChanged.connect(updateFrictionChart)

    def onGenerateReport(self, report):
        """
        Generate a report section for the bearing test, including a friction plot.

        Args:
            report: The report object to which the plot will be added.
        """
        logger.debug("[BearingTest] onGenerateReport called")
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
        except Exception as e:
            logger.critical(
                "[BearingTest] Failed to add friction plot to report: %r", e
            )

    def onSaveData(self):
        """
        Save the friction data to a CSV file.

        Returns:
            Any: The result of the save operation from the base class.
        """
        logger.debug("[BearingTest] onSaveData called")
        dataFilePath = getattr(self, "dataFilePath", None)
        try:
            file = QtCore.QFile(dataFilePath)
            if file.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
                stream = QtCore.QTextStream(file)
                stream << f"Time (ns),{self.xtitle},{self.ytitle}\n"
                # Use enumerate and unpack directly for clarity
                for _time, (_x, _y) in enumerate(self.FrictionData):
                    stream << f"{_time},{_x},{_y}\n"
                file.close()
            else:
                logger.warning(
                    "[BearingTest] Could not open file %r for writing", dataFilePath
                )
        except Exception as e:
            logger.critical("[BearingTest] Failed to save friction data: %r", e)
        return super().onSaveData()

    def resetParameters(self):
        """
        Reset the test parameters and clear the friction data.
        """
        logger.debug("[BearingTest] resetParameters called")
        super().resetParameters()
        self.FrictionData = []

    def setDataDirectory(self, data_directory):
        """
        Set the directory for saving test data and figures.

        Args:
            data_directory (str): The root directory where data and figures will be saved.
        """
        logger.debug("[BearingTest] setDataDirectory called")
        super().setDataDirectory(data_directory)
        dir_obj = QtCore.QDir(self.dataDirectory)
        if not dir_obj.exists():
            dir_obj.mkpath(".")
        self.figurePath = dir_obj.filePath("friction_plot.png")
        self.dataFilePath = dir_obj.filePath("friction_plot_data.csv")

    def setup(self):
        """
        Configure the devices and prepare the test environment for the bearing test.
        """
        logger.debug("[BearingTest] setup called for serial: %r", self.SerialNumber)
        super().setup()
        MSO = self.devices.MSO5000
        MSO.acquire_settings(
            averages=16,
            memory_depth=MemoryDepth._10K,
            type_=AcquireType.Averages,
        )
        self.SampleRate = MSO.get_sample_rate()
        MSO.channel_settings(1, scale=2, display=True)
        MSO.channel_settings(
            2, scale=2, display=True, bandwidth_limit=BandwidthLimit._20M
        )
        MSO.channel_settings(
            3, scale=2, display=True, bandwidth_limit=BandwidthLimit._20M
        )
        MSO.timebase_settings(offset=2, scale=0.2, href_mode=HrefMode.Trigger)
        MSO.trigger_edge(nreject=False)
        MSO.function_generator_ramp(
            1,
            frequency=0.5,
            phase=270,
            amplitude=5,
            output_impedance=SourceOutputImpedance.Fifty,
        )
        MSO.function_generator_square(2, frequency=0.5, phase=270, amplitude=5)
        MSO.function_generator_state(1, True)
        MSO.function_generator_state(2, True)
        MSO.phase_align(2)
        MSO.clear()
        self.checkCancelled()

    def run(self):
        """
        Execute the bearing test, collecting position and current data from the connected devices.
        """
        logger.debug("[BearingTest] run called")
        super().run()
        MSO = self.devices.MSO5000
        MSO.single()
        QtCore.QThread.msleep(1000 * int(self.readDelay))
        get_waveform = MSO.get_waveform
        _positions_raw = get_waveform(
            source=Source.Channel2,
            mode=WaveformMode.Raw,
            format_=WaveformFormat.Ascii,
            stop=10000,
        )
        _currents_raw = get_waveform(
            source=Source.Channel3,
            mode=WaveformMode.Raw,
            format_=WaveformFormat.Ascii,
            stop=10000,
        )
        self.checkCancelled()
        # Use zip and list comprehension for efficient tuple creation
        self.FrictionData = [
            (4.5 * x, 100 * y) for x, y in zip(_positions_raw, _currents_raw)
        ]
        MSO.function_generator_state(1, False)
        MSO.function_generator_state(2, False)

    def analyzeResults(self) -> bool:
        """
        Analyze the results of the bearing test.

        Returns:
            bool: The result of the analysis from the base class.
        """
        logger.debug("[BearingTest] analyzeResults called")
        result = super().analyzeResults()
        return result
