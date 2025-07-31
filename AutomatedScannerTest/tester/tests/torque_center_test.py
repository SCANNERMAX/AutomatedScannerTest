# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets, QtCharts
import time

import tester
from tester.devices.mso5000 import MSO5000
import tester.tests


class TorqueCenterTest(tester.tests.Test):
    """
    TorqueCenterTest performs a torque center analysis on a scanner device by applying a sinusoidal signal
    with varying offsets and measuring the resulting RMS current. The test determines the torque center,
    which is expected to correspond to a zero crossing in the measured current.
    """

    torqueDataChanged = QtCore.Signal(list)
    """Signal emitted when the torque data changes."""

    torqueCenterChanged = QtCore.Signal(float)
    """Signal emitted when the torque center value changes."""

    def __init__(self, cancel: tester.tests.CancelToken):
        """
        Initialize the TorqueCenterTest instance.

        Args:
            cancel (tester.tests.CancelToken): Token to signal cancellation of the test.
        """
        super().__init__("Torque Center Test", cancel)

    def get_torque_data(self) -> list:
        """
        Get the current torque data.

        Returns:
            list: The list of (offset, RMS current) tuples.
        """
        return self.getParameter("TorqueData", [])

    def set_torque_data(self, value: list):
        """
        Set the torque data and emit the torqueDataChanged signal.

        Args:
            value (list): The new torque data as a list of (offset, RMS current) tuples.
        """
        self.setParameter("TorqueData", value)
        self.torqueDataChanged.emit(value)

    TorqueData = QtCore.Property(list, get_torque_data, set_torque_data)
    """Qt Property for accessing and setting the torque data."""

    def get_torque_center(self) -> float:
        """
        Get the current torque center value.

        Returns:
            float: The torque center value.
        """
        return self.getParameter("TorqueCenter", 0.0)

    def set_torque_center(self, value: float):
        """
        Set the torque center value and emit the torqueCenterChanged signal.

        Args:
            value (float): The new torque center value.
        """
        self.setParameter("TorqueCenter", value)
        self.torqueCenterChanged.emit(value)

    TorqueCenter = QtCore.Property(float, get_torque_center, set_torque_center)
    """Qt Property for accessing and setting the torque center value."""

    
    def analyzeResults(self, serial_number: str):
        """
        Analyze the test results for a given serial number.

        Determines the torque center by finding the offset with the minimum RMS current.
        Sets the test status to "Pass" if the absolute value of the torque center is less than the tolerance.

        Args:
            serial_number (str): The serial number of the device under test.

        Returns:
            bool: True if the test passes, False otherwise.
        """
        super().analyzeResults(serial_number)
        if self.TorqueData:
            self.TorqueCenter = min(self.TorqueData, key=lambda x: x[1])[0]
        else:
            self.TorqueCenter = 0.0
        self.Status = "Pass" if abs(self.TorqueCenter) < self.centerTolerance else "Fail"
        return self.Status == "Pass"

    def onSettingsModified(self):
        """
        Handle modifications to the test settings.
        Loads settings for read delay, center tolerance, chart titles, and axis ranges.
        """
        super().onSettingsModified()
        self.readDelay = self.getSetting("ReadDelay", 0.2)
        self.centerTolerance = self.getSetting("CenterTolerance", 1.0)
        self.charttitle = self.getSetting("ChartTitle", "Torque Center Plot")
        self.xtitle = self.getSetting("PositionTitle", "Position (deg)")
        self.xmin = self.getSetting("PositionMinimum", -30.0)
        self.xmax = self.getSetting("PositionMaximum", 30.0)
        self.ytitle = self.getSetting("TorqueCurrentTitle", "RMS Current (mA)")
        self.ymin = self.getSetting("TorqueCurrentMinimum", 0)
        self.ymax = self.getSetting("TorqueCurrentMaximum", 500.0)

    
    def setupUi(self, widget: QtWidgets.QWidget):
        """
        Initialize and configure the UI components for displaying the torque center plot and value.

        Args:
            widget (QtWidgets.QWidget): The parent widget to which the UI components will be added.
        """
        super().setupUi(widget)
        chart = QtCharts.QChart()
        chart.setObjectName("chartTorqueCenter")
        line_series = QtCharts.QLineSeries()
        line_series.setObjectName("lineSeriesTorqueCenter")
        line_series.replace(self.TorqueData)
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

        chart_view = QtCharts.QChartView(chart, widget)
        chart_view.setObjectName("chartViewTorqueCenter")
        chart_view.setWindowTitle(self.charttitle)
        chart_view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        layout_test_data = getattr(self, "layoutTestData", None)
        if layout_test_data is not None:
            layout_test_data.addWidget(chart_view)
        else:
            layout = widget.layout() or QtWidgets.QVBoxLayout(widget)
            widget.setLayout(layout)
            layout.addWidget(chart_view)

        self.torqueDataChanged.connect(line_series.replace)

        self.chartTorqueCenter = chart
        self.lineSeriesTorqueCenter = line_series
        self.axisX = axis_x
        self.axisY = axis_y
        self.chartViewTorqueCenter = chart_view

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

    
    def onGenerateReport(self, report):
        """
        Generate a report section for the torque center test, including a torque plot and value.

        Args:
            report: The report object to which the plot and value will be added.
        """
        super().onGenerateReport(report)
        report.plotXYData(
            self.TorqueData,
            self.charttitle,
            self.xtitle,
            self.ytitle,
            str(self.figurePath),
            xmin=self.xmin,
            xmax=self.xmax,
            ymin=self.ymin,
            ymax=self.ymax,
            yTickCount=8,
        )
        report.writeLine(f"Torque Center: {self.TorqueCenter:.2f} deg")

    
    def onSave(self):
        """
        Save the torque data to a CSV file using Qt's QFile and QTextStream.

        Returns:
            Any: The result of the save operation from the base class.
        """
        try:
            file = QtCore.QFile(self.dataFilePath)
            if file.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
                stream = QtCore.QTextStream(file)
                stream << f"Time (ns),{self.xtitle},{self.ytitle}\n"
                for _time, _data in enumerate(self.TorqueData):
                    stream << f"{_time},{_data[0]},{_data[1]}\n"
                file.close()
        except Exception:
            pass
        return super().onSave()

    def resetParameters(self):
        super().resetParameters()
        self.TorqueData = []
        self.TorqueCenter = 0.0

    
    def run(self, serial_number, devices):
        """
        Run the torque center test by iteratively adjusting the source offset and collecting RMS measurements.

        Args:
            serial_number (str): The serial number of the device under test.
            devices: An object providing access to connected devices, including the MSO5000.
        """
        super().run(serial_number, devices)
        mso = devices.MSO5000
        mso.function_generator_state(1, True)
        mso.run()
        _data = []
        for i in range(-25, 26):
            _offset = i / 10
            mso.set_source_offset(1, _offset)
            time.sleep(self.readDelay)
            try:
                _rms = mso.get_measure_item(
                    MSO5000.Measurement.VoltageRms, MSO5000.Source.Channel2
                )
                _data.append((_offset * 4.5, _rms * 100))
            except Exception:
                pass
        self.TorqueData = _data
        mso.function_generator_state(1, False)

    
    def setup(self, serial_number, devices):
        """
        Set up the test environment for the torque center test using the provided serial number and devices.

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
            frequency=5,
            amplitude=0.5,
            output_impedance=MSO5000.SourceOutputImpedance.Fifty,
        )
        mso.channel_settings(1, display=False)
        mso.channel_settings(
            2, scale=2, display=True, bandwidth_limit=MSO5000.BandwidthLimit._20M
        )
        mso.set_measure_item(
            MSO5000.Measurement.VoltageRms, MSO5000.Source.Channel2
        )

    
    def setDataDirectory(self, root_directory):
        """
        Set the root directory for data storage and update internal paths for figure and data files.

        Args:
            root_directory (str): The root directory where data should be stored.
        """
        super().setDataDirectory(root_directory)
        dir_obj = QtCore.QDir(self.dataDirectory)
        if not dir_obj.exists():
            dir_obj.mkpath(".")
        self.figurePath = dir_obj.filePath("torque_plot.png")
        self.dataFilePath = dir_obj.filePath("torque_center_data.csv")

    
    def teardown(self, devices):
        """
        Tear down the test environment and perform any necessary cleanup.

        Args:
            devices: An object containing device interfaces.
        """
        super().teardown(devices)
