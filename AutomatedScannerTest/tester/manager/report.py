import math
from PySide6 import QtCharts, QtCore, QtGui, QtWidgets

import tester
import tester.asset.tester_rc


class TestReport:
    """
    TestReport generates a PDF report for test results, including formatted pages, headers, footers, and graphical data.
    This class uses Qt's PDF and painting APIs to create professional test reports with customizable fonts, page decorations, and embedded images or plots. It supports multi-page reports with automatic page numbering, company branding, and test metadata. The report can include a title page, test sections, blank pages for formatting, and XY data plots.
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
        setFont(family: str = "Helvitica", pointSize: int = 10, bold: bool = False, italic: bool = False, underline: bool = False, strikeOut: bool = False):
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
        Initializes the TestReport object with the specified file path.
        Args:
            path (str): The file path where the PDF report will be saved.
        Attributes:
            writer (QtGui.QPdfWriter): The PDF writer object used to create the report.
            painter (QtGui.QPainter): The painter object used to draw on the PDF.
            pageSize: The size of the PDF pages (should be set elsewhere in the class).
            resolution: The resolution of the PDF pages (should be set elsewhere in the class).
        Note:
            This constructor initializes the PDF writer and painter, sets the page size and resolution,
            and prepares the report for content generation.
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
        Converts a measurement in inches to pixels based on the report's resolution.

        Args:
            inches (float): The measurement in inches.

        Returns:
            int: The equivalent measurement in pixels.
        """
        return int(inches * self.resolution)

    @tester._member_logger
    def _insertBlankSpace(self, inches: float) -> None:
        """
        Inserts blank vertical space in the current drawing rectangle.

        Args:
            inches (float): The height of the blank space in inches.

        Returns:
            None
        """
        _pixels = self._convertInches(inches)
        self.rect.adjust(0, _pixels, 0, 0)

    @tester._member_logger
    def finish(self) -> None:
        """
        Finalizes the PDF report by ensuring an even number of pages and closing the painter.

        If the current page number is odd, adds a blank page to make the total page count even.
        Ends the painter session to complete and save the PDF report.
        """
        if self.pageNumber % 2 == 1:
            self.blankPage()
        self.painter.end()

    @tester._member_logger
    def setFont(
        self,
        family: str = "Helvitica",
        pointSize: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikeOut: bool = False,
    ) -> None:
        """
        Sets the font properties for the PDF report painter.

        Args:
            family (str, optional): The font family to use. Defaults to "Helvitica".
            pointSize (int, optional): The size of the font in points. Defaults to 10.
            bold (bool, optional): Whether to use a bold font. Defaults to False.
            italic (bool, optional): Whether to use an italic font. Defaults to False.
            underline (bool, optional): Whether to underline the text. Defaults to False.
            strikeOut (bool, optional): Whether to strike out the text. Defaults to False.

        Returns:
            None
        """
        font = QtGui.QFont(family, pointSize)
        font.setBold(bold)
        font.setItalic(italic)
        font.setUnderline(underline)
        font.setStrikeOut(strikeOut)
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
        Writes a line of text to the PDF report with specified formatting options.

        Args:
            text (str, optional): The text to write. Defaults to an empty string.
            pointSize (int, optional): Font size in points. Defaults to 10.
            bold (bool, optional): Whether the text is bold. Defaults to False.
            italic (bool, optional): Whether the text is italicized. Defaults to False.
            underline (bool, optional): Whether the text is underlined. Defaults to False.
            strikeOut (bool, optional): Whether the text has a strikethrough. Defaults to False.
            halign (QtCore.Qt.AlignmentFlag, optional): Horizontal alignment of the text. Defaults to AlignLeft.

        Returns:
            None

        Notes:
            - Automatically moves to a new page if the text does not fit in the current rectangle.
            - Advances the drawing rectangle for subsequent lines.
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
        # Move the rectangle down for the next line
        self.rect.adjust(0, _text_height, 0, 0)

    @tester._member_logger
    def newPage(self) -> None:
        """
        Starts a new page in the PDF report, drawing the header, footer, and page decorations.
        This method:
        - Increments and tracks the current page number.
        - Adjusts the drawing rectangle to account for page margins.
        - Draws a logo image in the upper left corner of the header.
        - Draws the application title centered at the top of the page.
        - Draws the page number at the bottom right of the footer.
        - Draws the company name centered at the bottom of the footer.
        - Draws a horizontal line above the footer.
        Requires that `self.painter`, `self.writer`, and the `tester` module with `__application__` and `__company__` attributes are available.
        """
        # Track page number
        if not hasattr(self, "pageNumber"):
            self.pageNumber = 1
        else:
            self.pageNumber += 1
            self.writer.newPage()

        self.rect = self.painter.window()
        self.rect.adjust(
            self.margin, self.margin, -self.margin, -self.margin
        )  # Adjust margins
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

        # Put logo from resources in the upper left corner of the page
        _logo_path = ":/rsc/logo.png"  # Use Qt resource path
        _logo_image = QtGui.QImage(_logo_path)
        if not _logo_image.isNull():
            # Set desired logo size (e.g., 80x80 pixels)
            _scaled_logo = _logo_image.scaledToHeight(
                _header.height() / 2,
                QtGui.Qt.SmoothTransformation,
            )
            _logo_top = _header.top() + (_header.height() - _scaled_logo.height()) / 2
            self.painter.drawImage(_header.left(), _logo_top, _scaled_logo)

        # Add __application__ to the top center as the title
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
        # Add page number to the bottom right corner
        self.setFont(pointSize=9)
        self.painter.drawText(
            _footer,
            f"Page {self.pageNumber}",
            QtGui.QTextOption(
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignBottom
            ),
        )

        # Add __company__ to the bottom center
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
        Creates a formatted title page for the test report.

        Parameters:
            serial_number (str): The serial number of the device under test.
            model_name (str): The model name of the device.
            date (str): The date when the test was conducted.
            start_time (str): The time when the test started.
            end_time (str): The time when the test ended.
            duration (str): The total duration of the test.
            tester_name (str): The name of the person who performed the test.
            computer_name (str): The name of the computer used for testing.
            status (str): The overall status of the test.

        Returns:
            None
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
        self.writeLine(f"Serial Number: {serial_number}", pointSize=12, bold=True)
        self.writeLine(f"Model Name: {model_name}", pointSize=12, bold=True)
        self.writeLine(f"Date: {date}", pointSize=12, bold=True)
        self.writeLine(f"Start Time: {start_time}", pointSize=12, bold=True)
        self.writeLine(f"End Time: {end_time}", pointSize=12, bold=True)
        self.writeLine(f"Duration: {duration}", pointSize=12, bold=True)
        self.writeLine(f"Tester: {tester_name}", pointSize=12, bold=True)
        self.writeLine(f"Computer: {computer_name}", pointSize=12, bold=True)
        self.writeLine(f"Status: {status}", pointSize=12, bold=True)

    @tester._member_logger
    def blankPage(self) -> None:
        """
        Creates a new blank page in the report with a centered message indicating that the page is intentionally left blank.

        This method initializes a new page, sets the default font, and draws the text
        "This page intentionally left blank" centered on the page.
        """
        self.newPage()
        self.setFont()
        _text_opt = QtGui.QTextOption(QtGui.Qt.AlignCenter)
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
        Starts a new test section in the report, adding test metadata and formatting the page.

        If the current page number is odd, inserts a blank page before starting a new one.
        Writes the test name, serial number, start and end times, duration, and status to the report,
        followed by a "Results" section header.

        Args:
            name (str): The name of the test.
            serial_number (str): The serial number of the device or test subject.
            start_time (str): The start time of the test.
            end_time (str): The end time of the test.
            duration (str): The duration of the test.
            status (str): The status of the test (e.g., "Passed", "Failed").
        """
        # If page number is odd, insert a blank page before continuing
        if self.pageNumber % 2 == 1:
            self.blankPage()
        self.newPage()
        self.writeLine(
            name, pointSize=14, bold=True, halign=QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        self.writeLine()
        self.writeLine(f"Serial Number: {serial_number}")
        self.writeLine(f"Start Time: {start_time}")
        self.writeLine(f"End Time: {end_time}")
        self.writeLine(f"Duration: {duration}")
        self.writeLine(f"Status: {status}")
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
        Plots XY data, saves the plot as a PNG image, and inserts it into a PDF report.
        Args:
            data (list): A list of (x, y) tuples representing the data points to plot.
            title (str): The title of the plot.
            xlabel (str): The label for the x-axis.
            ylabel (str): The label for the y-axis.
            path (str): The file path where the plot image will be saved.
        Returns:
            None
        Notes:
            - If the data list is empty, the function returns without doing anything.
            - The plot is sized based on the current rectangle dimensions.
            - If the plot height exceeds the available space, a new page is started.
            - The generated image is inserted into the PDF and the drawing rectangle is adjusted for subsequent content.
        """
        # Prepare data
        if not data:
            return

        # Create plot and save to file
        _width = self.rect.width()
        _height = int(0.75 * _width)
        if _height > self.rect.height():
            self.newPage()

        # Generate and save plot image using QChart
        # Prepare the series
        _series = QtCharts.QLineSeries()
        for _x_point, _y_point in data:
            _series.append(float(_x_point), float(_y_point))
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

        # Customize the chart appearance
        self.setFont()
        _font = self.painter.font()
        _chart.setFont(_font)
        _chart.setTitleFont(_font)
        _chart.axisX().setTitleFont(_font)
        _chart.axisX().setLabelsFont(_font)
        _chart.axisY().setTitleFont(_font)
        _chart.axisY().setLabelsFont(_font)
        _chart.axisX().setGridLinePen(
            QtGui.QPen(QtCore.Qt.lightGray, 3, QtCore.Qt.PenStyle.DotLine)
        )
        _chart.axisY().setGridLinePen(
            QtGui.QPen(QtCore.Qt.lightGray, 3, QtCore.Qt.PenStyle.DotLine)
        )
        _chart.axisX().setLinePen(QtGui.QPen(QtCore.Qt.black, 5))
        _chart.axisY().setLinePen(QtGui.QPen(QtCore.Qt.black, 5))

        # Set tick count for axes
        _chart.axisX().setRange(xmin, xmax)
        _chart.axisX().setTickCount(xTickCount)
        _chart.axisY().setRange(ymin, ymax)
        _chart.axisY().setTickCount(yTickCount)

        # Set the chart size
        _chart.resize(_width, _height)

        # ... inside plotXYData
        _scene = QtWidgets.QGraphicsScene()
        _scene.addItem(_chart)
        _scene.setSceneRect(0, 0, _width, _height)

        # Render chart directly to QImage
        _image = QtGui.QImage(_width, _height, QtGui.QImage.Format_ARGB32)
        _image.fill(QtCore.Qt.white)
        _painter = QtGui.QPainter(_image)
        _scene.render(_painter, QtCore.QRectF(0, 0, _width, _height))
        _painter.end()

        _painter = QtGui.QPainter(_image)
        _chart.scene().render(_painter, QtCore.QRectF(0, 0, _width, _height))
        _painter.end()
        _image.save(path, None, -1)

        # Center image horizontally
        _target_rect = QtCore.QRectF(self.rect.left(), self.rect.top(), _width, _height)
        self.painter.drawImage(_target_rect, _image)

        # Move rect down for next content
        self.rect.adjust(0, _height + self._convertInches(0.05), 0, 0)
