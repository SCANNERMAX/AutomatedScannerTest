# -*- coding: utf-8 -*-
from PySide6 import QtCharts, QtCore, QtGui, QtWidgets


class TestReport:
    """
    Generates a PDF report for test results, including formatted pages, headers, footers, and graphical data.

    Attributes:
        __settings: The application settings object.
        appName (str): The application name.
        company (str): The company name.
        writer (QtGui.QPdfWriter): The PDF writer object.
        painter (QtGui.QPainter): The painter for drawing on the PDF.
        pageSize (QtGui.QPageSize): The page size for the PDF.
        resolution (int): The DPI resolution for the PDF.
        buffer (int): The buffer space in pixels.
        margin (int): The margin in pixels.
        header_height (int): The header height in pixels.
        footer_height (int): The footer height in pixels.
        fontMetrics (QtGui.QFontMetrics): The current font metrics.
        rect (QtCore.QRect): The current drawing rectangle.
        pageNumber (int): The current page number.
    """

    def __init__(self, path: str):
        """
        Initialize the TestReport object, set up PDF writer, painter, and settings.

        Args:
            path (str): The file path for the PDF report.

        Raises:
            RuntimeError: If not running inside a TesterApp instance.
        """
        app = QtCore.QCoreApplication.instance()
        if app is not None and app.__class__.__name__ == "TesterApp":
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
            self.appName = app.applicationName()
            self.company = app.companyName()
            QtCore.qInfo("[TestReport] Settings initialized.")
        else:
            QtCore.qCritical(
                "[TestReport] TesterApp instance not found. Ensure the application is initialized correctly."
            )
            raise RuntimeError(
                "TesterApp instance not found. Ensure the application is initialized correctly."
            )

        # Ensure parent directory exists using QDir
        parent_dir = QtCore.QFileInfo(path).dir()
        if not parent_dir.exists():
            parent_dir.mkpath(".")
        self.writer = QtGui.QPdfWriter(path)
        self.writer.setPageSize(self.pageSize)
        self.writer.setResolution(self.resolution)
        self.painter = QtGui.QPainter(self.writer)
        self.painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        QtCore.qInfo(f"[TestReport] PDF writer initialized at {path}.")

    def onSettingsModified(self) -> None:
        """
        Update page and layout settings from the application settings.
        """
        s = self.__settings
        cls = self.__class__.__name__
        _size = s.getSetting(cls, "PageSize", "Letter")
        _pageWidth = s.getSetting(cls, "PageWidth", 8.5)
        _pageHeight = s.getSetting(cls, "PageHeight", 11)
        self.resolution = s.getSetting(cls, "Resolution", 300)
        self.buffer = self.convertInches(s.getSetting(cls, "Buffer", 0.05))
        self.margin = self.convertInches(s.getSetting(cls, "Margin", 0.5))
        self.header_height = self.convertInches(s.getSetting(cls, "HeaderHeight", 1))
        self.footer_height = self.convertInches(s.getSetting(cls, "FooterHeight", 0.33))
        if _size == "Custom":
            self.pageSize = QtGui.QPageSize(
                QtCore.QSizeF(_pageWidth, _pageHeight), QtGui.QPageSize.Unit.Inch
            )
        else:
            self.pageSize = QtGui.QPageSize(QtGui.QPageSize.id(_size))
        QtCore.qInfo("[TestReport] Settings modified and page parameters updated.")

    def convertInches(self, inches: float) -> int:
        """
        Convert inches to pixels based on the current resolution.

        Args:
            inches (float): The value in inches.

        Returns:
            int: The value in pixels.
        """
        return int(inches * self.resolution)

    def insertBlankSpace(self, inches: float) -> None:
        """
        Insert blank vertical space in the current drawing rectangle.

        Args:
            inches (float): The height of the blank space in inches.
        """
        self.rect.adjust(0, self.convertInches(inches), 0, 0)

    def finish(self) -> None:
        """
        Finalize the PDF report, add a blank page if needed, and end the painter.
        """
        if getattr(self, "pageNumber", 1) % 2 == 1:
            self.blankPage()
        self.painter.end()
        QtCore.qInfo("[TestReport] PDF report finished and painter ended.")

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
        Set the font for the painter, using a cache for efficiency.

        Args:
            family (str): Font family.
            pointSize (int): Font size in points.
            bold (bool): Bold style.
            italic (bool): Italic style.
            underline (bool): Underline style.
            strikeOut (bool): Strikeout style.
        """
        cache = getattr(self, "_font_cache", None)
        if cache is None:
            cache = {}
            self._font_cache = cache
        key = (family, pointSize, bold, italic, underline, strikeOut)
        font = cache.get(key)
        if font is None:
            font = QtGui.QFont(family, pointSize)
            font.setBold(bold)
            font.setItalic(italic)
            font.setUnderline(underline)
            font.setStrikeOut(strikeOut)
            cache[key] = font
        self.painter.setFont(font)
        self.fontMetrics = self.painter.fontMetrics()
        QtCore.qDebug(f"[TestReport] Font set: {key}")

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
        Write a line of text to the PDF at the current position.

        Args:
            text (str): The text to write.
            pointSize (int): Font size in points.
            bold (bool): Bold style.
            italic (bool): Italic style.
            underline (bool): Underline style.
            strikeOut (bool): Strikeout style.
            halign (QtCore.Qt.AlignmentFlag): Horizontal alignment.
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
        QtCore.qDebug(f"[TestReport] Wrote line: '{text}'")

    def newPage(self) -> None:
        """
        Start a new page in the PDF, draw header and footer, and update the drawing rectangle.
        """
        if not hasattr(self, "pageNumber"):
            self.pageNumber = 1
        else:
            self.pageNumber += 1
            self.writer.newPage()

        self.rect = QtCore.QRect(self.painter.window())
        self.rect.adjust(self.margin, self.margin, -self.margin, -self.margin)
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

        self.painter.setPen(QtGui.QPen(QtCore.Qt.black, 5))
        self.painter.drawRect(_header)
        _header.adjust(self.buffer, self.buffer, -self.buffer, -self.buffer)

        _logo_path = ":/rsc/logo.png"
        _logo_image = QtGui.QImage(_logo_path)
        if not _logo_image.isNull():
            _scaled_logo = _logo_image.scaledToHeight(
                int(_header.height() / 2), QtCore.Qt.SmoothTransformation
            )
            _logo_top = _header.top() + (_header.height() - _scaled_logo.height()) // 2
            self.painter.drawImage(_header.left(), int(_logo_top), _scaled_logo)

        self.setFont(pointSize=16, bold=True)
        self.painter.drawText(
            _header,
            self.appName,
            QtGui.QTextOption(
                QtCore.Qt.AlignmentFlag.AlignCenter
                | QtCore.Qt.AlignmentFlag.AlignBottom
            ),
        )

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
            self.company,
            QtGui.QTextOption(
                QtCore.Qt.AlignmentFlag.AlignCenter
                | QtCore.Qt.AlignmentFlag.AlignBottom
            ),
        )

        self.painter.setPen(QtGui.QPen(QtCore.Qt.black, 2.0))
        self.painter.drawLine(
            QtCore.QLine(_footer.left(), _footer.top(), _footer.right(), _footer.top())
        )
        QtCore.qDebug(f"[TestReport] New page created, page number: {self.pageNumber}")

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
        Write the title page of the report with summary information.

        Args:
            serial_number (str): The serial number.
            model_name (str): The model name.
            date (str): The date.
            start_time (str): The start time.
            end_time (str): The end time.
            duration (str): The duration.
            tester_name (str): The tester's name.
            computer_name (str): The computer name.
            status (str): The test status.
        """
        self.newPage()
        self.insertBlankSpace(1)
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
        self.insertBlankSpace(0.75)
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
        QtCore.qInfo("[TestReport] Title page written.")

    def blankPage(self) -> None:
        """
        Add a blank page to the PDF with a centered message.
        """
        self.newPage()
        self.setFont()
        _text_opt = QtGui.QTextOption(QtCore.Qt.AlignCenter)
        self.painter.drawText(
            self.rect, "This page intentionally left blank", _text_opt
        )
        QtCore.qDebug("[TestReport] Blank page inserted.")

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
        Start a new test section in the report, writing test metadata and section headers.

        Args:
            name (str): The test name.
            serial_number (str): The serial number.
            start_time (str): The start time.
            end_time (str): The end time.
            duration (str): The duration.
            status (str): The test status.
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
        QtCore.qInfo(f"[TestReport] Test section started for '{name}'.")

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
        Plot XY data as a chart, save as an image, and embed in the PDF.

        Args:
            data (list): List of (x, y) tuples.
            title (str): Chart title.
            xlabel (str): X-axis label.
            ylabel (str): Y-axis label.
            path (str): Path to save the image.
            xmin (float): Minimum X value.
            xmax (float): Maximum X value.
            xTickCount (int): Number of X ticks.
            ymin (float): Minimum Y value.
            ymax (float): Maximum Y value.
            yTickCount (int): Number of Y ticks.
        """
        if not data:
            QtCore.qWarning("[TestReport] No data provided to plotXYData.")
            return

        _width = int(self.rect.width())
        _height = int(0.75 * _width)
        if _height > self.rect.height():
            self.newPage()

        _series = QtCharts.QLineSeries()
        _series.append([QtCore.QPointF(float(x), float(y)) for x, y in data])
        _series.setPen(QtGui.QPen(QtCore.Qt.blue, 4))

        _chart = QtCharts.QChart()
        _chart.addSeries(_series)
        _chart.setTitle(title)
        _chart.createDefaultAxes()
        _chart.axisX().setTitleText(xlabel)
        _chart.axisY().setTitleText(ylabel)
        _chart.legend().hide()
        _chart.setBackgroundVisible(False)
        _chart.setBackgroundRoundness(0)

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

        _scene = QtWidgets.QGraphicsScene()
        _scene.addItem(_chart)
        _scene.setSceneRect(QtCore.QRectF(0, 0, _width, _height))

        _image = QtGui.QImage(_width, _height, QtGui.QImage.Format_ARGB32)
        _image.fill(QtCore.Qt.white)
        _painter = QtGui.QPainter(_image)
        _scene.render(_painter, QtCore.QRectF(0, 0, _width, _height))
        _painter.end()

        # Ensure parent directory exists using QDir
        parent_dir = QtCore.QFileInfo(path).dir()
        if not parent_dir.exists():
            parent_dir.mkpath(".")
        _image.save(path, None, -1)

        _target_rect = QtCore.QRectF(self.rect.left(), self.rect.top(), _width, _height)
        self.painter.drawImage(_target_rect, _image)
        self.rect.adjust(0, _height + self.buffer, 0, 0)
        QtCore.qInfo(f"[TestReport] XY data plot saved to {path} and drawn in report.")
