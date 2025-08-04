# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets, QtCharts
import logging

import tester
from tester.devices.mso5000 import MSO5000
from tester.manager.devices import DeviceManager
import tester.tests

__logger = logging.getLogger(__name__)


class TorqueCenterTest(tester.tests.Test):
    """
    TorqueCenterTest performs a torque center analysis on a scanner device by applying a sinusoidal signal
    with varying offsets and measuring the resulting RMS current. The test determines the torque center,
    which is expected to correspond to a zero crossing in the measured current.

    Signals:
        torqueDataChanged (list): Emitted when the torque data changes.
        torqueCenterChanged (float): Emitted when the torque center value changes.
    """

    torqueDataChanged = QtCore.Signal(list)
    torqueCenterChanged = QtCore.Signal(float)

    def __init__(self, cancel: tester.tests.CancelToken, devices: DeviceManager = None):
        """
        Initialize the TorqueCenterTest instance.

        Args:
            cancel (tester.tests.CancelToken): Token to signal cancellation of the test.
            devices (DeviceManager, optional): Device manager for hardware interaction.
        """
        __logger.debug(
            f"TorqueCenterTest initialized with cancel token and devices: "
            f"{cancel}, {devices}"
        )
        super().__init__(
            "Torque Center Test",
            cancel,
            devices if devices is not None else DeviceManager(),
        )

    @QtCore.Property(list, notify=torqueDataChanged)
    def TorqueData(self):
        """
        Get the current torque data.

        Returns:
            list: The list of QPointF (offset, RMS current) points.
        """
        data = self.getParameter("TorqueData", [])
        __logger.debug(f"TorqueData value: {data}.")
        return data

    @TorqueData.setter
    def TorqueData(self, value):
        """
        Set the torque data and emit the torqueDataChanged signal.

        Args:
            value (list): The new torque data as a list of QPointF.
        """
        __logger.debug(f"Setting TorqueData property: {value}.")
        self.setParameter("TorqueData", value)
        self.torqueDataChanged.emit(value)

    @QtCore.Property(float, notify=torqueCenterChanged)
    def TorqueCenter(self):
        """
        Get the current torque center value.

        Returns:
            float: The torque center value.
        """
        center = self.getParameter("TorqueCenter", 0.0)
        __logger.debug(f"TorqueCenter value: {center}.")
        return center

    @TorqueCenter.setter
    def TorqueCenter(self, value: float):
        """
        Set the torque center value and emit the torqueCenterChanged signal.

        Args:
            value (float): The new torque center value.
        """
        __logger.debug(f"Setting TorqueCenter property: {value}.")
        self.setParameter("TorqueCenter", value)
        self.torqueCenterChanged.emit(value)

    def onSettingsModified(self):
        """
        Handle modifications to the test settings.
        Loads settings for read delay, center tolerance, chart titles, and axis ranges.
        """
        super().onSettingsModified()
        s = self.getSetting
        self.readDelay = s("ReadDelay", 0.2)
        self.centerTolerance = s("CenterTolerance", 1.0)
        self.charttitle = s("ChartTitle", "Torque Center Plot")
        self.xtitle = s("PositionTitle", "Position (deg)")
        self.xmin = s("PositionMinimum", -30.0)
        self.xmax = s("PositionMaximum", 30.0)
        self.ytitle = s("TorqueCurrentTitle", "RMS Current (mA)")
        self.ymin = s("TorqueCurrentMinimum", 0)
        self.ymax = s("TorqueCurrentMaximum", 500.0)
        __logger.debug(
            f"Settings modified: readDelay={self.readDelay}, centerTo"
            f"lerance={self.centerTolerance}, charttitle={self.charttitle}, xt"
            f"itle={self.xtitle}, xmin={self.xmin}, xmax={self.xmax}, ytitle="
            f"{self.ytitle}, ymin={self.ymin}, ymax={self.ymax}"
        )

    def setupUi(self, parent=None):
        """
        Initialize and configure the UI components for displaying the torque center plot and value.

        Args:
            parent (QtWidgets.QWidget): The parent widget to which the UI components will be added.
        """
        __logger.debug(f"Setting up UI for TorqueCenterTest.")
        super().setupUi(parent)
        chart = QtCharts.QChart()
        chart.setObjectName("chartTorqueCenter")
        line_series = QtCharts.QLineSeries()
        line_series.setObjectName("lineSeriesTorqueCenter")
        data = self.TorqueData
        __logger.debug(f"Initial chart data: {data}.")
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

        chart_view = QtCharts.QChartView(chart, parent)
        chart_view.setObjectName("chartViewTorqueCenter")
        chart_view.setWindowTitle(self.charttitle)
        chart_view.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        layout_test_data = getattr(self, "layoutTestData", None)
        if layout_test_data is not None:
            layout_test_data.addWidget(chart_view)
            __logger.debug(f"Added chart_view to layoutTestData.")
        else:
            layout = parent.layout() or QtWidgets.QVBoxLayout(parent)
            parent.setLayout(layout)
            layout.addWidget(chart_view)
            __logger.debug(f"Added chart_view to parent layout.")

        self.torqueDataChanged.connect(line_series.replace)

        self.chartTorqueCenter = chart
        self.lineSeriesTorqueCenter = line_series
        self.axisX = axis_x
        self.axisY = axis_y
        self.chartViewTorqueCenter = chart_view

        widget_torque_center = QtWidgets.QWidget(parent)
        widget_torque_center.setObjectName("widgetTorqueCenter")
        layout_torque_center = QtWidgets.QHBoxLayout(widget_torque_center)
        label_torque_center_name = QtWidgets.QLabel(
            "Torque Center: ", widget_torque_center
        )
        label_torque_center_name.setObjectName("labelTorqueCenterName")
        layout_torque_center.addWidget(label_torque_center_name)
        text_box_torque_center = QtWidgets.QLineEdit(
            f"{self.TorqueCenter:.2f}", widget_torque_center
        )
        text_box_torque_center.setObjectName("textBoxTorqueCenter")
        text_box_torque_center.setEnabled(False)
        self.torqueCenterChanged.connect(
            lambda value: text_box_torque_center.setText(f"{value:.2f}")
        )
        layout_torque_center.addWidget(text_box_torque_center)

        if layout_test_data is not None:
            layout_test_data.addWidget(widget_torque_center)
            __logger.debug(f"Added widget_torque_center to layoutTestData.")
        else:
            parent.layout().addWidget(widget_torque_center)
            __logger.debug(f"Added widget_torque_center to parent layout.")

        self.widgetTorqueCenter = widget_torque_center
        self.layoutTorqueCenter = layout_torque_center
        self.labelTorqueCenterName = label_torque_center_name
        self.textBoxTorqueCenter = text_box_torque_center
        __logger.debug(f"UI setup for TorqueCenterTest complete.")

    def onGenerateReport(self, report):
        """
        Generate a report section for the torque center test, including a torque plot and value.

        Args:
            report: The report object to which the plot and value will be added.
        """
        __logger.debug(f"Generating report for TorqueCenterTest.")
        super().onGenerateReport(report)
        try:
            __logger.debug(
                f"Report plotXYData: data={self.TorqueData}, charttitle={self.charttitle}, "
                f"xtitle={self.xtitle}, ytitle={self.ytitle}, figurePath={getattr(self, 'figurePath', '')}, "
                f"xmin={self.xmin}, xmax={self.xmax}, ymin={self.ymin}, ymax={self.ymax}"
            )
            report.plotXYData(
                self.TorqueData,
                self.charttitle,
                self.xtitle,
                self.ytitle,
                getattr(self, "figurePath", ""),
                xmin=self.xmin,
                xmax=self.xmax,
                ymin=self.ymin,
                ymax=self.ymax,
                yTickCount=8,
            )
            report.writeLine(f"Torque Center: {self.TorqueCenter:.2f} deg")
            __logger.debug(f"Report generated and plot added.")
        except Exception as e:
            __logger.critical(f"Failed to generate report: {e}.")
        __logger.debug(f"Exiting onGenerateReport.")

    def onSaveData(self):
        """
        Save the torque data to a CSV file using Qt's QFile and QTextStream.

        Returns:
            Any: The result of the save operation from the base class.
        """
        dataFilePath = getattr(self, "dataFilePath", "")
        __logger.debug(f"Saving torque data to {dataFilePath}.")
        try:
            file = QtCore.QFile(dataFilePath)
            if file.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
                stream = QtCore.QTextStream(file)
                stream << f"Time (ns),{self.xtitle},{self.ytitle}\n"
                for _time, _data in enumerate(self.TorqueData):
                    __logger.debug(f"Writing data row: time={_time}, data={_data}.")
                    if isinstance(_data, QtCore.QPointF):
                        stream << f"{_time},{_data.x()},{_data.y()}\n"
                    else:
                        stream << f"{_time},{_data[0]},{_data[1]}\n"
                file.close()
                __logger.debug(f"Torque data saved to {dataFilePath}.")
            else:
                __logger.warning(f"Could not open file {dataFilePath} for writing.")
        except Exception as e:
            __logger.critical(f"Failed to save torque data: {e}.")
        __logger.debug(f"Exiting onSaveData.")
        return super().onSaveData()

    def resetParameters(self):
        """
        Reset the test parameters and clear the torque data and center.
        """
        __logger.debug(f"Entering resetParameters.")
        super().resetParameters()
        self.TorqueData = []
        self.TorqueCenter = 0.0
        __logger.debug(
            f"Parameters reset: TorqueData cleared, TorqueCenter set to 0.0."
        )
        __logger.debug(f"Exiting resetParameters.")

    def setDataDirectory(self, data_directory):
        """
        Set the root directory for data storage and update internal paths for figure and data files.

        Args:
            data_directory (str): The root directory where data should be stored.
        """
        __logger.debug(
            f"Setting data directory for TorqueCenterTest: {data_directory}."
        )
        super().setDataDirectory(data_directory)
        dir_obj = QtCore.QDir(self.dataDirectory)
        if not dir_obj.exists():
            __logger.warning(
                f"Data directory {self.dataDirectory} does not exist. Creating directory."
            )
            dir_obj.mkpath(".")
        self.figurePath = dir_obj.filePath("torque_plot.png")
        __logger.debug(f"Figure path set to: {self.figurePath}.")
        self.dataFilePath = dir_obj.filePath("torque_center_data.csv")
        __logger.debug(f"Data file path set to: {self.dataFilePath}.")

    def setup(self):
        """
        Set up the test environment for the torque center test using the provided serial number and devices.
        """
        __logger.debug(f"Setting up TorqueCenterTest for serial: {self.SerialNumber}.")
        super().setup()
        mso = self.devices.MSO5000
        __logger.debug(f"Configuring MSO5000 device.")
        mso.timebase_settings(offset=2, scale=0.02, href_mode=MSO5000.HrefMode.Trigger)
        mso.function_generator_sinusoid(
            1,
            frequency=5,
            amplitude=0.5,
            output_impedance=MSO5000.SourceOutputImpedance.Fifty,
        )
        mso.channel_settings(1, display=False)
        mso.channel_settings(
            2, scale=2, display=True, bandwidth_limit=MSO5000.BandwidthLimit._20M
        )
        mso.set_measure_item(MSO5000.Measurement.VoltageRms, MSO5000.Source.Channel2)
        __logger.debug(f"Device setup for TorqueCenterTest complete.")

    def run(self):
        """
        Run the torque center test by iteratively adjusting the source offset and collecting RMS measurements.
        """
        __logger.debug(f"Running TorqueCenterTest for serial: {self.SerialNumber}.")
        super().run()
        mso = self.devices.MSO5000
        mso.function_generator_state(1, True)
        mso.run()
        data = []
        msleep = QtCore.QThread.msleep
        sleepDelay = int(self.readDelay * 1000)
        __logger.debug(f"Starting data collection loop: sleepDelay={sleepDelay}.")
        for i in range(-25, 26):
            offset = i / 10
            __logger.info(f"Setting source offset: {offset}.")
            mso.set_source_offset(1, offset)
            for _ in range(0, sleepDelay, 100):
                self.checkCancelled()
                msleep(100)
            try:
                rms = mso.get_measure_item(
                    MSO5000.Measurement.VoltageRms, MSO5000.Source.Channel2
                )
                __logger.debug(f"Measured RMS: {rms} at offset: {offset}.")
                data.append(QtCore.QPointF(offset * 4.5, rms * 100))
            except Exception as e:
                __logger.warning(f"Failed to get RMS at offset {offset:.2f}: {e}.")
        self.TorqueData = data
        __logger.info(f"Collected {len(data)} torque data points.")
        mso.function_generator_state(1, False)
        __logger.debug(f"Function generator disabled after run.")

    def analyzeResults(self) -> bool:
        """
        Analyze the test results for a given serial number.

        Determines the torque center by finding the offset with the minimum RMS current.
        Sets the test status to "Pass" if the absolute value of the torque center is less than the tolerance.

        Returns:
            bool: True if the test passes, False otherwise.
        """
        __logger.debug(f"Analyzing results for serial: {self.SerialNumber}.")
        super().analyzeResults()
        data = self.TorqueData
        if data:
            min_point = min(
                data, key=lambda p: p.y() if isinstance(p, QtCore.QPointF) else p[1]
            )
            __logger.debug(f"Minimum RMS point: {min_point}.")
            self.TorqueCenter = (
                min_point.x() if isinstance(min_point, QtCore.QPointF) else min_point[0]
            )
            __logger.info(f"TorqueCenter determined: {self.TorqueCenter:.4f}.")
        else:
            __logger.critical("No torque data available for analysis.")
            raise ValueError("No torque data available for analysis.")
        result = abs(self.TorqueCenter) < self.centerTolerance
        __logger.debug(
            f"Test result: {'Pass' if result else 'Fail'} (TorqueCen"
            f"ter={self.TorqueCenter}, centerTolerance={self.centerTolerance})"
        )
        return result

    def teardown(self):
        """
        Tear down the test environment and perform any necessary cleanup.
        """
        __logger.debug(f"Tearing down TorqueCenterTest.")
        super().teardown()
