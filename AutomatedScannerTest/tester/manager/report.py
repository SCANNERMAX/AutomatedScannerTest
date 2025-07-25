#-*- coding: utf-8 -*-
from PySide6 import QtCharts, QtCore, QtGui, QtWidgets
import math

import tester
import tester.asset.tester_rc


class TestReport:
    """
    TestReport generates a PDF report for test results, including formatted pages, headers, footers, and graphical data.

    This class uses Qt's PDF and painting APIs to create professional test reports with customizable fonts, page decorations, and embedded images or plots. It supports multi-page reports with automatic page numbering, company branding, and test metadata. The report can include a title page, test sections, blank pages for formatting, and XY data plots.

    Attributes:
        pageSize (QtGui.QPageSize.PageSizeId): The size of the PDF pages (default: Letter).
        resolution (int): The resolution of the PDF pages in DPI (default: 300).
        rect (QtCore.QRect): The current drawing rectangle for content.
        pageNumber (int): The current page number in the report.
        fontMetrics (QtGui.QFontMetrics): The metrics of the current font for layout calculations.

    Methods:
        __init__(path: str):
            Initializes the TestReport object, sets up the PDF writer and painter, and prepares the report for content generation.
        finish():
            Finalizes the PDF report, ensuring an even number of pages and closing the painter.
        setFont(family: str = "Helvetica", pointSize: int = 10, bold: bool = False, italic: bool = False, underline: bool = False, strikeOut: bool = False):
            Sets the font properties for the painter.
        writeLine(text: str = "", pointSize: int = 10, bold: bool = False, italic: bool = False, underline: bool = False, strikeOut: bool = False, halign: QtCore.Qt.AlignmentFlag = QtCore.Qt.AlignmentFlag.AlignLeft):
            Writes a line of text to the PDF with specified formatting and alignment.
        newPage():
            Starts a new page, draws headers, footers, and page decorations, and updates the drawing rectangle.
        titlePage(serial_number: str, model_name: str, date: str, start_time: str, end_time: str, duration: str, tester_name: str, computer_name: str, status: str):
            Creates a formatted title page with test and device metadata.
        blankPage():
            Inserts a new blank page with a centered message indicating intentional blankness.
        startTest(name: str, serial_number: str, start_time: str, end_time: str, duration: str, status: str):
            Starts a new test section, adding test metadata and formatting the page.
        plotXYData(data: list, title: str, xlabel: str, ylabel: str, path: str):
            Plots XY data, saves the plot as a PNG, and inserts it into the PDF report.

    Usage:
        report = TestReport("output.pdf")
        report.titlePage(...)
        report.startTest(...)
        report.writeLine(...)
        report.plotXYData(...)
        report.finish()
    """

    pageSize = QtGui.QPageSize.PageSizeId.Letter
    resolution = 300

    def __init__(self, path: str):
        """
        Initialize the TestReport object.

        Args:
            path (str): The file path for the output PDF report.
        """
        self.writer = QtGui.QPdfWriter(path)
        self.writer.setPageSize(self.pageSize)
        self.writer.setResolution(self.resolution)
        self.painter = QtGui.QPainter(self.writer)
        self.buffer = self._convertInches(0.05)
        self.margin = self._convertInches(0.5)
        self.header_height = self._convertInches(1)
        self.footer_height = self._convertInches(1 / 3)

    @tester._member_logger
    def _convertInches(self, inches: float) -> int:
        """
        Convert inches to pixels based on the report's resolution.

        Args:
            inches (float): The value in inches.

        Returns:
            int: The value in pixels.
        """
        return int(inches * self.resolution)

    @tester._member_logger
    def _insertBlankSpace(self, inches: float) -> None:
        """
        Insert blank vertical space in the current drawing rectangle.

        Args:
            inches (float): The height of the blank space in inches.
        """
        self.rect.adjust(0, self._convertInches(inches), 0, 0)

    @tester._member_logger
    def finish(self) -> None:
        """
        Finalize the PDF report.

        Ensures the report has an even number of pages and closes the painter.
        """
        if getattr(self, "pageNumber", 1) % 2 == 1:
            self.blankPage()
        self.painter.end()

    @tester._member_logger
    def setFont(
        self,
        family: str = "Helvetica",
        pointSize: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikeOut: bool = False,
    ) -> None:
        """
        Set the font properties for the painter.

        Args:
            family (str): Font family name.
            pointSize (int): Font size in points.
            bold (bool): Whether the font is bold.
            italic (bool): Whether the font is italic.
            underline (bool): Whether the font is underlined.
            strikeOut (bool): Whether the font is struck out.
        """
        # Cache font objects to avoid redundant creation
        if not hasattr(self, "_font_cache"):
            self._font_cache = {}
        key = (family, pointSize, bold, italic, underline, strikeOut)
        font = self._font_cache.get(key)
        if font is None:
            font = QtGui.QFont(family, pointSize)
            font.setBold(bold)
            font.setItalic(italic)
            font.setUnderline(underline)
            font.setStrikeOut(strikeOut)
            self._font_cache[key] = font
        self.painter.setFont(font)
        self.fontMetrics = self.painter.fontMetrics()

    @tester._member_logger
    def writeLine(
        self,
        text: str = "",
        pointSize: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikeOut: bool = False,
        halign: QtCore.Qt.AlignmentFlag = QtCore.Qt.AlignmentFlag.AlignLeft,
    ) -> None:
        """
        Write a line of text to the PDF with specified formatting and alignment.

        Args:
            text (str): The text to write.
            pointSize (int): Font size in points.
            bold (bool): Whether the font is bold.
            italic (bool): Whether the font is italic.
            underline (bool): Whether the font is underlined.
            strikeOut (bool): Whether the font is struck out.
            halign (QtCore.Qt.AlignmentFlag): Horizontal alignment for the text.
        """
        self.setFont(
            pointSize=pointSize,
            bold=bold,
            italic=italic,
            underline=underline,
            strikeOut=strikeOut,
        )
        _text_height = self.fontMetrics.height()
        if _text_height > self.rect.height():
            self.newPage()
        self.painter.drawText(
            self.rect,
            text,
            QtGui.QTextOption(halign | QtCore.Qt.AlignmentFlag.AlignTop),
        )
        self.rect.adjust(0, _text_height, 0, 0)

    @tester._member_logger
    def newPage(self) -> None:
        """
        Start a new page in the PDF report.

        Draws headers, footers, and page decorations, and updates the drawing rectangle.
        """
        if not hasattr(self, "pageNumber"):
            self.pageNumber = 1
        else:
            self.pageNumber += 1
            self.writer.newPage()

        self.rect = self.painter.window()
        self.rect.adjust(
            self.margin, self.margin, -self.margin, -self.margin
        )
        _header = QtCore.QRect(
            self.rect.left(), self.rect.top(), self.rect.width(), self.header_height
        )
        _footer = QtCore.QRect(
            self.rect.left(),
            self.rect.bottom() - self.footer_height,
            self.rect.width(),
            self.footer_height,
        )
        self.rect.adjust(
            0, self.header_height + self.buffer, 0, -self.footer_height - self.buffer
        )

        # Draw a box around the header
        self.painter.setPen(QtGui.QPen(QtCore.Qt.black, 5))
        self.painter.drawRect(_header)
        _header.adjust(self.buffer, self.buffer, -self.buffer, -self.buffer)

        # Draw logo only if resource exists
        _logo_path = ":/rsc/logo.png"
        _logo_image = QtGui.QImage(_logo_path)
        if not _logo_image.isNull():
            _scaled_logo = _logo_image.scaledToHeight(
                int(_header.height() / 2),
                QtCore.Qt.SmoothTransformation,
            )
            _logo_top = _header.top() + (_header.height() - _scaled_logo.height()) / 2
            self.painter.drawImage(_header.left(), int(_logo_top), _scaled_logo)

        # Application title
        _app_title = getattr(tester, "__application__", "Application")
        self.setFont(pointSize=16, bold=True)
        self.painter.drawText(
            _header,
            _app_title,
            QtGui.QTextOption(
                QtCore.Qt.AlignmentFlag.AlignCenter
                | QtCore.Qt.AlignmentFlag.AlignBottom
            ),
        )

        # Footer
        self.setFont(pointSize=9)
        self.painter.drawText(
            _footer,
            f"Page {self.pageNumber}",
            QtGui.QTextOption(
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignBottom
            ),
        )
        self.painter.drawText(
            _footer,
            getattr(tester, "__company__", "Company"),
            QtGui.QTextOption(
                QtCore.Qt.AlignmentFlag.AlignCenter
                | QtCore.Qt.AlignmentFlag.AlignBottom
            ),
        )

        self.painter.setPen(QtGui.QPen(QtCore.Qt.black, 2.0))
        self.painter.drawLine(
            QtCore.QLine(
                _footer.left(),
                _footer.top(),
                _footer.right(),
                _footer.top(),
            )
        )

    @tester._member_logger
    def titlePage(
        self,
        serial_number: str,
        model_name: str,
        date: str,
        start_time: str,
        end_time: str,
        duration: str,
        tester_name: str,
        computer_name: str,
        status: str,
    ) -> None:
        """
        Create a formatted title page with test and device metadata.

        Args:
            serial_number (str): Device serial number.
            model_name (str): Device model name.
            date (str): Test date.
            start_time (str): Test start time.
            end_time (str): Test end time.
            duration (str): Test duration.
            tester_name (str): Name of the tester.
            computer_name (str): Name of the test computer.
            status (str): Test status.
        """
        self.newPage()
        self._insertBlankSpace(1)
        self.writeLine(
            "Test Report",
            pointSize=24,
            bold=True,
            halign=QtCore.Qt.AlignmentFlag.AlignHCenter,
        )
        self.writeLine()
        self.writeLine(
            "This report contains the results of the tests performed.",
            pointSize=12,
            halign=QtCore.Qt.AlignmentFlag.AlignHCenter,
        )
        self._insertBlankSpace(0.75)
        for label, value in [
            ("Serial Number", serial_number),
            ("Model Name", model_name),
            ("Date", date),
            ("Start Time", start_time),
            ("End Time", end_time),
            ("Duration", duration),
            ("Tester", tester_name),
            ("Computer", computer_name),
            ("Status", status),
        ]:
            self.writeLine(f"{label}: {value}", pointSize=12, bold=True)

    @tester._member_logger
    def blankPage(self) -> None:
        """
        Insert a new blank page with a centered message indicating intentional blankness.
        """
        self.newPage()
        self.setFont()
        _text_opt = QtGui.QTextOption(QtCore.Qt.AlignCenter)
        self.painter.drawText(
            self.rect, "This page intentionally left blank", _text_opt
        )

    @tester._member_logger
    def startTest(
        self,
        name: str,
        serial_number: str,
        start_time: str,
        end_time: str,
        duration: str,
        status: str,
    ):
        """
        Start a new test section, adding test metadata and formatting the page.

        Args:
            name (str): Test name.
            serial_number (str): Device serial number.
            start_time (str): Test start time.
            end_time (str): Test end time.
            duration (str): Test duration.
            status (str): Test status.
        """
        if getattr(self, "pageNumber", 1) % 2 == 1:
            self.blankPage()
        self.newPage()
        self.writeLine(
            name, pointSize=14, bold=True, halign=QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        self.writeLine()
        for label, value in [
            ("Serial Number", serial_number),
            ("Start Time", start_time),
            ("End Time", end_time),
            ("Duration", duration),
            ("Status", status),
        ]:
            self.writeLine(f"{label}: {value}")
        self.writeLine()
        self.writeLine("Results", pointSize=12, bold=True)
        self.writeLine()

    @tester._member_logger
    def plotXYData(
        self,
        data: list,
        title: str,
        xlabel: str,
        ylabel: str,
        path: str,
        xmin: float = -30,
        xmax: float = 30,
        xTickCount: int = 7,
        ymin: float = -100,
        ymax: float = 100,
        yTickCount=21,
    ):
        """
        Plot XY data, save the plot as a PNG, and insert it into the PDF report.

        Args:
            data (list): List of (x, y) tuples for the plot.
            title (str): Plot title.
            xlabel (str): X-axis label.
            ylabel (str): Y-axis label.
            path (str): File path to save the plot image.
            xmin (float): Minimum X-axis value.
            xmax (float): Maximum X-axis value.
            xTickCount (int): Number of X-axis ticks.
            ymin (float): Minimum Y-axis value.
            ymax (float): Maximum Y-axis value.
            yTickCount (int): Number of Y-axis ticks.
        """
        if not data:
            return

        _width = self.rect.width()
        _height = int(0.75 * _width)
        if _height > self.rect.height():
            self.newPage()

        # Prepare the series efficiently
        _series = QtCharts.QLineSeries()
        _series.append([QtCore.QPointF(float(x), float(y)) for x, y in data])
        _series.setPen(QtGui.QPen(QtCore.Qt.blue, 4))

        # Create chart and configure
        _chart = QtCharts.QChart()
        _chart.addSeries(_series)
        _chart.setTitle(title)
        _chart.createDefaultAxes()
        _chart.axisX().setTitleText(xlabel)
        _chart.axisY().setTitleText(ylabel)
        _chart.legend().hide()
        _chart.setBackgroundVisible(False)
        _chart.setBackgroundRoundness(0)

        # Set font only once
        self.setFont()
        _font = self.painter.font()
        for axis in (_chart.axisX(), _chart.axisY()):
            axis.setTitleFont(_font)
            axis.setLabelsFont(_font)
        _chart.setFont(_font)
        _chart.setTitleFont(_font)
        _chart.axisX().setGridLinePen(
            QtGui.QPen(QtCore.Qt.lightGray, 3, QtCore.Qt.PenStyle.DotLine)
        )
        _chart.axisY().setGridLinePen(
            QtGui.QPen(QtCore.Qt.lightGray, 3, QtCore.Qt.PenStyle.DotLine)
        )
        _chart.axisX().setLinePen(QtGui.QPen(QtCore.Qt.black, 5))
        _chart.axisY().setLinePen(QtGui.QPen(QtCore.Qt.black, 5))

        _chart.axisX().setRange(xmin, xmax)
        _chart.axisX().setTickCount(xTickCount)
        _chart.axisY().setRange(ymin, ymax)
        _chart.axisY().setTickCount(yTickCount)

        _chart.resize(_width, _height)

        # Use QGraphicsScene only once for rendering
        _scene = QtWidgets.QGraphicsScene()
        _scene.addItem(_chart)
        _scene.setSceneRect(0, 0, _width, _height)

        _image = QtGui.QImage(_width, _height, QtGui.QImage.Format_ARGB32)
        _image.fill(QtCore.Qt.white)
        _painter = QtGui.QPainter(_image)
        _scene.render(_painter, QtCore.QRectF(0, 0, _width, _height))
        _painter.end()
        _image.save(path, None, -1)

        _target_rect = QtCore.QRectF(self.rect.left(), self.rect.top(), _width, _height)
        self.painter.drawImage(_target_rect, _image)
        self.rect.adjust(0, _height + self._convertInches(0.05), 0, 0)
