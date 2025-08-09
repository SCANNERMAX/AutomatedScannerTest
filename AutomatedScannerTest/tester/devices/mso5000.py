# -*- coding: utf-8 -*-
from venv import logger
from PySide6.QtCore import QSettings
from ctypes.wintypes import BYTE
import logging
import pyvisa
import time

from tester.devices import Device
from tester.devices.enums import (
    AcquireType,
    BandwidthLimit,
    Coupling,
    HrefMode,
    ImageColor,
    ImageType,
    Measurement,
    MeasureItem,
    MeasureMode,
    MemoryDepth,
    Units,
    SaveCsvChannel,
    SaveCsvLength,
    Source,
    SourceBurstType,
    SourceFunction,
    SourceModulation,
    SourceOutputImpedance,
    SourceSweepType,
    SourceType,
    TimebaseMode,
    TriggerCoupling,
    TriggerMode,
    TriggerSlope,
    TriggerSource,
    TriggerSweep,
    TriggerWhen,
    TriggerWindow,
    WaveformFormat,
    WaveformMode,
)

logger = logging.getLogger(__name__)

class MSO5000(Device):
    """
    MSO5000 device abstraction for RIGOL MSO5000 series oscilloscopes.

    Provides methods for instrument discovery, parameter configuration, waveform acquisition,
    and function generator control using SCPI commands via PyVISA.

    Attributes:
        __cache (dict): Class-level cache for parameter values.
        Name (str): Device name, set to "MSO5000".
        __instrument: PyVISA instrument instance after successful connection.
    """

    __cache = {}

    def __init__(self):
        """
        Initialize a new MSO5000 device instance.

        Args:
            settings (QSettings): Application settings for device configuration.

        Side Effects:
            Sets the device name and initializes the instrument reference.
        """
        super().__init__("MSO5000")
        self.__instrument = None

    def __getattr__(self, name):
        """
        Retrieve an attribute from the internal instrument or cache.

        Args:
            name (str): The attribute name.

        Returns:
            Any: The value from the instrument or cache.

        Raises:
            AttributeError: If the attribute is not found.
        """
        inst = self.__instrument
        if inst is not None:
            try:
                return getattr(inst, name)
            except AttributeError:
                pass
        try:
            return self.__cache[name]
        except KeyError:
            raise AttributeError(f"Attribute {name} not found.")

    def __query(self, message: str) -> str:
        """
        Send a SCPI query to the instrument and return the response.

        Args:
            message (str): The SCPI command string.

        Returns:
            str: The response string.

        Raises:
            AssertionError: If the message is empty or no response after retries.
        """
        _message = message.strip()
        assert _message, "Message cannot be empty."
        logger.debug(f'sending request "{_message}"...')
        for _ in range(5):
            try:
                _response = self.__instrument.query(_message).rstrip()
                if _response:
                    return _response
            except pyvisa.errors.VisaIOError:
                logger.debug("retrying...")
                time.sleep(0.1)
        raise AssertionError("Failed to get response.")

    def __write(self, message: str):
        """
        Send a SCPI command to the instrument.

        Args:
            message (str): The SCPI command string.

        Raises:
            AssertionError: If the message is empty.
        """
        _message = message.strip()
        assert _message, "Message cannot be empty."
        for _ in range(5):
            try:
                logger.debug(f'sending command "{_message}"...')
                self.__instrument.write(_message)
                return
            except pyvisa.errors.VisaIOError:
                logger.debug("retrying...")
                time.sleep(0.1)

    def __get_names(self, channel: str, parameter: str):
        """
        Generate the SCPI parameter string and cache key for a given channel and parameter.

        Args:
            channel (str): The channel identifier.
            parameter (str): The parameter name.

        Returns:
            tuple: (_attribute, _parameter) where _attribute is the cache key and _parameter is the SCPI string.
        """
        if channel.startswith(":"):
            _parameter = f"{channel}:{parameter}"
        else:
            _parameter = f":{channel}:{parameter}"
        _attribute = _parameter.replace(":", "_").lower()
        return _attribute, _parameter

    def getParameter(self, channel: str, parameter: str, default=None):
        """
        Retrieve a parameter value from the device, using cache if available.

        Args:
            channel (str): The channel identifier.
            parameter (str): The parameter name.
            default (Any, optional): Default value/type for conversion.

        Returns:
            Any: The parameter value, type-cast if default is provided.
        """
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        _cache = self.__cache
        if _attribute in _cache:
            return _cache[_attribute]
        _query_result = self.__query(f"{_parameter}?")
        if default is not None:
            try:
                _value = type(default)(_query_result)
            except Exception:
                _value = default
        else:
            _value = _query_result
        _cache[_attribute] = _value
        return _value

    def setParameter(self, channel: str, parameter: str, value):
        """
        Set a device parameter for the specified channel and cache the value.

        Args:
            channel (str): The channel identifier.
            parameter (str): The parameter name.
            value (Any): The value to set.
        """
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        if self.__cache.get(_attribute) == value:
            return
        self.__write(f"{_parameter} {value}")
        self.__cache[_attribute] = value

    def findInstrument(self):
        """
        Discover and connect to a RIGOL MSO5000 oscilloscope using PyVISA.

        Side Effects:
            Sets self.__instrument and updates device settings.
        Raises:
            AssertionError: If no MSO5000 oscilloscope is found.
        """
        _resource_manager = pyvisa.ResourceManager()
        found = False
        for _resource_name in _resource_manager.list_resources():
            try:
                logger.info(f"Found device: {_resource_name}")
                _instrument = _resource_manager.open_resource(_resource_name)
                idn = _instrument.query("*IDN?").strip()
                if "RIGOL" in idn and "MSO5" in idn:
                    logger.info(f"Found MSO5000 oscilloscope: {_resource_name}")
                    self.__instrument = _instrument
                    found = True
                    break
            except Exception as e:
                logger.debug(f"Error opening resource {_resource_name}: {e}")
        assert found, "No oscilloscope found."
        try:
            idn = self.__instrument.query("*IDN?").strip()
            parts = idn.split(",")
            if len(parts) >= 4:
                settings = {
                    "manufacturer_name": parts[0],
                    "model_name": parts[1],
                    "serial_number": parts[2],
                    "model_code": parts[1],
                    "manufacturer_id": parts[0],
                }
                for k, v in settings.items():
                    self.setSetting(k, v)
        except Exception as e:
            logger.debug(f"Error parsing IDN: {e}")
        logger.info(
            f"Connected to {getattr(self, 'model_name', 'Unknown')} oscilloscope."
        )

    # The device command system
    def autoscale(self):
        """
        Automatically adjusts the oscilloscope's vertical, horizontal, and trigger settings
        to optimally display the input signals on all active channels.

        This method sends the "AUToscale" SCPI command to the instrument, causing it to analyze
        the current input signals and configure itself for the best possible display.

        Side Effects:
            - The oscilloscope's display and measurement settings may change.
            - All channels may be enabled and their ranges adjusted automatically.

        Example:
            >>> device.autoscale()
        """
        self.__write("AUToscale")

    def clear(self):
        self.__write("CLEar")

    def run(self):
        self.__write(":RUN")

    def stop(self):
        self.__write(":STOP")

    def single(self):
        self.__write(":SINGle")

    def force_trigger(self):
        self.__write(":TFORce")

    # The :ACQ commands are used to set the memory depth of the
    # oscilloscope, the acquisition mode, the average times, as well as query
    # the current sample rate
    def set_acquire_averages(self, averages: int):
        """
        Sets the number of averages for the acquisition mode of the MSO5000 oscilloscope.

        Args:
            averages (int): The number of averages to set. Must be a power of two between 2 and 65536.

        Raises:
            AssertionError: If 'averages' is not a power of two or is outside the valid range [2, 65536].

        Side Effects:
            Updates the acquisition averages parameter on the device.
        """
        if averages < 2 or averages > 65536 or (averages & (averages - 1)) != 0:
            raise AssertionError("Averages must be a power of two between 2 and 65536.")
        self.setParameter("ACQuire", "AVERages", averages)

    def set_acquire_memory_depth(self, depth: MemoryDepth):
        assert (
            depth in MemoryDepth
        ), "Memory depth must be one of the MemoryDepth enum values."
        self.setParameter("ACQuire", "MDEPth", depth.value)

    def set_acquire_type(self, type_: AcquireType):
        assert (
            type_ in AcquireType
        ), "Acquire type must be one of the AcquireType enum values."
        self.setParameter("ACQuire", "TYPE", type_.value)

    def get_sample_rate(self) -> float:
        return self.getParameter("ACQuire", "SRATe", 0.0)

    def get_digital_sample_rate(self) -> float:
        return self.getParameter("ACQuire", "LA:SRATe", 0.0)

    def get_digital_memory_depth(self) -> float:
        return self.getParameter("ACQuire", "LA:MDEPth", 0.0)

    def set_acquire_antialiasing(self, state: bool):
        self.setParameter("ACQuire", "AALias", state)

    def acquire_settings(
        self,
        averages: int = 2,
        memory_depth: MemoryDepth = MemoryDepth.Auto,
        type_: AcquireType = AcquireType.Normal,
        antialiasing: bool = False,
    ):
        self.set_acquire_type(type_)
        if type_ == AcquireType.Averages:
            self.set_acquire_averages(averages)
        self.set_acquire_memory_depth(memory_depth)
        self.set_acquire_antialiasing(antialiasing)

    # The :BOD commands are used to execute the bode related settings and operations.

    # The :BUS<n> commands are used to execute the decoding related settings and operations.

    # The :CHANnel<n> commands are used to set or query the bandwidth limit,
    # coupling, vertical scale, vertical offset, and other vertical system
    # parameters of the analog channel.
    def set_channel_bandwidth_limit(self, channel: int, limit: BandwidthLimit):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        if self.model_name == "MSO5354":
            _valid = BandwidthLimit.__members__.values()
        elif self.model_name == "MSO5204":
            _valid = [
                BandwidthLimit.Off,
                BandwidthLimit._20M,
                BandwidthLimit._100M,
            ]
        else:
            _valid = [BandwidthLimit.Off, BandwidthLimit._20M]
        assert (
            limit in _valid
        ), "Bandwidth limit must be one of the BandwidthLimit enum values."
        self.setParameter(f"CHANnel{channel}", "BWLimit", limit.value)

    def set_channel_coupling(self, channel: int, coupling: Coupling):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert (
            coupling in Coupling
        ), "Coupling must be one of the Coupling enum values."
        self.setParameter(f"CHANnel{channel}", "COUPling", coupling.value)

    def set_channel_display(self, channel: int, display: bool):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        self.setParameter(f"CHANnel{channel}", "DISPlay", display)

    def set_channel_invert(self, channel: int, invert: bool):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        self.setParameter(f"CHANnel{channel}", "INVert", invert)

    def set_channel_offset(self, channel: int, offset: float):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        _minimum = -10
        _maximum = 100
        assert (
            offset >= _minimum and offset <= _maximum
        ), f"Offset must be between {_minimum} and {_maximum}."
        self.setParameter(f"CHANnel{channel}", "OFFSet", offset)

    def set_channel_calibration_time(self, channel: int, time: float):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert (
            time >= -100e-9 and time <= 100e-9
        ), "Delay calibration time must be between -100e-9 and 100e-9 seconds."
        self.setParameter(f"CHANnel{channel}", "TCALibrate", time)

    def set_channel_scale(self, channel: int, scale: float):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        _minimum = 500e-6
        _maximum = 10
        assert (
            scale >= _minimum and scale <= _maximum
        ), f"Scale must be between {_minimum} and {_maximum}."
        self.setParameter(f"CHANnel{channel}", "SCALe", scale)

    def set_channel_probe(self, channel: int, probe: float):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
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
        self.setParameter(f"CHANnel{channel}", "PROBe", probe)

    def set_channel_units(self, channel: int, units: Units):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert units in Units, "Units must be one of the Units enum values."
        self.setParameter(f"CHANnel{channel}", "UNITs", units.value)

    def set_channel_vernier(self, channel: int, vernier: bool):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        self.setParameter(f"CHANnel{channel}", "VERNier", vernier)

    def set_channel_position(self, channel: int, position: float):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert (
            position >= -100 and position <= 100
        ), "Position must be between -100 and 100."
        self.setParameter(f"CHANnel{channel}", "POSition", position)

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
        self.set_channel_display(channel, display)
        time.sleep(1)
        self.set_channel_probe(channel, probe)
        self.set_channel_scale(channel, scale)
        self.set_channel_bandwidth_limit(channel, bandwidth_limit)
        self.set_channel_coupling(channel, coupling)
        self.set_channel_invert(channel, invert)
        self.set_channel_offset(channel, offset)
        self.set_channel_calibration_time(channel, delay_calibration_time)
        self.set_channel_units(channel, units)
        self.set_channel_vernier(channel, vernier)
        self.set_channel_position(channel, position)

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
    def clear_registers(self):
        self.__write("*CLS")

    def get_standard_event_register_enable(self) -> BYTE:
        _response = self.__query("*ESE?")
        return BYTE(int(_response))

    def set_standard_event_register_enable(self, bits: BYTE):
        self.__write(f"*ESE {bits}")

    def get_standard_event_register_event(self) -> BYTE:
        _response = self.__query("*ESR?")
        return BYTE(int(_response))

    def get_identity(self) -> str:
        return self.__query("*IDN?")

    def get_operation_complete(self) -> bool:
        _response = self.__query("*OPC?")
        return bool(int(_response))

    def set_operation_complete(self, state: bool):
        self.__write(f"*OPC {int(state)}")

    def save(self, register: int):
        assert register >= 0 and register <= 49, "Register must be between 0 and 49."
        self.__write(f"*SAVe {register}")

    def recall(self, register: int):
        assert register >= 0 and register <= 49, "Register must be between 0 and 49."
        self.__write(f"*RCL {register}")

    def reset(self):
        """
        Resets the MSO5000 oscilloscope to its default state.

        This method sends the SCPI reset command ("*RST") to the instrument and clears the internal cache
        of parameter values. This ensures that all device settings are returned to their factory defaults
        and any cached values are invalidated.

        Side Effects:
            - Sends the "*RST" command to the oscilloscope.
            - Clears the internal parameter cache.

        Example:
            >>> device.reset()
        """
        self.__write("*RST")
        self.__cache.clear()

    def get_status_byte_register_enable(self) -> BYTE:
        _response = self.__query("*SRE?")
        return BYTE(int(_response))

    def set_status_byte_register_enable(self, bits: BYTE):
        self.__write(f"*SRE {bits}")

    def get_status_byte_register_event(self) -> BYTE:
        _response = self.__query("*STB?")
        return BYTE(int(_response))

    def self_test(self) -> str:
        _response = self.__query("*TST?")
        return _response

    def wait(self):
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
    def set_measure_source(self, source: Source):
        assert source in Source, "Source must be one of the Source enum values."
        self.setParameter("MEASure", "SOURce", source.value)

    def clear_measurement(self, item: MeasureItem):
        assert (
            item in MeasureItem
        ), "Item must be one of the MeasureItem enum values."
        self.setParameter("MEASure", "CLEar", item.value)

    def set_measure_threshold_source(self, source: Source):
        _valid = [
            Source.Channel1,
            Source.Channel2,
            Source.Channel3,
            Source.Channel4,
            Source.Math1,
            Source.Math2,
            Source.Math3,
            Source.Math4,
        ]
        assert source in _valid, f"Item must be one of {_valid}."
        self.setParameter("MEASure", "THReshold:SOURce", source.value)

    def set_measure_threshold_default(self):
        self.__write(":MEASure:THReshold:DEFault")

    def set_measure_mode(self, mode: MeasureMode):
        self.setParameter("MEASure", "MODE", mode.value)

    def set_measure_item(self, measurement: Measurement, source: Source):
        self.__write(f":MEASure:ITEM {measurement.value},{source.value}")

    def get_measure_item(self, measurement: Measurement, source: Source):
        return float(self.__query(f":MEASure:ITEM? {measurement.value},{source.value}"))

    # The :POWer commands are used to set the relevant parameters of the power supply module.

    # The :QUICk command is used to set and query the relevant parameters for shortcut keys.

    # The :RECOrd commands are used to set the relevant parameters of the record function.

    # The :REFerence commands are used to set relevant parameters for reference waveforms.

    # The :SAVE commands are used to save data or settings from the oscilloscope.
    def set_save_csv_length(self, length: SaveCsvLength):
        assert (
            length in SaveCsvLength
        ), "Length must be one of the SaveCsvLength enum values."
        self.setParameter("SAVE", "CSV:LENGth", length.value)

    def set_save_csv_channel(self, channel: SaveCsvChannel, state: bool):
        assert (
            channel in SaveCsvChannel
        ), "Channel must be one of the SaveCsvChannel enum values."
        self.setParameter("SAVE", "CSV:CHANnel", f"{channel.value},{int(state)}")

    def save_csv(
        self,
        filename: str,
        length: SaveCsvLength = SaveCsvLength.Display,
    ):
        self.set_save_csv_length(length)
        self.setParameter("SAVE", "CSV", filename)

    def save_image_type(self, type_: ImageType):
        assert (
            type_ in ImageType
        ), "Type must be one of the ImageType enum values."
        self.setParameter("SAVE", "IMAGe:TYPE", type_.value)

    def save_image_invert(self, invert: bool):
        self.__set_parameter("SAVE", "IMAGe:INVert", invert)

    def save_image_color(self, color: ImageColor):
        self.setParameter("SAVE", "COLor", color.value)

    def save_image(
        self,
        path: str,
        type_: ImageType,
        invert: bool = False,
        color: ImageColor = ImageColor.Color,
    ):
        self.save_image_type(type_)
        self.save_image_invert(invert)
        self.save_image_color(color)
        self.setParameter("SAVE", "IMAGe", path)

    def save_setup(self, path: str):
        self.setParameter("SAVE", "SETup", path)

    def save_waveform(self, path: str):
        self.setParameter("SAVE", "WAVeform", path)

    def get_save_status(self) -> bool:
        return self.getParameter("SAVE", "STATus")

    def load_setup(self, filename: str):
        self.__write(f":LOAD:SETup {filename}")

    # The :SEARch commands are used to set the relevant parameters of the search function.

    # The [:SOURce [<n>]] commands are used to set the relevant parameters of the built in function arbitrary
    # waveform generator. <n> can set to 1 or 2, which indicates the corresponding built in function/arbitrary
    # waveform generator channel. When <n> or :SOURce[<n>] is omitted, by default, the operations are
    # carried out on AWG GI.
    def function_generator_state(self, channel: int, state: bool):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        self.setParameter(f"SOURce{channel}", f"OUTPut{channel}:STATe", state)

    def set_source_function(self, channel: int, function: SourceFunction):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            function in SourceFunction
        ), "Function must be one of the Waveform enum values."
        self.setParameter(f"SOURce{channel}", "FUNCtion", function.value)

    def set_source_type(self, channel: int, type_: SourceType):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert type in SourceType, "Type must be one of the Type enum values."
        self.setParameter(f"SOURce{channel}", "TYPE", type_.value)

    def set_source_frequency(self, channel: int, frequency: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            frequency > 0.01 and frequency < 25000000
        ), "Frequency must be between 0.1 and 25000000 Hz."
        self.setParameter(f"SOURce{channel}", "FREQuency", frequency)

    def set_source_phase(self, channel: int, phase: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert phase >= 0 and phase <= 360, "Phase must be between 0 and 360 degrees."
        self.setParameter(f"SOURce{channel}", "PHASe", phase)

    def set_source_amplitude(self, channel: int, amplitude: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            amplitude >= 0.02 and amplitude <= 5
        ), "Amplitude must be between 0.02 and 5 Vpp."
        self.setParameter(
            f"SOURce{channel}", "VOLTage:LEVel:IMMediate:AMPLitude", amplitude
        )

    def set_source_offset(self, channel: int, offset: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            offset >= -2.5 and offset <= 2.5
        ), "Offset must be between -2.5 and 2.5 V."
        self.setParameter(f"SOURce{channel}", "VOLTage:LEVel:IMMediate:OFFSet", offset)

    def phase_align(self, channel: int):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        self.__write(f"SOURce{channel}:PHASe:INITiate")

    def set_source_output_impedance(
        self, channel: int, impedance: SourceOutputImpedance
    ):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            impedance in SourceOutputImpedance
        ), "Output impedance must be one of the OutputImpedance enum values."
        self.setParameter(f"SOURce{channel}", "OUTPut:IMPedance", impedance.value)

    # Function Generator Function: Sinusoid
    def function_generator_sinusoid(
        self,
        channel: int,
        frequency: float = 1000,
        phase: float = 0,
        amplitude: float = 0.5,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.Sinusoid)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: Square
    def function_generator_square(
        self,
        channel: int,
        frequency: float = 1000,
        phase: float = 0,
        amplitude: float = 0.5,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.Square)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: RAMP
    def set_source_function_ramp_symmetry(self, channel: int, symmetry: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert symmetry >= 1 and symmetry <= 100, "Symmetry must be between 1 and 100%."
        self.setParameter(f"SOURce{channel}", "FUNCtion:RAMP:SYMMetry", symmetry)

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
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.Ramp)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_function_ramp_symmetry(channel, symmetry)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: PULSe
    def set_source_duty_cycle(self, channel: int, duty_cycle: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            duty_cycle >= 10 and duty_cycle <= 90
        ), "Duty cycle must be between 10 and 90%."
        self.setParameter(f"SOURce{channel}", "PULSe:DCYCle", duty_cycle)

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
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.Pulse)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_duty_cycle(channel, duty_cycle)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: NOISe
    def function_generator_noise(
        self,
        channel: int,
        amplitude: float = 0.5,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.Noise)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: DC
    def function_generator_dc(
        self,
        channel: int,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.DC)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: SINC
    def function_generator_sinc(
        self,
        channel: int,
        frequency: float = 1000,
        phase: float = 0,
        amplitude: float = 0.5,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.Sinc)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: EXPRise
    # Function Generator Function: EXPFall
    # Function Generator Function: ECG
    # Function Generator Function: GAUSs
    # Function Generator Function: LORentz
    # Function Generator Function: HAVersine
    # Function Generator Function: ARBitrary
    # Function Generator Type: None
    def function_generator_no_modulation(self, channel: int):
        self.function_generator_state(channel, False)
        self.set_source_type(channel, SourceType._None)

    # Function Generator Type: Modulation
    def set_source_mod_type(self, channel: int, mod_type: SourceModulation):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            mod_type in SourceModulation
        ), "Modulation type must be one of the Modulation enum values."
        self.setParameter(f"SOURce{channel}", "MODulation:TYPE", mod_type.value)

    def set_source_mod_am_depth(self, channel: int, depth: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            depth >= 0 and depth <= 120
        ), "Modulation amplitude depth must be between 0 and 120%."
        self.setParameter(f"SOURce{channel}", "MOD:DEPTh", depth)

    def set_source_mod_am_freq(self, channel: int, frequency: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            frequency >= 1 and frequency <= 50
        ), "Modulation frequency must be between 1 and 50 Hz."
        self.setParameter(f"SOURce{channel}", "MOD:AM:INTernal:FREQuency", frequency)

    def set_source_mod_fm_freq(self, channel: int, frequency: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            frequency >= 1 and frequency <= 50
        ), "Modulation frequency must be between 1 and 50 Hz."
        self.setParameter(f"SOURce{channel}", "MOD:FM:INTernal:FREQuency", frequency)

    def set_source_mod_am_function(self, channel: int, function: SourceFunction):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert function in [
            SourceFunction.SINusoid,
            SourceFunction.SQUare,
            SourceFunction.RAMP,
            SourceFunction.NOISe,
        ], "Modulation function must be one of SINusoid, SQUare, RAMP, NOISe."
        self.setParameter(
            f"SOURce{channel}", "MOD:AM:INTernal:FUNCtion", function.value
        )

    def set_source_mod_fm_function(self, channel: int, function: SourceFunction):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert function in [
            SourceFunction.SINusoid,
            SourceFunction.SQUare,
            SourceFunction.RAMP,
            SourceFunction.NOISe,
        ], "Modulation function must be one of SINusoid, SQUare, RAMP, NOISe."
        self.setParameter(
            f"SOURce{channel}", "MOD:FM:INTernal:FUNCtion", function.value
        )

    def set_source_mod_fm_deviation(self, channel: int, deviation: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            deviation >= 0
        ), "Modulation frequency deviation must be greater than or equal to 0 Hz."
        self.setParameter(f"SOURce{channel}", "MOD:FM:DEViation", deviation)

    def function_generator_modulation(
        self,
        channel: int,
        type_: SourceModulation = SourceModulation.AmplitudeModulation,
        am_depth: float = 100,
        frequency: float = 1000,
        function: SourceFunction = SourceFunction.Sinusoid,
        fm_deviation: float = 1000,
    ):
        self.function_generator_state(channel, False)
        self.set_source_type(channel, SourceType.Modulated)
        self.set_source_mod_type(channel, type_)
        if type_ == SourceModulation.AM:
            self._set_source_am_depth(channel, am_depth)
            self.set_source_mod_am_freq(channel, frequency)
            self.set_source_mod_am_function(channel, function)
        elif type_ == SourceModulation.FM:
            self._set_source_mod_fm_frequency(channel, frequency)
            self.set_source_mod_fm_function(channel, function)
            self.set_source_mod_fm_deviation(channel, fm_deviation)

    # Function Generator Type: Sweep
    def set_source_sweep_type(self, channel: int, type_: SourceSweepType):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            type_ in SourceSweepType
        ), "Sweep type must be one of the SweepType enum values."
        self.setParameter(f"SOURce{channel}", "SWEep:TYPE", type_.value)

    def set_source_sweep_sweep_time(self, channel: int, time: int):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            time >= 1 and time <= 500
        ), "Sweep time must be between 1 and 500 seconds."
        self.setParameter(f"SOURce{channel}", "SWEep:STIMe", time)

    def set_source_sweep_return_time(self, channel: int, time: int):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            time >= 1 and time <= 500
        ), "Return time must be between 1 and 500 seconds."
        self.setParameter(f"SOURce{channel}", "SWEep:BTIMe", time)

    def function_generator_sweep(
        self,
        channel: int,
        type_: SourceSweepType = SourceSweepType.Linear,
        sweep_time: int = 1,
        return_time: int = 0,
    ):
        self.function_generator_state(channel, False)
        self.set_source_type(channel, SourceType.Sweep)
        self.set_source_sweep_type(channel, type_)
        self.set_source_sweep_sweep_time(channel, sweep_time)
        self.set_source_sweep_return_time(channel, return_time)

    # Function Generator Type: Burst
    def set_source_burst_type(self, channel: int, type_: SourceBurstType):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            type_ in SourceBurstType
        ), "Burst type must be one of the BurstType enum values."
        self.setParameter(f"SOURce{channel}", "BURSt:TYPE", type_.value)

    def set_source_burst_cycles(self, channel: int, cycles: int):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            cycles >= 1 and cycles <= 1000000
        ), "Burst cycles must be between 1 and 1000000."
        self.setParameter(f"SOURce{channel}", "BURSt:CYCLes", cycles)

    def set_source_burst_delay(self, channel: int, delay: int):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            delay >= 1 and delay <= 1000000
        ), "Burst delay must be between 1 and 1000000."
        self.setParameter(f"SOURce{channel}", "BURSt:DELay", delay)

    def function_generator_burst(
        self,
        channel: int,
        type_: SourceBurstType = SourceBurstType.Ncycle,
        cycles: int = 1,
        delay: int = 0,
    ):
        self.function_generator_state(channel, False)
        self.set_source_type(channel, SourceType.Sweep)
        self.set_source_burst_type(channel, type_)
        self.set_source_burst_cycles(channel, cycles)
        self.set_source_burst_delay(channel, delay)

    # The :SYSTem commands are used to set sound, language, and other relevant system settings.
    def get_system_error(self) -> str:
        return self.getParameter("SYSTem", "ERRor:NEXT")

    # The :TIMebase commands are used to set the horizontal system. For example, enable the delayed sweep,
    # set the horizontal time base mode, etc.
    def set_timebase_delay_enable(self, enable: bool):
        self.__set_parameter("TIMebase", "DELay:ENABle", enable)

    def set_timebase_delay_offset(self, offset: float):
        self.setParameter("TIMebase", "DELay:OFFSet", offset)

    def set_timebase_delay_scale(self, scale: float):
        self.setParameter("TIMebase", "DELay:SCALe", scale)

    def timebase_delay(
        self, enable: bool = False, offset: float = 0, scale: float = 500e-9
    ):
        self.set_timebase_delay_enable(enable)
        self.set_timebase_delay_offset(offset)
        self.set_timebase_delay_scale(scale)

    def set_timebase_offset(self, offset: float):
        self.setParameter("TIMebase", "MAIN:OFFSet", offset)

    def set_timebase_scale(self, scale: float):
        self.setParameter("TIMebase", "MAIN:SCALe", scale)

    def set_timebase_mode(self, mode: TimebaseMode):
        assert (
            mode in TimebaseMode
        ), "Timebase mode must be one of the TimebaseMode enum values."
        self.setParameter("TIMebase", "MODE", mode.value)

    def set_timebase_href_mode(self, mode: HrefMode):
        assert (
            mode in HrefMode
        ), "Href mode must be one of the HrefMode enum values."
        self.setParameter("TIMebase", "HREFerence:MODE", mode.value)

    def set_timebase_position(self, position: int):
        assert (
            position >= -500 and position <= 500
        ), "Horizontal reference position must be between -500 to 500."
        self.setParameter("TIMebase", "HREFerence:POSition", position)

    def set_timebase_vernier(self, vernier: bool):
        self.setParameter("TIMebase", "VERNier", vernier)

    def timebase_settings(
        self,
        offset: float = 0,
        scale: float = 1e-6,
        mode: TimebaseMode = TimebaseMode.Main,
        href_mode: HrefMode = HrefMode.Center,
        position: float = 0,
        vernier: bool = False,
    ):
        self.set_timebase_mode(mode)
        self.set_timebase_scale(scale)
        self.set_timebase_offset(offset)
        self.set_timebase_href_mode(href_mode)
        self.set_timebase_position(position)
        self.set_timebase_vernier(vernier)

    # The [:TRACe[< n>]] commands are used to set the arbitrary waveform parameters of the built in signal
    # sources. <n> can be 1 or 2 which denotes the corresponding built in signal source channel. If <n>
    # or :TRACe[<n>] is omitted, the operation will be applied to source 1 by default.

    # The :TRIGger commands are used to set the trigger system of the oscilloscope.
    def get_trigger_status(self):
        """
        Retrieves the current trigger status from the device.

        Returns:
            TriggerStatus: An enumeration value representing the current trigger status.

        Raises:
            ValueError: If the returned status string cannot be converted to a TriggerStatus enum.
        """
        _status = self.getParameter("TRIGger", "STATus")
        return TriggerStatus(_status)

    def set_trigger_mode(self, mode: TriggerMode):
        """
        Sets the trigger mode of the MSO5000 device.

        Args:
            mode (TriggerMode): The desired trigger mode, must be a member of the TriggerMode enum.

        Raises:
            AssertionError: If the provided mode is not a valid TriggerMode enum value.

        Side Effects:
            Updates the trigger mode parameter on the device via the __set_parameter_str method.
        """
        assert (
            mode in TriggerMode
        ), "Trigger mode must be one of the TriggerMode enum values."
        self.setParameter("TRIGger", "MODE", mode.value)

    def set_trigger_coupling(self, coupling: TriggerCoupling):
        """
        Sets the trigger coupling mode for the device.

        Args:
            coupling (TriggerCoupling): The desired trigger coupling mode. Must be a member of the TriggerCoupling enum.

        Raises:
            AssertionError: If the provided coupling is not a valid TriggerCoupling enum value.

        """
        assert (
            coupling in TriggerCoupling
        ), "Trigger coupling must be one of the TriggerCoupling enum values."
        self.setParameter("TRIGger", "COUPling", coupling.value)

    def set_trigger_sweep(self, sweep: TriggerSweep):
        """
        Sets the trigger sweep mode for the device.

        Args:
            sweep (TriggerSweep): The desired trigger sweep mode. Must be a member of the TriggerSweep enum.

        Raises:
            AssertionError: If the provided sweep is not a valid TriggerSweep enum value.

        Side Effects:
            Updates the device's trigger sweep setting by sending the appropriate command.

        Example:
            set_trigger_sweep(TriggerSweep.AUTO)
        """
        assert (
            sweep in TriggerSweep
        ), "Trigger sweep must be one of the TriggerSweep enum values."
        self.setParameter("TRIGger", "SWEep", sweep.value)

    def set_trigger_holdoff(self, holdoff: float):
        """
        Sets the trigger holdoff time for the device.

        The trigger holdoff is the minimum time between valid triggers. This method asserts that the
        holdoff value is within the valid range of 8 nanoseconds (8e-9 s) to 10 seconds.

        Args:
            holdoff (float): The desired trigger holdoff time in seconds. Must be between 8e-9 and 10.

        Raises:
            AssertionError: If the holdoff value is outside the allowed range.
        """
        assert (
            holdoff >= 8e-9 and holdoff <= 10
        ), "Trigger holdoff must be between 8ns and 10s."
        self.setParameter("TRIGger", "HOLDoff", holdoff)

    def set_trigger_noise_reject(self, status: bool):
        """
        Enables or disables the noise reject function for the trigger system.

        Args:
            status (bool): If True, enables noise rejection on the trigger. If False, disables it.

        Raises:
            Any exceptions raised by the underlying __set_parameter_bool method.

        Note:
            Noise rejection helps to prevent false triggering caused by noise on the input signal.
        """
        self.setParameter("TRIGger", "NREJect", status)

    # Trigger mode: Edge
    def set_trigger_edge_source(self, source: TriggerSource):
        """
        Set the trigger edge source for the oscilloscope.

        Args:
            source (TriggerSource): The trigger source to set. Must be a member of the TriggerSource enum.

        Raises:
            AssertionError: If the provided source is not a valid TriggerSource enum value.

        This method configures the oscilloscope to use the specified trigger edge source.
        """
        assert (
            source in TriggerSource
        ), "Trigger edge source must be one of the TriggerSource enum values."
        self.setParameter("TRIGger", "EDGE:SOURce", source.value)

    def set_trigger_edge_slope(self, slope: TriggerSlope):
        """
        Sets the trigger edge slope for the oscilloscope.

        Args:
            slope (TriggerSlope): The desired trigger edge slope. Must be a member of TriggerSlope.

        Raises:
            AssertionError: If the provided slope is not a valid TriggerSlope enum value.

        Side Effects:
            Updates the oscilloscope's trigger edge slope setting via the __set_parameter_str method.
        """
        assert (
            slope in TriggerSlope
        ), "Trigger edge slope must be one of the TriggerEdgeSlope enum values."
        self.setParameter("TRIGger", "EDGE:SLOPe", slope.value)

    def set_trigger_edge_level(self, level: float):
        """
        Sets the trigger edge level for the oscilloscope.

        Args:
            level (float): The voltage level to set for the trigger edge, in volts.
                Must be between -15 and 15 (inclusive).

        Raises:
            AssertionError: If the provided level is outside the valid range [-15, 15].

        """
        assert (
            level >= -15 and level <= 15
        ), "Trigger edge level must be between -15 and 15 V."
        self.setParameter("TRIGger", "EDGE:LEVel", level)

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
        """
        Configures the oscilloscope to use edge triggering with the specified parameters.

        Parameters:
            coupling (TriggerCoupling, optional): The trigger coupling mode (e.g., DC, AC). Defaults to TriggerCoupling.DC.
            sweep (TriggerSweep, optional): The trigger sweep mode (e.g., Auto, Normal). Defaults to TriggerSweep.Auto.
            holdoff (float, optional): The trigger holdoff time in seconds. Defaults to 8e-9.
            nreject (bool, optional): Whether to enable noise rejection. Defaults to False.
            edge_source (TriggerSource, optional): The source channel for edge triggering. Defaults to TriggerSource.Channel1.
            edge_slope (TriggerSlope, optional): The edge slope for triggering (e.g., Positive, Negative). Defaults to TriggerSlope.Positive.
            edge_level (float, optional): The voltage level at which to trigger. Defaults to 0.

        Returns:
            None
        """
        self.set_trigger_mode(TriggerMode.Edge)
        self.set_trigger_coupling(coupling)
        self.set_trigger_sweep(sweep)
        self.set_trigger_holdoff(holdoff)
        self.set_trigger_noise_reject(nreject)
        self.set_trigger_edge_source(edge_source)
        self.set_trigger_edge_slope(edge_slope)
        self.set_trigger_edge_level(edge_level)

    # Trigger mode: Pulse
    def set_trigger_pulse_source(self, source: TriggerSource):
        """
        Sets the trigger pulse source for the oscilloscope.

        Args:
            source (TriggerSource): The trigger source to set. Must be a member of the TriggerSource enum.

        Raises:
            AssertionError: If the provided source is not a valid TriggerSource enum value.

        """
        assert (
            source in TriggerSource
        ), "Trigger pulse source must be one of the TriggerSource enum values."
        self.setParameter("TRIGger", "PULSe:SOURce", source.value)

    def set_trigger_pulse_when(self, when: TriggerWhen):
        """
        Sets the trigger condition for pulse width triggering on the device.

        Args:
            when (TriggerWhen): The trigger condition, must be a value from the TriggerWhen enum.

        Raises:
            AssertionError: If the provided when is not a valid TriggerWhen enum value.

        This method configures the oscilloscope to trigger when the pulse width condition specified by 'when' is met.
        """
        assert (
            when in TriggerWhen
        ), "Trigger pulse when must be one of the TriggerWhen enum values."
        self.setParameter("TRIGger", "PULSe:WHEN", when.value)

    def set_trigger_pulse_upper_width(self, width: float):
        """
        Sets the upper width for the trigger pulse.

        Parameters:
            width (float): The upper width of the trigger pulse in seconds. Must be less than or equal to 10.

        Raises:
            AssertionError: If the specified width is greater than 10 seconds.

        This method configures the trigger system to use the specified upper width for pulse detection.
        """
        assert width <= 10, "Trigger pulse upper width must be less than 10s."
        self.setParameter("TRIGger", "PULSe:UWIDth", width)

    def set_trigger_pulse_lower_width(self, width: float):
        """
        Sets the lower width threshold for the trigger pulse.

        Args:
            width (float): The lower width of the trigger pulse in seconds.
                Must be greater than or equal to 8 picoseconds (8e-12 s).

        Raises:
            AssertionError: If the specified width is less than 8 picoseconds.

        """
        assert width >= 8e-12, "Trigger pulse lower width must be greater than 8 ps."
        self.setParameter("TRIGger", "PULSe:LWIDth", width)

    def set_trigger_pulse_level(self, level: float):
        """
        Sets the trigger pulse level for the device.

        Args:
            level (float): The desired trigger pulse level in volts. Must be between -15 and 15.

        Raises:
            AssertionError: If the specified level is not within the range -15 to 15.

        """
        assert (
            level >= -15 and level <= 15
        ), "Trigger pulse level must be between -15 and 15 V."
        self.setParameter("TRIGger", "PULSe:LEVel", level)

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
        """
        Configures the oscilloscope to trigger on a pulse with specified parameters.

        Parameters:
            coupling (TriggerCoupling, optional): The trigger coupling mode (e.g., DC, AC). Defaults to TriggerCoupling.DC.
            sweep (TriggerSweep, optional): The trigger sweep mode (e.g., Auto, Normal). Defaults to TriggerSweep.Auto.
            holdoff (float, optional): The trigger holdoff time in seconds. Defaults to 8e-9.
            nreject (bool, optional): Whether to enable noise rejection. Defaults to False.
            pulse_source (TriggerSource, optional): The source channel for the pulse trigger. Defaults to TriggerSource.Channel1.
            pulse_when (TriggerWhen, optional): The pulse condition (e.g., Greater, Less). Defaults to TriggerWhen.Greater.
            pulse_upper_width (float, optional): The upper width threshold for the pulse in seconds. Defaults to 2e-6.
            pulse_lower_width (float, optional): The lower width threshold for the pulse in seconds. Defaults to 1e-6.
            pulse_level (float, optional): The voltage level at which to trigger on the pulse. Defaults to 0.

        Returns:
            None
        """
        self.set_trigger_mode(TriggerMode.Edge)
        self.set_trigger_coupling(coupling)
        self.set_trigger_sweep(sweep)
        self.set_trigger_holdoff(holdoff)
        self.set_trigger_noise_reject(nreject)
        self.set_trigger_pulse_source(pulse_source)
        self.set_trigger_pulse_when(pulse_when)
        self.set_trigger_pulse_upper_width(pulse_upper_width)
        self.set_trigger_pulse_lower_width(pulse_lower_width)
        self.set_trigger_pulse_level(pulse_level)

    # Trigger mode: Slope
    def set_trigger_slope_source(self, source: TriggerSource):
        """
        Sets the trigger slope source for the oscilloscope.

        Args:
            source (TriggerSource): The trigger source to set. Must be one of
                TriggerSource.CHANnel1, TriggerSource.CHANnel2,
                TriggerSource.CHANnel3, or TriggerSource.CHANnel4.

        Raises:
            AssertionError: If the provided source is not a valid channel trigger source.

        """
        assert source in [
            TriggerSource.Channel1,
            TriggerSource.Channel2,
            TriggerSource.Channel3,
            TriggerSource.Channel4,
        ], "Trigger source must be one of Channel 1, Channel 2, Channel 3 or Channel 4."
        self.setParameter("TRIGger", "SLOPe:SOURce", source.value)

    def set_trigger_slope_when(self, when: TriggerWhen):
        """
        Sets the trigger slope condition for the oscilloscope.

        Args:
            when (TriggerWhen): The trigger condition to set. Must be a value from the TriggerWhen enum.

        Raises:
            AssertionError: If the provided when is not a valid TriggerWhen enum value.

        """
        assert (
            when in TriggerWhen
        ), "Trigger when must be one of the TriggerWhen enum values."
        self.setParameter("TRIGger", "SLOPe:WHEN", when.value)

    def set_trigger_slope_time_upper(self, time: float):
        """
        Sets the upper time limit for the trigger slope.

        Args:
            time (float): The upper time limit in seconds. Must be less than or equal to 10.

        Raises:
            AssertionError: If the specified time is greater than 10 seconds.

        """
        assert time <= 10, "Upper time limit must be less than 10 s."
        self.setParameter("TRIGger", "SLOPe:TUPPer", time)

    def set_trigger_slope_time_lower(self, time: float):
        """
        Sets the lower time limit for the trigger slope on the oscilloscope.

        Parameters:
            time (float): The lower time limit for the trigger slope, in seconds. Must be greater than or equal to 800 picoseconds (800e-12 s).

        Raises:
            AssertionError: If the provided time is less than 800 picoseconds.

        This method configures the oscilloscope to use the specified lower time limit for the trigger slope, ensuring precise triggering based on signal slope duration.
        """
        assert time >= 800e-12, "Lower time limit must be greater than 800 ps."
        self.setParameter("TRIGger", "SLOPe:TLOWer", time)

    def set_trigger_slope_window(self, window: TriggerWindow):
        """
        Sets the trigger slope window of the oscilloscope.

        Args:
            window (TriggerWindow): The trigger slope window to set. Must be a value from the TriggerWindow enum.

        Raises:
            AssertionError: If the provided window is not a valid TriggerWindow enum value.

        This method configures the oscilloscope to use the specified trigger slope window by sending the appropriate command.
        """
        assert (
            window in TriggerWindow
        ), "Trigger window must be one of the TriggerWindow enum values."
        self.setParameter("TRIGger", "SLOPe:WINDow", window.value)

    def set_trigger_slope_amplitude_upper(self, amplitude: float):
        """
        Sets the upper amplitude limit for the trigger slope on the oscilloscope.

        Args:
            amplitude (float): The upper amplitude threshold to set for the trigger slope.

        Raises:
            ValueError: If the provided amplitude is out of the valid range for the oscilloscope.
        """
        self.setParameter("TRIGger", "SLOPe:ALEVel", amplitude)

    def set_trigger_slope_amplitude_lower(self, amplitude: float):
        """
        Sets the lower amplitude limit for the trigger slope on the oscilloscope.

        Args:
            amplitude (float): The lower amplitude threshold to set for the trigger slope.

        Raises:
            ValueError: If the provided amplitude is out of the valid range for the device.

        Note:
            This method configures the oscilloscope's trigger system to only respond to signals
            exceeding the specified lower amplitude limit on the slope.
        """
        self.setParameter("TRIGger", "SLOPe:BLEVel", amplitude)

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
        """
        Configures the slope trigger settings for the oscilloscope.

        Parameters:
            coupling (TriggerCoupling): The trigger coupling mode (e.g., DC, AC).
            sweep (TriggerSweep): The trigger sweep mode (e.g., Auto, Normal).
            holdoff (float): The trigger holdoff time in seconds.
            nreject (bool): Enable or disable trigger noise rejection.
            source (TriggerSource): The trigger source channel.
            when (TriggerWhen): The trigger condition (e.g., Greater, Less).
            time_upper (float): The upper time threshold for the slope trigger in seconds.
            time_lower (float): The lower time threshold for the slope trigger in seconds.
            window (TriggerWindow): The trigger window type.
            amplitude_upper (float): The upper amplitude threshold for the slope trigger.
            amplitude_lower (float): The lower amplitude threshold for the slope trigger.

        Sets the oscilloscope to slope trigger mode and applies the specified trigger parameters.
        """
        self.set_trigger_mode(TriggerMode.Slope)
        self.set_trigger_coupling(coupling)
        self.set_trigger_sweep(sweep)
        self.set_trigger_holdoff(holdoff)
        self.set_trigger_noise_reject(nreject)
        self.set_trigger_slope_source(source)
        self.set_trigger_slope_when(when)
        self.set_trigger_slope_time_upper(time_upper)
        self.set_trigger_slope_time_lower(time_lower)
        self.set_trigger_slope_window(window)
        self.set_trigger_slope_amplitude_upper(amplitude_upper)
        self.set_trigger_slope_amplitude_lower(amplitude_lower)

    # Trigger mode: Video
    # Trigger mode: Pattern
    # Trigger mode: Duration
    # Trigger mode: Timeout
    def set_trigger_timeout_source(self, source: TriggerSource):
        """
        Sets the trigger timeout source for the oscilloscope.

        Args:
            source (TriggerSource): The trigger source to set. Must not be `TriggerSource.AcLine`.

        Raises:
            AssertionError: If the provided source is `TriggerSource.AcLine`.

        """
        assert (
            source is not TriggerSource.AcLine
        ), "Trigger source cannot be ACLine."
        self.setParameter("TRIGger", "TIMeout:SOURce", source.value)

    def set_trigger_timeout_slope(self, slope: TriggerSlope):
        """
        Sets the trigger timeout slope for the device.

        Args:
            slope (TriggerSlope): The desired trigger slope. Must be a member of the TriggerSlope enum.

        Raises:
            AssertionError: If the provided slope is not a valid TriggerSlope enum value.

        """
        assert (
            slope in TriggerSlope
        ), "Trigger slope must be one of the TriggerSlope enum values."
        self.setParameter("TRIGger", "TIMeout:SLOPe", slope.value)

    def set_trigger_timeout_time(self, time: float):
        """
        Sets the trigger timeout time for the device.

        The trigger timeout time determines how long the device waits for a trigger event before timing out.

        Args:
            time (float): The timeout duration in seconds. Must be between 16 nanoseconds (16e-9) and 10 seconds.

        Raises:
            AssertionError: If the provided time is not within the valid range [16e-9, 10].
        """
        assert (
            time >= 16e-9 and time <= 10
        ), "Trigger time must be between 16ns and 10s."
        self.setParameter("TRIGger", "TIMeout:TIME", time)

    def set_trigger_timeout_level(self, level: float):
        """
        Sets the trigger timeout level for the device.

        Args:
            level (float): The desired trigger timeout level in volts. Must be between -15 and 15.

        Raises:
            AssertionError: If the specified level is not within the range -15 to 15.

        """
        assert (
            level >= -15 and level <= 15
        ), "Trigger level must be between -15V and 15V."
        self.setParameter("TRIGger", "TIMeout:LEVel", level)

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
        """
        Configures the timeout trigger settings for the oscilloscope.

        Parameters:
            coupling (TriggerCoupling, optional): The trigger coupling mode (e.g., DC, AC). Defaults to TriggerCoupling.DC.
            sweep (TriggerSweep, optional): The trigger sweep mode (e.g., Auto, Normal). Defaults to TriggerSweep.Auto.
            holdoff (float, optional): The trigger holdoff time in seconds. Defaults to 8e-9.
            nreject (bool, optional): Whether to enable noise rejection. Defaults to False.
            source (TriggerSource, optional): The source channel for the pulse trigger. Defaults to TriggerSource.Channel1.
            slope (TriggerSlope, optional): The trigger slope (e.g., Positive, Negative). Defaults to TriggerSlope.Positive.
            time (float, optional): The timeout duration in seconds. Defaults to 1e-6.
            level (float, optional): The trigger level. Defaults to 0.

        This method sets the oscilloscope to use the timeout trigger mode and applies the specified settings.
        """
        self.set_trigger_mode(TriggerMode.Slope)
        self.set_trigger_coupling(coupling)
        self.set_trigger_sweep(sweep)
        self.set_trigger_holdoff(holdoff)
        self.set_trigger_noise_reject(nreject)
        self.set_trigger_timeout_source(source)
        self.set_trigger_timeout_slope(slope)
        self.set_trigger_timeout_time(time)
        self.set_trigger_timeout_level(level)

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
    def set_waveform_source(self, source: Source):
        """
        Sets the waveform source for the device.

        Args:
            source (Source): The source to set for waveform acquisition. Must be a member of the Source enum.

        Raises:
            AssertionError: If the provided source is not a valid member of Source.

        """
        assert (
            source in Source
        ), "Waveform source must be one of the WaveformSource enum values."
        self.setParameter("WAVeform", "SOURce", source.value)

    def set_waveform_mode(self, mode: WaveformMode):
        """
        Sets the waveform mode of the device.

        Args:
            mode (WaveformMode): The desired waveform mode to set. Must be a member of the WaveformMode enum.

        Raises:
            AssertionError: If the provided mode is not a valid WaveformMode enum value.

        Side Effects:
            Updates the device's waveform mode parameter via the __set_parameter_str method.
        """
        assert (
            mode in WaveformMode
        ), "Waveform mode must be one of the WaveformMode enum values."
        self.setParameter("WAVeform", "MODE", mode.value)

    def set_waveform_format(self, format_: WaveformFormat):
        """
        Sets the waveform data format for the device.

        Args:
            format_ (WaveformFormat): The desired waveform format, must be a member of the WaveformFormat enum.

        Raises:
            AssertionError: If the provided format_ is not a valid WaveformFormat enum value.

        """
        assert (
            format_ in WaveformFormat
        ), "Waveform format must be one of the WaveformFormat enum values."
        self.setParameter("WAVeform", "FORMat", format_.value)

    def set_waveform_points(self, points: int):
        """
        Sets the number of waveform points for the device.

        Args:
            points (int): The number of points to set for the waveform. Must be greater than or equal to 1.

        Raises:
            AssertionError: If points is less than 1.
        """
        assert points >= 1, "Waveform points must be greater than 1."
        self.setParameter("WAVeform", "POINts", points)

    def get_waveform(
        self,
        source: Source = Source.Channel1,
        format_: WaveformFormat = WaveformFormat.Byte,
        mode: WaveformMode = WaveformMode.Normal,
        start: int = 1,
        stop: int = 1000,
    ):
        """
        Reads waveform data from the oscilloscope for a specified channel and range.

        Parameters:
            source (Source, optional): The waveform source channel. Defaults to Source.Channel1.
            format_ (WaveformFormat, optional): The format of the waveform data (Byte, Word, or Ascii). Defaults to WaveformFormat.Byte.
            mode (WaveformMode, optional): The acquisition mode for the waveform. Defaults to WaveformMode.Normal.
            start (int, optional): The starting data point (1-based index). Must be >= 1. Defaults to 1.
            stop (int, optional): The ending data point (exclusive). Must be greater than start. Defaults to 1000.

        Returns:
            list: The acquired waveform data as a list of values, with type depending on the selected format.

        Raises:
            AssertionError: If start < 1, stop <= start, or if the oscilloscope response is malformed.
        """
        assert start >= 1, "Waveform start must be greater than 1."
        assert stop > start, "Waveform stop must be greater than start."
        self.set_waveform_source(source)
        self.set_waveform_mode(mode)
        self.set_waveform_format(format_)
        _start = start
        _stop = min(start + 100, stop)
        _data = [0] * (stop - start + 1)
        while _start < stop:
            self.set_waveform_start(_start)
            self.set_waveform_stop(_stop)
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
            if format_ == WaveformFormat.Ascii:
                _points = "".join([chr(x) for x in _response]).split(",")
                for _index in range(_start, _stop):
                    _data[_index - start] = float(_points[_index - _start])
            elif format_ == WaveformFormat.Word:
                for _index in range(_start, _stop):
                    _rind = _index - _start
                    _byte1 = _response[_rind * 2]
                    _byte2 = _response[_rind * 2 + 1]
                    _data[_index - start] = (_byte1 << 8) + _byte2
            else:
                for _index in range(_start, _stop):
                    _data[_index - start] = _response[_index - _start]
            _start = _stop
            _stop = min(_start + 100, stop)
        return _data

    def get_waveform_xincrement(self) -> float:
        """
        Retrieves the horizontal (X-axis) increment value of the current waveform.

        Returns:
            float: The time interval between consecutive data points in the waveform.
        """
        return self.getParameter("WAVeform", "XINCrement")

    def get_waveform_xorigin(self) -> float:
        """
        Retrieves the X origin value of the current waveform.

        Returns:
            float: The X origin of the waveform, typically representing the starting point on the X-axis (time axis) in waveform data.
        """
        return self.getParameter("WAVeform", "XORigin")

    def get_waveform_xreference(self) -> float:
        """
        Retrieves the X reference value of the current waveform.

        Returns:
            float: The X reference value of the waveform, typically representing the horizontal offset or reference point on the X-axis.
        """
        return self.getParameter("WAVeform", "XREFerence")

    def get_waveform_yincrement(self) -> float:
        """
        Retrieves the vertical increment (Y increment) value of the current waveform.

        Returns:
            float: The Y increment value, representing the voltage difference between adjacent data points in the waveform.
        """
        return self.getParameter("WAVeform", "YINCrement")

    def get_waveform_yorigin(self) -> float:
        """
        Gets the Y origin value of the current waveform.

        Returns:
            float: The Y origin of the waveform as a floating-point number.
        """
        return self.getParameter("WAVeform", "YORigin")

    def get_waveform_yreference(self) -> float:
        """
        Retrieves the Y reference value of the current waveform.

        Returns:
            float: The Y reference value used for scaling the waveform data.
        """
        return self.getParameter("WAVeform", "YREFerence")

    def set_waveform_start(self, start: int):
        """
        Sets the starting point for waveform data acquisition.

        Parameters:
            start (int): The starting index for the waveform data. Must be greater than or equal to 1.

        Raises:
            AssertionError: If 'start' is less than 1.
        """
        assert start >= 1, "Waveform start must be greater than 1."
        self.setParameter("WAVeform", "STARt", start)

    def set_waveform_stop(self, stop: int):
        """
        Sets the stop point for waveform data acquisition.

        Parameters:
            stop (int): The index at which to stop waveform acquisition. Must be greater than or equal to 1.

        Raises:
            AssertionError: If 'stop' is less than 1.
        """
        assert stop >= 1, "Waveform stop must be greater than 1."
        self.setParameter("WAVeform", "STOP", stop)

    def get_waveform_preamble(self) -> str:
        """
        Retrieves the waveform preamble from the device.

        Returns:
            str: The waveform preamble as a string, typically containing information about the waveform format, such as scaling, offset, and other acquisition parameters.
        """
        return self.getParameter("WAVeform", "PREamble")
