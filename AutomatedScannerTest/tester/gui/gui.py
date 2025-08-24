# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtGui, QtWidgets, QtCharts
import logging

from tester.gui.settings import SettingsDialog
from tester.gui.tester_ui import Ui_TesterWindow
from tester.manager.worker import TestWorker, moveWorkerToThread

_SERIAL_RE = QtCore.QRegularExpression(r"^[A-Z]{2}[0-9]{6}$")
logger = logging.getLogger(__name__)


class TesterWindow(QtWidgets.QMainWindow):
    """
    Main Qt application window for the Automated Scanner Test GUI.

    This window manages the user interface, user actions, and coordinates with the TestSequence model and worker.
    It provides actions for opening, saving, and reporting test data, as well as starting and stopping tests.
    The window uses Qt's property and signal/slot system for integration with the rest of the application.
    """

    signalGenerateReport = QtCore.Signal(str)
    """Signal emitted to generate a report, with the file path as argument."""

    signalLoadData = QtCore.Signal(str)
    """Signal emitted to load test data from a file."""

    signalSaveData = QtCore.Signal(str)
    """Signal emitted to save test data to a file."""

    signalStartTest = QtCore.Signal(str, str, str)
    """Signal emitted to start a test, with serial number, model name, and an extra argument."""

    signalStopWorker = QtCore.Signal()
    """Signal emitted to exit the application."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the TesterWindow, set up the UI, connect signals, and configure logging.

        Args:
            *args: Positional arguments for QMainWindow.
            **kwargs: Keyword arguments for QMainWindow.

        Raises:
            RuntimeError: If the application instance is not a TesterApp.
        """
        logger.debug(f"[TesterWindow] Begin TesterWindow.__init__({args}, {kwargs}).")
        super().__init__(*args, **kwargs)

        # Initialize UI property defaults before UI setup
        self.ui = Ui_TesterWindow()
        self.ui.setupUi(self)
        self.ui.tableSequence.verticalHeader().setVisible(False)

        # Initialize worker
        self.worker = TestWorker()
        self.worker.setupUi(self.ui)
        self.worker.resetTestData()
        self.thread = moveWorkerToThread(self.worker)
        self.ui.tableSequence.selectionModel().currentRowChanged.connect(self.onTableSequenceRowChanged)

        self.signalGenerateReport.connect(self.worker.onGenerateReport)
        self.signalLoadData.connect(self.worker.onLoadData)
        self.signalSaveData.connect(self.worker.onSaveData)
        self.signalStartTest.connect(self.worker.onStartTest)
        self.signalStopWorker.connect(self.worker.onStopWorker)

        # Map worker signals to UI slots
        label_signal_map = {
            self.worker.computerNameSignal: self.ui.labelComputerName.setText,
            self.worker.durationSignal: self.ui.labelDuration.setText,
            self.worker.endTimeSignal: self.ui.labelEndTime.setText,
            self.worker.modelNameSignal: self.ui.labelModelName.setText,
            self.worker.serialNumberSignal: self.ui.labelSerialNumber.setText,
            self.worker.startTimeSignal: self.ui.labelStartTime.setText,
            self.worker.statusSignal: self.ui.labelStatus.setText,
            self.worker.testerNameSignal: self.ui.labelTesterName.setText,
            self.worker.testStartedSignal: self.onTestStarted,
            self.worker.testFinishedSignal: self.onTestFinished,
            self.worker.testingFinishedSignal: self.onTestingFinished,
            self.worker.reportFinishedSignal: self.onReportFinished,
            self.worker.openFinishedSignal: self.onOpenFinished,
            self.worker.savingFinishedSignal: self.onSavingFinished,
            }
        for signal, slot in label_signal_map.items():
            signal.connect(slot, QtCore.Qt.QueuedConnection)

        # Connect UI signals using a loop for efficiency
        actions_slots = [
            (self.ui.actionAbout, self.onAbout),
            (self.ui.actionOpen, self.onOpen),
            (self.ui.actionReport, self.onReport),
            (self.ui.actionSave, self.onSave),
            (self.ui.actionSettings, self.onSettings),
            (self.ui.actionStart, self.onStartTest),
            (self.ui.actionStop, self.onStopTest),
            (self.ui.actionExit, self.onExit),
        ]
        for action, slot in actions_slots:
            action.triggered.connect(slot)

        app = QtCore.QCoreApplication.instance()
        if not (app and hasattr(app, "addSettingsToObject")):
            logger.critical("[TesterWindow] TesterApp instance not found.")
            raise RuntimeError(
                "TesterApp instance not found. Ensure the application is initialized correctly."
            )
        app.addSettingsToObject(self)
        app.statusMessage.connect(self.onUpdateStatus)
        self.ui.tableSequence.horizontalHeader().sectionResized.connect(self.onTableSequenceColumnResized)
        logger.debug("[TesterWindow] Connected to TesterApp instance and settings.")

        # Timer to update current time label every second
        self._current_time_timer = QtCore.QTimer(self)
        self._current_time_timer.timeout.connect(self.onUpdateCurrentTime)
        self._current_time_timer.start(1000)

        logger.debug(f"[TesterWindow] TesterWindow.__init__() complete.")

    @QtCore.Property(str)
    def LastDirectory(self):
        """
        Property for the last directory used for file operations.

        Returns:
            str: The last directory path.
        """
        logger.debug(f"[TesterWindow] Getting LastDirectory property.")
        return self.getSetting("LastDirectory", "")

    @LastDirectory.setter
    def LastDirectory(self, value):
        """
        Setter for the last directory used for file operations.

        Args:
            value (str): The directory path to set.
        """
        logger.debug(f"[TesterWindow] Setting LastDirectory property to {value}.")
        self.setSetting("LastDirectory", value)

    def show(self):
        """
        Show the main window.

        Returns:
            bool: True if the window is shown successfully.
        Raises:
            RuntimeError: If no QCoreApplication instance is found.
        """
        logger.debug(f"[TesterWindow] Calling TesterWindow.show().")
        app = QtWidgets.QApplication.instance()
        if not app:
            raise RuntimeError(
                "No QCoreApplication instance found. Ensure the application is initialized correctly."
            )
        self.setWindowTitle("Startup")
        return super().show()

    def updateSubTitle(self, subTitle: str):
        """
        Update the window subtitle and the subtitle label in the UI.

        Args:
            subTitle (str): The subtitle to display.
        """
        logger.debug(f"[TesterWindow] Updating subtitle to {subTitle}.")
        self.setWindowTitle(subTitle)
        self.ui.labelSubtitle.setText(subTitle)

    @QtCore.Slot(object, object)
    def onTableSequenceRowChanged(self, selected: QtCore.QModelIndex, deselected: QtCore.QModelIndex):
        """
        Slot called when the selection in the test sequence table changes.

        Args:
            selected: The newly selected indexes.
            deselected: The previously selected indexes.
        """
        logger.debug(f"[TesterWindow] Table selection changed to {selected.row()}, changing test window.")
        self.ui.stackedWidgetTest.setCurrentIndex(selected.row())

    @QtCore.Slot()
    def onAbout(self):
        """
        Slot to show the About dialog with application information.

        Raises:
            RuntimeError: If no QCoreApplication instance is found.
        """
        logger.debug(f"[TesterWindow] Showing About dialog.")
        app = QtCore.QCoreApplication.instance()
        if not app:
            raise RuntimeError(
                "No QCoreApplication instance found. Ensure the application is initialized correctly."
            )
        _title = QtCore.QCoreApplication.translate("TesterWindow", "About")
        _version_string = QtCore.QCoreApplication.translate("TesterWindow", "Version")
        _company_string = QtCore.QCoreApplication.translate("TesterWindow", "Developed by")
        _application = app.applicationName()
        _version = app.applicationVersion()
        _company = app.organizationName()
        QtWidgets.QMessageBox.about(
            self,
            _title,
            f"{_application}\n{_version_string} {_version}\n{_company_string} {_company}",
        )

    @QtCore.Slot()
    def onExit(self):
        """
        Slot to handle the exit action, stopping any running test and quitting the application.
        """
        logger.debug(f"[TesterWindow] Exit action triggered, stopping test and quitting application.")
        self.onUpdateStatus("Exit menu clicked, stopping test and quitting application.")
        self.signalStopWorker.emit()
        while self.thread.isRunning():
            QtCore.QCoreApplication.processEvents()
        self.close()

    @QtCore.Slot()
    def onOpenFinished(self):
        """
        Slot called when test data is loaded from a file.

        Args:
            file_path (str): The path to the loaded data file.
        """
        logger.debug(f"[TesterWindow] Data loaded from file.")
        self.ui.actionOpen.setEnabled(True)
        self.ui.actionReport.setEnabled(True)
        self.ui.actionSave.setEnabled(True)
        self.ui.actionStart.setEnabled(True)
        self.ui.actionStop.setEnabled(False)


    @QtCore.Slot()
    def onReportFinished(self):
        """
        Slot called when report generation is finished.

        Args:
            file_path (str): The path to the generated report file.
        """
        logger.debug(f"[TesterWindow] Report generated to file {file_path}.")
        self.onUpdateStatus(f"Report generated: {file_path}.")
        self.ui.actionOpen.setEnabled(True)
        self.ui.actionReport.setEnabled(True)
        self.ui.actionSave.setEnabled(True)
        self.ui.actionStart.setEnabled(True)
        self.ui.actionStop.setEnabled(False)

    @QtCore.Slot()
    def onSavingFinished(self):
        """
        Slot called when test data is saved to a file.

        Args:
            file_path (str): The path to the saved data file.
        """
        logger.debug(f"[TesterWindow] Data saved to file.")
        self.ui.actionOpen.setEnabled(True)
        self.ui.actionReport.setEnabled(True)
        self.ui.actionSave.setEnabled(True)
        self.ui.actionStart.setEnabled(True)
        self.ui.actionStop.setEnabled(False)

    @QtCore.Slot(int, str, bool)
    def onTestFinished(self, index: int, name: str, result: bool):
        """
        Slot called when a test is finished.

        Args:
            index (int): The index of the test.
            name (str): The name of the test.
            result (bool): The result of the test (True for pass, False for fail).
        """
        logger.debug(f"[TesterWindow] Test {index + 1} {name} finished with result {result}.")
        _status = "PASSED" if result else "FAILED"
        self.onUpdateStatus(f"Test {index + 1} {name} {_status}.")

    @QtCore.Slot(bool)
    def onTestingFinished(self, result: bool):
        """
        Slot called when all tests are complete.

        Args:
            result (bool): The overall result (True for pass, False for fail).
        """
        logger.debug(f"[TesterWindow] All tests complete with overall result {result}.")
        _status = "Pass" if result else "Fail"
        self.onUpdateStatus(f"All tests complete with status {_status}.")
        self.ui.actionOpen.setEnabled(True)
        self.ui.actionReport.setEnabled(True)
        self.ui.actionSave.setEnabled(True)
        self.ui.actionStart.setEnabled(True)
        self.ui.actionStop.setEnabled(False)

    @QtCore.Slot()
    def onOpen(self):
        """
        Slot to open a file dialog for loading test data from a file.
        """
        logger.debug(f"[TesterWindow] Open action triggered, showing file dialog.")
        self.ui.actionOpen.setEnabled(False)
        self.ui.actionReport.setEnabled(False)
        self.ui.actionSave.setEnabled(False)
        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(False)
        _caption = QtCore.QCoreApplication.translate("TesterWindow", "Open test data file")
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Data files")
        file_dialog = QtWidgets.QFileDialog(
            self, _caption, self.LastDirectory or "", f"{_filter} (*.json)"
        )
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        if file_dialog.exec() == QtWidgets.QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            self.LastDirectory = QtCore.QFileInfo(file_path).absolutePath()
            self.onUpdateStatus(f"Loading test data from file {file_path}.")
            self.signalLoadData.emit(file_path)

    @QtCore.Slot()
    def onReport(self):
        """
        Slot to open a file dialog for saving a test report.
        """
        logger.debug(f"[TesterWindow] Report action triggered, showing file dialog.")
        self.ui.actionOpen.setEnabled(False)
        self.ui.actionReport.setEnabled(False)
        self.ui.actionSave.setEnabled(False)
        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(False)
        _title = QtCore.QCoreApplication.translate("TesterWindow", "Save test report file")
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Report files")
        file_dialog = QtWidgets.QFileDialog(
            self, _title, self.LastDirectory or "", f"{_filter} (*.pdf)"
        )
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        if file_dialog.exec() == QtWidgets.QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            self.LastDirectory = QtCore.QFileInfo(file_path).absolutePath()
            self.onUpdateStatus(f"Generating report to file {file_path}.")
            self.signalGenerateReport.emit(file_path)

    @QtCore.Slot()
    def onSave(self):
        """
        Slot to open a file dialog for saving test data to a file.
        """
        logger.debug(f"[TesterWindow] Save action triggered, showing file dialog.")
        self.ui.actionOpen.setEnabled(False)
        self.ui.actionReport.setEnabled(False)
        self.ui.actionSave.setEnabled(False)
        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(False)
        _title = QtCore.QCoreApplication.translate("TesterWindow", "Save test data file")
        _filter = QtCore.QCoreApplication.translate("TesterWindow", "Test Data files")
        file_dialog = QtWidgets.QFileDialog(
            self, _title, self.LastDirectory or "", f"{_filter} (*.json)"
        )
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        if file_dialog.exec() == QtWidgets.QDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            self.LastDirectory = QtCore.QFileInfo(file_path).absolutePath()
            self.onUpdateStatus(f"Saving test data to file {file_path}.")
            self.signalSaveData.emit(file_path)

    @QtCore.Slot()
    def onSettings(self):
        """
        Slot to open the settings dialog and apply changes if accepted.
        """
        logger.debug(f"[TesterWindow] Settings action triggered, showing settings dialog.")
        _dialog = SettingsDialog(self.settings)
        _dialog.setWindowTitle(QtCore.QCoreApplication.translate("TesterWindow", "Settings"))
        _dialog.setWindowIcon(QtGui.QIcon(":/rsc/Pangolin.ico"))
        _dialog.exec()

    @QtCore.Slot()
    def onSettingsModified(self):
        """
        Slot called when settings are modified. Updates UI properties accordingly.
        """
        logger.debug(f"[TesterWindow] Settings modified, updating UI properties.")
        self.firstColumnWidth = int(self.getSetting("FirstColumnWidth", 175))
        self.secondColumnWidth = int(self.getSetting("SecondColumnWidth", 75))
        self.dateTimeFormat = str(
            self.getSetting("DateTimeFormat", "yyyy-MM-dd HH:mm:ss")
        )
        if hasattr(self, "ui"):
            self.ui.tableSequence.setColumnWidth(0, self.firstColumnWidth)
            self.ui.tableSequence.setColumnWidth(1, self.secondColumnWidth)

    @QtCore.Slot()
    def onStartTest(self):
        """
        Slot to prompt for serial number and model name, validate input, and start the test.
        """
        logger.debug(f"[TesterWindow] Start Test action triggered, prompting for serial number and model name.")
        self.ui.actionOpen.setEnabled(False)
        self.ui.actionReport.setEnabled(False)
        self.ui.actionSave.setEnabled(False)
        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(True)
        _title = QtCore.QCoreApplication.translate("TesterWindow", "Input Serial Number")
        _message = QtCore.QCoreApplication.translate("TesterWindow", "Enter galvo serial number (q to quit):")
        serial_dialog = QtWidgets.QInputDialog(self)
        serial_dialog.setWindowTitle(_title)
        serial_dialog.setLabelText(_message)
        serial_dialog.setInputMode(QtWidgets.QInputDialog.TextInput)
        if serial_dialog.exec() != QtWidgets.QDialog.Accepted:
            return
        _serial_number = serial_dialog.textValue().strip()
        if not _serial_number or _serial_number.lower() == "q":
            return
        if not _SERIAL_RE.match(_serial_number):
            _title = QtCore.QCoreApplication.translate("TesterWindow", "Invalid Serial Number")
            _message = QtCore.QCoreApplication.translate(
                "TesterWindow", "Serial number must be two uppercase letters followed by six digits."
            )
            QtWidgets.QMessageBox.warning(self, _title, _message)
            return

        _title = QtCore.QCoreApplication.translate("TesterWindow", "Input Model Name")
        _message = QtCore.QCoreApplication.translate("TesterWindow", "Enter model name:")
        model_dialog = QtWidgets.QInputDialog(self)
        model_dialog.setWindowTitle(_title)
        model_dialog.setLabelText(_message)
        model_dialog.setInputMode(QtWidgets.QInputDialog.TextInput)
        if model_dialog.exec() != QtWidgets.QDialog.Accepted:
            return
        _model_name = model_dialog.textValue().strip()
        if not _model_name:
            _title = QtCore.QCoreApplication.translate("TesterWindow", "Invalid Model Name")
            _message = QtCore.QCoreApplication.translate("TesterWindow", "Model name cannot be empty.")
            QtWidgets.QMessageBox.warning(self, _title, _message)
            return

        self.ui.actionStart.setEnabled(False)
        self.ui.actionStop.setEnabled(True)
        self.ui.actionReport.setEnabled(False)
        self.signalStartTest.emit(_serial_number, _model_name, "")

    @QtCore.Slot()
    def onStopTest(self):
        """
        Slot to stop the current test and update UI actions.
        """
        logger.debug(f"[TesterWindow] Stop Test action triggered, stopping current test.")
        self.onUpdateStatus("Stopping current test.")
        self.cancelToken.cancel()

    @QtCore.Slot(int, str)
    def onTestStarted(self, index: int, name: str):
        """
        Slot called when a test is started.

        Args:
            index (int): The index of the test.
            name (str): The name of the test.
        """
        logger.debug(f"[TesterWindow] Test {index + 1} {name} started.")
        self.ui.tableSequence.selectRow(index)
        self.onUpdateStatus(f"Test {index + 1} {name} started.")
        self.updateSubTitle(name)

    @QtCore.Slot()
    def onUpdateCurrentTime(self):
        """
        Update the current time label in the UI with the current date and time.
        """
        current_time = QtCore.QDateTime.currentDateTime().toString(self.dateTimeFormat)
        self.ui.labelCurrentTime.setText(current_time)

    @QtCore.Slot(str)
    def onUpdateStatus(self, message: str):
        """
        Update the status bar message in the UI.

        Args:
            message (str): The message to display.
        """
        _message = QtCore.QCoreApplication.translate("TesterWindow", message)
        self.ui.statusBar.showMessage(_message, 5000)

    # Add this new slot method to TesterWindow
    @QtCore.Slot(int, int, int)
    def onTableSequenceColumnResized(self, logicalIndex: int, oldSize: int, newSize: int):
        """
        Slot called when a tableSequence column is resized. Saves the new size to settings.
        Args:
            logicalIndex (int): The index of the column resized.
            oldSize (int): The previous size of the column.
            newSize (int): The new size of the column.
        """
        if logicalIndex == 0:
            self.setSetting("FirstColumnWidth", newSize)
            self.firstColumnWidth = newSize
        elif logicalIndex == 1:
            self.setSetting("SecondColumnWidth", newSize)
            self.secondColumnWidth = newSize

    @QtCore.Slot(list, str, str, str, str, float, float, int, float, float, int, object, object)
    def addXYPlotToReport(
        self,
        report: QtGui.QPdfWriter,
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
        series_colors=None,
        series_labels=None,
    ):
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
        _width = int(report.rect.width())
        _height = min(int(0.75 * _width), report.rect.height())
        if _height > report.rect.height():
            report.newPage()

        # Create chart and scene only once
        _chart = QtCharts.QChart()
        _chart.setTitle(title)
        _chart.setBackgroundVisible(False)
        _chart.setBackgroundRoundness(0)
        font = report.painter.font()
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

        _target_rect = QtCore.QRectF(report.rect.left(), report.rect.top(), _width, _height)
        report.painter.drawImage(_target_rect, _image)
        report.rect.adjust(0, _height + report.buffer, 0, 0)
        logger.debug(f"[TestReport] XY data plot saved to {path} and drawn in report.")
