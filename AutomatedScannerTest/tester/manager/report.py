# -*- coding: utf-8 -*-
from PySide6 import QtCharts, QtCore, QtGui, QtWidgets

import tester
import tester.asset.tester_rc


class TestReport:
    """
    Generates a PDF report for test results, including formatted pages, headers, footers, and graphical data.
    """

    def __init__(self, path: str):
        app = QtCore.QCoreApplication.instance()
        if app.__class__.__name__ == "TesterApp":
            self.__logger = app.get_logger(self.__class__.__name__)
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
        else:
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")

        # Ensure parent directory exists using QDir
        parent_dir = QtCore.QFileInfo(path).dir()
        if not parent_dir.exists():
            parent_dir.mkpath(".")
        self.writer = QtGui.QPdfWriter(path)
        self.writer.setPageSize(self.pageSize)
        self.writer.setResolution(self.resolution)
        self.painter = QtGui.QPainter(self.writer)
        self.painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

    def onSettingsModified(self) -> None:
        _size = self.__settings.getSetting(self.__class__.__name__, "PageSize", "Letter")
        _pageWidth = self.__settings.getSetting(self.__class__.__name__, "PageWidth", 8.5)
        _pageHeight = self.__settings.getSetting(self.__class__.__name__, "PageHeight", 11)
        self.resolution = self.__settings.getSetting(self.__class__.__name__, "Resolution", 300)
        _buffer = self.__settings.getSetting(self.__class__.__name__, "Buffer", 0.05)
        _margin = self.__settings.getSetting(self.__class__.__name__, "Margin", 0.5)
        _header = self.__settings.getSetting(self.__class__.__name__, "HeaderHeight", 1)
        _footer = self.__settings.getSetting(self.__class__.__name__, "FooterHeight", 0.33)
        if _size == "Custom":
            self.pageSize = QtGui.QPageSize(_pageWidth, _pageHeight, QtGui.QPageSize.Unit.Inch)
        else:
            self.pageSize = QtGui.QPageSize.id(_size)
        self.buffer = self.convertInches(_buffer)
        self.margin = self.convertInches(_margin)
        self.header_height = self.convertInches(_header)
        self.footer_height = self.convertInches(_footer)

    
    def convertInches(self, inches: float) -> int:
        return int(inches * self.resolution)

    
    def insertBlankSpace(self, inches: float) -> None:
        self.rect.adjust(0, self.convertInches(inches), 0, 0)

    
    def finish(self) -> None:
        if getattr(self, "pageNumber", 1) % 2 == 1:
            self.blankPage()
        self.painter.end()

    
    def setFont(
        self,
        family: str = "Helvetica",
        pointSize: int = 10,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikeOut: bool = False,
    ) -> None:
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

    
    def newPage(self) -> None:
        if not hasattr(self, "pageNumber"):
            self.pageNumber = 1
        else:
            self.pageNumber += 1
            self.writer.newPage()

        self.rect = self.painter.window()
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
            _logo_top = _header.top() + (_header.height() - _scaled_logo.height()) / 2
            self.painter.drawImage(_header.left(), int(_logo_top), _scaled_logo)

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
            QtCore.QLine(_footer.left(), _footer.top(), _footer.right(), _footer.top())
        )

    
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

    
    def blankPage(self) -> None:
        self.newPage()
        self.setFont()
        _text_opt = QtGui.QTextOption(QtCore.Qt.AlignCenter)
        self.painter.drawText(
            self.rect, "This page intentionally left blank", _text_opt
        )

    
    def startTest(
        self,
        name: str,
        serial_number: str,
        start_time: str,
        end_time: str,
        duration: str,
        status: str,
    ):
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
        if not data:
            return

        _width = self.rect.width()
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
        _scene.setSceneRect(0, 0, _width, _height)

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
