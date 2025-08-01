# -*- coding: utf-8 -*-
from PySide6 import QtCore

from tester.manager.report import TestReport
from tester.tests import _test_list


class TestWorker(QtCore.QObject):
    """
    Worker class to run tests in a separate thread.
    This allows the UI to remain responsive during test execution.
    """

    computerNameChanged = QtCore.Signal(str)
    durationChanged = QtCore.Signal(str)
    endTimeChanged = QtCore.Signal(str)
    finishedGeneratingReport = QtCore.Signal()
    finishedLoadingData = QtCore.Signal()
    finishedSavingData = QtCore.Signal()
    finishedTest = QtCore.Signal(int, str, bool)
    finishedTesting = QtCore.Signal(bool)
    modelNameChanged = QtCore.Signal(str)
    serialNumberChanged = QtCore.Signal(str)
    startTimeChanged = QtCore.Signal(str)
    startedTest = QtCore.Signal(int, str)
    statusChanged = QtCore.Signal(str)
    testerNameChanged = QtCore.Signal(str)

    def __init__(self, sequence):
        super().__init__()
        app = QtCore.QCoreApplication.instance()
        if app is not None and app.__class__.__name__ == "TesterApp":
            self.__settings = app.get_settings()
            self.__settings.settingsModified.connect(self.onSettingsModified)
            self.onSettingsModified()
        else:
            QtCore.qCritical("TesterApp instance not found. Ensure the application is initialized correctly.")
            raise RuntimeError("TesterApp instance not found. Ensure the application is initialized correctly.")
        self.sequence = sequence
        QtCore.qInfo("TestWorker initialized.")

    @QtCore.Property(str, notify=computerNameChanged)
    def ComputerName(self):
        return self.sequence.ComputerName

    @ComputerName.setter
    def ComputerName(self, value):
        self.sequence.ComputerName = value
        self.computerNameChanged.emit(value)

    @QtCore.Property(float, notify=durationChanged)
    def Duration(self):
        return self.sequence.Duration

    @Duration.setter
    def Duration(self, value):
        self.sequence.Duration = value
        self.durationChanged.emit(f"{value} sec")

    @QtCore.Property(QtCore.QDateTime, notify=endTimeChanged)
    def EndTime(self):
        return self.sequence.EndTime

    @EndTime.setter
    def EndTime(self, value):
        self.sequence.EndTime = value
        try:
            self.endTimeChanged.emit(value.toString("HH:mm:ss") if value and value.isValid() else "")
        except Exception:
            self.endTimeChanged.emit("")

    @QtCore.Property(str, notify=modelNameChanged)
    def ModelName(self):
        return self.sequence.ModelName

    @ModelName.setter
    def ModelName(self, value):
        self.sequence.ModelName = value
        self.modelNameChanged.emit(value)

    @QtCore.Property(str, notify=serialNumberChanged)
    def SerialNumber(self):
        return self.sequence.SerialNumber

    @SerialNumber.setter
    def SerialNumber(self, value):
        self.sequence.SerialNumber = value
        self.serialNumberChanged.emit(value)

    @QtCore.Property(QtCore.QDateTime, notify=startTimeChanged)
    def StartTime(self):
        return self.sequence.StartTime

    @StartTime.setter
    def StartTime(self, value):
        self.sequence.StartTime = value
        try:
            self.startTimeChanged.emit(value.toString("HH:mm:ss") if value and value.isValid() else "")
        except Exception:
            self.startTimeChanged.emit("")

    @QtCore.Property(object, notify=statusChanged)
    def Status(self):
        return self.sequence.Status

    @Status.setter
    def Status(self, value):
        self.sequence.Status = value
        self.statusChanged.emit(value)

    @QtCore.Property(str, notify=testerNameChanged)
    def TesterName(self):
        return self.sequence.TesterName

    @TesterName.setter
    def TesterName(self, value):
        self.sequence.TesterName = value
        self.testerNameChanged.emit(value)

    def resetTestData(self):
        self.Duration = 0
        self.EndTime = QtCore.QDateTime()
        self.ModelName = ""
        self.SerialNumber = ""
        self.StartTime = QtCore.QDateTime()
        self.Status = "Idle"
        self.sequence.Cancel.reset()
        self.sequence.resetTests()

    @QtCore.Slot()
    def onSettingsModified(self):
        QtCore.qInfo("[onSettingsModified] Settings modified, updating worker settings.")

    @QtCore.Slot(str)
    def onGenerateReport(self, path: str = None):
        _path = QtCore.QDir(path or self.sequence.PdfReportPath).absolutePath()
        parent_dir = QtCore.QDir(QtCore.QDir(_path).filePath(".."))
        if not parent_dir.exists():
            parent_dir.mkpath(".")
        QtCore.qInfo(f"[onGenerateReport] Generating report at {_path}.")

        _report = TestReport(_path)
        _startTime = self.StartTime
        _endTime = self.EndTime
        _report.titlePage(
            self.SerialNumber,
            self.ModelName,
            _startTime.toString("dddd, MMMM dd, yyyy") if _startTime and _startTime.isValid() else "",
            _startTime.toString("HH:mm:ss") if _startTime and _startTime.isValid() else "",
            _endTime.toString("HH:mm:ss") if _endTime and _endTime.isValid() else "",
            f"{self.Duration} sec",
            self.TesterName,
            self.ComputerName,
            self.Status,
        )

        for _test in self.sequence.Tests:
            if getattr(_test, "Status", None) != "Skipped":
                _test.onGenerateReport(_report)

        _report.finish()
        QtCore.qInfo("[onGenerateReport] Report generation finished.")
        self.finishedGeneratingReport.emit()

    @QtCore.Slot(str)
    def onLoadData(self, path: str):
        QtCore.qInfo(f"[onLoadData] Loading test data from file {path}.")
        file_obj = QtCore.QFile(path)
        if file_obj.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            doc = QtCore.QJsonDocument.fromJson(file_obj.readAll())
            if not doc.isObject():
                QtCore.qWarning(f"[onLoadData] File {path} does not contain a valid JSON object.")
                file_obj.close()
                self.finishedLoadingData.emit()
                return
            _data = doc.object().toVariantMap()
            _tests_data = _data.pop("Tests", None)
            if _tests_data:
                _name_to_test = {t.Name: t for t in self.sequence.Tests}
                for _test_name, _test_data in _tests_data.items():
                    _test_obj = _name_to_test.get(_test_name)
                    if _test_obj:
                        _test_obj.onOpen(_test_data)
            for _key, _value in _data.items():
                self.sequence._set_parameter(_key, _value)
            file_obj.close()
        else:
            QtCore.qWarning(f"[onLoadData] Could not open file {path} for reading.")
        QtCore.qInfo("[onLoadData] Finished loading test data.")
        self.finishedLoadingData.emit()

    @QtCore.Slot(str)
    def onSaveData(self, path: str = None):
        _data = self.sequence.Parameters.copy()
        _data["Tests"] = {t.Name: t.onSave() for t in self.sequence.Tests}
        _path = QtCore.QDir(path or self.sequence.DataFilePath).absolutePath()
        QtCore.qInfo(f"[onSaveData] Saving test data to file {_path}.")

        def _to_qvariant(obj):
            # Recursively convert dicts/lists to QVariant-compatible types
            if isinstance(obj, dict):
                return {k: _to_qvariant(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_to_qvariant(v) for v in obj]
            elif isinstance(obj, QtCore.QDateTime):
                return obj.toString(QtCore.Qt.ISODate)
            return obj

        qjson_obj = QtCore.QJsonObject.fromVariantMap(_to_qvariant(_data))
        doc = QtCore.QJsonDocument(qjson_obj)

        file_obj = QtCore.QFile(_path)
        if file_obj.open(QtCore.QIODevice.WriteOnly | QtCore.QIODevice.Text):
            file_obj.write(doc.toJson(QtCore.QJsonDocument.Indented))
            file_obj.close()
            QtCore.qInfo(f"[onSaveData] Test data saved to {_path}.")
        else:
            QtCore.qWarning(f"[onSaveData] Could not open file {_path} for writing.")
        self.finishedSavingData.emit()

    @QtCore.Slot(str, str, str)
    def onStartTest(self, serial_number: str, model_name: str, test: str = None):
        QtCore.qInfo(
            f"[onStartTest] Starting test sequence for serial number '{serial_number}', model '{model_name}', test='{test}'."
        )
        self.resetTestData()
        self.SerialNumber = serial_number
        self.ModelName = model_name
        self.StartTime = self.sequence.getTime()
        self.Status = "Running"
        self.sequence.setupDevices()
        _data_directory = self.sequence.RunDataDirectory
        _statuses = []
        _cancel = self.sequence.Cancel
        for _index, _test in enumerate(self.sequence.Tests):
            self.startedTest.emit(_index, _test.Name)
            if getattr(_cancel, "cancelled", False):
                break
            if test and _test.Name != test:
                _test.Status = "Skipped"
                continue
            _test.setDataDirectory(_data_directory)
            result = _test.onStartTest(serial_number, self.sequence.Devices)
            _statuses.append(result)
            self.finishedTest.emit(_index, _test.Name, result)
        _final_status = all(_statuses) if _statuses else False
        if getattr(_cancel, "cancelled", False):
            self.Status = "Cancelled"
        else:
            if not _statuses:
                QtCore.qCritical(f"[onStartTest] Test '{test}' not found.")
            else:
                self.Status = "Pass" if _final_status else "Fail"
        self.sequence.Devices.teardown()
        self.EndTime = self.sequence.getTime()
        if self.StartTime and self.EndTime and self.StartTime.isValid() and self.EndTime.isValid():
            self.Duration = self.StartTime.secsTo(self.EndTime)
        else:
            self.Duration = 0
        self.onSaveData()
        self.onGenerateReport()
        self.finishedTesting.emit(_final_status)

    @QtCore.Slot()
    def threadStarted(self):
        QtCore.qInfo("[threadStarted] TestWorker thread started. Initializing test sequence model.")
        seq = self.sequence
        if hasattr(seq, "beginResetModel"):
            seq.beginResetModel()
        if hasattr(seq, "Devices"):
            self.ComputerName = seq.Devices.ComputerName
            self.TesterName = seq.Devices.UserName
        tests = list(_test_list())
        if hasattr(seq, "beginInsertRows") and hasattr(seq, "endInsertRows"):
            seq.beginInsertRows(QtCore.QModelIndex(), 0, len(tests) - 1)
            if hasattr(seq, "extend"):
                seq.extend(tests)
            seq.endInsertRows()
        if hasattr(seq, "endResetModel"):
            seq.endResetModel()
        QtCore.qInfo("[threadStarted] Test sequence model initialized.")
