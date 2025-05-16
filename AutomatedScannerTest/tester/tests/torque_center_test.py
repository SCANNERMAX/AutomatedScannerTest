# -*- utf-8 -*-
from tester import _get_class_logger, _member_logger
from tester.devices.mso5000 import MSO5000
from tester.devices.station import Station
from tester.tests.test import TestModel, TestView, TestController
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import tkinter as tk
from tkinter import ttk


class TorqueCenterTestModel(TestModel):
    """Model for Torque Center Test."""

    @_member_logger
    def __init__(self):
        """Initialize the model for Torque Center Test."""
        super().__init__()
        self.__logger = _get_class_logger(self.__class__)

    @_member_logger
    def setup_test(self, station, target):
        super().setup_test(station, target)

        station.osc.acquire_settings(
            averages=8,
            memory_depth=MSO5000.MemoryDepth._10K,
            type_=MSO5000.AcquireType.Averages,
        )
        self.SampleRate = station.osc.get_sample_rate()
        station.osc.channel_settings(1, scale=2, display=True)
        station.osc.channel_settings(
            2, scale=2, display=True, bandwidth_limit=MSO5000.BandwidthLimit._20M
        )
        station.osc.channel_settings(
            3, scale=2, display=True, bandwidth_limit=MSO5000.BandwidthLimit._20M
        )
        station.osc.timebase_settings(
            offset=2, scale=0.2, href_mode=MSO5000.HrefMode.Trigger
        )
        station.osc.trigger_timeout(nreject=True, time=0.5)
        station.osc.trigger_edge()
        station.osc.function_generator_ramp(
            1,
            frequency=0.5,
            phase=270,
            amplitude=5,
            output_impedance=MSO5000.SourceOutputImpedance.Fifty,
        )
        station.osc.function_generator_square(2, frequency=0.5, phase=270, amplitude=5)

    @_member_logger
    def run_test(self, station, target):
        super().run_test(station, target)

        _data = []
        for _iteration in range(101):
            _offset = (_iteration - 50) / 20
            station.osc.function_generator_sinusoid(
                1,
                frequency=0.5,
                phase=270,
                amplitude=0.1,
                output_impedance=MSO5000.SourceOutputImpedance.Fifty,
                offset=_offset,
            )
            station.osc.function_generator_state(1, True)
            station.osc.function_generator_state(2, True)
            station.osc.phase_align(2)
            station.osc.clear()
            station.osc.single()
            time.sleep(10)
            station.osc.function_generator_state(1, False)
            station.osc.function_generator_state(2, False)
            _currents = [
                100 * x
                for x in station.osc.get_waveform(
                    source=MSO5000.WaveformSource.Channel3,
                    mode=MSO5000.WaveformMode.Raw,
                    format_=MSO5000.WaveformFormat.Ascii,
                    stop=10000,
                )
            ]
            _rms = 0
            _data.append((_offset, _rms))
        self.TorqueData = _data

    @_member_logger
    def analyze_results(self, target):
        super().analyze_results(target)
        self.Status = True

    @_member_logger
    def append_report(self, report):
        super().append_report(report)

        report.set_font("Helvetica", style="B", size=14)
        report.cell(200, 10, txt="Plots", ln=True)
        report.ln(5)

        report.set_font("Helvetica", size=12)
        report.cell(200, 10, txt="Torque Plot", ln=True)
        report.image(str(self._figure_path), x=10, y=None, w=200)
        report.ln(10)


class TorqueCenterTestView(TestView):
    """View for Torque Center Test."""

    @property
    def TorqueData(self):
        _data = []
        for _child in self.__data_table.get_children():
            _values = self.__data_table.item(_child, "values")
            _data.append((_values[1], _values[2]))
        return _data

    @TorqueData.setter
    def TorqueData(self, data):
        self.__data_table.delete(*self.__data_table.get_children())
        for _index, (_position, _current) in enumerate(data):
            _time = 1e9 * _index / self.SampleRate
            self.__data_table.insert("", "end", values=(_time, _position, _current))

        # Plot position vs. current
        self.__figure.clear()
        _fric_axis = self.__figure.add_subplot(1, 1, 1)
        _fric_axis.plot(_position, _current, label="Torque Plot")
        _fric_axis.set_xlabel("Position (deg)")
        _fric_axis.set_ylabel("RMS Current (mA)")
        _fric_axis.set_title("Torque Plot")
        _fric_axis.grid(True)
        self.__figure.savefig(self._figure_path)

    @_member_logger
    def __init__(self):
        """Initialize the view for Torque Center Test."""
        super().__init__()
        self.__logger = _get_class_logger(self.__class__)

    @_member_logger
    def configure_gui(self, parent):
        super().configure_gui(parent)

        # Add a tabbed frame
        _notebook = ttk.Notebook(self.parent)
        _notebook.pack(expand=1, fill="both")

        # Add a data tab
        _frame = ttk.Frame(_notebook)
        _notebook.add(_frame, text=" Data ")
        self.__data_table = ttk.Treeview(
            _frame, columns=("Column1", "Column2", "Column3"), show="headings"
        )
        self.__data_table.heading("Column1", text="Time (ns)")
        self.__data_table.heading("Column2", text="Position (deg)")
        self.__data_table.heading("Column3", text="RMS Current (mA)")
        self.__data_table.column("Column1", anchor=tk.CENTER)
        self.__data_table.column("Column2", anchor=tk.CENTER)
        self.__data_table.column("Column3", anchor=tk.CENTER)
        self.__data_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        _scrollbar = ttk.Scrollbar(_frame, command=self.__data_table.yview)
        _scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.__data_table.config(yscrollcommand=_scrollbar.set)

        # Add friction plot tab
        _frame = ttk.Frame(_notebook)
        _notebook.add(_frame, text=" Graph ")
        self.__figure = plt.figure(figsize=(5, 4))
        _canvas = FigureCanvasTkAgg(self.__figure, master=_frame)
        _canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)


class TorqueCenterTestController(TestController):

    @_member_logger
    def __init__(self):
        super().__init__(
            TorqueCenterTestModel, TorqueCenterTestView, "Torque Center Test"
        )
        self.__logger = _get_class_logger(self.__class__)

    @_member_logger
    def set_data_directory(self, root_directory):
        super().set_data_directory(root_directory)
        self._figure_path = self._data_directory / "torque_plot.png"
        self._model._figure_path = self._figure_path
        self._view._figure_path = self._figure_path
