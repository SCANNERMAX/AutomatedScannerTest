# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import ctypes
from ctypes.wintypes import BYTE
from datetime import datetime, timedelta
from enum import StrEnum
from fpdf import FPDF
import logging
import logging.handlers
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy
import os
import pathlib
import pyvisa
import re
import sys
import time
import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk


def member_log(name):
    __logger = logging.getLogger(name)

    def function_log(func):
        def wrapper(*args, **kwargs):
            try:
                __logger.debug(
                    f"Calling function: {func.__name__} with arguments: {args} and keyword arguments: {kwargs}"
                )
                _result = func(*args, **kwargs)
                __logger.debug(f"Function: {func.__name__} returned: {_result}")
                return _result
            except Exception as e:
                __logger.error(f"Function: {func.__name__} failed with error: {e}")
                raise e

        return wrapper

    return __logger, function_log


_friction_class_logger, friction_method_wrapper = member_log("FrictionPlot")


class FrictionPlot(object):
    __logger = _friction_class_logger
    __serial_number = None
    __root_directory = None
    __data_directory = None
    __results_directory = None
    __position = []
    __current = []

    @property
    def RootDirectory(self):
        """Get the result directory path."""
        return self.__root_directory

    @RootDirectory.setter
    def RootDirectory(self, value):
        """Set the result directory path."""
        self.__root_directory = value

    @property
    def SampleRate(self):
        """Get the sample rate of the device."""
        return self.__sample_rate

    @SampleRate.setter
    def SampleRate(self, value):
        """Set the sample rate of the device."""
        self.__sample_rate = value

    @property
    def SerialNumber(self):
        """Get the serial number of the device."""
        return self.__serial_number

    @SerialNumber.setter
    def SerialNumber(self, value):
        """Set the serial number of the device."""
        self.__serial_number = value
        _test_unit_directory = self.__root_directory / self.__serial_number
        if not _test_unit_directory.exists():
            _test_unit_directory.mkdir()
        _test_unit_directory = _test_unit_directory / datetime.today().strftime(
            "%Y%m%d_%H%M%S"
        )
        if not _test_unit_directory.exists():
            _test_unit_directory.mkdir()
        self.__data_directory = _test_unit_directory / "Data"
        if not self.__data_directory.exists():
            self.__data_directory.mkdir()
        self.__results_directory = _test_unit_directory / "Results"
        if not self.__results_directory.exists():
            self.__results_directory.mkdir()

    @friction_method_wrapper
    def __init__(self):
        """Initialize the friction plot with the given directory and serial number."""
        self.__position = []
        self.__current = []

    @friction_method_wrapper
    def add_data_tab(self, notebook: ttk.Notebook):
        """Adds a data tab to the given notebook."""
        _frame = ttk.Frame(notebook)
        notebook.add(_frame, text="  Data  ")
        self.__data_table = ttk.Treeview(
            _frame, columns=("Column1", "Column2", "Column3"), show="headings"
        )
        self.__data_table.heading("Column1", text="Time (ns)")
        self.__data_table.heading("Column2", text="Position (deg)")
        self.__data_table.heading("Column3", text="Torque Current (mA)")
        self.__data_table.column("Column1", anchor=tk.CENTER)
        self.__data_table.column("Column2", anchor=tk.CENTER)
        self.__data_table.column("Column3", anchor=tk.CENTER)
        self.__data_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        _scrollbar = ttk.Scrollbar(_frame, command=self.__data_table.yview)
        _scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.__data_table.config(yscrollcommand=_scrollbar.set)

    @friction_method_wrapper
    def add_position_tab(self, notebook: ttk.Notebook):
        _frame = ttk.Frame(notebook)
        notebook.add(_frame, text="  Position  ")
        self.__pos_figure = plt.figure(figsize=(5, 4))
        _canvas = FigureCanvasTkAgg(self.__pos_figure, master=_frame)
        _canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    @friction_method_wrapper
    def add_current_tab(self, notebook: ttk.Notebook):
        _frame = ttk.Frame(notebook)
        notebook.add(_frame, text="  Torque Current  ")
        self.__curr_figure = plt.figure(figsize=(5, 4))
        _canvas = FigureCanvasTkAgg(self.__curr_figure, master=_frame)
        _canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    @friction_method_wrapper
    def add_friction_tab(self, notebook: ttk.Notebook):
        _frame = ttk.Frame(notebook)
        notebook.add(_frame, text="  Friction  ")
        self.__fric_figure = plt.figure(figsize=(5, 4))
        _canvas = FigureCanvasTkAgg(self.__fric_figure, master=_frame)
        _canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    @friction_method_wrapper
    def add_data(self, position: list(), current: list()):
        """Adds data to the friction plot."""
        self.__position = position
        self.__current = current

        # Create and save a plot of the position data
        self.__pos_figure.clear()
        _pos_axis = self.__pos_figure.add_subplot(1, 1, 1)
        _pos_axis.plot(self.__position, label="Position")
        _pos_axis.set_xlabel("Time (ns)")
        _pos_axis.set_ylabel("Position (deg)")
        _pos_axis.set_title("Position Over Time")
        _pos_axis.grid(True)
        self.__pos_figure.savefig(self.__data_directory / "position_plot.png")

        # Plot current over time
        self.__curr_figure.clear()
        _curr_axis = self.__curr_figure.add_subplot(1, 1, 1)
        _curr_axis.plot(self.__current, label="Torque Current")
        _curr_axis.set_xlabel("Time (ns)")
        _curr_axis.set_ylabel("Torque Current (mA)")
        _curr_axis.set_title("Current Over Time")
        _curr_axis.grid(True)
        self.__curr_figure.savefig(self.__data_directory / "current_plot.png")

        # Plot position vs. current
        self.__fric_figure.clear()
        _fric_axis = self.__fric_figure.add_subplot(1, 1, 1)
        _fric_axis.plot(self.__position, self.__current, label="Friction Plot")
        _fric_axis.set_xlabel("Position (deg)")
        _fric_axis.set_ylabel("Torque Current (mA)")
        _fric_axis.set_title("Friction Plot")
        _fric_axis.grid(True)
        self.__fric_figure.savefig(self.__data_directory / "friction_plot.png")

        # Save data to CSV
        self.__data_table.delete(*self.__data_table.get_children())
        with open(self.__data_directory / "bearing_test_data.csv", "w") as _file:
            _file.write("Time (ns),Position (deg),Torque Current (mA)\n")
            for _index, (_position, _current) in enumerate(zip(position, current)):
                _time = 1e9 * _index / self.__sample_rate
                _file.write(f"{_time:.12f},{_position:.12f},{_current:.12f}\n")
                self.__data_table.insert("", "end", values=(_time, _position, _current))
        self.generate_pdf_report()

    @friction_method_wrapper
    def generate_pdf_report(self):
        """Generates a PDF report of the friction plot data."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)

        # Add title
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(200, 10, txt="Bearing Test Report", ln=True, align="C")
        pdf.ln(10)

        # Add metadata
        pdf.set_font("Helvetica", size=12)
        pdf.cell(200, 10, txt=f"Serial Number: {self.__serial_number}", ln=True)
        pdf.cell(200, 10, txt=f"Date: {datetime.today().strftime('%Y-%m-%d')}", ln=True)
        pdf.ln(10)

        # Add plots
        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(200, 10, txt="Plots", ln=True)
        pdf.ln(5)

        for plot_name, plot_file in [
            ("Position Over Time", self.__data_directory / "position_plot.png"),
            ("Torque Current Over Time", self.__data_directory / "current_plot.png"),
            ("Friction Plot", self.__data_directory / "friction_plot.png"),
        ]:
            pdf.set_font("Helvetica", size=12)
            pdf.cell(200, 10, txt=plot_name, ln=True)
            pdf.image(str(plot_file), x=10, y=None, w=200)
            pdf.ln(10)

        # Save PDF
        pdf_output_path = self.__results_directory / "friction_plot_report.pdf"
        pdf.output(str(pdf_output_path))
        self.__logger.info(f"PDF report generated: {pdf_output_path}")


_mso5000_logger, mso5000_method_wrapper = member_log("MSO5000")


class MSO5000(object):
    __logger = _mso5000_logger
    __instrument = None

    @mso5000_method_wrapper
    def __init__(self, instrument):
        """Initialize the oscilloscope to factory settings."""
        self.__logger.info(f"Connecting to Rigol Oscilloscope {instrument}.")
        self.__instrument = instrument
        self.stop()
        self.reset()

    def __getattr__(self, name):
        """If an attribute is not found, forward the request to the embedded instrument."""
        if hasattr(self.__instrument, name):
            _response = getattr(self.__instrument, name)
            return _response
        else:
            raise AttributeError(f"Attribute {name} not found.")

    # Basic communication commands
    @mso5000_method_wrapper
    def __query(self, message: str) -> str:
        """Sends a request command to the oscilloscope and returns the response."""
        _message = message.strip()
        assert _message, "Message cannot be empty."
        self.__logger.debug(f'sending request "{_message}"...')
        _response = None
        _attempts = 5
        while _attempts > 0:
            _attempts = _attempts - 1
            try:
                _response = self.__instrument.query(_message).rstrip()
                break
            except pyvisa.errors.VisaIOError:
                self.__logger.debug("retrying...")
        assert _response, "Failed to get response."
        return _response

    @mso5000_method_wrapper
    def __write(self, message: str):
        """Sends a command to the oscilloscope."""
        _message = message.strip()
        assert _message, "Message cannot be empty."
        _attempts = 5
        while _attempts > 0:
            _attempts = _attempts - 1
            try:
                self.__logger.debug(f'sending command "{_message}"...')
                self.__instrument.write(_message)
                break
            except pyvisa.errors.VisaIOError:
                self.__logger.debug("retrying...")

    @mso5000_method_wrapper
    def __get_names(self, channel: str, parameter: str):
        """Generate the parameter and attribute names."""
        _parameter = f":{channel}:{parameter}"
        _attribute = _parameter.replace(":", "_").lower()
        return _attribute, _parameter

    @mso5000_method_wrapper
    def __get_parameter_str(self, channel: str, parameter: str) -> str:
        """Queries a parameter of the oscilloscope."""
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        _value = None
        if hasattr(self, _attribute):
            _value = getattr(self, _attribute)
        else:
            _value = self.__query(f"{_parameter}?")
            setattr(self, _attribute, _value)
        return _value

    @mso5000_method_wrapper
    def __get_parameter_int(self, channel: str, parameter: str) -> int:
        """Queries a parameter of the oscilloscope."""
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        _value = None
        if hasattr(self, _attribute):
            _value = getattr(self, _attribute)
        else:
            _value = int(self.__query(f"{_parameter}?"))
            setattr(self, _attribute, _value)
        return _value

    @mso5000_method_wrapper
    def __get_parameter_float(self, channel: str, parameter: str) -> float:
        """Queries a parameter of the oscilloscope."""
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        _value = None
        if hasattr(self, _attribute):
            _value = getattr(self, _attribute)
        else:
            _value = float(self.__query(f"{_parameter}?"))
            setattr(self, _attribute, _value)
        return _value

    @mso5000_method_wrapper
    def __get_parameter_bool(self, channel: str, parameter: str) -> bool:
        """Queries a parameter of the oscilloscope."""
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        _value = None
        if hasattr(self, _attribute):
            _value = getattr(self, _attribute)
        else:
            _value = bool(int(self.__query(f"{_parameter}?")))
            setattr(self, _attribute, _value)
        return _value

    @mso5000_method_wrapper
    def __set_parameter_str(self, channel: str, parameter: str, value: str):
        """Sets a parameter of the oscilloscope."""
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        _current = getattr(self, _attribute, None)
        while _current != value:
            _current = self.__get_parameter_str(channel, parameter)
            if _current == value:
                return
            else:
                self.__write(f"{_parameter} {value}")
                setattr(self, _attribute, value)

    @mso5000_method_wrapper
    def __set_parameter_int(self, channel: str, parameter: str, value: int):
        """Sets a parameter of the oscilloscope."""
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        _current = getattr(self, _attribute, None)
        while _current != value:
            _current = self.__get_parameter_int(channel, parameter)
            if _current == value:
                return
            else:
                self.__write(f"{_parameter} {value}")
                setattr(self, _attribute, value)

    @mso5000_method_wrapper
    def __set_parameter_float(self, channel: str, parameter: str, value: float):
        """Sets a parameter of the oscilloscope."""
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        _current = getattr(self, _attribute, None)
        while _current != value:
            _current = self.__get_parameter_float(channel, parameter)
            if _current == value:
                return
            else:
                self.__write(f"{_parameter} {value}")
                setattr(self, _attribute, value)

    @mso5000_method_wrapper
    def __set_parameter_bool(self, channel: str, parameter: str, value: bool):
        """Sets a parameter of the oscilloscope."""
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        _current = getattr(self, _attribute, None)
        while _current != value:
            _current = self.__get_parameter_bool(channel, parameter)
            if _current == value:
                return
            else:
                self.__write(f"{_parameter} {value}")
                setattr(self, _attribute, value)

    @mso5000_method_wrapper
    def __set_parameter(self, channel: str, parameter: str, value: str):
        """Sets a parameter of the oscilloscope without checking the current value."""
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        self.__write(f"{_parameter} {value}")
        setattr(self, _attribute, value)

    # The device command system
    @mso5000_method_wrapper
    def autoscale(self):
        """Enables the waveform auto setting function. The oscilloscope will
        automatically adjust the vertical scale, horizontal time base, and
        trigger mode according to the input signal to realize optimal
        waveform display. This command functions the same as the AUTO key on
        the front panel.
        """
        self.__write("AUToscale")

    @mso5000_method_wrapper
    def clear(self):
        """Clears all the waveforms on the screen. This command functions the
        same as the CLEAR key on the front panel.
        """
        self.__write("CLEar")

    @mso5000_method_wrapper
    def run(self):
        """Starts the oscilloscope. This command functions the same as the
        RUN/STOP key on the front panel.
        """
        self.__write(":RUN")

    @mso5000_method_wrapper
    def stop(self):
        """Stops the oscilloscope. This command functions the same as the
        RUN/STOP key on the front panel.
        """
        self.__write(":STOP")

    @mso5000_method_wrapper
    def single(self):
        """Sets the trigger mode of the oscilloscope to "Single". This command
        functions the same as either of the following two operation: press
        SINGLE on the front panel; or send the :TRIGger:SWEep SINGle
        command.
        """
        self.__write(":SINGle")

    @mso5000_method_wrapper
    def force_trigger(self):
        """Generates a trigger signal forcefully. This command is only
        applicable to the normal and single trigger modes (refer to the
        :TRIGger:SWEep command). This command functions the same as the
        FORCE key in the trigger control area of the front panel.
        """
        self.__write(":TFORce")

    # The :ACQ commands are used to set the memory depth of the
    # oscilloscope, the acquisition mode, the average times, as well as query
    # the current sample rate
    class MemoryDepth(StrEnum):
        """The memory depth of the oscilloscope, i.g. the number of waveform
        points.
        """

        Auto = "AUTO"
        _1K = "1K"
        _10K = "10K"
        _100K = "100K"
        _1M = "1M"
        _10M = "10M"
        _25M = "25M"
        _50M = "50M"
        _100M = "100M"
        _200M = "200M"

    class AcquireType(StrEnum):
        """The acquisition mode of the oscilloscope"""

        Normal = "NORM"
        Averages = "AVER"
        Peak = "PEAK"
        HighResolution = "HRES"

    @mso5000_method_wrapper
    def _set_acquire_averages(self, averages: int):
        """Sets the number of averages in the average acquisition mode."""
        _valid_values = [2**x for x in range(1, 17)]
        assert averages in _valid_values, "Averages must be one of the valid values."
        self.__set_parameter("ACQuire", "AVERages", averages)

    @mso5000_method_wrapper
    def _set_acquire_memory_depth(self, depth: MemoryDepth):
        """Sets the memory depth of the oscilloscope (i.g. the number of
        waveform points that can be stored through the sampling in a single
        trigger). The default unit is pts.
        """
        assert (
            depth in MSO5000.MemoryDepth
        ), "Memory depth must be one of the MemoryDepth enum values."
        self.__set_parameter("ACQuire", "MDEPth", depth.value)

    @mso5000_method_wrapper
    def _set_acquire_type(self, type_: AcquireType):
        """Sets the acquisition mode of the oscilloscope."""
        assert (
            type_ in MSO5000.AcquireType
        ), "Acquire type must be one of the AcquireType enum values."
        self.__set_parameter_str("ACQuire", "TYPE", type_.value)

    @mso5000_method_wrapper
    def get_sample_rate(self) -> float:
        """Queries the current sample rate. The def ault unit is Sa/s."""
        _response = self.__get_parameter_float("ACQuire", "SRATe")
        return _response

    @mso5000_method_wrapper
    def get_digital_sample_rate(self) -> float:
        """Queries the current LA sample rate. The default unit is Sa/s."""
        return self.__get_parameter_float("ACQuire", "LA:SRATe")

    @mso5000_method_wrapper
    def get_digital_memory_depth(self) -> float:
        """Queries the current LA memory depth."""
        return self.__get_parameter_float("ACQuire", "LA:MDEPth")

    @mso5000_method_wrapper
    def _set_acquire_antialiasing(self, state: bool):
        """Enables or disables the anti aliasing function of the oscilloscope."""
        self.__set_parameter_str("ACQuire", "AALias", state)

    @mso5000_method_wrapper
    def acquire_settings(
        self,
        averages: int = 2,
        memory_depth: MemoryDepth = MemoryDepth.Auto,
        type_: AcquireType = AcquireType.Normal,
        antialiasing: bool = False,
    ):
        """Sets the acquisition settings of the oscilloscope."""
        self._set_acquire_type(type_)
        if type_ == MSO5000.AcquireType.Averages:
            self._set_acquire_averages(averages)
        self._set_acquire_memory_depth(memory_depth)
        self._set_acquire_antialiasing(antialiasing)

    # The :BOD commands are used to execute the bode related settings and operations.

    # The :BUS<n> commands are used to execute the decoding related settings and operations.

    # The :CHANnel<n> commands are used to set or query the bandwidth limit,
    # coupling, vertical scale, vertical offset, and other vertical system
    # parameters of the analog channel.
    class BandwidthLimit(StrEnum):
        """The bandwidth limit of the oscilloscope"""

        Off = "OFF"
        Auto = "AUTO"
        _20M = "20M"
        _100M = "100M"
        _200M = "200M"

    class Coupling(StrEnum):
        """The channel coupling of the oscilloscope"""

        AC = "AC"
        DC = "DC"
        Ground = "GND"

    class Units(StrEnum):
        """The channel units of the oscilloscope"""

        Voltage = "VOLT"
        Watt = "WATT"
        Ampere = "AMP"
        Unknown = "UNKN"

    @mso5000_method_wrapper
    def _set_channel_bandwidth_limit(self, channel: int, limit: BandwidthLimit):
        """Sets the bandwidth limit of the specified channel."""
        if self.model_name == "MSO5354":
            _valid = MSO5000.BandwidthLimit.__members__.values()
        elif self.model_name == "MSO5204":
            _valid = [
                MSO5000.BandwidthLimit.Off,
                MSO5000.BandwidthLimit._20M,
                MSO5000.BandwidthLimit._100M,
            ]
        else:
            _valid = [MSO5000.BandwidthLimit.Off, MSO5000.BandwidthLimit._20M]
        assert (
            limit in _valid
        ), "Bandwidth limit must be one of the BandwidthLimit enum values."
        self.__set_parameter_str(f"CHANnel{channel}", "BWLimit", limit.value)

    @mso5000_method_wrapper
    def _set_channel_coupling(self, channel: int, coupling: Coupling):
        """Sets the coupling mode of the specified channel."""
        assert (
            coupling in MSO5000.Coupling
        ), "Coupling must be one of the Coupling enum values."
        self.__set_parameter_str(f"CHANnel{channel}", "COUPling", coupling.value)

    @mso5000_method_wrapper
    def _set_channel_display(self, channel: int, display: bool):
        """Turns on or off the specified channel."""
        self.__set_parameter_bool(f"CHANnel{channel}", "DISPlay", display)

    @mso5000_method_wrapper
    def _set_channel_invert(self, channel: int, invert: bool):
        """Turns on or off the waveform invert for the specified channel."""
        self.__set_parameter_bool(f"CHANnel{channel}", "INVert", invert)

    @mso5000_method_wrapper
    def _set_channel_offset(self, channel: int, offset: float):
        """Sets the vertical offset of the specified channel. The default unit
        is V.
        """
        _minimum = -10
        _maximum = 100
        assert (
            offset >= _minimum and offset <= _maximum
        ), f"Offset must be between {_minimum} and {_maximum}."
        self.__set_parameter_float(f"CHANnel{channel}", "OFFSet", offset)

    @mso5000_method_wrapper
    def _set_channel_calibration_time(self, channel: int, time: float):
        """Sets the delay calibration time (used to calibrate the zero offset
        of the corresponding channel) of the specified channel. The default
        unit is s.
        """
        assert (
            time >= -100e-9 and time <= 100e-9
        ), "Delay calibration time must be between -100e-9 and 100e-9 seconds."
        self.__set_parameter_float(f"CHANnel{channel}", "TCALibrate", time)

    @mso5000_method_wrapper
    def _set_channel_scale(self, channel: int, scale: float):
        """Sets the vertical scale of the specified channel. The default unit
        is V.
        """
        _minimum = 500e-6
        _maximum = 10
        assert (
            scale >= _minimum and scale <= _maximum
        ), f"Scale must be between {_minimum} and {_maximum}."
        self.__set_parameter_float(f"CHANnel{channel}", "SCALe", scale)

    @mso5000_method_wrapper
    def _set_channel_probe(self, channel: int, probe: float):
        """Sets the probe ratio of the specified channel."""
        assert probe in [
            0.0001,
            0.0002,
            0.0005,
            0.001,
            0.002,
            0.005,
            0.01,
            0.02,
            0.05,
            0.1,
            0.2,
            0.5,
            1,
            2,
            5,
            10,
            20,
            50,
            100,
            200,
            500,
            1000,
            2000,
            5000,
            10000,
            20000,
            50000,
        ], "Probe must be one of the valid values."
        self.__set_parameter_float(f"CHANnel{channel}", "PROBe", probe)

    @mso5000_method_wrapper
    def _set_channel_units(self, channel: int, units: Units):
        """Sets the amplitude display unit of the specified analog channel."""
        assert units in MSO5000.Units, "Units must be one of the Units enum values."
        self.__set_parameter_str(f"CHANnel{channel}", "UNITs", units.value)

    @mso5000_method_wrapper
    def _set_channel_vernier(self, channel: int, vernier: bool):
        """Enables or disables the fine adjustment of the vertical scale of the
        specified analog channel.
        """
        self.__set_parameter_bool(f"CHANnel{channel}", "VERNier", vernier)

    @mso5000_method_wrapper
    def _set_channel_position(self, channel: int, position: float):
        """Sets the offset calibration voltage for calibrating the zero point
        of the specified analog channel.
        """
        assert (
            position >= -100 and position <= 100
        ), "Position must be between -100 and 100."
        self.__set_parameter_float(f"CHANnel{channel}", "POSition", position)

    @mso5000_method_wrapper
    def channel_settings(
        self,
        channel: int,
        bandwidth_limit: BandwidthLimit = BandwidthLimit.Off,
        coupling: Coupling = Coupling.DC,
        display: bool = False,
        invert: bool = False,
        offset: float = 0,
        delay_calibration_time: float = 0,
        scale: float = 100e-3,
        probe: float = 1,
        units: Units = Units.Voltage,
        vernier: bool = False,
        position: float = 0,
    ):
        """Sets the channel settings of the specified channel."""
        self._set_channel_display(channel, display)
        self._set_channel_probe(channel, probe)
        self._set_channel_scale(channel, scale)
        self._set_channel_bandwidth_limit(channel, bandwidth_limit)
        self._set_channel_coupling(channel, coupling)
        self._set_channel_invert(channel, invert)
        self._set_channel_offset(channel, offset)
        self._set_channel_calibration_time(channel, delay_calibration_time)
        self._set_channel_units(channel, units)
        self._set_channel_vernier(channel, vernier)
        self._set_channel_position(channel, position)

    # The :COUNter commands are used to set the relevant parameters of the built in counter.

    # The :CURSor commands are used to measure the X axis values (e.g. Time)
    # and Y axis values (e.g. Voltage) of the waveform on the screen.

    # The :DISPlay commands can be used to set the displayed type of the
    # waveform, persistence time, intensity, grid type, grid brightness, etc.

    # The :DVM commands are used to set the relevant parameters of the built in DVM.

    # The :HISTogram commands are used to set the relevant parameters of the built in histogram.

    # The IEEE488.2 common commands are used to query the basic information of
    # the instrument or executing basic operations. These commands usually
    # start with "*", and the keywords in a command contain 3 characters.
    @mso5000_method_wrapper
    def clear_registers(self):
        """Clears the status registers of the oscilloscope."""
        self.__write("*CLS")

    @mso5000_method_wrapper
    def get_standard_event_register_enable(self) -> BYTE:
        """Queries the enable register bit of the standard event register set."""
        _response = self.__query("*ESE?")
        return BYTE(int(_response))

    @mso5000_method_wrapper
    def set_standard_event_register_enable(self, bits: BYTE):
        """Sets the enable register bit of the standard event register set."""
        self.__write(f"*ESE {bits}")

    @mso5000_method_wrapper
    def get_standard_event_register_event(self) -> BYTE:
        """Queries and clears the event register of the standard event status
        register.
        """
        _response = self.__query("*ESR?")
        return BYTE(int(_response))

    @mso5000_method_wrapper
    def get_identity(self) -> str:
        """Queries the ID string of the instrument."""
        return self.__query("*IDN?")

    @mso5000_method_wrapper
    def get_operation_complete(self) -> bool:
        """The OPC? command queries whether the current operation is finished."""
        _response = self.__query("*OPC?")
        return bool(int(_response))

    @mso5000_method_wrapper
    def set_operation_complete(self, state: bool):
        """The *OPC command sets bit 0 (Operation Complete, OPC) in the
        standard event status register to 1 after the current operation is
        finished.
        """
        self.__write(f"*OPC {int(state)}")

    @mso5000_method_wrapper
    def save(self, register: int):
        """Saves the current settings of the oscilloscope to the specified
        register.
        """
        assert register >= 0 and register <= 49, "Register must be between 0 and 49."
        self.__write(f"*SAVe {register}")

    @mso5000_method_wrapper
    def recall(self, register: int):
        """Recalls the settings of the oscilloscope from the specified
        register.
        """
        assert register >= 0 and register <= 49, "Register must be between 0 and 49."
        self.__write(f"*RCL {register}")

    @mso5000_method_wrapper
    def reset(self):
        """Restores the instrument to its factory default settings."""
        self.__write("*RST")
        self.wait()

    @mso5000_method_wrapper
    def get_status_byte_register_enable(self) -> BYTE:
        """Queries the enable register bit of the status byte register set."""
        _response = self.__query("*SRE?")
        return BYTE(int(_response))

    @mso5000_method_wrapper
    def set_status_byte_register_enable(self, bits: BYTE):
        """Sets the enable register bit of the status byte register set."""
        self.__write(f"*SRE {bits}")

    @mso5000_method_wrapper
    def get_status_byte_register_event(self) -> BYTE:
        """Queries and clears the event register of the status byte register."""
        _response = self.__query("*STB?")
        return BYTE(int(_response))

    @mso5000_method_wrapper
    def self_test(self) -> str:
        """Performs a self-test and queries the self-test result."""
        _response = self.__query("*TST?")
        return _response

    @mso5000_method_wrapper
    def wait(self):
        """Waits for all the pending operations to complete before executing
        any additional commands.
        """
        self.__write("*WAI")

    # The :LA commands are used to perform relevant operations on the digital
    # channels. PLA2216 active logic probe option is required to be ordered.

    # The :LAN commands are used to set and query the LAN parameters.

    # The :MASK commands are used to set or query the relevant parameters of
    # the pass/fail test.

    # The :MATH<n> commands are used to set various math operation function of
    # the waveform between channels.

    # The :MEASure commands are used to set and query the relevant parameters
    # for measurement.

    # The :POWer commands are used to set the relevant parameters of the power supply module.

    # The :QUICk command is used to set and query the relevant parameters for shortcut keys.

    # The :RECOrd commands are used to set the relevant parameters of the record function.

    # The :REFerence commands are used to set relevant parameters for reference waveforms.

    # The :SAVE commands are used to save data or settings from the oscilloscope.
    class SaveCsvLength(StrEnum):
        """The data length type in saving the "*.csv" file."""

        Display = "DISP"
        Maximum = "MAX"

    class SaveCsvChannel(StrEnum):
        """The on/off status of the storage channel."""

        Channel1 = "CHAN1"
        Channel2 = "CHAN2"
        Channel3 = "CHAN3"
        Channel4 = "CHAN4"
        Pod1 = "POD1"
        Pod2 = "POD2"

    class ImageType(StrEnum):
        """The image type of the saved image."""

        Bitmap = "BMP24"
        Jpeg = "JPEG"
        Png = "PNG"
        Tiff = "TIFF"

    class ImageColor(StrEnum):
        """The color setting of the saved image."""

        Color = "COL"
        Gray = "GRAY"

    @mso5000_method_wrapper
    def _set_save_csv_length(self, length: SaveCsvLength):
        """Sets or queries the data length type in saving the "*.csv" file."""
        assert (
            length in MSO5000.SaveCsvLength
        ), "Length must be one of the SaveCsvLength enum values."
        self.__set_parameter_str("SAVE", "CSV:LENGth", length.value)

    @mso5000_method_wrapper
    def _set_save_csv_channel(self, channel: SaveCsvChannel, state: bool):
        """Sets the on/off status of the storage channel"""
        assert (
            channel in MSO5000.SaveCsvChannel
        ), "Channel must be one of the SaveCsvChannel enum values."
        self.__set_parameter_str("SAVE", "CSV:CHANnel", f"{channel.value},{int(state)}")

    @mso5000_method_wrapper
    def save_csv(
        self,
        filename: str,
        length: SaveCsvLength = SaveCsvLength.Display,
    ):
        """Saves the waveform data displayed on the screen to the internal or
        external memory in "*.csv" format.
        """
        self._set_save_csv_length(length)
        self.__set_parameter_str("SAVE", "CSV", filename)

    @mso5000_method_wrapper
    def _save_image_type(self, type_: ImageType):
        """Sets the image type of the saved image."""
        assert (
            type_ in MSO5000.ImageType
        ), "Type must be one of the ImageType enum values."
        self.__set_parameter_str("SAVE", "IMAGe:TYPE", type_.value)

    @mso5000_method_wrapper
    def _save_image_invert(self, invert: bool):
        """Enables or disables the invert function when saving the image."""
        self.__set_parameter_bool("SAVE", "IMAGe:INVert", invert)

    @mso5000_method_wrapper
    def _save_image_color(self, color: ImageColor):
        """Sets the image color for image saving to Color or Gray."""
        self.__set_parameter_str("SAVE", "COLor", color.value)

    @mso5000_method_wrapper
    def save_image(
        self,
        path: str,
        type_: ImageType,
        invert: bool = False,
        color: ImageColor = ImageColor.Color,
    ):
        """Stores the contents displayed on the screen into the internal or external memory in image format."""
        self._save_image_type(type_)
        self._save_image_invert(invert)
        self._save_image_color(color)
        self.__set_parameter_str("SAVE", "IMAGe", path)

    @mso5000_method_wrapper
    def save_setup(self, path: str):
        """Saves the current setup parameters of the oscilloscope to the
        internal or external memory as a file.
        """
        self.__set_parameter_str("SAVE", "SETup", path)

    @mso5000_method_wrapper
    def save_waveform(self, path: str):
        """Saves the waveform data to the internal or external memory as a file."""
        self.__set_parameter_str("SAVE", "WAVeform", path)

    @mso5000_method_wrapper
    def get_save_status(self) -> bool:
        """Queries the saving status of the internal memory or the external USB
        storage device.
        """
        return self.__get_parameter_bool("SAVE", "STATus")

    @mso5000_method_wrapper
    def load_setup(self, filename: str):
        """Loads the setup file of the oscilloscope from the specified path."""
        self.__write(f":LOAD:SETup {filename}")

    # The :SEARch commands are used to set the relevant parameters of the search function.

    # The [:SOURce [<n>]] commands are used to set the relevant parameters of the built in function arbitrary
    # waveform generator. <n> can set to 1 or 2, which indicates the corresponding built in function/arbitrary
    # waveform generator channel. When <n> or :SOURce[<n>] is omitted, by default, the operations are
    # carried out on AWG GI.
    class SourceFunction(StrEnum):
        Sinusoid = "SIN"
        Square = "SQU"
        Ramp = "RAMP"
        Pulse = "PULS"
        Noise = "NOIS"
        Dc = "DC"
        Sinc = "SINC"
        ExponentialRise = "EXPR"
        ExponentialFall = "EXPF"
        Ecg = "ECG"
        Guass = "GUAS"
        Lorentz = "LOR"
        Haversine = "HAV"
        Arbitrary = "ARB"

    class SourceType(StrEnum):
        _None = "NONE"
        Modulated = "MOD"
        Sweep = "SWE"
        Burst = "BUR"

    class SourceModulation(StrEnum):
        AmplitudeModulation = "AM"
        FrequencyModulation = "FM"
        FrequencyShiftKey = "FSK"

    class SourceSweepType(StrEnum):
        Linear = "LIN"
        Log = "LOG"
        Step = "STEP"

    class SourceBurstType(StrEnum):
        Ncycle = "NCYCL"
        Infinite = "INF"

    class SourceOutputImpedance(StrEnum):
        Omeg = "OMEG"
        Fifty = "FIFT"

    @mso5000_method_wrapper
    def function_generator_state(self, channel: int, state: bool):
        """Enables or disables the function generator."""
        self.__set_parameter_bool(f"SOURce{channel}", f"OUTPut{channel}:STATe", state)

    @mso5000_method_wrapper
    def _set_source_function(self, channel: int, function: SourceFunction):
        """Sets the function of the function generator."""
        assert (
            function in MSO5000.SourceFunction
        ), "Function must be one of the Waveform enum values."
        self.__set_parameter_str(f"SOURce{channel}", "FUNCtion", function.value)

    @mso5000_method_wrapper
    def _set_source_type(self, channel: int, type_: SourceType):
        """Sets the type of the function generator."""
        assert type in MSO5000.SourceType, "Type must be one of the Type enum values."
        self.__set_parameter_str(f"SOURce{channel}", "TYPE", type_.value)

    @mso5000_method_wrapper
    def _set_source_frequency(self, channel: int, frequency: float):
        """Set the frequency of the function generator."""
        assert (
            frequency > 0.01 and frequency < 25000000
        ), "Frequency must be between 0.1 and 25000000 Hz."
        self.__set_parameter_float(f"SOURce{channel}", "FREQuency", frequency)

    @mso5000_method_wrapper
    def _set_source_phase(self, channel: int, phase: float):
        """Sets the phase of the function generator. The default unit is degrees."""
        assert phase >= 0 and phase <= 360, "Phase must be between 0 and 360 degrees."
        self.__set_parameter_float(f"SOURce{channel}", "PHASe", phase)

    @mso5000_method_wrapper
    def _set_source_amplitude(self, channel: int, amplitude: float):
        """Sets the amplitude of the function generator. The default unit is Vpp."""
        assert (
            amplitude >= 0.02 and amplitude <= 5
        ), "Amplitude must be between 0.02 and 5 Vpp."
        self.__set_parameter_float(
            f"SOURce{channel}", "VOLTage:LEVel:IMMediate:AMPLitude", amplitude
        )

    @mso5000_method_wrapper
    def _set_source_offset(self, channel: int, offset: float):
        """Sets the offset of the function generator. The default unit is V."""
        assert (
            offset >= -2.5 and offset <= 2.5
        ), "Offset must be between -2.5 and 2.5 V."
        self.__set_parameter_float(
            f"SOURce{channel}", "VOLTage:LEVel:IMMediate:OFFSet", offset
        )

    @mso5000_method_wrapper
    def phase_align(self, channel: int):
        """Sets the phase alignment of the function generator."""
        self.__write(f"SOURce{channel}:PHASe:INITiate")

    @mso5000_method_wrapper
    def _set_source_output_impedance(
        self, channel: int, impedance: SourceOutputImpedance
    ):
        """Sets the output impedance of the function generator."""
        assert (
            impedance in MSO5000.SourceOutputImpedance
        ), "Output impedance must be one of the OutputImpedance enum values."
        self.__set_parameter_str(
            f"SOURce{channel}", "OUTPut:IMPedance", impedance.value
        )

    # Function Generator Function: Sinusoid
    @mso5000_method_wrapper
    def function_generator_sinusoid(
        self,
        channel: int,
        frequency: float = 1000,
        phase: float = 0,
        amplitude: float = 0.5,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        """Sets the function generator to sinusoidal waveform."""
        self.function_generator_state(channel, False)
        self._set_source_function(channel, MSO5000.SourceFunction.Sinusoid)
        self._set_source_frequency(channel, frequency)
        self._set_source_phase(channel, phase)
        self._set_source_amplitude(channel, amplitude)
        self._set_source_offset(channel, offset)
        self._set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: Square
    @mso5000_method_wrapper
    def function_generator_square(
        self,
        channel: int,
        frequency: float = 1000,
        phase: float = 0,
        amplitude: float = 0.5,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        """Sets the function generator to square waveform."""
        self.function_generator_state(channel, False)
        self._set_source_function(channel, MSO5000.SourceFunction.Square)
        self._set_source_frequency(channel, frequency)
        self._set_source_phase(channel, phase)
        self._set_source_amplitude(channel, amplitude)
        self._set_source_offset(channel, offset)
        self._set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: RAMP
    @mso5000_method_wrapper
    def _set_source_function_ramp_symmetry(self, channel: int, symmetry: float):
        """Sets the symmetry of the ramp waveform. The default unit is %."""
        assert symmetry >= 1 and symmetry <= 100, "Symmetry must be between 1 and 100%."
        self.__set_parameter_float(
            f"SOURce{channel}", "FUNCtion:RAMP:SYMMetry", symmetry
        )

    @mso5000_method_wrapper
    def function_generator_ramp(
        self,
        channel: int,
        frequency: float = 1000,
        phase: float = 0,
        symmetry: float = 50,
        amplitude: float = 0.5,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        """Sets the function generator to ramp waveform."""
        self.function_generator_state(channel, False)
        self._set_source_function(channel, MSO5000.SourceFunction.Ramp)
        self._set_source_frequency(channel, frequency)
        self._set_source_phase(channel, phase)
        self._set_source_function_ramp_symmetry(channel, symmetry)
        self._set_source_amplitude(channel, amplitude)
        self._set_source_offset(channel, offset)
        self._set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: PULSe
    @mso5000_method_wrapper
    def _set_source_duty_cycle(self, channel: int, duty_cycle: float):
        """Sets the duty cycle of the pulse waveform. The default unit is %."""
        assert (
            duty_cycle >= 10 and duty_cycle <= 90
        ), "Duty cycle must be between 10 and 90%."
        self.__set_parameter_float(f"SOURce{channel}", "PULSe:DCYCle", duty_cycle)

    @mso5000_method_wrapper
    def function_generator_pulse(
        self,
        channel: int,
        frequency: float = 1000,
        phase: float = 0,
        duty_cycle: float = 20,
        amplitude: float = 0.5,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        """Sets the function generator to pulse waveform."""
        self.function_generator_state(channel, False)
        self._set_source_function(channel, MSO5000.SourceFunction.Pulse)
        self._set_source_frequency(channel, frequency)
        self._set_source_phase(channel, phase)
        self._set_source_duty_cycle(channel, duty_cycle)
        self._set_source_amplitude(channel, amplitude)
        self._set_source_offset(channel, offset)
        self._set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: NOISe
    @mso5000_method_wrapper
    def function_generator_noise(
        self,
        channel: int,
        amplitude: float = 0.5,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        """Sets the function generator to noise waveform."""
        self.function_generator_state(channel, False)
        self._set_source_function(channel, MSO5000.SourceFunction.Noise)
        self._set_source_amplitude(channel, amplitude)
        self._set_source_offset(channel, offset)
        self._set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: DC
    @mso5000_method_wrapper
    def function_generator_dc(
        self,
        channel: int,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        """Sets the function generator to DC waveform."""
        self.function_generator_state(channel, False)
        self._set_source_function(channel, MSO5000.SourceFunction.DC)
        self._set_source_offset(channel, offset)
        self._set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: SINC
    @mso5000_method_wrapper
    def function_generator_sinc(
        self,
        channel: int,
        frequency: float = 1000,
        phase: float = 0,
        amplitude: float = 0.5,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        """Sets the function generator to sinc waveform."""
        self.function_generator_state(channel, False)
        self._set_source_function(channel, MSO5000.SourceFunction.Sinc)
        self._set_source_frequency(channel, frequency)
        self._set_source_phase(channel, phase)
        self._set_source_amplitude(channel, amplitude)
        self._set_source_offset(channel, offset)
        self._set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: EXPRise
    # Function Generator Function: EXPFall
    # Function Generator Function: ECG
    # Function Generator Function: GAUSs
    # Function Generator Function: LORentz
    # Function Generator Function: HAVersine
    # Function Generator Function: ARBitrary
    # Function Generator Type: None
    @mso5000_method_wrapper
    def function_generator_no_modulation(self, channel: int):
        """Sets the function generator to unmodulated."""
        self.function_generator_state(channel, False)
        self._set_source_type(channel, MSO5000.SourceType._None)

    # Function Generator Type: Modulation
    @mso5000_method_wrapper
    def _set_source_mod_type(self, channel: int, mod_type: SourceModulation):
        """Sets the modulation type of the function generator."""
        assert (
            mod_type in MSO5000.SourceModulation
        ), "Modulation type must be one of the Modulation enum values."
        self.__set_parameter_str(f"SOURce{channel}", "MODulation:TYPE", mod_type.value)

    @mso5000_method_wrapper
    def _set_source_mod_am_depth(self, channel: int, depth: float):
        """Sets the modulation depth of the function generator. The default unit is percentage."""
        assert (
            depth >= 0 and depth <= 120
        ), "Modulation amplitude depth must be between 0 and 120%."
        self.__set_parameter_float(f"SOURce{channel}", "MOD:DEPTh", depth)

    @mso5000_method_wrapper
    def _set_source_mod_am_freq(self, channel: int, frequency: float):
        """Sets the modulation frequency of the function generator. The default unit is Hz."""
        assert (
            frequency >= 1 and frequency <= 50
        ), "Modulation frequency must be between 1 and 50 Hz."
        self.__set_parameter_float(
            f"SOURce{channel}", "MOD:AM:INTernal:FREQuency", frequency
        )

    @mso5000_method_wrapper
    def _set_source_mod_fm_freq(self, channel: int, frequency: float):
        """Sets the modulation frequency of the function generator. The default unit is Hz."""
        assert (
            frequency >= 1 and frequency <= 50
        ), "Modulation frequency must be between 1 and 50 Hz."
        self.__set_parameter_float(
            f"SOURce{channel}", "MOD:FM:INTernal:FREQuency", frequency
        )

    @mso5000_method_wrapper
    def _set_source_mod_am_function(self, channel: int, function: SourceFunction):
        """Sets the modulation function of the function generator."""
        assert function in [
            MSO5000.SourceFunction.SINusoid,
            MSO5000.SourceFunction.SQUare,
            MSO5000.SourceFunction.RAMP,
            MSO5000.SourceFunction.NOISe,
        ], "Modulation function must be one of SINusoid, SQUare, RAMP, NOISe."
        self.__set_parameter_str(
            f"SOURce{channel}", "MOD:AM:INTernal:FUNCtion", function.value
        )

    @mso5000_method_wrapper
    def _set_source_mod_fm_function(self, channel: int, function: SourceFunction):
        """Sets the modulation function of the function generator."""
        assert function in [
            MSO5000.SourceFunction.SINusoid,
            MSO5000.SourceFunction.SQUare,
            MSO5000.SourceFunction.RAMP,
            MSO5000.SourceFunction.NOISe,
        ], "Modulation function must be one of SINusoid, SQUare, RAMP, NOISe."
        self.__set_parameter_str(
            f"SOURce{channel}", "MOD:FM:INTernal:FUNCtion", function.value
        )

    @mso5000_method_wrapper
    def _set_source_mod_fm_deviation(self, channel: int, deviation: float):
        """Sets the modulation frequency deviation of the function generator. The default unit is Hz."""
        assert (
            deviation >= 0
        ), "Modulation frequency deviation must be greater than or equal to 0 Hz."
        self.__set_parameter_float(f"SOURce{channel}", "MOD:FM:DEViation", deviation)

    @mso5000_method_wrapper
    def function_generator_modulation(
        self,
        channel: int,
        type_: SourceModulation = SourceModulation.AmplitudeModulation,
        am_depth: float = 100,
        frequency: float = 1000,
        function: SourceFunction = SourceFunction.Sinusoid,
        fm_deviation: float = 1000,
    ):
        """Sets the function generator to modulation waveform."""
        self.function_generator_state(channel, False)
        self._set_source_type(channel, MSO5000.SourceType.Modulated)
        self._set_source_mod_type(channel, type_)
        if type_ == MSO5000.SourceModulation.AM:
            self._set_source_am_depth(channel, am_depth)
            self._set_source_mod_am_freq(channel, frequency)
            self._set_source_mod_am_function(channel, function)
        elif type_ == MSO5000.SourceModulation.FM:
            self._set_source_mod_fm_frequency(channel, frequency)
            self._set_source_mod_fm_function(channel, function)
            self._set_source_mod_fm_deviation(channel, fm_deviation)

    # Function Generator Type: Sweep
    @mso5000_method_wrapper
    def _set_source_sweep_type(self, channel: int, type_: SourceSweepType):
        """Sets the sweep type of the function generator."""
        assert (
            type_ in MSO5000.SourceSweepType
        ), "Sweep type must be one of the SweepType enum values."
        self.__set_parameter_str(f"SOURce{channel}", "SWEep:TYPE", type_.value)

    @mso5000_method_wrapper
    def _set_source_sweep_sweep_time(self, channel: int, time: int):
        assert (
            time >= 1 and time <= 500
        ), "Sweep time must be between 1 and 500 seconds."
        self.__set_parameter_int(f"SOURce{channel}", "SWEep:STIMe", time)

    @mso5000_method_wrapper
    def _set_source_sweep_return_time(self, channel: int, time: int):
        assert (
            time >= 1 and time <= 500
        ), "Return time must be between 1 and 500 seconds."
        self.__set_parameter_int(f"SOURce{channel}", "SWEep:BTIMe", time)

    @mso5000_method_wrapper
    def function_generator_sweep(
        self,
        channel: int,
        type_: SourceSweepType = SourceSweepType.Linear,
        sweep_time: int = 1,
        return_time: int = 0,
    ):
        self.function_generator_state(channel, False)
        self._set_source_type(channel, MSO5000.SourceType.Sweep)
        self._set_source_sweep_type(channel, type_)
        self._set_source_sweep_sweep_time(channel, sweep_time)
        self._set_source_sweep_return_time(channel, return_time)

    # Function Generator Type: Burst
    @mso5000_method_wrapper
    def _set_source_burst_type(self, channel: int, type_: SourceBurstType):
        assert (
            type_ in MSO5000.SourceBurstType
        ), "Burst type must be one of the BurstType enum values."
        self.__set_parameter_str(f"SOURce{channel}", "BURSt:TYPE", type_.value)

    @mso5000_method_wrapper
    def _set_source_burst_cycles(self, channel: int, cycles: int):
        assert (
            cycles >= 1 and cycles <= 1000000
        ), "Burst cycles must be between 1 and 1000000."
        self.__set_parameter_int(f"SOURce{channel}", "BURSt:CYCLes", cycles)

    @mso5000_method_wrapper
    def _set_source_burst_delay(self, channel: int, delay: int):
        assert (
            delay >= 1 and delay <= 1000000
        ), "Burst delay must be between 1 and 1000000."
        self.__set_parameter_int(f"SOURce{channel}", "BURSt:DELay", delay)

    @mso5000_method_wrapper
    def function_generator_burst(
        self,
        channel: int,
        type_: SourceBurstType = SourceBurstType.Ncycle,
        cycles: int = 1,
        delay: int = 0,
    ):
        self.function_generator_state(channel, False)
        self._set_source_type(channel, MSO5000.SourceType.Sweep)
        self._set_source_burst_type(channel, type_)
        self._set_source_burst_cycles(channel, cycles)
        self._set_source_burst_delay(channel, delay)

    # The :SYSTem commands are used to set sound, language, and other relevant system settings.
    @mso5000_method_wrapper
    def get_system_error(self) -> str:
        """Queries and clears the latest error message."""
        return self.__get_parameter_str("SYSTem", "ERRor:NEXT")

    # The :TIMebase commands are used to set the horizontal system. For example, enable the delayed sweep,
    # set the horizontal time base mode, etc.
    class TimebaseMode(StrEnum):
        Main = "MAIN"
        Xy = "XY"
        Roll = "ROLL"

    class HrefMode(StrEnum):
        Center = "CENT"
        Lb = "LB"
        Rb = "RB"
        Trigger = "TRIG"
        User = "USER"

    @mso5000_method_wrapper
    def _set_timebase_delay_enable(self, enable: bool):
        """Turns on or off the delayed sweep."""
        self.__set_parameter_bool("TIMebase", "DELay:ENABle", enable)

    @mso5000_method_wrapper
    def _set_timebase_delay_offset(self, offset: float):
        """Sets the offset of the delayed time base. The default unit is s."""
        self.__set_parameter_float("TIMebase", "DELay:OFFSet", offset)

    @mso5000_method_wrapper
    def _set_timebase_delay_scale(self, scale: float):
        """Sets the scale of the delayed time base. The default unit is s/div."""
        self.__set_parameter_float("TIMebase", "DELay:SCALe", scale)

    @mso5000_method_wrapper
    def timebase_delay(
        self, enable: bool = False, offset: float = 0, scale: float = 500e-9
    ):
        self._set_timebase_delay_enable(enable)
        self._set_timebase_delay_offset(offset)
        self._set_timebase_delay_scale(scale)

    @mso5000_method_wrapper
    def _set_timebase_offset(self, offset: float):
        """Sets the offset of the main time base. The default unit is s."""
        self.__set_parameter_float("TIMebase", "MAIN:OFFSet", offset)

    @mso5000_method_wrapper
    def _set_timebase_scale(self, scale: float):
        """Sets the scale of the main time base."""
        self.__set_parameter_float("TIMebase", "MAIN:SCALe", scale)

    @mso5000_method_wrapper
    def _set_timebase_mode(self, mode: TimebaseMode):
        """Sets the horizontal time base mode."""
        assert (
            mode in MSO5000.TimebaseMode
        ), "Timebase mode must be one of the TimebaseMode enum values."
        self.__set_parameter_str("TIMebase", "MODE", mode.value)

    @mso5000_method_wrapper
    def _set_timebase_href_mode(self, mode: HrefMode):
        """Sets the horizontal reference mode."""
        assert (
            mode in MSO5000.HrefMode
        ), "Href mode must be one of the HrefMode enum values."
        self.__set_parameter_str("TIMebase", "HREFerence:MODE", mode.value)

    @mso5000_method_wrapper
    def _set_timebase_position(self, position: int):
        """Sets the user defined reference position when the waveforms are
        expanded or compressed horizontally.
        """
        assert (
            position >= -500 and position <= 500
        ), "Horizontal reference position must be between -500 to 500."
        self.__set_parameter_int("TIMebase", "HREFerence:POSition", position)

    @mso5000_method_wrapper
    def _set_timebase_vernier(self, vernier: bool):
        """Enables or disables the fine adjustment function of the horizontal
        scale.
        """
        self.__set_parameter_bool("TIMebase", "VERNier", vernier)

    @mso5000_method_wrapper
    def timebase_settings(
        self,
        offset: float = 0,
        scale: float = 1e-6,
        mode: TimebaseMode = TimebaseMode.Main,
        href_mode: HrefMode = HrefMode.Center,
        position: float = 0,
        vernier: bool = False,
    ):
        self._set_timebase_mode(mode)
        self._set_timebase_scale(scale)
        self._set_timebase_offset(offset)
        self._set_timebase_href_mode(href_mode)
        self._set_timebase_position(position)
        self._set_timebase_vernier(vernier)

    # The [:TRACe[< n>]] commands are used to set the arbitrary waveform parameters of the built in signal
    # sources. <n> can be 1 or 2 which denotes the corresponding built in signal source channel. If <n>
    # or :TRACe[<n>] is omitted, the operation will be applied to source 1 by default.

    # The :TRIGger commands are used to set the trigger system of the oscilloscope.
    class TriggerMode(StrEnum):
        Edge = "EDGE"
        Pulse = "PULS"
        Slope = "SLOP"
        Video = "VID"
        Pattern = "PATT"
        Duration = "DUR"
        Timeout = "TIM"
        Runt = "RUNT"
        Window = "WIND"
        Delay = "DEL"
        Setup = "SET"
        Nedge = "NEDG"
        RS232 = "RS232"
        IIC = "IIC"
        SPI = "SPI"
        CAN = "CAN"
        Flexray = "FLEX"
        LIN = "LIN"
        IIS = "IIS"
        M1553 = "M1553"

    class TriggerCoupling(StrEnum):
        AC = "AC"
        DC = "DC"
        LfReject = "LFR"
        HfReject = "HFR"

    class TriggerStatus(StrEnum):
        TD = "TD"
        Wait = "WAIT"
        Run = "RUN"
        Auto = "AUTO"
        Stop = "STOP"

    class TriggerSweep(StrEnum):
        Auto = "AUTO"
        Normal = "NORM"
        Single = "SING"

    class TriggerSource(StrEnum):
        D0 = "D0"
        D1 = "D1"
        D2 = "D2"
        D3 = "D3"
        D4 = "D4"
        D5 = "D5"
        D6 = "D6"
        D7 = "D7"
        D8 = "D8"
        D9 = "D9"
        D10 = "D10"
        D11 = "D11"
        D12 = "D12"
        D13 = "D13"
        D14 = "D14"
        D15 = "D15"
        Channel1 = "CHAN1"
        Channel2 = "CHAN2"
        Channel3 = "CHAN3"
        Channel4 = "CHAN4"
        AcLine = "ACL"

    class TriggerSlope(StrEnum):
        Positive = "POS"
        Negative = "NEG"
        RFall = "RFAL"

    class TriggerWhen(StrEnum):
        Greater = "GRE"
        Less = "LESS"
        Gless = "GLES"

    class TriggerWindow(StrEnum):
        TA = "TA"
        TB = "TB"
        TAB = "TAB"

    @mso5000_method_wrapper
    def get_trigger_status(self):
        """Queries the trigger status of the oscilloscope."""
        _status = self.__get_parameter_str("TRIGger", "STATus")
        return MSO5000.TriggerStatus(_status)

    @mso5000_method_wrapper
    def _set_trigger_mode(self, mode: TriggerMode):
        assert (
            mode in MSO5000.TriggerMode
        ), "Trigger mode must be one of the TriggerMode enum values."
        self.__set_parameter_str("TRIGger", "MODE", mode.value)

    @mso5000_method_wrapper
    def _set_trigger_coupling(self, coupling: TriggerCoupling):
        assert (
            coupling in MSO5000.TriggerCoupling
        ), "Trigger coupling must be one of the TriggerCoupling enum values."
        self.__set_parameter_str("TRIGger", "COUPling", coupling.value)

    @mso5000_method_wrapper
    def _set_trigger_sweep(self, sweep: TriggerSweep):
        assert (
            sweep in MSO5000.TriggerSweep
        ), "Trigger sweep must be one of the TriggerSweep enum values."
        self.__set_parameter_str("TRIGger", "SWEep", sweep.value)

    @mso5000_method_wrapper
    def _set_trigger_holdoff(self, holdoff: float):
        assert (
            holdoff >= 8e-9 and holdoff <= 10
        ), "Trigger holdoff must be between 8ns and 10s."
        self.__set_parameter_float("TRIGger", "HOLDoff", holdoff)

    @mso5000_method_wrapper
    def _set_trigger_noise_reject(self, status: bool):
        self.__set_parameter_bool("TRIGger", "NREJect", status)

    # Trigger mode: Edge
    @mso5000_method_wrapper
    def _set_trigger_edge_source(self, source: TriggerSource):
        assert (
            source in MSO5000.TriggerSource
        ), "Trigger edge source must be one of the TriggerSource enum values."
        self.__set_parameter_str("TRIGger", "EDGE:SOURce", source.value)

    @mso5000_method_wrapper
    def _set_trigger_edge_slope(self, slope: TriggerSlope):
        assert (
            slope in MSO5000.TriggerSlope
        ), "Trigger edge slope must be one of the TriggerEdgeSlope enum values."
        self.__set_parameter_str("TRIGger", "EDGE:SLOPe", slope.value)

    @mso5000_method_wrapper
    def _set_trigger_edge_level(self, level: float):
        assert (
            level >= -15 and level <= 15
        ), "Trigger edge level must be between -15 and 15 V."
        self.__set_parameter_float("TRIGger", "EDGE:LEVel", level)

    @mso5000_method_wrapper
    def trigger_edge(
        self,
        coupling: TriggerCoupling = TriggerCoupling.DC,
        sweep: TriggerSweep = TriggerSweep.Auto,
        holdoff: float = 8e-9,
        nreject: bool = False,
        edge_source: TriggerSource = TriggerSource.Channel1,
        edge_slope: TriggerSlope = TriggerSlope.Positive,
        edge_level: float = 0,
    ):
        self._set_trigger_mode(MSO5000.TriggerMode.Edge)
        self._set_trigger_coupling(coupling)
        self._set_trigger_sweep(sweep)
        self._set_trigger_holdoff(holdoff)
        self._set_trigger_noise_reject(nreject)
        self._set_trigger_edge_source(edge_source)
        self._set_trigger_edge_slope(edge_slope)
        self._set_trigger_edge_level(edge_level)

    # Trigger mode: Pulse
    @mso5000_method_wrapper
    def _set_trigger_pulse_source(self, source: TriggerSource):
        assert (
            source in MSO5000.TriggerSource
        ), "Trigger pulse source must be one of the TriggerSource enum values."
        self.__set_parameter_str("TRIGger", "PULSe:SOURce", source.value)

    @mso5000_method_wrapper
    def _set_trigger_pulse_when(self, when: TriggerWhen):
        assert (
            when in MSO5000.TriggerWhen
        ), "Trigger pulse when must be one of the TriggerWhen enum values."
        self.__set_parameter_str("TRIGger", "PULSe:WHEN", when.value)

    @mso5000_method_wrapper
    def _set_trigger_pulse_upper_width(self, width: float):
        assert width <= 10, "Trigger pulse upper width must be less than 10s."
        self.__set_parameter_float("TRIGger", "PULSe:UWIDth", width)

    @mso5000_method_wrapper
    def _set_trigger_pulse_lower_width(self, width: float):
        assert width >= 8e-12, "Trigger pulse lower width must be greater than 8 ps."
        self.__set_parameter_float("TRIGger", "PULSe:LWIDth", width)

    @mso5000_method_wrapper
    def _set_trigger_pulse_level(self, level: float):
        assert (
            level >= -15 and level <= 15
        ), "Trigger pulse level must be between -15 and 15 V."
        self.__set_parameter_float("TRIGger", "PULSe:LEVel", level)

    @mso5000_method_wrapper
    def trigger_pulse(
        self,
        coupling: TriggerCoupling = TriggerCoupling.DC,
        sweep: TriggerSweep = TriggerSweep.Auto,
        holdoff: float = 8e-9,
        nreject: bool = False,
        pulse_source: TriggerSource = TriggerSource.Channel1,
        pulse_when: TriggerWhen = TriggerWhen.Greater,
        pulse_upper_width: float = 2e-6,
        pulse_lower_width: float = 1e-6,
        pulse_level: float = 0,
    ):
        self._set_trigger_mode(MSO5000.TriggerMode.Edge)
        self._set_trigger_coupling(coupling)
        self._set_trigger_sweep(sweep)
        self._set_trigger_holdoff(holdoff)
        self._set_trigger_noise_reject(nreject)
        self._set_trigger_pulse_source(pulse_source)
        self._set_trigger_pulse_when(pulse_when)
        self._set_trigger_pulse_upper_width(pulse_upper_width)
        self._set_trigger_pulse_lower_width(pulse_lower_width)
        self._set_trigger_pulse_level(pulse_level)

    # Trigger mode: Slope
    @mso5000_method_wrapper
    def _set_trigger_slope_source(self, source: TriggerSource):
        assert source in [
            MSO5000.TriggerSource.CHANnel1,
            MSO5000.TriggerSource.CHANnel2,
            MSO5000.TriggerSource.CHANnel3,
            MSO5000.TriggerSource.CHANnel4,
        ], "Trigger source must be one of Channel 1, Channel 2, Channel 3 or Channel 4."
        self.__set_parameter_str("TRIGger", "SLOPe:SOURce", source.value)

    @mso5000_method_wrapper
    def _set_trigger_slope_when(self, when: TriggerWhen):
        assert (
            when in MSO5000.TriggerWhen
        ), "Trigger when must be one of the TriggerWhen enum values."
        self.__set_parameter_str("TRIGger", "SLOPe:WHEN", when.value)

    @mso5000_method_wrapper
    def _set_trigger_slope_time_upper(self, time: float):
        assert time <= 10, "Upper time limit must be less than 10 s."
        self.__set_parameter_float("TRIGger", "SLOPe:TUPPer", time)

    @mso5000_method_wrapper
    def _set_trigger_slope_time_lower(self, time: float):
        assert time >= 800e-12, "Lower time limit must be greater than 800 ps."
        self.__set_parameter_float("TRIGger", "SLOPe:TLOWer", time)

    @mso5000_method_wrapper
    def _set_trigger_slope_window(self, window: TriggerWindow):
        assert (
            window in MSO5000.TriggerWindow
        ), "Trigger window must be one of the TriggerWindow enum values."
        self.__set_parameter_str("TRIGger", "SLOPe:WINDow", window.value)

    @mso5000_method_wrapper
    def _set_trigger_slope_amplitude_upper(self, amplitude: float):
        self.__set_parameter_float("TRIGger", "SLOPe:ALEVel", amplitude)

    @mso5000_method_wrapper
    def _set_trigger_slope_amplitude_lower(self, amplitude: float):
        self.__set_parameter_float("TRIGger", "SLOPe:BLEVel", amplitude)

    @mso5000_method_wrapper
    def trigger_slope(
        self,
        coupling: TriggerCoupling = TriggerCoupling.DC,
        sweep: TriggerSweep = TriggerSweep.Auto,
        holdoff: float = 8e-9,
        nreject: bool = False,
        source: TriggerSource = TriggerSource.Channel1,
        when: TriggerWhen = TriggerWhen.Greater,
        time_upper: float = 1e-6,
        time_lower: float = 1e-6,
        window: TriggerWhen = TriggerWindow.TA,
        amplitude_upper: float = 0,
        amplitude_lower: float = 0,
    ):
        self._set_trigger_mode(MSO5000.TriggerMode.Slope)
        self._set_trigger_coupling(coupling)
        self._set_trigger_sweep(sweep)
        self._set_trigger_holdoff(holdoff)
        self._set_trigger_noise_reject(nreject)
        self._set_trigger_slope_source(source)
        self._set_trigger_slope_when(when)
        self._set_trigger_slope_time_upper(time_upper)
        self._set_trigger_slope_time_lower(time_lower)
        self._set_trigger_slope_window(window)
        self._set_trigger_slope_amplitude_upper(amplitude_upper)
        self._set_trigger_slope_amplitude_lower(amplitude_lower)

    # Trigger mode: Video
    # Trigger mode: Pattern
    # Trigger mode: Duration
    # Trigger mode: Timeout
    @mso5000_method_wrapper
    def _set_trigger_timeout_source(self, source: TriggerSource):
        assert (
            source is not MSO5000.TriggerSource.AcLine
        ), "Trigger source cannot be ACLine."
        self.__set_parameter_str("TRIGger", "TIMeout:SOURce", source.value)

    @mso5000_method_wrapper
    def _set_trigger_timeout_slope(self, slope: TriggerSlope):
        assert (
            slope in MSO5000.TriggerSlope
        ), "Trigger slope must be one of the TriggerSlope enum values."
        self.__set_parameter_str("TRIGger", "TIMeout:SLOPe", slope.value)

    @mso5000_method_wrapper
    def _set_trigger_timeout_time(self, time: float):
        """Sets the trigger timeout time. The default unit is s."""
        assert (
            time >= 16e-9 and time <= 10
        ), "Trigger time must be between 16ns and 10s."
        self.__set_parameter_float("TRIGger", "TIMeout:TIME", time)

    @mso5000_method_wrapper
    def _set_trigger_timeout_level(self, level: float):
        """Sets the trigger timeout level. The default unit is V."""
        assert (
            level >= -15 and level <= 15
        ), "Trigger level must be between -15V and 15V."
        self.__set_parameter_float("TRIGger", "TIMeout:LEVel", level)

    @mso5000_method_wrapper
    def trigger_timeout(
        self,
        coupling: TriggerCoupling = TriggerCoupling.DC,
        sweep: TriggerSweep = TriggerSweep.Auto,
        holdoff: float = 8e-9,
        nreject: bool = False,
        source: TriggerSource = TriggerSource.Channel1,
        slope: TriggerSlope = TriggerSlope.Positive,
        time: float = 1e-6,
        level: float = 0,
    ):
        """Sets the trigger timeout settings."""
        self._set_trigger_mode(MSO5000.TriggerMode.Slope)
        self._set_trigger_coupling(coupling)
        self._set_trigger_sweep(sweep)
        self._set_trigger_holdoff(holdoff)
        self._set_trigger_noise_reject(nreject)
        self._set_trigger_timeout_source(source)
        self._set_trigger_timeout_slope(slope)
        self._set_trigger_timeout_time(time)
        self._set_trigger_timeout_level(level)

    # Trigger mode: Runt
    # Trigger mode: Windows
    # Trigger mode: Delay
    # Trigger mode: Setup and Hold
    # Trigger mode: Nth Edge
    # Trigger mode: RS232
    # Trigger mode: IIC
    # Trigger mode: CAN
    # Trigger mode: SPI
    # Trigger mode: FlexRay
    # Trigger mode: IIS
    # Trigger mode: LIN
    # Trigger mode: M1553

    # The :WAVeform commands are used to read waveform data and relevant settings. The
    # :WAVeform:MODE command is used to set the reading mode of waveform data. In different
    # modes, the definitions for the parameters are different.
    class WaveformSource(StrEnum):
        D0 = "D0"
        D1 = "D1"
        D2 = "D2"
        D3 = "D3"
        D4 = "D4"
        D5 = "D5"
        D6 = "D6"
        D7 = "D7"
        D8 = "D8"
        D9 = "D9"
        D10 = "D10"
        D11 = "D11"
        D12 = "D12"
        D13 = "D13"
        D14 = "D14"
        D15 = "D15"
        Channel1 = "CHAN1"
        Channel2 = "CHAN2"
        Channel3 = "CHAN3"
        Channel4 = "CHAN4"
        Math1 = "MATH1"
        Math2 = "MATH2"
        Math3 = "MATH3"
        Math4 = "MATH4"

    class WaveformMode(StrEnum):
        Normal = "NORM"
        Maximum = "MAX"
        Raw = "RAW"

    class WaveformFormat(StrEnum):
        Word = "WORD"
        Byte = "BYTE"
        Ascii = "ASC"

    @mso5000_method_wrapper
    def _set_waveform_source(self, source: WaveformSource):
        assert (
            source in MSO5000.WaveformSource
        ), "Waveform source must be one of the WaveformSource enum values."
        self.__set_parameter_str("WAVeform", "SOURce", source.value)

    @mso5000_method_wrapper
    def _set_waveform_mode(self, mode: WaveformMode):
        assert (
            mode in MSO5000.WaveformMode
        ), "Waveform mode must be one of the WaveformMode enum values."
        self.__set_parameter_str("WAVeform", "MODE", mode.value)

    @mso5000_method_wrapper
    def _set_waveform_format(self, format_: WaveformFormat):
        assert (
            format_ in MSO5000.WaveformFormat
        ), "Waveform format must be one of the WaveformFormat enum values."
        self.__set_parameter_str("WAVeform", "FORMat", format_.value)

    @mso5000_method_wrapper
    def _set_waveform_points(self, points: int):
        assert points >= 1, "Waveform points must be greater than 1."
        self.__set_parameter_int("WAVeform", "POINts", points)

    @mso5000_method_wrapper
    def get_waveform(
        self,
        source: WaveformSource = WaveformSource.Channel1,
        format_: WaveformFormat = WaveformFormat.Byte,
        mode: WaveformMode = WaveformMode.Normal,
        start: int = 1,
        stop: int = 1000,
    ):
        """Queries the waveform data from the oscilloscope. The default unit is V."""
        assert start >= 1, "Waveform start must be greater than 1."
        assert stop > start, "Waveform stop must be greater than start."
        self._set_waveform_source(source)
        self._set_waveform_mode(mode)
        self._set_waveform_format(format_)
        _data = [0] * (stop - start + 1)
        for _start in range(start, stop, 100):
            _stop = min(_start + 99, stop)
            self._set_waveform_start(_start)
            self._set_waveform_stop(_stop)
            self.__write(":WAVeform:DATA?")
            _response = self.__instrument._read_raw()
            assert _response[0] == 35, "Data must start with the '#' character."
            assert _response[-1] == 10, "Data must end with the '\n' character."
            _header_length = int(chr(_response[1]))
            _data_length = int(
                "".join([chr(x) for x in _response[2 : 2 + _header_length]])
            )
            _response = _response[
                2 + _header_length : 2 + _header_length + _data_length
            ]
            if format_ == MSO5000.WaveformFormat.Ascii:
                _points = "".join([chr(x) for x in _response]).split(",")
                for _index in range(_start, _stop + 1):
                    _data[_index - start] = float(_points[_index - _start])
            elif format_ == MSO5000.WaveformFormat.Word:
                for _index in range(_start, _stop + 1):
                    _rind = _index - _start
                    _byte1 = _response[_rind * 2]
                    _byte2 = _response[_rind * 2 + 1]
                    _data[_index - start] = (_byte1 << 8) + _byte2
            else:
                for _index in range(_start, _stop + 1):
                    _data[_index - start] = _response[_index - _start]
        return _data

    @mso5000_method_wrapper
    def get_waveform_xincrement(self) -> float:
        return self.__get_parameter_float("WAVeform", "XINCrement")

    @mso5000_method_wrapper
    def get_waveform_xorigin(self) -> float:
        return self.__get_parameter_float("WAVeform", "XORigin")

    @mso5000_method_wrapper
    def get_waveform_xreference(self) -> float:
        return self.__get_parameter_float("WAVeform", "XREFerence")

    @mso5000_method_wrapper
    def get_waveform_yincrement(self) -> float:
        return self.__get_parameter_float("WAVeform", "YINCrement")

    @mso5000_method_wrapper
    def get_waveform_yorigin(self) -> float:
        return self.__get_parameter_float("WAVeform", "YORigin")

    @mso5000_method_wrapper
    def get_waveform_yreference(self) -> float:
        return self.__get_parameter_float("WAVeform", "YREFerence")

    @mso5000_method_wrapper
    def _set_waveform_start(self, start: int):
        assert start >= 1, "Waveform start must be greater than 1."
        self.__set_parameter_int("WAVeform", "STARt", start)

    @mso5000_method_wrapper
    def _set_waveform_stop(self, stop: int):
        assert stop >= 1, "Waveform stop must be greater than 1."
        self.__set_parameter_int("WAVeform", "STOP", stop)

    @mso5000_method_wrapper
    def get_waveform_preamble(self) -> str:
        return self.__get_parameter_str("WAVeform", "PREamble")


_test_logger, test_method_wrapper = member_log("BearingTest")


class BearingTest(tk.Tk):
    __logger = _test_logger
    __mso5104 = None
    __sample_rate = 1e-9
    __friction_plot = FrictionPlot()
    __directory = None

    @test_method_wrapper
    def __init__(self):
        """Initializes the GUI and sets up the oscilloscope connection."""
        super().__init__()
        self.setup_logging()
        self.__logger.debug(
            "Initializing the GUI and setting up the oscilloscope connection."
        )

        self.title("Bearing Test")
        self.geometry("800x600")  # Default size of the window
        self.resizable(True, True)  # Allow resizing in both directions
        self.configure(bg="white")
        self.protocol("WM_DELETE_WINDOW", self.quit)

        # Add a status bar at the bottom of the window filled in by the logger
        self.__status_bar = ttk.Label(
            self,
            text="Status: Ready",
            relief=tk.SUNKEN,
            anchor=tk.W,
        )
        self.__status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        class StatusBarHandler(logging.Handler):
            def __init__(self, status_bar):
                super().__init__()
                self.status_bar = status_bar

            def emit(self, record):
                log_entry = self.format(record)
                self.status_bar.config(text=f"Status: {log_entry}")

        _status_bar_handler = StatusBarHandler(self.__status_bar)
        _status_bar_handler.setLevel(logging.INFO)
        logging.root.addHandler(_status_bar_handler)

        # Add a frame at the bottom for buttons
        _button_frame = ttk.Frame(self, relief=tk.RAISED)
        _button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Add a button to quit the application
        self.__quit_button = ttk.Button(
            _button_frame,
            text="Quit",
            command=self.quit,
            width=10,
        )
        self.__quit_button.pack(side=tk.RIGHT, padx=10, pady=10)
        self.locate_connected_devices()

        # Add a button to start the test
        self.__start_button = ttk.Button(
            _button_frame,
            text="Start Test",
            command=self.run_test,
            width=10,
        )
        self.__start_button.pack(side=tk.RIGHT, padx=10, pady=10)

        # Add a tabbed frame
        _notebook = ttk.Notebook(self)
        _notebook.pack(expand=1, fill="both")

        # Add a data tab
        self.__friction_plot.add_data_tab(_notebook)
        self.__friction_plot.add_position_tab(_notebook)
        self.__friction_plot.add_current_tab(_notebook)
        self.__friction_plot.add_friction_tab(_notebook)

        _log_tab = ttk.Frame(_notebook)
        _notebook.add(_log_tab, text="  Logs  ")

        # Add a text box to the Logs tab to display logger messages
        _log_frame = ttk.Frame(_log_tab)
        _log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        _log_text = tk.Text(
            _log_frame,
            bg="black",
            fg="white",
            state=tk.DISABLED,
            wrap=tk.WORD,
        )
        _log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        _log_scrollbar = ttk.Scrollbar(_log_frame, command=_log_text.yview)
        _log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        _log_text.config(yscrollcommand=_log_scrollbar.set)

        class LogTextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                log_entry = self.format(record)
                self.text_widget.config(state=tk.NORMAL)
                self.text_widget.insert(tk.END, log_entry + "\n")
                self.text_widget.config(state=tk.DISABLED)
                self.text_widget.see(tk.END)

        _log_text_handler = LogTextHandler(_log_text)
        _log_text_handler.setLevel(logging.INFO)
        logging.root.addHandler(_log_text_handler)

    @test_method_wrapper
    def setup_logging(self):
        # Configure data directories
        _home_directory = os.path.expanduser("~")
        _company_directory = pathlib.Path(_home_directory) / "Pangolin Laser Systems"
        if not _company_directory.exists():
            _company_directory.mkdir()
        _tester_directory = _company_directory / "Auto Scanner Test"
        if not _tester_directory.exists():
            _tester_directory.mkdir()
        self.__directory = _tester_directory / "Bearing Test"
        if not self.__directory.exists():
            self.__directory.mkdir()
        self.__friction_plot.RootDirectory = self.__directory

        LOGFILE = self.__directory / (
            "log_" + datetime.today().strftime("%Y%m%d") + ".log"
        )
        _handler = logging.handlers.RotatingFileHandler(
            LOGFILE, maxBytes=(1048576 * 5), backupCount=7
        )
        _formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        _handler.setFormatter(_formatter)
        logging.root.addHandler(_handler)

    @test_method_wrapper
    def locate_connected_devices(self):
        self.__logger.debug("Locating connected devices using VISA resource manager.")
        _resource_manager = pyvisa.ResourceManager()
        for _device in _resource_manager.list_resources():
            try:
                self.__logger.info(f"Found device: {_device}")
                _instrument = _resource_manager.open_resource(_device)
                if (
                    hasattr(_instrument, "manufacturer_name")
                    and _instrument.manufacturer_name == "Rigol"
                    and _instrument.model_name.startswith("MSO5")
                ):
                    self.__logger.info(f"Found MSO5000 oscilloscope: {_device}")
                    self.__mso5104 = MSO5000(_instrument)
            except:
                pass
        assert self.__mso5104 is not None, "No oscilloscope found."

        # Configure scope for test
        self.__mso5104.acquire_settings(
            averages=16,
            memory_depth=MSO5000.MemoryDepth._10K,
            type_=MSO5000.AcquireType.Averages,
        )
        self.__friction_plot.SampleRate = self.__mso5104.get_sample_rate()
        self.__mso5104.channel_settings(1, scale=2, display=True)
        self.__mso5104.channel_settings(
            2, scale=2, display=True, bandwidth_limit=MSO5000.BandwidthLimit._20M
        )
        self.__mso5104.channel_settings(
            3, scale=2, display=True, bandwidth_limit=MSO5000.BandwidthLimit._20M
        )
        self.__mso5104.timebase_settings(
            offset=2, scale=0.2, href_mode=MSO5000.HrefMode.Trigger
        )
        self.__mso5104.trigger_timeout(nreject=True, time=0.5)
        self.__mso5104.trigger_edge()
        self.__mso5104.function_generator_ramp(
            1,
            frequency=0.5,
            phase=270,
            amplitude=5,
            output_impedance=MSO5000.SourceOutputImpedance.Fifty,
        )
        self.__mso5104.function_generator_square(
            2, frequency=0.5, phase=270, amplitude=5
        )

    @test_method_wrapper
    def run_test(self):
        """Runs the test and updates the GUI."""
        # Placeholder function to run the test
        self.__logger.info("Running test...")
        _serial_number = self.get_serial_number()
        for _iteration in range(100):
            self.__friction_plot.SerialNumber = _serial_number
            self.__logger.info(
                f"Testing galvo with serial number {self.__friction_plot.SerialNumber}, iteration #{_iteration + 1}."
            )
            _start_time = time.time()
            _working_dir_path = pathlib.Path(os.path.realpath(__file__)).parent
            self.__mso5104.function_generator_state(1, True)
            self.__mso5104.function_generator_state(2, True)
            self.__mso5104.phase_align(2)
            self.__mso5104.clear()
            self.__mso5104.single()
            time.sleep(10)
            _positions = [
                2 * x
                for x in self.__mso5104.get_waveform(
                    source=MSO5000.WaveformSource.Channel2,
                    mode=MSO5000.WaveformMode.Raw,
                    format_=MSO5000.WaveformFormat.Ascii,
                    stop=10000,
                )
            ]
            _currents = [
                100 * x
                for x in self.__mso5104.get_waveform(
                    source=MSO5000.WaveformSource.Channel3,
                    mode=MSO5000.WaveformMode.Raw,
                    format_=MSO5000.WaveformFormat.Ascii,
                    stop=10000,
                )
            ]
            self.__friction_plot.add_data(_positions, _currents)
            self.__mso5104.function_generator_state(1, False)
            self.__mso5104.function_generator_state(2, False)
        self.__logger.info(
            f"Test completed in {time.time() - _start_time:.2f} seconds."
        )

    @test_method_wrapper
    def get_serial_number(self):
        """Prompts the user for the serial number of the galvo using an input box."""
        _serial_number = simpledialog.askstring(
            "Input", "Enter galvo serial number (q to quit):"
        )
        if _serial_number and re.match(r"^[A-Z]{2}[0-9]{6}$", _serial_number):
            return _serial_number
        else:
            self.__logger.error("Invalid serial number format.")
            return None


logger, method_wrapper = member_log(__name__)


@method_wrapper
def main():
    """Main function to set up the GUI and run the test."""
    # Set up GUI
    logging.root.setLevel(logging.DEBUG)
    root = BearingTest()
    root.mainloop()


if __name__ == "__main__":
    main()
