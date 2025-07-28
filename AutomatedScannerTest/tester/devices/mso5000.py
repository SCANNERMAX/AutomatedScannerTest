# -*- coding: utf-8 -*-
import time
from PySide6.QtCore import QSettings
from ctypes.wintypes import BYTE
from enum import StrEnum
import pyvisa

import tester
from tester.devices import Device


class MSO5000(Device):
    __cache = {}

    def __init__(self):
        """
        Initializes a new instance of the MSO5000 device class.

        Args:
            settings (QSettings): The application settings used for device configuration.

        Side Effects:
            Calls the base Device class initializer with the device name "MSO5000" and the provided settings.
            Initializes the internal instrument reference to None.
        """
        super().__init__("MSO5000")
        self.__instrument = None

    def __getattr__(self, name):
        """
        Retrieves an attribute from the internal instrument or cache.

        Args:
            name (str): The name of the attribute to retrieve.

        Returns:
            Any: The value of the requested attribute from the instrument or cache.

        Raises:
            AttributeError: If the attribute is not found in either the instrument or cache.
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
        Sends a query command to the instrument and retrieves the response.

        Args:
            message (str): The SCPI command string to send to the instrument.

        Returns:
            str: The response string from the instrument.

        Raises:
            AssertionError: If the message is empty or if no response is received after 5 attempts.
            pyvisa.errors.VisaIOError: If a VISA IO error occurs during communication.

        Side Effects:
            Logs the request and any retries to the device logger.
            Waits 0.1 seconds between retries if a VISA IO error occurs.
        """
        _message = message.strip()
        assert _message, "Message cannot be empty."
        self.logger.debug(f'sending request "{_message}"...')
        for _ in range(5):
            try:
                _response = self.__instrument.query(_message).rstrip()
                if _response:
                    return _response
            except pyvisa.errors.VisaIOError:
                self.logger.debug("retrying...")
                time.sleep(0.1)
        raise AssertionError("Failed to get response.")

    def __write(self, message: str):
        """
        Sends a command to the instrument.

        Args:
            message (str): The SCPI command string to send to the instrument.

        Raises:
            AssertionError: If the message is empty.

        Side Effects:
            Logs the command being sent and any retries to the device logger.
            Retries up to 5 times if a pyvisa VisaIOError occurs, waiting 0.1 seconds between attempts.
        """
        _message = message.strip()
        assert _message, "Message cannot be empty."
        for _ in range(5):
            try:
                self.logger.debug(f'sending command "{_message}"...')
                self.__instrument.write(_message)
                return
            except pyvisa.errors.VisaIOError:
                self.logger.debug("retrying...")
                time.sleep(0.1)

    def __get_names(self, channel: str, parameter: str):
        """
        Generates the SCPI parameter string and corresponding cache attribute name for a given channel and parameter.

        Args:
            channel (str): The channel identifier (e.g., "CHANnel1", "ACQuire", etc.). May optionally start with ':'.
            parameter (str): The parameter name to be appended to the channel (e.g., "SCALe", "TYPE", etc.).

        Returns:
            tuple:
                _attribute (str): The cache key for the parameter, formatted as a lowercase string with colons replaced by underscores.
                _parameter (str): The SCPI command string for the parameter, formatted with a leading colon if not present.

        Example:
            >>> self.__get_names("CHANnel1", "SCALe")
            ('_channel1_scale', ':CHANnel1:SCALe')
        """
        # Avoid repeated string operations and use f-string efficiently
        if channel.startswith(':'):
            _parameter = f"{channel}:{parameter}"
        else:
            _parameter = f":{channel}:{parameter}"
        # Use str.translate for faster character replacement and avoid .lower() if not needed
        _attribute = _parameter.replace(":", "_").lower()
        return _attribute, _parameter

    def _get_parameter(self, channel: str, parameter: str, default=None):
        """
        Retrieves a parameter value from the device, using caching to avoid redundant queries.

        Args:
            channel (str): The channel identifier (e.g., "CHANnel1", "ACQuire").
            parameter (str): The parameter name to query (e.g., "SCALe", "TYPE").
            default (Any, optional): The default value and type to cast the result to if provided.

        Returns:
            Any: The value of the requested parameter, type-cast to the type of 'default' if specified.

        Raises:
            AssertionError: If 'channel' or 'parameter' is empty.
            Exception: If type conversion fails and 'default' is provided.

        Side Effects:
            Caches the result for future queries.
            Sends a query to the instrument if the value is not cached.
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

    def _set_parameter(self, channel: str, parameter: str, value):
        """
        Sets a device parameter for the specified channel and caches the value.

        Args:
            channel (str): The channel identifier (e.g., "CHANnel1", "ACQuire").
            parameter (str): The parameter name to set (e.g., "SCALe", "TYPE").
            value (Any): The value to set for the parameter.

        Returns:
            None

        Raises:
            AssertionError: If 'channel' or 'parameter' is empty.

        Side Effects:
            Sends a command to the instrument to set the parameter.
            Updates the internal cache with the new value.
            Skips sending the command if the cached value matches the new value.
        """
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        if self.__cache.get(_attribute) == value:
            return
        self.__write(f"{_parameter} {value}")
        self.__cache[_attribute] = value

    class Source(StrEnum):
        """
        Enumeration representing possible signal sources for the MSO5000 device.

        Attributes:
            D0-D15: Digital channels 0 through 15.
            Channel1-Channel4: Analog channels 1 through 4 ("CHAN1" to "CHAN4").
            Math1-Math4: Math function channels ("MATH1" to "MATH4").
        """
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

    class MemoryDepth(StrEnum):
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
        Normal = "NORM"
        Averages = "AVER"
        Peak = "PEAK"
        HighResolution = "HRES"

    class BandwidthLimit(StrEnum):
        Off = "OFF"
        Auto = "AUTO"
        _20M = "20M"
        _100M = "100M"
        _200M = "200M"

    class Coupling(StrEnum):
        AC = "AC"
        DC = "DC"
        Ground = "GND"

    class Units(StrEnum):
        Voltage = "VOLT"
        Watt = "WATT"
        Ampere = "AMP"
        Unknown = "UNKN"

    def findInstrument(self):
        """
        Finds and connects to a MSO5000 oscilloscope instrument using PyVISA.

        This method scans all available VISA resources, attempts to open each one,
        and queries its identification string. If a device is identified as a RIGOL MSO5000
        oscilloscope, it sets the internal instrument reference and updates device settings
        with manufacturer and model information.

        Side Effects:
            - Sets self.__instrument to the connected instrument.
            - Updates device settings with manufacturer and model information.
            - Logs device discovery and connection status.

        Raises:
            AssertionError: If no MSO5000 oscilloscope is found.
            Exception: If there is an error opening a resource or parsing the IDN string.

        Example:
            >>> device = MSO5000(settings)
            >>> device.find_instrument()
        """
        _resource_manager = pyvisa.ResourceManager()
        found = False
        for _resource_name in _resource_manager.list_resources():
            try:
                self.logger.info(f"Found device: {_resource_name}")
                _instrument = _resource_manager.open_resource(_resource_name)
                idn = _instrument.query("*IDN?").strip()
                # Example IDN: "RIGOL TECHNOLOGIES,MSO5074,DS5A123456789,00.01.01"
                if "RIGOL" in idn and "MSO5" in idn:
                    self.logger.info(f"Found MSO5000 oscilloscope: {_resource_name}")
                    self.__instrument = _instrument
                    found = True
                    break
            except Exception as e:
                self.logger.debug(f"Error opening resource {_resource_name}: {e}")
        assert found, "No oscilloscope found."
        # Parse IDN string for model and serial info
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
            self.logger.debug(f"Error parsing IDN: {e}")
        self.logger.info(f"Connected to {getattr(self, 'model_name', 'Unknown')} oscilloscope.")

    # The device command system
    @tester._member_logger
    def autoscale(self):
        self.__write("AUToscale")

    @tester._member_logger
    def clear(self):
        self.__write("CLEar")

    @tester._member_logger
    def run(self):
        self.__write(":RUN")

    @tester._member_logger
    def stop(self):
        self.__write(":STOP")

    @tester._member_logger
    def single(self):
        self.__write(":SINGle")

    @tester._member_logger
    def force_trigger(self):
        self.__write(":TFORce")

    # The :ACQ commands are used to set the memory depth of the
    # oscilloscope, the acquisition mode, the average times, as well as query
    # the current sample rate
    @tester._member_logger
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
        self._set_parameter("ACQuire", "AVERages", averages)

    @tester._member_logger
    def set_acquire_memory_depth(self, depth: MemoryDepth):
        assert (
            depth in MSO5000.MemoryDepth
        ), "Memory depth must be one of the MemoryDepth enum values."
        self._set_parameter("ACQuire", "MDEPth", depth.value)

    @tester._member_logger
    def set_acquire_type(self, type_: AcquireType):
        assert (
            type_ in MSO5000.AcquireType
        ), "Acquire type must be one of the AcquireType enum values."
        self._set_parameter("ACQuire", "TYPE", type_.value)

    @tester._member_logger
    def get_sample_rate(self) -> float:
        return self._get_parameter("ACQuire", "SRATe", 0.0)

    @tester._member_logger
    def get_digital_sample_rate(self) -> float:
        return self._get_parameter("ACQuire", "LA:SRATe", 0.0)

    @tester._member_logger
    def get_digital_memory_depth(self) -> float:
        return self._get_parameter("ACQuire", "LA:MDEPth", 0.0)

    @tester._member_logger
    def set_acquire_antialiasing(self, state: bool):
        self._set_parameter("ACQuire", "AALias", state)

    @tester._member_logger
    def acquire_settings(
        self,
        averages: int = 2,
        memory_depth: MemoryDepth = MemoryDepth.Auto,
        type_: AcquireType = AcquireType.Normal,
        antialiasing: bool = False,
    ):
        self.set_acquire_type(type_)
        if type_ == MSO5000.AcquireType.Averages:
            self.set_acquire_averages(averages)
        self.set_acquire_memory_depth(memory_depth)
        self.set_acquire_antialiasing(antialiasing)

    # The :BOD commands are used to execute the bode related settings and operations.

    # The :BUS<n> commands are used to execute the decoding related settings and operations.

    # The :CHANnel<n> commands are used to set or query the bandwidth limit,
    # coupling, vertical scale, vertical offset, and other vertical system
    # parameters of the analog channel.
    @tester._member_logger
    def set_channel_bandwidth_limit(self, channel: int, limit: BandwidthLimit):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
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
        self._set_parameter(f"CHANnel{channel}", "BWLimit", limit.value)

    @tester._member_logger
    def set_channel_coupling(self, channel: int, coupling: Coupling):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert (
            coupling in MSO5000.Coupling
        ), "Coupling must be one of the Coupling enum values."
        self._set_parameter(f"CHANnel{channel}", "COUPling", coupling.value)

    @tester._member_logger
    def set_channel_display(self, channel: int, display: bool):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        self._set_parameter(f"CHANnel{channel}", "DISPlay", display)

    @tester._member_logger
    def set_channel_invert(self, channel: int, invert: bool):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        self._set_parameter(f"CHANnel{channel}", "INVert", invert)

    @tester._member_logger
    def set_channel_offset(self, channel: int, offset: float):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        _minimum = -10
        _maximum = 100
        assert (
            offset >= _minimum and offset <= _maximum
        ), f"Offset must be between {_minimum} and {_maximum}."
        self._set_parameter(f"CHANnel{channel}", "OFFSet", offset)

    @tester._member_logger
    def set_channel_calibration_time(self, channel: int, time: float):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert (
            time >= -100e-9 and time <= 100e-9
        ), "Delay calibration time must be between -100e-9 and 100e-9 seconds."
        self._set_parameter(f"CHANnel{channel}", "TCALibrate", time)

    @tester._member_logger
    def set_channel_scale(self, channel: int, scale: float):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        _minimum = 500e-6
        _maximum = 10
        assert (
            scale >= _minimum and scale <= _maximum
        ), f"Scale must be between {_minimum} and {_maximum}."
        self._set_parameter(f"CHANnel{channel}", "SCALe", scale)

    @tester._member_logger
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
        self._set_parameter(f"CHANnel{channel}", "PROBe", probe)

    @tester._member_logger
    def set_channel_units(self, channel: int, units: Units):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert units in MSO5000.Units, "Units must be one of the Units enum values."
        self._set_parameter(f"CHANnel{channel}", "UNITs", units.value)

    @tester._member_logger
    def set_channel_vernier(self, channel: int, vernier: bool):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        self._set_parameter(f"CHANnel{channel}", "VERNier", vernier)

    @tester._member_logger
    def set_channel_position(self, channel: int, position: float):
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert (
            position >= -100 and position <= 100
        ), "Position must be between -100 and 100."
        self._set_parameter(f"CHANnel{channel}", "POSition", position)

    @tester._member_logger
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
    @tester._member_logger
    def clear_registers(self):
        self.__write("*CLS")

    @tester._member_logger
    def get_standard_event_register_enable(self) -> BYTE:
        _response = self.__query("*ESE?")
        return BYTE(int(_response))

    @tester._member_logger
    def set_standard_event_register_enable(self, bits: BYTE):
        self.__write(f"*ESE {bits}")

    @tester._member_logger
    def get_standard_event_register_event(self) -> BYTE:
        _response = self.__query("*ESR?")
        return BYTE(int(_response))

    @tester._member_logger
    def get_identity(self) -> str:
        return self.__query("*IDN?")

    @tester._member_logger
    def get_operation_complete(self) -> bool:
        _response = self.__query("*OPC?")
        return bool(int(_response))

    @tester._member_logger
    def set_operation_complete(self, state: bool):
        self.__write(f"*OPC {int(state)}")

    @tester._member_logger
    def save(self, register: int):
        assert register >= 0 and register <= 49, "Register must be between 0 and 49."
        self.__write(f"*SAVe {register}")

    @tester._member_logger
    def recall(self, register: int):
        assert register >= 0 and register <= 49, "Register must be between 0 and 49."
        self.__write(f"*RCL {register}")

    @tester._member_logger
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

    @tester._member_logger
    def get_status_byte_register_enable(self) -> BYTE:
        _response = self.__query("*SRE?")
        return BYTE(int(_response))

    @tester._member_logger
    def set_status_byte_register_enable(self, bits: BYTE):
        self.__write(f"*SRE {bits}")

    @tester._member_logger
    def get_status_byte_register_event(self) -> BYTE:
        _response = self.__query("*STB?")
        return BYTE(int(_response))

    @tester._member_logger
    def self_test(self) -> str:
        _response = self.__query("*TST?")
        return _response

    @tester._member_logger
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
    class MeasureItem(StrEnum):
        Item1 = "ITEM1"
        Item2 = "ITEM2"
        Item3 = "ITEM3"
        Item4 = "ITEM4"
        Item5 = "ITEM5"
        Item6 = "ITEM6"
        Item7 = "ITEM7"
        Item8 = "ITEM8"
        Item9 = "ITEM9"
        Item10 = "ITEM10"
        All = "ALL"

    class Measurement(StrEnum):
        VoltageMaximum = "VMAX"
        VoltageMinimum = "VMIN"
        VoltagePeakToPeak = "VPP"
        VoltageTOP = "VTOP"
        VoltageBase = "VBASe"
        VoltageAmplitude = "VAMP"
        VoltageAverage = "VAVG"
        VoltageRms = "VRMS"
        Overshoot = "OVERshoot"
        Preshoot = "PREShoot"
        MARea = "MARea"
        MPARea = "MPARea"
        Period = "PERiod"
        Frequency = "FREQuency"
        RiseTime = "RTIMe"
        FallTime = "FTIMe"
        PositivePulseWidth = "PWIDth"
        NegativePulseWidth = "NWIDth"
        PositiveDuty = "PDUTy"
        NegativeDuty = "NDUTy"
        TVMAX = "TVMAX"
        TVMIN = "TVMIN"
        PositiveSlewrate = "PSLewrate"
        NegativeSlewrate = "NSLewrate"
        VUPPer = "VUPPer"
        VMID = "VMID"
        VLOWer = "VLOWer"
        VARiance = "VARiance"
        PVRMs = "PVRMs"
        PPULses = "PPULses"
        NPULses = "NPULses"
        PEDGes = "PEDGes"
        NEDGes = "NEDGes"
        RRDelay = "RRDelay"
        RFDelay = "RFDelay"
        FRDelay = "FRDelay"
        FFDelay = "FFDelay"
        RRPHase = "RRPHase"
        RFPHase = "RFPHase"
        FRPHase = "FRPHase"
        FFPHase = "FFPHase"

    @tester._member_logger
    def set_measure_source(self, source: Source):
        assert source in MSO5000.Source, "Source must be one of the Source enum values."
        self._set_parameter("MEASure", "SOURce", source.value)

    @tester._member_logger
    def clear_measurement(self, item: MeasureItem):
        assert (
            item in MSO5000.MeasureItem
        ), "Item must be one of the MeasureItem enum values."
        self._set_parameter("MEASure", "CLEar", item.value)

    @tester._member_logger
    def set_measure_threshold_source(self, source: Source):
        _valid = [
            MSO5000.Source.Channel1,
            MSO5000.Source.Channel2,
            MSO5000.Source.Channel3,
            MSO5000.Source.Channel4,
            MSO5000.Source.Math1,
            MSO5000.Source.Math2,
            MSO5000.Source.Math3,
            MSO5000.Source.Math4,
        ]
        assert source in _valid, f"Item must be one of {_valid}."
        self._set_parameter("MEASure", "THReshold:SOURce", source.value)

    @tester._member_logger
    def set_measure_threshold_default(self):
        self.__write(":MEASure:THReshold:DEFault")

    class MeasureMode(StrEnum):
        Normal = "NORMal"
        Precision = "PRECision"

    @tester._member_logger
    def set_measure_mode(self, mode: MeasureMode):
        self._set_parameter("MEASure", "MODE", mode.value)

    @tester._member_logger
    def set_measure_item(self, measurement: Measurement, source: Source):
        self.__write(f":MEASure:ITEM {measurement.value},{source.value}")

    @tester._member_logger
    def get_measure_item(self, measurement: Measurement, source: Source):
        return float(self.__query(f":MEASure:ITEM? {measurement.value},{source.value}"))

    # The :POWer commands are used to set the relevant parameters of the power supply module.

    # The :QUICk command is used to set and query the relevant parameters for shortcut keys.

    # The :RECOrd commands are used to set the relevant parameters of the record function.

    # The :REFerence commands are used to set relevant parameters for reference waveforms.

    # The :SAVE commands are used to save data or settings from the oscilloscope.
    class SaveCsvLength(StrEnum):
        Display = "DISP"
        Maximum = "MAX"

    class SaveCsvChannel(StrEnum):
        Channel1 = "CHAN1"
        Channel2 = "CHAN2"
        Channel3 = "CHAN3"
        Channel4 = "CHAN4"
        Pod1 = "POD1"
        Pod2 = "POD2"

    class ImageType(StrEnum):
        Bitmap = "BMP24"
        Jpeg = "JPEG"
        Png = "PNG"
        Tiff = "TIFF"

    class ImageColor(StrEnum):
        Color = "COL"
        Gray = "GRAY"

    @tester._member_logger
    def set_save_csv_length(self, length: SaveCsvLength):
        assert (
            length in MSO5000.SaveCsvLength
        ), "Length must be one of the SaveCsvLength enum values."
        self._set_parameter("SAVE", "CSV:LENGth", length.value)

    @tester._member_logger
    def set_save_csv_channel(self, channel: SaveCsvChannel, state: bool):
        assert (
            channel in MSO5000.SaveCsvChannel
        ), "Channel must be one of the SaveCsvChannel enum values."
        self._set_parameter("SAVE", "CSV:CHANnel", f"{channel.value},{int(state)}")

    @tester._member_logger
    def save_csv(
        self,
        filename: str,
        length: SaveCsvLength = SaveCsvLength.Display,
    ):
        self.set_save_csv_length(length)
        self._set_parameter("SAVE", "CSV", filename)

    @tester._member_logger
    def save_image_type(self, type_: ImageType):
        assert (
            type_ in MSO5000.ImageType
        ), "Type must be one of the ImageType enum values."
        self._set_parameter("SAVE", "IMAGe:TYPE", type_.value)

    @tester._member_logger
    def save_image_invert(self, invert: bool):
        self.__set_parameter("SAVE", "IMAGe:INVert", invert)

    @tester._member_logger
    def save_image_color(self, color: ImageColor):
        self._set_parameter("SAVE", "COLor", color.value)

    @tester._member_logger
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
        self._set_parameter("SAVE", "IMAGe", path)

    @tester._member_logger
    def save_setup(self, path: str):
        self._set_parameter("SAVE", "SETup", path)

    @tester._member_logger
    def save_waveform(self, path: str):
        self._set_parameter("SAVE", "WAVeform", path)

    @tester._member_logger
    def get_save_status(self) -> bool:
        return self._get_parameter("SAVE", "STATus")

    @tester._member_logger
    def load_setup(self, filename: str):
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

    @tester._member_logger
    def function_generator_state(self, channel: int, state: bool):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        self._set_parameter(f"SOURce{channel}", f"OUTPut{channel}:STATe", state)

    @tester._member_logger
    def set_source_function(self, channel: int, function: SourceFunction):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            function in MSO5000.SourceFunction
        ), "Function must be one of the Waveform enum values."
        self._set_parameter(f"SOURce{channel}", "FUNCtion", function.value)

    @tester._member_logger
    def set_source_type(self, channel: int, type_: SourceType):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert type in MSO5000.SourceType, "Type must be one of the Type enum values."
        self._set_parameter(f"SOURce{channel}", "TYPE", type_.value)

    @tester._member_logger
    def set_source_frequency(self, channel: int, frequency: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            frequency > 0.01 and frequency < 25000000
        ), "Frequency must be between 0.1 and 25000000 Hz."
        self._set_parameter(f"SOURce{channel}", "FREQuency", frequency)

    @tester._member_logger
    def set_source_phase(self, channel: int, phase: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert phase >= 0 and phase <= 360, "Phase must be between 0 and 360 degrees."
        self._set_parameter(f"SOURce{channel}", "PHASe", phase)

    @tester._member_logger
    def set_source_amplitude(self, channel: int, amplitude: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            amplitude >= 0.02 and amplitude <= 5
        ), "Amplitude must be between 0.02 and 5 Vpp."
        self._set_parameter(
            f"SOURce{channel}", "VOLTage:LEVel:IMMediate:AMPLitude", amplitude
        )

    @tester._member_logger
    def set_source_offset(self, channel: int, offset: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            offset >= -2.5 and offset <= 2.5
        ), "Offset must be between -2.5 and 2.5 V."
        self._set_parameter(
            f"SOURce{channel}", "VOLTage:LEVel:IMMediate:OFFSet", offset
        )

    @tester._member_logger
    def phase_align(self, channel: int):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        self.__write(f"SOURce{channel}:PHASe:INITiate")

    @tester._member_logger
    def set_source_output_impedance(
        self, channel: int, impedance: SourceOutputImpedance
    ):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            impedance in MSO5000.SourceOutputImpedance
        ), "Output impedance must be one of the OutputImpedance enum values."
        self._set_parameter(
            f"SOURce{channel}", "OUTPut:IMPedance", impedance.value
        )

    # Function Generator Function: Sinusoid
    @tester._member_logger
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
        self.set_source_function(channel, MSO5000.SourceFunction.Sinusoid)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: Square
    @tester._member_logger
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
        self.set_source_function(channel, MSO5000.SourceFunction.Square)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: RAMP
    @tester._member_logger
    def set_source_function_ramp_symmetry(self, channel: int, symmetry: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert symmetry >= 1 and symmetry <= 100, "Symmetry must be between 1 and 100%."
        self._set_parameter(
            f"SOURce{channel}", "FUNCtion:RAMP:SYMMetry", symmetry
        )

    @tester._member_logger
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
        self.set_source_function(channel, MSO5000.SourceFunction.Ramp)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_function_ramp_symmetry(channel, symmetry)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: PULSe
    @tester._member_logger
    def set_source_duty_cycle(self, channel: int, duty_cycle: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            duty_cycle >= 10 and duty_cycle <= 90
        ), "Duty cycle must be between 10 and 90%."
        self._set_parameter(f"SOURce{channel}", "PULSe:DCYCle", duty_cycle)

    @tester._member_logger
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
        self.set_source_function(channel, MSO5000.SourceFunction.Pulse)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_duty_cycle(channel, duty_cycle)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: NOISe
    @tester._member_logger
    def function_generator_noise(
        self,
        channel: int,
        amplitude: float = 0.5,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        self.function_generator_state(channel, False)
        self.set_source_function(channel, MSO5000.SourceFunction.Noise)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: DC
    @tester._member_logger
    def function_generator_dc(
        self,
        channel: int,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        self.function_generator_state(channel, False)
        self.set_source_function(channel, MSO5000.SourceFunction.DC)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    # Function Generator Function: SINC
    @tester._member_logger
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
        self.set_source_function(channel, MSO5000.SourceFunction.Sinc)
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
    @tester._member_logger
    def function_generator_no_modulation(self, channel: int):
        self.function_generator_state(channel, False)
        self.set_source_type(channel, MSO5000.SourceType._None)

    # Function Generator Type: Modulation
    @tester._member_logger
    def set_source_mod_type(self, channel: int, mod_type: SourceModulation):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            mod_type in MSO5000.SourceModulation
        ), "Modulation type must be one of the Modulation enum values."
        self._set_parameter(f"SOURce{channel}", "MODulation:TYPE", mod_type.value)

    @tester._member_logger
    def set_source_mod_am_depth(self, channel: int, depth: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            depth >= 0 and depth <= 120
        ), "Modulation amplitude depth must be between 0 and 120%."
        self._set_parameter(f"SOURce{channel}", "MOD:DEPTh", depth)

    @tester._member_logger
    def set_source_mod_am_freq(self, channel: int, frequency: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            frequency >= 1 and frequency <= 50
        ), "Modulation frequency must be between 1 and 50 Hz."
        self._set_parameter(
            f"SOURce{channel}", "MOD:AM:INTernal:FREQuency", frequency
        )

    @tester._member_logger
    def set_source_mod_fm_freq(self, channel: int, frequency: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            frequency >= 1 and frequency <= 50
        ), "Modulation frequency must be between 1 and 50 Hz."
        self._set_parameter(
            f"SOURce{channel}", "MOD:FM:INTernal:FREQuency", frequency
        )

    @tester._member_logger
    def set_source_mod_am_function(self, channel: int, function: SourceFunction):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert function in [
            MSO5000.SourceFunction.SINusoid,
            MSO5000.SourceFunction.SQUare,
            MSO5000.SourceFunction.RAMP,
            MSO5000.SourceFunction.NOISe,
        ], "Modulation function must be one of SINusoid, SQUare, RAMP, NOISe."
        self._set_parameter(
            f"SOURce{channel}", "MOD:AM:INTernal:FUNCtion", function.value
        )

    @tester._member_logger
    def set_source_mod_fm_function(self, channel: int, function: SourceFunction):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert function in [
            MSO5000.SourceFunction.SINusoid,
            MSO5000.SourceFunction.SQUare,
            MSO5000.SourceFunction.RAMP,
            MSO5000.SourceFunction.NOISe,
        ], "Modulation function must be one of SINusoid, SQUare, RAMP, NOISe."
        self._set_parameter(
            f"SOURce{channel}", "MOD:FM:INTernal:FUNCtion", function.value
        )

    @tester._member_logger
    def set_source_mod_fm_deviation(self, channel: int, deviation: float):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            deviation >= 0
        ), "Modulation frequency deviation must be greater than or equal to 0 Hz."
        self._set_parameter(f"SOURce{channel}", "MOD:FM:DEViation", deviation)

    @tester._member_logger
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
        self.set_source_type(channel, MSO5000.SourceType.Modulated)
        self.set_source_mod_type(channel, type_)
        if type_ == MSO5000.SourceModulation.AM:
            self._set_source_am_depth(channel, am_depth)
            self.set_source_mod_am_freq(channel, frequency)
            self.set_source_mod_am_function(channel, function)
        elif type_ == MSO5000.SourceModulation.FM:
            self._set_source_mod_fm_frequency(channel, frequency)
            self.set_source_mod_fm_function(channel, function)
            self.set_source_mod_fm_deviation(channel, fm_deviation)

    # Function Generator Type: Sweep
    @tester._member_logger
    def set_source_sweep_type(self, channel: int, type_: SourceSweepType):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            type_ in MSO5000.SourceSweepType
        ), "Sweep type must be one of the SweepType enum values."
        self._set_parameter(f"SOURce{channel}", "SWEep:TYPE", type_.value)

    @tester._member_logger
    def set_source_sweep_sweep_time(self, channel: int, time: int):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            time >= 1 and time <= 500
        ), "Sweep time must be between 1 and 500 seconds."
        self._set_parameter(f"SOURce{channel}", "SWEep:STIMe", time)

    @tester._member_logger
    def set_source_sweep_return_time(self, channel: int, time: int):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            time >= 1 and time <= 500
        ), "Return time must be between 1 and 500 seconds."
        self._set_parameter(f"SOURce{channel}", "SWEep:BTIMe", time)

    @tester._member_logger
    def function_generator_sweep(
        self,
        channel: int,
        type_: SourceSweepType = SourceSweepType.Linear,
        sweep_time: int = 1,
        return_time: int = 0,
    ):
        self.function_generator_state(channel, False)
        self.set_source_type(channel, MSO5000.SourceType.Sweep)
        self.set_source_sweep_type(channel, type_)
        self.set_source_sweep_sweep_time(channel, sweep_time)
        self.set_source_sweep_return_time(channel, return_time)

    # Function Generator Type: Burst
    @tester._member_logger
    def set_source_burst_type(self, channel: int, type_: SourceBurstType):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            type_ in MSO5000.SourceBurstType
        ), "Burst type must be one of the BurstType enum values."
        self._set_parameter(f"SOURce{channel}", "BURSt:TYPE", type_.value)

    @tester._member_logger
    def set_source_burst_cycles(self, channel: int, cycles: int):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            cycles >= 1 and cycles <= 1000000
        ), "Burst cycles must be between 1 and 1000000."
        self._set_parameter(f"SOURce{channel}", "BURSt:CYCLes", cycles)

    @tester._member_logger
    def set_source_burst_delay(self, channel: int, delay: int):
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            delay >= 1 and delay <= 1000000
        ), "Burst delay must be between 1 and 1000000."
        self._set_parameter(f"SOURce{channel}", "BURSt:DELay", delay)

    @tester._member_logger
    def function_generator_burst(
        self,
        channel: int,
        type_: SourceBurstType = SourceBurstType.Ncycle,
        cycles: int = 1,
        delay: int = 0,
    ):
        self.function_generator_state(channel, False)
        self.set_source_type(channel, MSO5000.SourceType.Sweep)
        self.set_source_burst_type(channel, type_)
        self.set_source_burst_cycles(channel, cycles)
        self.set_source_burst_delay(channel, delay)

    # The :SYSTem commands are used to set sound, language, and other relevant system settings.
    @tester._member_logger
    def get_system_error(self) -> str:
        return self._get_parameter("SYSTem", "ERRor:NEXT")

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

    @tester._member_logger
    def set_timebase_delay_enable(self, enable: bool):
        self.__set_parameter("TIMebase", "DELay:ENABle", enable)

    @tester._member_logger
    def set_timebase_delay_offset(self, offset: float):
        self._set_parameter("TIMebase", "DELay:OFFSet", offset)

    @tester._member_logger
    def set_timebase_delay_scale(self, scale: float):
        self._set_parameter("TIMebase", "DELay:SCALe", scale)

    @tester._member_logger
    def timebase_delay(
        self, enable: bool = False, offset: float = 0, scale: float = 500e-9
    ):
        self.set_timebase_delay_enable(enable)
        self.set_timebase_delay_offset(offset)
        self.set_timebase_delay_scale(scale)

    @tester._member_logger
    def set_timebase_offset(self, offset: float):
        self._set_parameter("TIMebase", "MAIN:OFFSet", offset)

    @tester._member_logger
    def set_timebase_scale(self, scale: float):
        self._set_parameter("TIMebase", "MAIN:SCALe", scale)

    @tester._member_logger
    def set_timebase_mode(self, mode: TimebaseMode):
        assert (
            mode in MSO5000.TimebaseMode
        ), "Timebase mode must be one of the TimebaseMode enum values."
        self._set_parameter("TIMebase", "MODE", mode.value)

    @tester._member_logger
    def set_timebase_href_mode(self, mode: HrefMode):
        assert (
            mode in MSO5000.HrefMode
        ), "Href mode must be one of the HrefMode enum values."
        self._set_parameter("TIMebase", "HREFerence:MODE", mode.value)

    @tester._member_logger
    def set_timebase_position(self, position: int):
        assert (
            position >= -500 and position <= 500
        ), "Horizontal reference position must be between -500 to 500."
        self._set_parameter("TIMebase", "HREFerence:POSition", position)

    @tester._member_logger
    def set_timebase_vernier(self, vernier: bool):
        self._set_parameter("TIMebase", "VERNier", vernier)

    @tester._member_logger
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
        """
        Enumeration representing the possible trigger statuses for the device.

        Attributes:
            TD: Triggered and data acquisition is complete.
            Wait: Waiting for a trigger event.
            Run: Actively running and acquiring data.
            Auto: Automatically triggering when no trigger event occurs.
            Stop: Stopped, no data acquisition in progress.
        """

        TD = "TD"
        Wait = "WAIT"
        Run = "RUN"
        Auto = "AUTO"
        Stop = "STOP"

    class TriggerSweep(StrEnum):
        """
        Enumeration representing the available trigger sweep modes for the device.

        Attributes:
            Auto:   Automatic sweep mode ("AUTO"). The device continuously acquires data, even if no trigger event occurs.
            Normal: Normal sweep mode ("NORM"). The device acquires data only when a trigger event occurs.
            Single: Single sweep mode ("SING"). The device acquires data for a single trigger event and then stops.
        """

        Auto = "AUTO"
        Normal = "NORM"
        Single = "SING"

    class TriggerSource(StrEnum):
        """
        Enumeration of possible trigger sources for the MSO5000 device.

        Attributes:
            D0-D15: Digital channels 0 through 15.
            Channel1-Channel4: Analog channels 1 through 4 (represented as "CHAN1" to "CHAN4").
            AcLine: AC line trigger source ("ACL").
        """

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
        """
        Enumeration representing the possible trigger slope types for the device.

        Attributes:
            Positive: Trigger on a positive slope ("POS").
            Negative: Trigger on a negative slope ("NEG").
            RFall: Trigger on a rapid falling edge ("RFAL").
        """

        Positive = "POS"
        Negative = "NEG"
        RFall = "RFAL"

    class TriggerWhen(StrEnum):
        """
        Enumeration representing trigger conditions for a device.

        Attributes:
            Greater: Trigger when the value is greater than a specified threshold ("GRE").
            Less: Trigger when the value is less than a specified threshold ("LESS").
            Gless: Trigger when the value is greater or less than a specified threshold ("GLES").
        """

        Greater = "GRE"
        Less = "LESS"
        Gless = "GLES"

    class TriggerWindow(StrEnum):
        """
        Enumeration representing the available trigger windows for the device.

        Attributes:
            TA: Trigger window A.
            TB: Trigger window B.
            TAB: Trigger window A and B combined.
        """

        TA = "TA"
        TB = "TB"
        TAB = "TAB"

    @tester._member_logger
    def get_trigger_status(self):
        """
        Retrieves the current trigger status from the device.

        Returns:
            MSO5000.TriggerStatus: An enumeration value representing the current trigger status.

        Raises:
            ValueError: If the returned status string cannot be converted to a TriggerStatus enum.
        """
        _status = self._get_parameter("TRIGger", "STATus")
        return MSO5000.TriggerStatus(_status)

    @tester._member_logger
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
            mode in MSO5000.TriggerMode
        ), "Trigger mode must be one of the TriggerMode enum values."
        self._set_parameter("TRIGger", "MODE", mode.value)

    @tester._member_logger
    def set_trigger_coupling(self, coupling: TriggerCoupling):
        """
        Sets the trigger coupling mode for the device.

        Args:
            coupling (TriggerCoupling): The desired trigger coupling mode. Must be a member of the MSO5000.TriggerCoupling enum.

        Raises:
            AssertionError: If the provided coupling is not a valid TriggerCoupling enum value.

        """
        assert (
            coupling in MSO5000.TriggerCoupling
        ), "Trigger coupling must be one of the TriggerCoupling enum values."
        self._set_parameter("TRIGger", "COUPling", coupling.value)

    @tester._member_logger
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
            sweep in MSO5000.TriggerSweep
        ), "Trigger sweep must be one of the TriggerSweep enum values."
        self._set_parameter("TRIGger", "SWEep", sweep.value)

    @tester._member_logger
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
        self._set_parameter("TRIGger", "HOLDoff", holdoff)

    @tester._member_logger
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
        self._set_parameter("TRIGger", "NREJect", status)

    # Trigger mode: Edge
    @tester._member_logger
    def set_trigger_edge_source(self, source: TriggerSource):
        """
        Set the trigger edge source for the oscilloscope.

        Args:
            source (TriggerSource): The trigger source to set. Must be a member of the MSO5000.TriggerSource enum.

        Raises:
            AssertionError: If the provided source is not a valid TriggerSource enum value.

        This method configures the oscilloscope to use the specified trigger edge source.
        """
        assert (
            source in MSO5000.TriggerSource
        ), "Trigger edge source must be one of the TriggerSource enum values."
        self._set_parameter("TRIGger", "EDGE:SOURce", source.value)

    @tester._member_logger
    def set_trigger_edge_slope(self, slope: TriggerSlope):
        """
        Sets the trigger edge slope for the oscilloscope.

        Args:
            slope (TriggerSlope): The desired trigger edge slope. Must be a member of MSO5000.TriggerSlope.

        Raises:
            AssertionError: If the provided slope is not a valid TriggerSlope enum value.

        Side Effects:
            Updates the oscilloscope's trigger edge slope setting via the __set_parameter_str method.
        """
        assert (
            slope in MSO5000.TriggerSlope
        ), "Trigger edge slope must be one of the TriggerEdgeSlope enum values."
        self._set_parameter("TRIGger", "EDGE:SLOPe", slope.value)

    @tester._member_logger
    def set_trigger_edge_level(self, level: float):
        """
        Sets the trigger edge level for the device.

        Args:
            level (float): The voltage level to set for the trigger edge, in volts.
                Must be between -15 and 15 (inclusive).

        Raises:
            AssertionError: If the provided level is outside the valid range [-15, 15].

        """
        assert (
            level >= -15 and level <= 15
        ), "Trigger edge level must be between -15 and 15 V."
        self._set_parameter("TRIGger", "EDGE:LEVel", level)

    @tester._member_logger
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
        self.set_trigger_mode(MSO5000.TriggerMode.Edge)
        self.set_trigger_coupling(coupling)
        self.set_trigger_sweep(sweep)
        self.set_trigger_holdoff(holdoff)
        self.set_trigger_noise_reject(nreject)
        self.set_trigger_edge_source(edge_source)
        self.set_trigger_edge_slope(edge_slope)
        self.set_trigger_edge_level(edge_level)

    # Trigger mode: Pulse
    @tester._member_logger
    def set_trigger_pulse_source(self, source: TriggerSource):
        """
        Sets the trigger pulse source for the oscilloscope.

        Args:
            source (TriggerSource): The trigger source to set. Must be a member of the MSO5000.TriggerSource enum.

        Raises:
            AssertionError: If the provided source is not a valid TriggerSource enum value.

        """
        assert (
            source in MSO5000.TriggerSource
        ), "Trigger pulse source must be one of the TriggerSource enum values."
        self._set_parameter("TRIGger", "PULSe:SOURce", source.value)

    @tester._member_logger
    def set_trigger_pulse_when(self, when: TriggerWhen):
        """
        Sets the trigger condition for pulse width triggering on the device.

        Args:
            when (TriggerWhen): The trigger condition, must be a value from the MSO5000.TriggerWhen enum.

        Raises:
            AssertionError: If the provided when is not a valid TriggerWhen enum value.

        This method configures the oscilloscope to trigger when the pulse width condition specified by 'when' is met.
        """
        assert (
            when in MSO5000.TriggerWhen
        ), "Trigger pulse when must be one of the TriggerWhen enum values."
        self._set_parameter("TRIGger", "PULSe:WHEN", when.value)

    @tester._member_logger
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
        self._set_parameter("TRIGger", "PULSe:UWIDth", width)

    @tester._member_logger
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
        self._set_parameter("TRIGger", "PULSe:LWIDth", width)

    @tester._member_logger
    def set_trigger_pulse_level(self, level: float):
        """
        Sets the trigger pulse level for the device.

        Args:
            level (float): The desired trigger pulse level in volts. Must be between -15 and 15.

        Raises:
            AssertionError: If the specified level is not within the range -15 to 15 volts.

        """
        assert (
            level >= -15 and level <= 15
        ), "Trigger pulse level must be between -15 and 15 V."
        self._set_parameter("TRIGger", "PULSe:LEVel", level)

    @tester._member_logger
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
        self.set_trigger_mode(MSO5000.TriggerMode.Edge)
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
    @tester._member_logger
    def set_trigger_slope_source(self, source: TriggerSource):
        """
        Sets the trigger slope source for the oscilloscope.

        Args:
            source (TriggerSource): The trigger source to set. Must be one of
                MSO5000.TriggerSource.CHANnel1, MSO5000.TriggerSource.CHANnel2,
                MSO5000.TriggerSource.CHANnel3, or MSO5000.TriggerSource.CHANnel4.

        Raises:
            AssertionError: If the provided source is not a valid channel trigger source.

        """
        assert source in [
            MSO5000.TriggerSource.Channel1,
            MSO5000.TriggerSource.Channel2,
            MSO5000.TriggerSource.Channel3,
            MSO5000.TriggerSource.Channel4,
        ], "Trigger source must be one of Channel 1, Channel 2, Channel 3 or Channel 4."
        self._set_parameter("TRIGger", "SLOPe:SOURce", source.value)

    @tester._member_logger
    def set_trigger_slope_when(self, when: TriggerWhen):
        """
        Sets the trigger slope condition for the oscilloscope.

        Args:
            when (TriggerWhen): The trigger condition to set. Must be a value from the TriggerWhen enum.

        Raises:
            AssertionError: If the provided when is not a valid TriggerWhen enum value.

        """
        assert (
            when in MSO5000.TriggerWhen
        ), "Trigger when must be one of the TriggerWhen enum values."
        self._set_parameter("TRIGger", "SLOPe:WHEN", when.value)

    @tester._member_logger
    def set_trigger_slope_time_upper(self, time: float):
        """
        Sets the upper time limit for the trigger slope.

        Args:
            time (float): The upper time limit in seconds. Must be less than or equal to 10.

        Raises:
            AssertionError: If the specified time is greater than 10 seconds.

        """
        assert time <= 10, "Upper time limit must be less than 10 s."
        self._set_parameter("TRIGger", "SLOPe:TUPPer", time)

    @tester._member_logger
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
        self._set_parameter("TRIGger", "SLOPe:TLOWer", time)

    @tester._member_logger
    def set_trigger_slope_window(self, window: TriggerWindow):
        """
        Sets the trigger slope window of the oscilloscope.

        Args:
            window (TriggerWindow): The trigger slope window to set. Must be a value from the MSO5000.TriggerWindow enum.

        Raises:
            AssertionError: If the provided window is not a valid TriggerWindow enum value.

        This method configures the oscilloscope to use the specified trigger slope window by sending the appropriate command.
        """
        assert (
            window in MSO5000.TriggerWindow
        ), "Trigger window must be one of the TriggerWindow enum values."
        self._set_parameter("TRIGger", "SLOPe:WINDow", window.value)

    @tester._member_logger
    def set_trigger_slope_amplitude_upper(self, amplitude: float):
        """
        Sets the upper amplitude limit for the trigger slope on the oscilloscope.

        Args:
            amplitude (float): The upper amplitude threshold to set for the trigger slope.

        Raises:
            ValueError: If the provided amplitude is out of the valid range for the oscilloscope.
        """
        self._set_parameter("TRIGger", "SLOPe:ALEVel", amplitude)

    @tester._member_logger
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
        self._set_parameter("TRIGger", "SLOPe:BLEVel", amplitude)

    @tester._member_logger
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
        self.set_trigger_mode(MSO5000.TriggerMode.Slope)
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
    @tester._member_logger
    def set_trigger_timeout_source(self, source: TriggerSource):
        """
        Sets the trigger timeout source for the oscilloscope.

        Args:
            source (TriggerSource): The trigger source to set. Must not be `TriggerSource.AcLine`.

        Raises:
            AssertionError: If the provided source is `TriggerSource.AcLine`.

        """
        assert (
            source is not MSO5000.TriggerSource.AcLine
        ), "Trigger source cannot be ACLine."
        self._set_parameter("TRIGger", "TIMeout:SOURce", source.value)

    @tester._member_logger
    def set_trigger_timeout_slope(self, slope: TriggerSlope):
        """
        Sets the trigger timeout slope for the device.

        Args:
            slope (TriggerSlope): The desired trigger slope. Must be a member of the MSO5000.TriggerSlope enum.

        Raises:
            AssertionError: If the provided slope is not a valid TriggerSlope enum value.

        """
        assert (
            slope in MSO5000.TriggerSlope
        ), "Trigger slope must be one of the TriggerSlope enum values."
        self._set_parameter("TRIGger", "TIMeout:SLOPe", slope.value)

    @tester._member_logger
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
        self._set_parameter("TRIGger", "TIMeout:TIME", time)

    @tester._member_logger
    def set_trigger_timeout_level(self, level: float):
        """
        Sets the trigger timeout level for the device.

        The trigger timeout level determines the voltage threshold (in volts) for the trigger timeout event.
        The allowed range for the level is between -15V and 15V, inclusive.

        Args:
            level (float): The voltage level to set for the trigger timeout.

        Raises:
            AssertionError: If the provided level is not within the range -15V to 15V.
        """
        assert (
            level >= -15 and level <= 15
        ), "Trigger level must be between -15V and 15V."
        self._set_parameter("TRIGger", "TIMeout:LEVel", level)

    @tester._member_logger
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
        self.set_trigger_mode(MSO5000.TriggerMode.Slope)
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
    class WaveformMode(StrEnum):
        """
        Enumeration of available waveform acquisition modes for the device.

        Attributes:
            Normal: Standard acquisition mode, typically used for regular waveform capture.
            Maximum: Acquires waveform data at the maximum available rate or resolution.
            Raw: Captures raw, unprocessed waveform data directly from the device.
        """

        Normal = "NORM"
        Maximum = "MAX"
        Raw = "RAW"

    class WaveformFormat(StrEnum):
        """
        Enumeration of supported waveform data formats for the device.

        Attributes:
            Word: Represents waveform data in 16-bit word format ("WORD").
            Byte: Represents waveform data in 8-bit byte format ("BYTE").
            Ascii: Represents waveform data in ASCII format ("ASC").
        """

        Word = "WORD"
        Byte = "BYTE"
        Ascii = "ASC"

    @tester._member_logger
    def set_waveform_source(self, source: Source):
        """
        Sets the waveform source for the device.

        Args:
            source (Source): The source to set for waveform acquisition. Must be a member of the MSO5000.Source enum.

        Raises:
            AssertionError: If the provided source is not a valid member of MSO5000.Source.

        """
        assert (
            source in MSO5000.Source
        ), "Waveform source must be one of the WaveformSource enum values."
        self._set_parameter("WAVeform", "SOURce", source.value)

    @tester._member_logger
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
            mode in MSO5000.WaveformMode
        ), "Waveform mode must be one of the WaveformMode enum values."
        self._set_parameter("WAVeform", "MODE", mode.value)

    @tester._member_logger
    def set_waveform_format(self, format_: WaveformFormat):
        """
        Sets the waveform data format for the device.

        Args:
            format_ (WaveformFormat): The desired waveform format, must be a member of the WaveformFormat enum.

        Raises:
            AssertionError: If the provided format_ is not a valid WaveformFormat enum value.

        """
        assert (
            format_ in MSO5000.WaveformFormat
        ), "Waveform format must be one of the WaveformFormat enum values."
        self._set_parameter("WAVeform", "FORMat", format_.value)

    @tester._member_logger
    def set_waveform_points(self, points: int):
        """
        Sets the number of waveform points for the device.

        Args:
            points (int): The number of points to set for the waveform. Must be greater than or equal to 1.

        Raises:
            AssertionError: If points is less than 1.
        """
        assert points >= 1, "Waveform points must be greater than 1."
        self._set_parameter("WAVeform", "POINts", points)

    @tester._member_logger
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
            if format_ == MSO5000.WaveformFormat.Ascii:
                _points = "".join([chr(x) for x in _response]).split(",")
                for _index in range(_start, _stop):
                    _data[_index - start] = float(_points[_index - _start])
            elif format_ == MSO5000.WaveformFormat.Word:
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

    @tester._member_logger
    def get_waveform_xincrement(self) -> float:
        """
        Retrieves the horizontal (X-axis) increment value of the current waveform.

        Returns:
            float: The time interval between consecutive data points in the waveform.
        """
        return self._get_parameter("WAVeform", "XINCrement")

    @tester._member_logger
    def get_waveform_xorigin(self) -> float:
        """
        Retrieves the X origin value of the current waveform.

        Returns:
            float: The X origin of the waveform, typically representing the starting point on the X-axis (time axis) in waveform data.
        """
        return self._get_parameter("WAVeform", "XORigin")

    @tester._member_logger
    def get_waveform_xreference(self) -> float:
        """
        Retrieves the X reference value of the current waveform.

        Returns:
            float: The X reference value of the waveform, typically representing the horizontal offset or reference point on the X-axis.
        """
        return self._get_parameter("WAVeform", "XREFerence")

    @tester._member_logger
    def get_waveform_yincrement(self) -> float:
        """
        Retrieves the vertical increment (Y increment) value of the current waveform.

        Returns:
            float: The Y increment value, representing the voltage difference between adjacent data points in the waveform.
        """
        return self._get_parameter("WAVeform", "YINCrement")

    @tester._member_logger
    def get_waveform_yorigin(self) -> float:
        """
        Gets the Y origin value of the current waveform.

        Returns:
            float: The Y origin of the waveform as a floating-point number.
        """
        return self._get_parameter("WAVeform", "YORigin")

    @tester._member_logger
    def get_waveform_yreference(self) -> float:
        """
        Retrieves the Y reference value of the current waveform.

        Returns:
            float: The Y reference value used for scaling the waveform data.
        """
        return self._get_parameter("WAVeform", "YREFerence")

    @tester._member_logger
    def set_waveform_start(self, start: int):
        """
        Sets the starting point for waveform data acquisition.

        Parameters:
            start (int): The starting index for the waveform data. Must be greater than or equal to 1.

        Raises:
            AssertionError: If 'start' is less than 1.
        """
        assert start >= 1, "Waveform start must be greater than 1."
        self._set_parameter("WAVeform", "STARt", start)

    @tester._member_logger
    def set_waveform_stop(self, stop: int):
        """
        Sets the stop point for waveform data acquisition.

        Parameters:
            stop (int): The index at which to stop waveform acquisition. Must be greater than or equal to 1.

        Raises:
            AssertionError: If 'stop' is less than 1.
        """
        assert stop >= 1, "Waveform stop must be greater than 1."
        self._set_parameter("WAVeform", "STOP", stop)

    @tester._member_logger
    def get_waveform_preamble(self) -> str:
        """
        Retrieves the waveform preamble from the device.

        Returns:
            str: The waveform preamble as a string, typically containing information about the waveform format, such as scaling, offset, and other acquisition parameters.
        """
        return self._get_parameter("WAVeform", "PREamble")
