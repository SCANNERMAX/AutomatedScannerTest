# -*- coding: utf-8 -*-
from datetime import date
from PySide6 import QtCharts, QtCore, QtGui, QtWidgets
import logging

# Configure Python logging
logger = logging.getLogger(__name__)

QPageSizeMap = {QtGui.QPageSize.PageSizeId(s).name : QtGui.QPageSize(s) for s in QtGui.QPageSize.PageSizeId}

class TestReportGenerator(QtCore.QObject):
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

    tests = {}

    def __init__(self):
        """
        Initialize the TestReport object, set up PDF writer, painter, and settings.

        Args:
            path (str): The file path for the PDF report.

        Raises:
            RuntimeError: If not running inside a TesterApp instance.
        """
        logger.debug(f"[TestReport] __init__ called.")
        super().__init__()
        applicationInstance = QtCore.QCoreApplication.instance()
        if not (applicationInstance and hasattr(applicationInstance, "addSettingsToObject")):
            logger.critical(
                f"[TestReport] TesterApp instance not found. Ensure the application is initialized correctly."
            )
            raise RuntimeError(
                "TesterApp instance not found. Ensure the application is initialized correctly."
            )
        applicationInstance.addSettingsToObject(self)
        self.appName = applicationInstance.applicationName()
        self.company = applicationInstance.organizationName()
        logger.debug(f"[TestReport] Settings initialized.")

    QtCore.Slot()
    def onSettingsModified(self) -> None:
        """
        Update page and layout settings from the application settings.
        """
        logger.debug(f"[TestReport] onSettingsModified called.")
        s = self.getSetting
        _size = s("PageSize", "Letter")
        _pageWidth = s("PageWidth", 8.5)
        _pageHeight = s("PageHeight", 11)
        self.resolution = s("Resolution", 300)
        self.buffer = self.convertInches(s("Buffer", 0.05))
        self.margin = self.convertInches(s("Margin", 0.5))
        self.header_height = self.convertInches(s("HeaderHeight", 1))
        self.footer_height = self.convertInches(s("FooterHeight", 0.33))
        logger.debug(
            f"[TestReport] Settings: size={_size}, pageWidth={_pageWidth}, pag"
            f"eHeight={_pageHeight}, resolution={self.resolution}, buffer="
            f"{self.buffer}, margin={self.margin}, header_height="
            f"{self.header_height}, footer_height={self.footer_height}"
        )
        if _size == "Custom":
            self.pageSize = QtGui.QPageSize(
                QtCore.QSizeF(_pageWidth, _pageHeight), QtGui.QPageSize.Unit.Inch
            )
            logger.debug(f"[TestReport] Custom page size set: {_pageWidth} x {_pageHeight} inches")
        else:
            pageId = QPageSizeMap.get(_size)
            self.pageSize = QtGui.QPageSize(pageId)
            logger.debug(f"[TestReport] Standard page size set: {_size}")
        logger.debug(f"[TestReport] Settings modified and page parameters updated.")

    def generate(self, path: str = None) -> None:
        resolvedPath = QtCore.QFileInfo(path if path else self.filePath).absoluteFilePath()
        parentDir = QtCore.QFileInfo(resolvedPath).dir()
        logger.debug(f"[TestReport] Checking if parent directory exists: {parentDir.absolutePath()}")
        if not parentDir.exists():
            logger.debug(f"[TestReport] Parent directory does not exist. Creating...")
            parentDir.mkpath(".")
        self.writer = QtGui.QPdfWriter(resolvedPath)
        logger.debug(f"[TestReport] QPdfWriter created for path: {path}")
        self.writer.setPageSize(self.pageSize)
        self.writer.setResolution(self.resolution)
        self.painter = QtGui.QPainter(self.writer)
        self.painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.rect = QtCore.QRect(self.painter.window())
        self.pageNumber = 0
        self.fontCache = {}
        self.titlePage()
        for name, data in self.tests.items():
            self.startTest(
                name=name,
                serial_number=data.get("SerialNumber", "Unknown"),
                start_time=data.get("StartTime", "Unknown"),
                end_time=data.get("EndTime", "Unknown"),
                duration=data.get("Duration", "Unknown"),
                status=data.get("Status", "Unknown"),
            )
            for result_name, result_value in data.get("Results", {}).items():
                resultType = result_value.get("Type")
                if resultType == "XYPlot":
                    self.plotXYData(
                        data=result_value.get("Data", []),
                        title=result_value.get("Title", ""),
                        xlabel=result_value.get("XLabel", ""),
                        ylabel=result_value.get("YLabel", ""),
                        path=result_value.get("Path", "plot.png"),
                        xmin=result_value.get("XMin", -30),
                        xmax=result_value.get("XMax", 30),
                        xTickCount=result_value.get("XTickCount", 7),
                        ymin=result_value.get("YMin", -100),
                        ymax=result_value.get("YMax", 100),
                        yTickCount=result_value.get("YTickCount", 21),
                        series_colors=result_value.get("SeriesColors"),
                        series_labels=result_value.get("SeriesLabels"),
                    )
                elif resultType == "Text":
                    self.writeLine(
                        text=result_value.get("Content", ""),
                        pointSize=result_value.get("PointSize", 10),
                        bold=result_value.get("Bold", False),
                        italic=result_value.get("Italic", False),
                        underline=result_value.get("Underline", False),
                        strikeOut=result_value.get("StrikeOut", False),
                        halign=result_value.get("HAlign", QtCore.Qt.AlignmentFlag.AlignLeft),
                    )
        if self.pageNumber % 2 == 1:
            logger.debug(f"[TestReport] Odd page number detected. Inserting blank page.")
            self.blankPage()
        self.painter.end()
    
    def convertInches(self, inches: float) -> int:
        """
        Convert inches to pixels based on the current resolution.

        Args:
            inches (float): The value in inches.

        Returns:
            int: The value in pixels.
        """
        logger.debug(f"[TestReport] convertInches called with inches={inches}")
        result = int(inches * self.resolution)
        logger.debug(f"[TestReport] convertInches result: {result} pixels")
        return result

    def insertBlankSpace(self, inches: float) -> None:
        """
        Insert blank vertical space in the current drawing rectangle.

        Args:
            inches (float): The height of the blank space in inches.
        """
        logger.debug(f"[TestReport] insertBlankSpace called with inches={inches}")
        self.rect.adjust(0, self.convertInches(inches), 0, 0)
        logger.debug(f"[TestReport] Blank space inserted. New rect: {self.rect}")

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
        logger.debug(
            f"setFont called with family={family}, pointSize={pointSize}, bold={bold}, "
            f"italic={italic}, underline={underline}, strikeOut={strikeOut}"
        )
        # Use tuple key for font cache, avoid repeated QFont creation
        key = (family, pointSize, bold, italic, underline, strikeOut)
        font = self.fontCache.get(key)
        if font is None:
            font = QtGui.QFont(family, pointSize)
            font.setBold(bold)
            font.setItalic(italic)
            font.setUnderline(underline)
            font.setStrikeOut(strikeOut)
            self.fontCache[key] = font
        self.painter.setFont(font)
        self.fontMetrics = self.painter.fontMetrics()
        logger.debug(f"[TestReport] Font set: {key}")

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
        logger.debug(
            f"[TestReport] writeLine called with text='{text}', pointSize={pointSize}, bold={bold}, "
            f"italic={italic}, underline={underline}, strikeOut={strikeOut}, halign={halign}"
        )
        self.setFont(
            pointSize=pointSize,
            bold=bold,
            italic=italic,
            underline=underline,
            strikeOut=strikeOut,
        )
        _text_height = self.fontMetrics.height()
        logger.debug(f"[TestReport] Calculated text height: {_text_height}, rect height: {self.rect.height()}")
        if _text_height > self.rect.height():
            logger.debug(f"[TestReport] Not enough space for text. Creating new page.")
            self.newPage()
        self.painter.drawText(
            self.rect,
            text,
            QtGui.QTextOption(halign | QtCore.Qt.AlignmentFlag.AlignTop),
        )
        self.rect.adjust(0, _text_height, 0, 0)
        logger.debug(f"[TestReport] Wrote line: '{text}'. New rect: {self.rect}")

    def newPage(self) -> None:
        """
        Start a new page in the PDF, draw header and footer, and update the drawing rectangle.
        """
        logger.debug(f"[TestReport] newPage called. Current pageNumber: {self.pageNumber}")
        self.pageNumber += 1
        if self.pageNumber > 1:
            logger.debug(f"[TestReport] Adding new page to PDF writer.")
            self.writer.newPage()

        self.rect = QtCore.QRect(self.painter.window())
        self.rect.adjust(self.margin, self.margin, -self.margin, -self.margin)
        logger.debug(f"[TestReport] Page rect after margin adjustment: {self.rect}")
        _header = QtCore.QRect(
            self.rect.left(), self.rect.top(), self.rect.width(), self.header_height
        )
        _footer = QtCore.QRect(
            self.rect.left(),
            self.rect.bottom() - self.footer_height,
            self.rect.width(),
            self.footer_height,
        )
        logger.debug(f"[TestReport] Header rect: {_header}, Footer rect: {_footer}")
        self.rect.adjust(
            0, self.header_height + self.buffer, 0, -self.footer_height - self.buffer
        )
        logger.debug(f"[TestReport] Content rect after header/footer adjustment: {self.rect}")

        self.painter.setPen(QtGui.QPen(QtCore.Qt.black, 5))
        self.painter.drawRect(_header)
        _header.adjust(self.buffer, self.buffer, -self.buffer, -self.buffer)
        logger.debug(f"[TestReport] Header rect after buffer adjustment: {_header}")

        _logo_path = ":/rsc/logo.png"
        _logo_image = QtGui.QImage(_logo_path)
        logger.debug(f"[TestReport] Loading logo image from: {_logo_path}")
        if not _logo_image.isNull():
            logger.debug(f"[TestReport] Logo image loaded successfully.")
            _scaled_logo = _logo_image.scaledToHeight(
                int(_header.height() / 2), QtCore.Qt.SmoothTransformation
            )
            _logo_top = _header.top() + (_header.height() - _scaled_logo.height()) // 2
            self.painter.drawImage(_header.left(), int(_logo_top), _scaled_logo)
            logger.debug(f"[TestReport] Logo drawn at: ({_header.left()}, {_logo_top})")
        else:
            logger.debug(f"[TestReport] Logo image is null. Skipping logo drawing.")

        self.setFont(pointSize=16, bold=True)
        self.painter.drawText(
            _header,
            self.appName,
            QtGui.QTextOption(
                QtCore.Qt.AlignmentFlag.AlignCenter
                | QtCore.Qt.AlignmentFlag.AlignBottom
            ),
        )
        logger.debug(f"[TestReport] App name drawn in header: {self.appName}")

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
        logger.debug(f"[TestReport] Footer drawn with page number and company: {self.company}")

        self.painter.setPen(QtGui.QPen(QtCore.Qt.black, 2.0))
        self.painter.drawLine(
            QtCore.QLine(_footer.left(), _footer.top(), _footer.right(), _footer.top())
        )
        logger.debug(f"[TestReport] Footer line drawn.")
        logger.debug(f"[TestReport] New page created, page number: {self.pageNumber}")

    def titlePage(self) -> None:
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
        logger.debug(
            f"[TestReport] titlePage called."
        )
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
            ("Serial Number", self.serialNumber),
            ("Model Name", self.modelName),
            ("Date", self.testDate),
            ("Start Time", self.startTime),
            ("End Time", self.endTime),
            ("Duration", self.duration),
            ("Tester", self.testerName),
            ("Computer", self.computerName),
            ("Status", self.status),
        ]:
            logger.debug(f"[TestReport] Writing summary line: {label}: {value}")
            self.writeLine(f"{label}: {value}", pointSize=12, bold=True)
        logger.debug(f"[TestReport] Title page written.")

    def blankPage(self) -> None:
        """
        Add a blank page to the PDF with a centered message.
        """
        logger.debug(f"[TestReport] blankPage called.")
        self.newPage()
        self.setFont()
        _text_opt = QtGui.QTextOption(QtCore.Qt.AlignCenter)
        self.painter.drawText(
            self.rect, "This page intentionally left blank", _text_opt
        )
        logger.debug(f"[TestReport] Blank page inserted.")

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
        logger.debug(
            f"[TestReport] startTest called with name={name}, serial_number={serial_number}, "
            f"start_time={start_time}, end_time={end_time}, duration={duration}, status={status}"
        )
        if self.pageNumber % 2 == 1:
            logger.debug(f"[TestReport] Odd page number detected before test section. Inserting blank page.")
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
            logger.debug(f"[TestReport] Writing test metadata line: {label}: {value}")
            self.writeLine(f"{label}: {value}")
        self.writeLine()
        self.writeLine("Results", pointSize=12, bold=True)
        self.writeLine()
        logger.debug(f"[TestReport] Test section started for '{name}'.")

    def textResult(self, name: str, text: str) -> None:
        """
        Write a text result to the report.
        Args:
            text (str): The text result to write.
        """
        logger.debug(f"[TestReport] textResult called with text: {text}")
        self.writeLine(f"{name}: {text}")
        logger.debug(f"[TestReport] Text result written.")

    def plotXYData(self, data: list, title: str, xlabel: str, ylabel: str,
                   path: str, xmin: float = -30, xmax: float = 30,
                   xTickCount: int = 7, ymin: float = -100, ymax: float = 100,
                   yTickCount=21, series_colors=None, series_labels=None):
        """
        Plot one or more XY data series as a chart, save as an image, and embed in the PDF.

        If data is empty, an empty chart with axes and title is created and embedded.

        Args:
            data (list or list of lists): List of (x, y) tuples, or list of such lists for multiple series.
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
            series_colors (list, optional): List of Qt colors for each series.
            series_labels (list, optional): List of labels for each series.

        Returns:
            None
        """
        logger.debug(
            f"[TestReport] plotXYData called with title={title}, xlabel="
            f"{xlabel}, ylabel={ylabel}, path={path}, xmin={xmin}, xmax={xmax}"
            f", xTickCount={xTickCount}, ymin={ymin}, ymax={ymax}, yTickCount="
            f"{yTickCount}"
        )

        # Precompute width/height only once
        _width = int(self.rect.width())
        _height = min(int(0.75 * _width), self.rect.height())
        if _height > self.rect.height():
            self.newPage()

        # Create chart and scene only once
        _chart = QtCharts.QChart()
        _chart.setTitle(title)
        _chart.setBackgroundVisible(False)
        _chart.setBackgroundRoundness(0)
        font = self.painter.font()
        _chart.setFont(font)
        _chart.setTitleFont(font)
        _chart.resize(_width, _height)

        legend = _chart.legend()
        legend.setFont(font)

        def _setup_axis(axis, title, minv, maxv, ticks):
            """
            Configure a QValueAxis with title, range, tick count, font, and pen styles.

            Args:
                axis (QtCharts.QValueAxis): The axis to configure.
                title (str): Axis title.
                minv (float): Minimum value.
                maxv (float): Maximum value.
                ticks (int): Number of ticks.

            Returns:
                None
            """
            axis.setTitleText(title)
            axis.setRange(minv, maxv)
            axis.setTickCount(ticks)
            axis.setTitleFont(font)
            axis.setLabelsFont(font)
            axis.setGridLinePen(QtGui.QPen(QtCore.Qt.lightGray, 3, QtCore.Qt.PenStyle.DotLine))
            axis.setLinePen(QtGui.QPen(QtCore.Qt.black, 5))

        if not data:
            logger.warning(f"[TestReport] No data provided to plotXYData. Creating empty plot.")
            axis_x = QtCharts.QValueAxis()
            axis_y = QtCharts.QValueAxis()
            _setup_axis(axis_x, xlabel, xmin, xmax, xTickCount)
            _setup_axis(axis_y, ylabel, ymin, ymax, yTickCount)
            _chart.addAxis(axis_x, QtCore.Qt.AlignmentFlag.AlignBottom)
            _chart.addAxis(axis_y, QtCore.Qt.AlignmentFlag.AlignLeft)
            legend.hide()
        else:
            is_multi = isinstance(data[0], (list, tuple)) and (
                len(data) > 0 and isinstance(data[0][0], (list, tuple, QtCore.QPointF))
            )
            series_list = data if is_multi else [data]

            default_colors = [
                QtCore.Qt.blue,
                QtCore.Qt.red,
                QtCore.Qt.darkGreen,
                QtCore.Qt.magenta,
                QtCore.Qt.darkYellow,
                QtCore.Qt.darkCyan,
                QtCore.Qt.black,
            ]
            colors = series_colors if series_colors else default_colors
            labels = series_labels if series_labels else [f"Series {i+1}" for i in range(len(series_list))]

            for idx, series_data in enumerate(series_list):
                _series = QtCharts.QLineSeries()
                _series.setName(labels[idx] if idx < len(labels) else f"Series {idx+1}")
                _series.setPen(QtGui.QPen(colors[idx % len(colors)], 4))
                if series_data and isinstance(series_data[0], QtCore.QPointF):
                    _series.append(series_data)
                else:
                    # Use generator expression for better memory efficiency
                    _series.append((QtCore.QPointF(float(x), float(y)) for x, y in series_data))
                _chart.addSeries(_series)

            _chart.createDefaultAxes()
            for axis in (_chart.axisX(), _chart.axisY()):
                axis.setTitleFont(font)
                axis.setLabelsFont(font)
            _chart.axisX().setTitleText(xlabel)
            _chart.axisY().setTitleText(ylabel)
            _chart.axisX().setGridLinePen(QtGui.QPen(QtCore.Qt.lightGray, 3, QtCore.Qt.PenStyle.DotLine))
            _chart.axisY().setGridLinePen(QtGui.QPen(QtCore.Qt.lightGray, 3, QtCore.Qt.PenStyle.DotLine))
            _chart.axisX().setLinePen(QtGui.QPen(QtCore.Qt.black, 5))
            _chart.axisY().setLinePen(QtGui.QPen(QtCore.Qt.black, 5))
            _chart.axisX().setRange(xmin, xmax)
            _chart.axisX().setTickCount(xTickCount)
            _chart.axisY().setRange(ymin, ymax)
            _chart.axisY().setTickCount(yTickCount)
            if len(series_list) > 1:
                legend.setVisible(True)
                legend.setAlignment(QtCore.Qt.AlignmentFlag.AlignBottom)
                legend.setFont(font)
            else:
                legend.hide()

        # Use a single QGraphicsScene instance
        _scene = QtWidgets.QGraphicsScene()
        _scene.addItem(_chart)
        _scene.setSceneRect(QtCore.QRectF(0, 0, _width, _height))

        # Use QImage only once, avoid unnecessary fill if default is white
        _image = QtGui.QImage(_width, _height, QtGui.QImage.Format_ARGB32)
        _image.fill(QtCore.Qt.white)
        _painter = QtGui.QPainter(_image)
        _scene.render(_painter, QtCore.QRectF(0, 0, _width, _height))
        _painter.end()

        parent_dir = QtCore.QFileInfo(path).dir()
        if not parent_dir.exists():
            parent_dir.mkpath(".")
        _image.save(path, None, -1)

        _target_rect = QtCore.QRectF(self.rect.left(), self.rect.top(), _width, _height)
        self.painter.drawImage(_target_rect, _image)
        self.rect.adjust(0, _height + self.buffer, 0, 0)
        logger.debug(f"[TestReport] XY data plot saved to {path} and drawn in report.")

    @QtCore.Slot(str, str, str)
    def onTestInfoChanged(self, test_name: str, info_name: str, value: str) -> None:
        """
        Slot to handle changes to test information.
        Args:
            name (str): The test name.
            info (str): The test information.
        """
        logger.debug(f"[TestReport] onTestInfoChanged called with test_name={test_name}, info_name={info_name}, value={value}")
        if test_name not in self.tests:
            self.tests[test_name] = {
                "SerialNumber": "",
                "ModelName": "",
                "StartTime": "",
                "EndTime": "",
                "Duration": "",
                "Status": "",
                "Results": {},
            }
        if info_name in ("SerialNumber", "ModelName", "StartTime", "EndTime", "Duration", "Status"):
            self.tests[test_name][info_name] = value
            logger.debug(f"[TestReport] Test '{test_name}' info '{info_name}' updated to: {value}")
        else:
            logger.warning(f"[TestReport] Unknown info name '{info_name}' for test '{test_name}'. No update performed.")

    @QtCore.Slot(str, dict)
    def onTestResultAdded(self, test_name: str, result_name: str, result: dict) -> None:
        """
        Slot to handle adding a test result.
        Args:
            test_name (str): The name of the test.
            result (dict): The result data.
        """
        logger.debug(f"[TestReport] onTestResultAdded called with test_name={test_name}, result_name={result_name}, result={result}")
        if test_name not in self.tests:
            self.tests[test_name] = {
                "SerialNumber": "",
                "ModelName": "",
                "StartTime": "",
                "EndTime": "",
                "Duration": "",
                "Status": "",
                "Results": {},
            }
        self.tests[test_name]["Results"][result_name] = result
