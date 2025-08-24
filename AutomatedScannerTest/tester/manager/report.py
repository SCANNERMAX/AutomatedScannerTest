# -*- coding: utf-8 -*-
from PySide6 import QtCharts, QtCore, QtGui, QtWidgets
import logging

# Configure Python logging
logger = logging.getLogger(__name__)

QPageSizeMap = {QtGui.QPageSize.PageSizeId(s).name : QtGui.QPageSize(s) for s in QtGui.QPageSize.PageSizeId}

class TestReport(QtCore.QObject):
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
        logger.debug(f"[TestReport] __init__ called with path: {path}")
        super().__init__()
        app = QtCore.QCoreApplication.instance()
        if not (app and hasattr(app, "addSettingsToObject")):
            logger.critical(
                f"[TestReport] TesterApp instance not found. Ensure the application is initialized correctly."
            )
            raise RuntimeError(
                "TesterApp instance not found. Ensure the application is initialized correctly."
            )
        app.addSettingsToObject(self)
        self.appName = app.applicationName()
        self.company = app.organizationName()
        logger.debug(f"[TestReport] Settings initialized.")

        parent_dir = QtCore.QFileInfo(path).dir()
        logger.debug(f"[TestReport] Checking if parent directory exists: {parent_dir.absolutePath()}")
        if not parent_dir.exists():
            logger.debug(f"[TestReport] Parent directory does not exist. Creating...")
            parent_dir.mkpath(".")
        self.writer = QtGui.QPdfWriter(path)
        logger.debug(f"[TestReport] QPdfWriter created for path: {path}")
        self.writer.setPageSize(self.pageSize)
        self.writer.setResolution(self.resolution)
        self.painter = QtGui.QPainter(self.writer)
        self.painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.rect = QtCore.QRect(self.painter.window())
        self.pageNumber = 0
        self._font_cache = {}
        logger.debug(f"[TestReport] PDF writer initialized at {path}.")

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

    def finish(self) -> None:
        """
        Finalize the PDF report, add a blank page if needed, and end the painter.
        """
        logger.debug(f"[TestReport] finish called. Current pageNumber: {self.pageNumber}")
        if self.pageNumber % 2 == 1:
            logger.debug(f"[TestReport] Odd page number detected. Inserting blank page.")
            self.blankPage()
        self.painter.end()
        logger.debug(f"[TestReport] PDF report finished and painter ended.")

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
        logger.debug(
            f"[TestReport] titlePage called with serial_number={serial_number}, model_name={model_name}, "
            f"date={date}, start_time={start_time}, end_time={end_time}, duration={duration}, "
            f"tester_name={tester_name}, computer_name={computer_name}, status={status}"
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

    def plotXYData(self, data: list, title: str, xlabel: str, ylabel: str,
                   path: str, xmin: float = -30, xmax: float = 30,
                   xTickCount: int = 7, ymin: float = -100, ymax: float = 100,
                   yTickCount=21, series_colors=None, series_labels=None):
        # Ensure __plotXYData runs in the main GUI thread using QMetaObject.invokeMethod
        QtCore.QMetaObject.invokeMethod(
            self,
            "_plotXYDataSlot",
            QtCore.Qt.ConnectionType.QueuedConnection,
            QtCore.Q_ARG(list, data),
            QtCore.Q_ARG(str, title),
            QtCore.Q_ARG(str, xlabel),
            QtCore.Q_ARG(str, ylabel),
            QtCore.Q_ARG(str, path),
            QtCore.Q_ARG(float, xmin),
            QtCore.Q_ARG(float, xmax),
            QtCore.Q_ARG(int, xTickCount),
            QtCore.Q_ARG(float, ymin),
            QtCore.Q_ARG(float, ymax),
            QtCore.Q_ARG(int, yTickCount),
            QtCore.Q_ARG(object, series_colors),
            QtCore.Q_ARG(object, series_labels)
        )

