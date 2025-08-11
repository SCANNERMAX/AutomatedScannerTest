# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets, QtCharts
import logging
import numpy as np
import traceback

import tester
from tester.devices.mso5000 import MSO5000
from tester.devices.enums import Measurement, Source, HrefMode, BandwidthLimit, SourceOutputImpedance
from tester.manager.devices import DeviceManager
import tester.tests

logger = logging.getLogger(__name__)


class TorqueCenterTest(tester.tests.Test):
    """
    Performs a torque center analysis on a scanner device by applying a sinusoidal signal
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
        logger.debug(f"[TorqueCenterTest] Initializing TorqueCenterTest with cancel={cancel}, devices={devices}")
        try:
            super().__init__(
                "Torque Center Test",
                cancel,
                devices if devices is not None else DeviceManager(),
            )
            logger.debug("[TorqueCenterTest] Super __init__ called successfully")
        except Exception as e:
            logger.critical(f"[TorqueCenterTest] Exception in __init__: {e}\n{traceback.format_exc()}")
        logger.debug("[TorqueCenterTest] Exiting __init__")
        self.polyfit_coeffs = None  # Add this line

    @QtCore.Property(list, notify=torqueDataChanged)
    def TorqueData(self):
        """
        Get the current torque data.

        Returns:
            list: The list of QPointF (offset, RMS current) points.
        """
        return self.getParameter("TorqueData", [])

    @TorqueData.setter
    def TorqueData(self, value):
        """
        Set the torque data and emit the torqueDataChanged signal.

        Args:
            value (list): The new torque data as a list of QPointF.
        """
        self.setParameter("TorqueData", value)
        self.torqueDataChanged.emit(value)

    @QtCore.Property(float, notify=torqueCenterChanged)
    def TorqueCenter(self):
        """
        Get the current torque center value.

        Returns:
            float: The torque center value.
        """
        return self.getParameter("TorqueCenter", 0.0)

    @TorqueCenter.setter
    def TorqueCenter(self, value: float):
        """
        Set the torque center value and emit the torqueCenterChanged signal.

        Args:
            value (float): The new torque center value.
        """
        self.setParameter("TorqueCenter", value)
        self.torqueCenterChanged.emit(value)

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Handle modifications to the test settings.
        Loads settings for read delay, center tolerance, chart titles, and axis ranges.
        """
        logger.debug("[TorqueCenterTest] Entering onSettingsModified")
        try:
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
            logger.debug(
                f"[TorqueCenterTest] Settings loaded: readDelay={self.readDelay}, centerTolerance={self.centerTolerance}, "
                f"charttitle={self.charttitle}, xtitle={self.xtitle}, xmin={self.xmin}, xmax={self.xmax}, "
                f"ytitle={self.ytitle}, ymin={self.ymin}, ymax={self.ymax}"
            )
        except Exception as e:
            logger.critical(f"[TorqueCenterTest] Exception in onSettingsModified: {e}\n{traceback.format_exc()}")
        logger.debug("[TorqueCenterTest] Exiting onSettingsModified")

    def setupUi(self, parent=None):
        """
        Initialize and configure the UI components for displaying the torque center plot and value.

        Args:
            parent (QtWidgets.QWidget): The parent widget to which the UI components will be added.
        """
        logger.debug("[TorqueCenterTest] Entering setupUi")
        try:
            super().setupUi(parent)
            chart = QtCharts.QChart()
            chart.setObjectName("chartTorqueCenter")
            line_series = QtCharts.QLineSeries()
            line_series.setObjectName("lineSeriesTorqueCenter")
            data = self.TorqueData
            if data:
                line_series.replace(data)
            chart.addSeries(line_series)

            # --- Polynomial fit curve ---
            fit_series = QtCharts.QLineSeries()
            fit_series.setObjectName("lineSeriesTorqueFit")
            fit_series.setColor(QtCore.Qt.GlobalColor.red)  # Optional: make it red

            # Only plot if coefficients are available
            if self.polyfit_coeffs is not None:
                a, b, c = self.polyfit_coeffs
                # Use 100 points between xmin and xmax
                xs = np.linspace(self.xmin, self.xmax, 100)
                for x in xs:
                    y = a * x**2 + b * x + c
                    fit_series.append(x, y)
                chart.addSeries(fit_series)
                fit_series.attachAxis(axis_x)
                fit_series.attachAxis(axis_y)

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
                logger.info("[TorqueCenterTest] Added chart_view to layoutTestData")
            else:
                layout = parent.layout() or QtWidgets.QVBoxLayout(parent)
                parent.setLayout(layout)
                layout.addWidget(chart_view)
                logger.info("[TorqueCenterTest] Added chart_view to parent layout")

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
                logger.info("[TorqueCenterTest] Added widget_torque_center to layoutTestData")
            else:
                parent.layout().addWidget(widget_torque_center)
                logger.info("[TorqueCenterTest] Added widget_torque_center to parent layout")

            self.widgetTorqueCenter = widget_torque_center
            self.layoutTorqueCenter = layout_torque_center
            self.labelTorqueCenterName = label_torque_center_name
            self.textBoxTorqueCenter = text_box_torque_center
            logger.info("[TorqueCenterTest] UI setup for TorqueCenterTest complete")
        except Exception as e:
            logger.critical(f"[TorqueCenterTest] Exception in setupUi: {e}\n{traceback.format_exc()}")
        logger.debug("[TorqueCenterTest] Exiting setupUi")

    def onGenerateReport(self, report):
        """
        Generate a report section for the torque center test, including a torque plot and value.

        Args:
            report: The report object to which the plot and value will be added.
        """
        logger.debug("[TorqueCenterTest] Entering onGenerateReport")
        try:
            super().onGenerateReport(report)

            # Prepare measured data as (x, y) tuples
            measured_data = [
                (p.x(), p.y()) if isinstance(p, QtCore.QPointF) else (p[0], p[1])
                for p in self.TorqueData
            ]

            # Prepare polynomial fit data as (x, y) tuples
            fit_data = []
            if self.polyfit_coeffs is not None:
                a, b, c = self.polyfit_coeffs
                xs = np.linspace(self.xmin, self.xmax, 100)
                fit_data = [(x, a * x**2 + b * x + c) for x in xs]

            # Call plotXYData with both series
            report.plotXYData(
                [measured_data, fit_data] if fit_data else [measured_data],
                self.charttitle,
                self.xtitle,
                self.ytitle,
                getattr(self, "figurePath", ""),
                xmin=self.xmin,
                xmax=self.xmax,
                ymin=self.ymin,
                ymax=self.ymax,
                yTickCount=8,
                series_labels=["Measured", "Polynomial Fit"] if fit_data else ["Measured"],
                series_colors=[QtCore.Qt.blue, QtCore.Qt.red] if fit_data else [QtCore.Qt.blue],
            )
            report.writeLine(f"Torque Center: {self.TorqueCenter:.2f} deg")
        except Exception as e:
            logger.critical(f"[TorqueCenterTest] Failed to generate report: {e}\n{traceback.format_exc()}")
        logger.debug("[TorqueCenterTest] Exiting onGenerateReport")

    def onSaveData(self):
        """
        Save the torque data to a CSV file using Qt's QFile and QTextStream.

        Returns:
            Any: The result of the save operation from the base class.
        """
        logger.debug("[TorqueCenterTest] Entering onSaveData")
        dataFilePath = getattr(self, "dataFilePath", "")
        try:
            file = QtCore.QFile(dataFilePath)
            if file.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
                stream = QtCore.QTextStream(file)
                stream << f"Time (ns),{self.xtitle},{self.ytitle}\n"
                torque_data = self.TorqueData
                for _time, _data in enumerate(torque_data):
                    logger.debug(f"[TorqueCenterTest] Writing data row: time={_time}, data={_data}")
                    if isinstance(_data, QtCore.QPointF):
                        stream << f"{_time},{_data.x()},{_data.y()}\n"
                    else:
                        stream << f"{_time},{_data[0]},{_data[1]}\n"
                file.close()
                logger.info(f"[TorqueCenterTest] Torque data saved to {dataFilePath}")
            else:
                logger.warning(f"[TorqueCenterTest] Could not open file {dataFilePath} for writing")
        except Exception as e:
            logger.critical(f"[TorqueCenterTest] Failed to save torque data: {e}\n{traceback.format_exc()}")
        logger.debug("[TorqueCenterTest] Exiting onSaveData")
        return super().onSaveData()

    def resetParameters(self):
        """
        Reset the test parameters and clear the torque data and center.
        """
        logger.debug("[TorqueCenterTest] Entering resetParameters")
        try:
            super().resetParameters()
            self.TorqueData = []
            self.TorqueCenter = 0.0
        except Exception as e:
            logger.critical(f"[TorqueCenterTest] Exception in resetParameters: {e}\n{traceback.format_exc()}")
        logger.debug("[TorqueCenterTest] Exiting resetParameters")

    def setDataDirectory(self, data_directory):
        """
        Set the root directory for data storage and update internal paths for figure and data files.

        Args:
            data_directory (str): The root directory where data should be stored.
        """
        logger.debug(f"[TorqueCenterTest] Setting data directory: {data_directory}")
        try:
            super().setDataDirectory(data_directory)
            dir_obj = QtCore.QDir(self.dataDirectory)
            if not dir_obj.exists():
                logger.warning(f"[TorqueCenterTest] Data directory {self.dataDirectory} does not exist. Creating directory.")
                dir_obj.mkpath(".")
            self.figurePath = dir_obj.filePath("torque_plot.png")
            logger.debug(f"[TorqueCenterTest] Figure path set to: {self.figurePath}")
            self.dataFilePath = dir_obj.filePath("torque_center_data.csv")
            logger.debug(f"[TorqueCenterTest] Data file path set to: {self.dataFilePath}")
        except Exception as e:
            logger.critical(f"[TorqueCenterTest] Exception in setDataDirectory: {e}\n{traceback.format_exc()}")
        logger.debug("[TorqueCenterTest] Exiting setDataDirectory")

    def setup(self):
        """
        Set up the test environment for the torque center test using the provided serial number and devices.
        """
        logger.debug(f"[TorqueCenterTest] Setting up TorqueCenterTest for serial: {self.SerialNumber}")
        try:
            super().setup()
            mso = self.devices.MSO5000
            logger.info("[TorqueCenterTest] Configuring MSO5000 device")
            mso.timebase_settings(offset=2, scale=0.02, href_mode=HrefMode.Trigger)
            mso.function_generator_sinusoid(
                1,
                frequency=5,
                amplitude=0.5,
                output_impedance=SourceOutputImpedance.Fifty,
            )
            mso.channel_settings(1, display=False)
            mso.channel_settings(
                2, scale=2, display=True, bandwidth_limit=BandwidthLimit._20M
            )
            mso.set_measure_item(Measurement.VoltageRms, Source.Channel2)
            logger.info("[TorqueCenterTest] Device setup for TorqueCenterTest complete")
        except Exception as e:
            logger.critical(f"[TorqueCenterTest] Exception in setup: {e}\n{traceback.format_exc()}")
        logger.debug("[TorqueCenterTest] Exiting setup")

    def run(self):
        """
        Run the torque center test by iteratively adjusting the source offset and collecting RMS measurements.
        """
        logger.info(f"[TorqueCenterTest] Running TorqueCenterTest for serial: {self.SerialNumber}")
        try:
            super().run()
            mso = self.devices.MSO5000
            mso.function_generator_state(1, True)
            mso.run()
            data = []
            msleep = QtCore.QThread.msleep
            sleepDelay = int(self.readDelay * 1000)
            logger.info(f"[TorqueCenterTest] Starting data collection loop: sleepDelay={sleepDelay}")
            offsets = [(i / 10, i * 0.45) for i in range(-25, 26)]
            for i, (offset, offset_scaled) in enumerate(offsets):
                logger.info(f"[TorqueCenterTest] Setting source offset: {offset}")
                mso.set_source_offset(1, offset)
                for _ in range(0, sleepDelay, 100):
                    self.checkCancelled()
                    msleep(100)
                try:
                    rms = mso.get_measure_item(
                        Measurement.VoltageRms, Source.Channel2
                    )
                    logger.info(f"[TorqueCenterTest] Measured RMS: {rms} at offset: {offset}")
                    data.append(QtCore.QPointF(offset_scaled, rms * 100))
                except Exception as e:
                    logger.warning(f"[TorqueCenterTest] Failed to get RMS at offset {offset:.2f}: {e}\n{traceback.format_exc()}")
            self.TorqueData = data
            logger.info(f"[TorqueCenterTest] Collected {len(data)} torque data points")
            mso.function_generator_state(1, False)
            logger.info("[TorqueCenterTest] Function generator disabled after run")
        except Exception as e:
            logger.critical(f"[TorqueCenterTest] Exception in run: {e}\n{traceback.format_exc()}")
        logger.debug("[TorqueCenterTest] Exiting run")

    def analyzeResults(self) -> bool:
        """
        Analyze the test results for a given serial number.

        Determines the torque center by fitting a quadratic polynomial to the data
        and finding the offset corresponding to the minimum RMS current.
        Sets the test status to "Pass" if the absolute value of the torque center is less than the tolerance.

        Returns:
            bool: True if the test passes, False otherwise.
        """
        logger.info(f"[TorqueCenterTest] Analyzing results for serial: {self.SerialNumber}")
        try:
            super().analyzeResults()
            data = self.TorqueData
            if data:
                x = np.array([p.x() if isinstance(p, QtCore.QPointF) else p[0] for p in data])
                y = np.array([p.y() if isinstance(p, QtCore.QPointF) else p[1] for p in data])
                coeffs = np.polyfit(x, y, 2)
                self.polyfit_coeffs = coeffs  # Store coefficients
                a, b, c = coeffs
                if a != 0:
                    torque_center_fit = -b / (2 * a)
                    self.TorqueCenter = torque_center_fit
                else:
                    min_point = min(data, key=lambda p: p.y() if isinstance(p, QtCore.QPointF) else p[1])
                    self.TorqueCenter = min_point.x() if isinstance(min_point, QtCore.QPointF) else min_point[0]
            else:
                logger.critical("[TorqueCenterTest] No torque data available for analysis")
                raise ValueError("No torque data available for analysis")
            result = abs(self.TorqueCenter) < self.centerTolerance
            logger.info(
                f"[TorqueCenterTest] Test result: {'Pass' if result else 'Fail'} (TorqueCenter={self.TorqueCenter}, centerTolerance={self.centerTolerance})"
            )
        except Exception as e:
            logger.critical(f"[TorqueCenterTest] Exception in analyzeResults: {e}\n{traceback.format_exc()}")
            result = False
        logger.debug("[TorqueCenterTest] Exiting analyzeResults")
        return result

    def teardown(self):
        """
        Tear down the test environment and perform any necessary cleanup.
        """
        logger.debug("[TorqueCenterTest] Entering teardown")
        try:
            super().teardown()
            logger.info("[TorqueCenterTest] Teardown complete")
        except Exception as e:
            logger.critical(f"[TorqueCenterTest] Exception in teardown: {e}\n{traceback.format_exc()}")
        logger.debug("[TorqueCenterTest] Exiting teardown")
