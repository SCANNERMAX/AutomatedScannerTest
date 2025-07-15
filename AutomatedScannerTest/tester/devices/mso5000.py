# -*- coding: utf-8 -*-
"""
Module: mso5000
Driver for the Rigol MSO5000 series oscilloscopes.

This module provides a class-based interface for controlling and configuring
Rigol MSO5000 series oscilloscopes using SCPI commands via PyVISA. It includes
methods for device discovery, communication, configuration, and data acquisition.
"""

import time
from PySide6.QtCore import QSettings
from ctypes.wintypes import BYTE
from enum import StrEnum
import pyvisa

import tester
from tester.devices import Device


class MSO5000(Device):
    """
    Driver for the Rigol MSO5000 series oscilloscopes.

    This class provides a high-level interface for controlling and configuring
    Rigol MSO5000 series oscilloscopes using SCPI commands via PyVISA. It supports
    device discovery, communication, configuration, and data acquisition, as well as
    advanced features such as waveform capture, function generator control, and
    trigger configuration.

    Attributes:
        SampleRate (float): The current sample rate of the oscilloscope in Sa/s.

    Methods:
        __init__(settings: QSettings): Initializes the MSO5000 oscilloscope device.
        __getattr__(name): Forwards attribute access to the embedded instrument object.
        __query(message: str) -> str: Sends a SCPI query and returns the response.
        __write(message: str): Sends a SCPI command to the oscilloscope.
        __get_names(channel: str, parameter: str): Generates attribute and parameter names.
        __get_parameter_str(channel: str, parameter: str) -> str: Gets a string parameter.
        __get_parameter_int(channel: str, parameter: str) -> int: Gets an integer parameter.
        __get_parameter_float(channel: str, parameter: str) -> float: Gets a float parameter.
        __get_parameter_bool(channel: str, parameter: str) -> bool: Gets a boolean parameter.
        __set_parameter_str(channel: str, parameter: str, value: str): Sets a string parameter.
        __set_parameter_int(channel: str, parameter: str, value: int): Sets an integer parameter.
        __set_parameter_float(channel: str, parameter: str, value: float): Sets a float parameter.
        __set_parameter_bool(channel: str, parameter: str, value: bool): Sets a boolean parameter.
        __set_parameter_no_check(channel: str, parameter: str, value: str): Sets a parameter without checking.
        find_instrument(): Finds and initializes the connected instrument.
        autoscale(): Enables waveform auto setting.
        clear(): Clears all waveforms on the screen.
        run(): Starts the oscilloscope.
        stop(): Stops the oscilloscope.
        single(): Sets the trigger mode to "Single".
        force_trigger(): Forces a trigger event.
        set_acquire_averages(averages: int): Sets the number of averages in average mode.
        set_acquire_memory_depth(depth: MemoryDepth): Sets the memory depth.
        set_acquire_type(type_: AcquireType): Sets the acquisition mode.
        get_sample_rate() -> float: Gets the current sample rate.
        get_digital_sample_rate() -> float: Gets the digital sample rate.
        get_digital_memory_depth() -> float: Gets the digital memory depth.
        set_acquire_antialiasing(state: bool): Enables/disables anti-aliasing.
        acquire_settings(...): Sets acquisition settings.
        set_channel_bandwidth_limit(channel: int, limit: BandwidthLimit): Sets channel bandwidth limit.
        set_channel_coupling(channel: int, coupling: Coupling): Sets channel coupling.
        set_channel_display(channel: int, display: bool): Turns channel display on/off.
        set_channel_invert(channel: int, invert: bool): Inverts channel waveform.
        set_channel_offset(channel: int, offset: float): Sets channel vertical offset.
        set_channel_calibration_time(channel: int, time: float): Sets channel calibration time.
        set_channel_scale(channel: int, scale: float): Sets channel vertical scale.
        set_channel_probe(channel: int, probe: float): Sets channel probe ratio.
        set_channel_units(channel: int, units: Units): Sets channel units.
        set_channel_vernier(channel: int, vernier: bool): Enables/disables fine adjustment.
        set_channel_position(channel: int, position: float): Sets channel position.
        channel_settings(...): Sets all channel settings.
        clear_registers(): Clears status registers.
        get_standard_event_register_enable() -> BYTE: Gets standard event register enable.
        set_standard_event_register_enable(bits: BYTE): Sets standard event register enable.
        get_standard_event_register_event() -> BYTE: Gets and clears standard event register event.
        get_identity() -> str: Gets the instrument ID string.
        get_operation_complete() -> bool: Checks if operation is complete.
        set_operation_complete(state: bool): Sets operation complete bit.
        save(register: int): Saves settings to a register.
        recall(register: int): Recalls settings from a register.
        reset(): Restores factory default settings.
        get_status_byte_register_enable() -> BYTE: Gets status byte register enable.
        set_status_byte_register_enable(bits: BYTE): Sets status byte register enable.
        get_status_byte_register_event() -> BYTE: Gets and clears status byte register event.
        self_test() -> str: Performs a self-test.
        wait(): Waits for all pending operations to complete.
        set_measure_source(channel: int, source: Source): Sets measurement source.
        clear_measurement(item: MeasureItem): Clears measurement items.
        set_measure_threshold_source(source: Source): Sets measurement threshold source.
        set_save_csv_length(length: SaveCsvLength): Sets CSV save data length.
        set_save_csv_channel(channel: SaveCsvChannel, state: bool): Sets CSV save channel on/off.
        save_csv(filename: str, length: SaveCsvLength): Saves waveform data as CSV.
        save_image_type(type_: ImageType): Sets image save type.
        save_image_invert(invert: bool): Enables/disables image invert.
        save_image_color(color: ImageColor): Sets image color.
        save_image(path: str, type_: ImageType, invert: bool, color: ImageColor): Saves screen as image.
        save_setup(path: str): Saves setup parameters.
        save_waveform(path: str): Saves waveform data.
        get_save_status() -> bool: Gets save status.
        load_setup(filename: str): Loads setup file.
        function_generator_state(channel: int, state: bool): Enables/disables function generator output.
        set_source_function(channel: int, function: SourceFunction): Sets function generator waveform.
        set_source_type(channel: int, type_: SourceType): Sets function generator type.
        set_source_frequency(channel: int, frequency: float): Sets function generator frequency.
        set_source_phase(channel: int, phase: float): Sets function generator phase.
        set_source_amplitude(channel: int, amplitude: float): Sets function generator amplitude.
        set_source_offset(channel: int, offset: float): Sets function generator offset.
        phase_align(channel: int): Initiates phase alignment.
        set_source_output_impedance(channel: int, impedance: SourceOutputImpedance): Sets output impedance.
        function_generator_sinusoid(...): Configures sinusoid output.
        function_generator_square(...): Configures square output.
        set_source_function_ramp_symmetry(channel: int, symmetry: float): Sets ramp symmetry.
        function_generator_ramp(...): Configures ramp output.
        set_source_duty_cycle(channel: int, duty_cycle: float): Sets pulse duty cycle.
        function_generator_pulse(...): Configures pulse output.
        function_generator_noise(...): Configures noise output.
        function_generator_dc(...): Configures DC output.
        function_generator_sinc(...): Configures sinc output.
        function_generator_no_modulation(channel: int): Disables modulation.
        set_source_mod_type(channel: int, mod_type: SourceModulation): Sets modulation type.
        set_source_mod_am_depth(channel: int, depth: float): Sets AM depth.
        set_source_mod_am_freq(channel: int, frequency: float): Sets AM frequency.
        set_source_mod_fm_freq(channel: int, frequency: float): Sets FM frequency.
        set_source_mod_am_function(channel: int, function: SourceFunction): Sets AM function.
        set_source_mod_fm_function(channel: int, function: SourceFunction): Sets FM function.
        set_source_mod_fm_deviation(channel: int, deviation: float): Sets FM deviation.
        function_generator_modulation(...): Configures modulation.
        set_source_sweep_type(channel: int, type_: SourceSweepType): Sets sweep type.
        set_source_sweep_sweep_time(channel: int, time: int): Sets sweep time.
        set_source_sweep_return_time(channel: int, time: int): Sets sweep return time.
        function_generator_sweep(...): Configures sweep.
        set_source_burst_type(channel: int, type_: SourceBurstType): Sets burst type.
        set_source_burst_cycles(channel: int, cycles: int): Sets burst cycles.
        set_source_burst_delay(channel: int, delay: int): Sets burst delay.
        function_generator_burst(...): Configures burst.
        get_system_error() -> str: Gets and clears the next system error.
        set_timebase_delay_enable(enable: bool): Enables/disables delayed sweep.
        set_timebase_delay_offset(offset: float): Sets delayed timebase offset.
        set_timebase_delay_scale(scale: float): Sets delayed timebase scale.
        timebase_delay(...): Configures timebase delay.
        set_timebase_offset(offset: float): Sets main timebase offset.
        set_timebase_scale(scale: float): Sets main timebase scale.
        set_timebase_mode(mode: TimebaseMode): Sets timebase mode.
        set_timebase_href_mode(mode: HrefMode): Sets horizontal reference mode.
        set_timebase_position(position: int): Sets horizontal reference position.
        set_timebase_vernier(vernier: bool): Enables/disables timebase vernier.
        timebase_settings(...): Configures timebase settings.
        get_trigger_status(): Gets current trigger status.
        set_trigger_mode(mode: TriggerMode): Sets trigger mode.
        set_trigger_coupling(coupling: TriggerCoupling): Sets trigger coupling.
        set_trigger_sweep(sweep: TriggerSweep): Sets trigger sweep mode.
        set_trigger_holdoff(holdoff: float): Sets trigger holdoff time.
        set_trigger_noise_reject(status: bool): Enables/disables noise reject.
        set_trigger_edge_source(source: TriggerSource): Sets edge trigger source.
        set_trigger_edge_slope(slope: TriggerSlope): Sets edge trigger slope.
        set_trigger_edge_level(level: float): Sets edge trigger level.
        trigger_edge(...): Configures edge trigger.
        set_trigger_pulse_source(source: TriggerSource): Sets pulse trigger source.
        set_trigger_pulse_when(when: TriggerWhen): Sets pulse trigger condition.
        set_trigger_pulse_upper_width(width: float): Sets pulse upper width.
        set_trigger_pulse_lower_width(width: float): Sets pulse lower width.
        set_trigger_pulse_level(level: float): Sets pulse trigger level.
        trigger_pulse(...): Configures pulse trigger.
        set_trigger_slope_source(source: TriggerSource): Sets slope trigger source.
        set_trigger_slope_when(when: TriggerWhen): Sets slope trigger condition.
        set_trigger_slope_time_upper(time: float): Sets slope upper time.
        set_trigger_slope_time_lower(time: float): Sets slope lower time.
        set_trigger_slope_window(window: TriggerWindow): Sets slope trigger window.
        set_trigger_slope_amplitude_upper(amplitude: float): Sets slope upper amplitude.
        set_trigger_slope_amplitude_lower(amplitude: float): Sets slope lower amplitude.
        trigger_slope(...): Configures slope trigger.
        set_trigger_timeout_source(source: TriggerSource): Sets timeout trigger source.
        set_trigger_timeout_slope(slope: TriggerSlope): Sets timeout trigger slope.
        set_trigger_timeout_time(time: float): Sets timeout trigger time.
        set_trigger_timeout_level(level: float): Sets timeout trigger level.
        trigger_timeout(...): Configures timeout trigger.
        set_waveform_source(source: Source): Sets waveform source.
        set_waveform_mode(mode: WaveformMode): Sets waveform mode.
        set_waveform_format(format_: WaveformFormat): Sets waveform format.
        set_waveform_points(points: int): Sets number of waveform points.
        get_waveform(...): Reads waveform data.
        get_waveform_xincrement() -> float: Gets X increment.
        get_waveform_xorigin() -> float: Gets X origin.
        get_waveform_xreference() -> float: Gets X reference.
        get_waveform_yincrement() -> float: Gets Y increment.
        get_waveform_yorigin() -> float: Gets Y origin.
        get_waveform_yreference() -> float: Gets Y reference.
        set_waveform_start(start: int): Sets waveform start point.
        set_waveform_stop(stop: int): Sets waveform stop point.
        get_waveform_preamble() -> str: Gets waveform preamble.

    Enumerations:
        Source, MemoryDepth, AcquireType, BandwidthLimit, Coupling, Units,
        MeasureItem, SaveCsvLength, SaveCsvChannel, ImageType, ImageColor,
        SourceFunction, SourceType, SourceModulation, SourceSweepType, SourceBurstType,
        SourceOutputImpedance, TimebaseMode, HrefMode, TriggerMode, TriggerCoupling,
        TriggerStatus, TriggerSweep, TriggerSource, TriggerSlope, TriggerWhen,
        TriggerWindow, WaveformMode, WaveformFormat
    """

    @property
    def SampleRate(self):
        """
        Returns the current sample rate of the oscilloscope in samples per second (Sa/s).

        Returns:
            float: The current sample rate of the oscilloscope in Sa/s.
        """
        return self.get_sample_rate()

    def __init__(self, settings: QSettings):
        """
        Initialize the MSO5000 oscilloscope device with the provided settings. Initialize the oscilloscope to factory settings.

        Args:
            settings (QSettings): The settings object used to configure the oscilloscope.

        This constructor sets the oscilloscope to its factory settings by stopping any ongoing operations and performing a reset.
        """
        super().__init__("MSO5000", settings)
        self.stop()
        self.reset()

    def __getattr__(self, name):
        """
        Dynamically forwards attribute access to the embedded instrument object.

        If the requested attribute is not found in the current instance, this method checks
        if the embedded instrument (`self.__instrument`) has the attribute. If so, it returns
        the attribute from the instrument. Otherwise, it raises an AttributeError.

        Args:
            name (str): The name of the attribute to retrieve.

        Returns:
            Any: The value of the attribute from the embedded instrument.

        Raises:
            AttributeError: If the attribute is not found in either the current instance or the embedded instrument.
        """
        if hasattr(self.__instrument, name):
            _response = getattr(self.__instrument, name)
            return _response
        else:
            raise AttributeError(f"Attribute {name} not found.")

    # Basic communication commands
    @tester._member_logger
    def __query(self, message: str) -> str:
        """
        Sends a request command to the oscilloscope and returns the response.

        Args:
            message (str): The command string to send to the oscilloscope.

        Returns:
            str: The response received from the oscilloscope.

        Raises:
            AssertionError: If the message is empty or if no response is received after all retry attempts.

        Notes:
            - Retries up to 5 times in case of a pyvisa.errors.VisaIOError.
            - Logs each request and retry attempt for debugging purposes.
        """
        _message = message.strip()
        assert _message, "Message cannot be empty."
        self.logger.debug(f'sending request "{_message}"...')
        _response = None
        _attempts = 5
        while _attempts > 0:
            _attempts = _attempts - 1
            try:
                _response = self.__instrument.query(_message).rstrip()
                break
            except pyvisa.errors.VisaIOError:
                self.logger.debug("retrying...")
        assert _response, "Failed to get response."
        return _response

    @tester._member_logger
    def __write(self, message: str):
        """
        Sends a command to the oscilloscope, retrying up to 5 times on communication failure.

        Args:
            message (str): The command string to send to the oscilloscope.

        Raises:
            AssertionError: If the message is empty.
        """
        _message = message.strip()
        assert _message, "Message cannot be empty."
        _attempts = 5
        while _attempts > 0:
            _attempts = _attempts - 1
            try:
                self.logger.debug(f'sending command "{_message}"...')
                self.__instrument.write(_message)
                break
            except pyvisa.errors.VisaIOError:
                self.logger.debug("retrying...")

    @tester._member_logger
    def __get_names(self, channel: str, parameter: str):
        """
        Generate the attribute and parameter names for a given channel and parameter.

        Args:
            channel (str): The channel identifier (e.g., 'CH1', 'CH2').
            parameter (str): The parameter name to be formatted.

        Returns:
            tuple: A tuple containing:
                - _attribute (str): The formatted attribute name (lowercase, colons replaced with underscores).
                - _parameter (str): The formatted parameter name (prefixed with a colon and channel).
        """
        _parameter = f":{channel}:{parameter}"
        _attribute = _parameter.replace(":", "_").lower()
        return _attribute, _parameter

    @tester._member_logger
    def __get_parameter_str(self, channel: str, parameter: str) -> str:
        """
        Queries and returns the value of a specified parameter for a given oscilloscope channel.

        If the parameter value has already been retrieved and cached as an attribute, it returns the cached value.
        Otherwise, it queries the oscilloscope for the parameter value, caches it as an attribute, and returns it.

        Args:
            channel (str): The oscilloscope channel to query (must not be empty).
            parameter (str): The parameter name to query (must not be empty).

        Returns:
            str: The value of the requested parameter.

        Raises:
            AssertionError: If 'channel' or 'parameter' is empty.
        """
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

    @tester._member_logger
    def __get_parameter_int(self, channel: str, parameter: str) -> int:
        """
        Queries an integer parameter value from the oscilloscope for a given channel and parameter name.

        If the value has already been cached as an attribute, it is returned directly.
        Otherwise, the value is queried from the device, cached as an attribute, and then returned.

        Args:
            channel (str): The channel identifier (e.g., "CH1") to query.
            parameter (str): The parameter name to query (e.g., "VOLTAGE").

        Returns:
            int: The integer value of the requested parameter.

        Raises:
            AssertionError: If `channel` or `parameter` is empty.
        """
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

    @tester._member_logger
    def __get_parameter_float(self, channel: str, parameter: str) -> float:
        """
        Queries a floating-point parameter value from the oscilloscope for a given channel and parameter name.

        If the value has been previously queried and cached as an attribute, it returns the cached value.
        Otherwise, it sends a query command to the oscilloscope, caches the result, and returns it.

        Args:
            channel (str): The oscilloscope channel to query (must not be empty).
            parameter (str): The parameter name to query (must not be empty).

        Returns:
            float: The queried parameter value.

        Raises:
            AssertionError: If channel or parameter is empty.
        """
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

    @tester._member_logger
    def __get_parameter_bool(self, channel: str, parameter: str) -> bool:
        """
        Queries a boolean parameter from the oscilloscope for a given channel.

        This method checks if the specified parameter for the given channel has already been cached as an attribute.
        If not, it queries the oscilloscope for the parameter value, converts it to a boolean, caches it as an attribute,
        and returns the result.

        Args:
            channel (str): The oscilloscope channel to query. Must not be empty.
            parameter (str): The parameter name to query. Must not be empty.

        Returns:
            bool: The boolean value of the queried parameter.

        Raises:
            AssertionError: If `channel` or `parameter` is empty.
        """
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

    @tester._member_logger
    def __set_parameter_str(self, channel: str, parameter: str, value: str):
        """
        Sets a string parameter of the oscilloscope for a specified channel.

        This method asserts that both the channel and parameter are provided,
        retrieves the corresponding attribute and command name, and repeatedly
        checks the current value of the parameter. If the current value does not
        match the desired value, it sends a command to update the parameter and
        updates the internal attribute accordingly. The process repeats until the
        parameter is set to the desired value.

        Args:
            channel (str): The oscilloscope channel to configure.
            parameter (str): The name of the parameter to set.
            value (str): The value to set for the parameter.

        Raises:
            AssertionError: If channel or parameter is empty.
        """
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

    @tester._member_logger
    def __set_parameter_int(self, channel: str, parameter: str, value: int):
        """
        Sets an integer parameter for a specified oscilloscope channel.

        This method asserts that both the channel and parameter are provided, retrieves the corresponding attribute and parameter names,
        and updates the parameter value on the oscilloscope if it does not already match the desired value.

        Args:
            channel (str): The oscilloscope channel to set the parameter for.
            parameter (str): The name of the parameter to set.
            value (int): The integer value to set the parameter to.

        Raises:
            AssertionError: If the channel or parameter is empty.
        """
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

    @tester._member_logger
    def __set_parameter_float(self, channel: str, parameter: str, value: float):
        """
        Sets a floating-point parameter for a specified oscilloscope channel.

        This method asserts that both the channel and parameter are provided, retrieves the corresponding attribute and parameter names, and checks the current value. If the current value does not match the desired value, it sends a command to update the parameter and updates the internal attribute accordingly.

        Args:
            channel (str): The oscilloscope channel to set the parameter for.
            parameter (str): The name of the parameter to set.
            value (float): The floating-point value to set for the parameter.

        Raises:
            AssertionError: If the channel or parameter is empty.
        """
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

    @tester._member_logger
    def __set_parameter_bool(self, channel: str, parameter: str, value: bool):
        """
        Sets a boolean parameter for a specified oscilloscope channel.

        This method asserts that both the channel and parameter are provided, retrieves the corresponding attribute and parameter names, and checks the current value of the parameter. If the current value does not match the desired value, it writes the new value to the device and updates the attribute until the parameter is set as requested.

        Args:
            channel (str): The oscilloscope channel to configure.
            parameter (str): The name of the parameter to set.
            value (bool): The boolean value to assign to the parameter.

        Raises:
            AssertionError: If the channel or parameter is empty.
        """
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

    @tester._member_logger
    def __set_parameter_no_check(self, channel: str, parameter: str, value: str):
        """
        Sets a parameter of the oscilloscope without verifying its current value.

        Args:
            channel (str): The oscilloscope channel to set the parameter for. Must not be empty.
            parameter (str): The name of the parameter to set. Must not be empty.
            value (str): The value to assign to the parameter.

        Raises:
            AssertionError: If either `channel` or `parameter` is empty.

        Note:
            This method does not check the current value of the parameter before setting it.
        """
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        self.__write(f"{_parameter} {value}")
        setattr(self, _attribute, value)

    # Enumerations for various settings
    class Source(StrEnum):
        """
        Enumeration of possible signal sources for the MSO5000 device.

        Attributes:
            D0-D15: Digital channels 0 through 15.
            Channel1-Channel4: Analog channels 1 through 4 (labeled as "CHAN1" to "CHAN4").
            Math1-Math4: Math function channels 1 through 4 (labeled as "MATH1" to "MATH4").
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
        """
        Enumeration representing possible memory depth settings for the MSO5000 device.

        Attributes:
            Auto: Automatically selects the memory depth.
            _1K: 1,000 points memory depth.
            _10K: 10,000 points memory depth.
            _100K: 100,000 points memory depth.
            _1M: 1,000,000 points memory depth.
            _10M: 10,000,000 points memory depth.
            _25M: 25,000,000 points memory depth.
            _50M: 50,000,000 points memory depth.
            _100M: 100,000,000 points memory depth.
            _200M: 200,000,000 points memory depth.
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
        """
        Enumeration of acquisition types for the MSO5000 device.

        Attributes:
            Normal: Standard acquisition mode ("NORM").
            Averages: Averages multiple acquisitions to reduce noise ("AVER").
            Peak: Captures peak values within the acquisition window ("PEAK").
            HighResolution: Increases vertical resolution by oversampling ("HRES").
        """

        Normal = "NORM"
        Averages = "AVER"
        Peak = "PEAK"
        HighResolution = "HRES"

    class BandwidthLimit(StrEnum):
        """
        Enumeration representing the available bandwidth limit settings for the device.

        Attributes:
            Off: Disables bandwidth limiting ("OFF").
            Auto: Automatically selects the appropriate bandwidth limit ("AUTO").
            _20M: Sets the bandwidth limit to 20 MHz ("20M").
            _100M: Sets the bandwidth limit to 100 MHz ("100M").
            _200M: Sets the bandwidth limit to 200 MHz ("200M").
        """

        Off = "OFF"
        Auto = "AUTO"
        _20M = "20M"
        _100M = "100M"
        _200M = "200M"

    class Coupling(StrEnum):
        """
        Enumeration representing the possible coupling modes for a device.

        Attributes:
            AC: Alternating Current coupling mode.
            DC: Direct Current coupling mode.
            Ground: Ground coupling mode (GND).
        """

        AC = "AC"
        DC = "DC"
        Ground = "GND"

    class Units(StrEnum):
        """
        Enumeration of measurement units used by the device.

        Attributes:
            Voltage: Represents voltage measurements (VOLT).
            Watt: Represents power measurements in watts (WATT).
            Ampere: Represents current measurements in amperes (AMP).
            Unknown: Represents an unknown or unspecified unit (UNKN).
        """

        Voltage = "VOLT"
        Watt = "WATT"
        Ampere = "AMP"
        Unknown = "UNKN"

    def find_instrument(self):
        """
        Searches for and connects to a Rigol MSO5000 oscilloscope using the pyvisa library.

        This method scans all available VISA resources, identifies a connected Rigol MSO5000 oscilloscope,
        and initializes the instrument for further communication. It logs the discovery process, sets
        relevant instrument attributes as settings, and asserts that a compatible oscilloscope is found.

        Raises:
            AssertionError: If no compatible MSO5000 oscilloscope is found among connected devices.
        """
        _resource_manager = pyvisa.ResourceManager()
        for _resource_name in _resource_manager.list_resources():
            try:
                self.logger.info(f"Found device: {_resource_name}")
                _instrument = _resource_manager.open_resource(_resource_name)
                if (
                    hasattr(_instrument, "manufacturer_name")
                    and _instrument.manufacturer_name == "Rigol"
                    and _instrument.model_name.startswith("MSO5")
                ):
                    self.logger.info(f"Found MSO5000 oscilloscope: {_resource_name}")
                    self.__instrument = _instrument
            except:
                pass
        assert self.__instrument is not None, "No oscilloscope found."
        for _key in [
            "manufacturer_id",
            "manufacturer_name",
            "model_code",
            "model_name",
            "serial_number",
        ]:
            try:
                _value = getattr(self.__instrument, _key, None)
                self._set_setting(_key, _value)
            except:
                pass
        self.logger.info(f"Connected to {self.model_name} oscilloscope.")

    # The device command system
    @tester._member_logger
    def autoscale(self):
        """
        Enables the waveform auto setting function. The oscilloscope will
        automatically adjust the vertical scale, horizontal time base, and
        trigger mode according to the input signal to realize optimal
        waveform display. This command functions the same as the AUTO key on
        the front panel.
        """
        self.__write("AUToscale")

    @tester._member_logger
    def clear(self):
        """
        Clears all the waveforms displayed on the oscilloscope screen.

        This method sends the "CLEar" command to the device, which functions the same as pressing the CLEAR key on the front panel.
        """
        self.__write("CLEar")

    @tester._member_logger
    def run(self):
        """
        Starts the oscilloscope acquisition.

        This method sends the ':RUN' command to the oscilloscope, initiating data acquisition.
        It functions identically to pressing the RUN/STOP key on the device's front panel.

        Raises:
            CommunicationError: If the command could not be sent to the oscilloscope.
        """
        self.__write(":RUN")

    @tester._member_logger
    def stop(self):
        """
        Stops the oscilloscope acquisition.

        This method sends the STOP command to the oscilloscope, halting any ongoing data acquisition.
        It functions identically to pressing the RUN/STOP key on the device's front panel.
        """
        self.__write(":STOP")

    @tester._member_logger
    def single(self):
        """
        Sets the oscilloscope trigger mode to "Single".

        This method sends the ":SINGle" command to the device, which is equivalent to pressing the SINGLE button on the front panel or issuing the ":TRIGger:SWEep SINGle" SCPI command. In "Single" mode, the oscilloscope acquires a single waveform when the trigger condition is met, then stops acquisition until triggered again.

        Returns:
            None
        """
        self.__write(":SINGle")

    @tester._member_logger
    def force_trigger(self):
        """
        Forcefully generates a trigger signal on the device.

        This method sends the ':TFORce' command to the instrument, which is equivalent to pressing the FORCE key on the device's front panel. It is only applicable when the device is in normal or single trigger modes, as set by the :TRIGger:SWEep command.

        Raises:
            DeviceCommunicationError: If the command could not be sent to the device.
        """
        self.__write(":TFORce")

    # The :ACQ commands are used to set the memory depth of the
    # oscilloscope, the acquisition mode, the average times, as well as query
    # the current sample rate
    @tester._member_logger
    def set_acquire_averages(self, averages: int):
        """
        Sets the number of averages for the average acquisition mode.

        Parameters:
            averages (int): The number of averages to set. Must be a power of two between 2 and 65536 (inclusive).

        Raises:
            AssertionError: If 'averages' is not one of the valid values (2, 4, 8, ..., 65536).
        """
        _valid_values = [2**x for x in range(1, 17)]
        assert averages in _valid_values, "Averages must be one of the valid values."
        self.__set_parameter_no_check("ACQuire", "AVERages", averages)

    @tester._member_logger
    def set_acquire_memory_depth(self, depth: MemoryDepth):
        """
        Sets the memory depth of the oscilloscope.

        This method configures the oscilloscope to use the specified memory depth, which determines
        the number of waveform points that can be stored during sampling for a single trigger event.
        The memory depth is specified using the `MemoryDepth` enum, and the value is sent to the
        oscilloscope in points (pts).

        Args:
            depth (MemoryDepth): The desired memory depth, specified as a value from the `MemoryDepth` enum.

        Raises:
            AssertionError: If `depth` is not a valid member of the `MemoryDepth` enum.
        """
        assert (
            depth in MSO5000.MemoryDepth
        ), "Memory depth must be one of the MemoryDepth enum values."
        self.__set_parameter_no_check("ACQuire", "MDEPth", depth.value)

    @tester._member_logger
    def set_acquire_type(self, type_: AcquireType):
        """
        Sets the acquisition mode of the oscilloscope.

        Args:
            type_ (AcquireType): The acquisition mode to set. Must be a member of the AcquireType enum.

        Raises:
            AssertionError: If type_ is not a valid AcquireType enum value.

        This method sends a command to the oscilloscope to change its acquisition mode
        (e.g., Normal, Peak Detect, Average, etc.) according to the specified type.
        """
        assert (
            type_ in MSO5000.AcquireType
        ), "Acquire type must be one of the AcquireType enum values."
        self.__set_parameter_str("ACQuire", "TYPE", type_.value)

    @tester._member_logger
    def get_sample_rate(self) -> float:
        """
        Queries and returns the current sample rate of the device.

        Returns:
            float: The current sample rate in samples per second (Sa/s).
        """
        return self.__get_parameter_float("ACQuire", "SRATe")

    @tester._member_logger
    def get_digital_sample_rate(self) -> float:
        """
        Queries and returns the current Logic Analyzer (LA) digital sample rate from the device.

        Returns:
            float: The current LA sample rate in samples per second (Sa/s).
        """
        return self.__get_parameter_float("ACQuire", "LA:SRATe")

    @tester._member_logger
    def get_digital_memory_depth(self) -> float:
        """
        Queries and returns the current logic analyzer (LA) memory depth as a float.

        Returns:
            float: The current memory depth setting of the logic analyzer.
        """
        return self.__get_parameter_float("ACQuire", "LA:MDEPth")

    @tester._member_logger
    def set_acquire_antialiasing(self, state: bool):
        """
        Enables or disables the oscilloscope's anti-aliasing function.

        Args:
            state (bool): If True, enables anti-aliasing; if False, disables it.
        """
        self.__set_parameter_str("ACQuire", "AALias", state)

    @tester._member_logger
    def acquire_settings(
        self,
        averages: int = 2,
        memory_depth: MemoryDepth = MemoryDepth.Auto,
        type_: AcquireType = AcquireType.Normal,
        antialiasing: bool = False,
    ):
        """
        Configures the acquisition settings of the oscilloscope.

        Parameters:
            averages (int, optional): The number of averages to use when the acquisition type is set to 'Averages'. Defaults to 2.
            memory_depth (MemoryDepth, optional): The memory depth setting for the acquisition. Defaults to MemoryDepth.Auto.
            type_ (AcquireType, optional): The acquisition type (e.g., Normal, Averages). Defaults to AcquireType.Normal.
            antialiasing (bool, optional): Whether to enable antialiasing. Defaults to False.

        Notes:
            - If 'type_' is set to 'Averages', the 'averages' parameter will be applied.
            - Other acquisition settings are always applied regardless of the acquisition type.
        """
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
        """
        Sets the bandwidth limit for a specified channel on the oscilloscope.

        Args:
            channel (int): The channel number to configure (must be between 1 and 4).
            limit (BandwidthLimit): The desired bandwidth limit, as a member of the BandwidthLimit enum.

        Raises:
            AssertionError: If the channel is not between 1 and 4.
            AssertionError: If the provided limit is not a valid BandwidthLimit for the current model.

        Model-specific behavior:
            - For model "MSO5354": All BandwidthLimit enum values are valid.
            - For model "MSO5204": Only Off, _20M, and _100M are valid.
            - For other models: Only Off and _20M are valid.

        """
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
        self.__set_parameter_str(f"CHANnel{channel}", "BWLimit", limit.value)

    @tester._member_logger
    def set_channel_coupling(self, channel: int, coupling: Coupling):
        """
        Sets the coupling mode (AC, DC, or GND) for a specified oscilloscope channel.

        Args:
            channel (int): The channel number to configure (must be between 1 and 4).
            coupling (Coupling): The desired coupling mode, as a member of the Coupling enum.

        Raises:
            AssertionError: If the channel is not between 1 and 4.
            AssertionError: If the coupling is not a valid Coupling enum value.

        Example:
            set_channel_coupling(1, Coupling.DC)
        """
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert (
            coupling in MSO5000.Coupling
        ), "Coupling must be one of the Coupling enum values."
        self.__set_parameter_str(f"CHANnel{channel}", "COUPling", coupling.value)

    @tester._member_logger
    def set_channel_display(self, channel: int, display: bool):
        """
        Enables or disables the display of a specified channel.

        Args:
            channel (int): The channel number to modify (must be between 1 and 4).
            display (bool): If True, turns the channel display on; if False, turns it off.

        Raises:
            AssertionError: If the channel number is not between 1 and 4.
        """
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        self.__set_parameter_bool(f"CHANnel{channel}", "DISPlay", display)

    @tester._member_logger
    def set_channel_invert(self, channel: int, invert: bool):
        """
        Enables or disables waveform inversion for the specified channel.

        Args:
            channel (int): The channel number (must be between 1 and 4).
            invert (bool): If True, inverts the waveform for the specified channel; if False, disables inversion.

        Raises:
            AssertionError: If the channel number is not between 1 and 4 (inclusive).
        """
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        self.__set_parameter_bool(f"CHANnel{channel}", "INVert", invert)

    @tester._member_logger
    def set_channel_offset(self, channel: int, offset: float):
        """
        Sets the vertical offset for a specified channel on the device.

        Parameters:
            channel (int): The channel number to set the offset for (must be between 1 and 4).
            offset (float): The vertical offset value in volts (must be between -10 and 100).

        Raises:
            AssertionError: If the channel is not between 1 and 4.
            AssertionError: If the offset is not between -10 and 100.

        The offset adjusts the vertical position of the waveform for the selected channel.
        """
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        _minimum = -10
        _maximum = 100
        assert (
            offset >= _minimum and offset <= _maximum
        ), f"Offset must be between {_minimum} and {_maximum}."
        self.__set_parameter_float(f"CHANnel{channel}", "OFFSet", offset)

    @tester._member_logger
    def set_channel_calibration_time(self, channel: int, time: float):
        """
        Sets the delay calibration time (zero offset) for a specified channel.

        This method calibrates the zero offset of the given channel by setting its delay calibration time.
        The calibration time must be between -100e-9 and 100e-9 seconds.

        Args:
            channel (int): The channel number to calibrate (must be between 1 and 4).
            time (float): The delay calibration time in seconds (must be between -100e-9 and 100e-9).

        Raises:
            AssertionError: If the channel is not between 1 and 4.
            AssertionError: If the time is not between -100e-9 and 100e-9 seconds.
        """
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert (
            time >= -100e-9 and time <= 100e-9
        ), "Delay calibration time must be between -100e-9 and 100e-9 seconds."
        self.__set_parameter_float(f"CHANnel{channel}", "TCALibrate", time)

    @tester._member_logger
    def set_channel_scale(self, channel: int, scale: float):
        """
        Sets the vertical scale (volts/division) for a specified oscilloscope channel.

        Args:
            channel (int): The channel number to configure (must be between 1 and 4).
            scale (float): The vertical scale value in volts (must be between 500e-6 and 10).

        Raises:
            AssertionError: If the channel is not between 1 and 4.
            AssertionError: If the scale is not between 500e-6 and 10.

        Notes:
            The scale determines the voltage represented by each vertical division on the oscilloscope display.
        """
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        _minimum = 500e-6
        _maximum = 10
        assert (
            scale >= _minimum and scale <= _maximum
        ), f"Scale must be between {_minimum} and {_maximum}."
        self.__set_parameter_float(f"CHANnel{channel}", "SCALe", scale)

    @tester._member_logger
    def set_channel_probe(self, channel: int, probe: float):
        """
        Sets the probe ratio of the specified channel.

        This method configures the probe attenuation ratio for the given analog channel.
        The probe ratio determines the scaling factor applied to the measured signal, allowing
        the oscilloscope to correctly interpret voltage levels based on the probe's attenuation.

        Args:
            channel (int): The analog channel number to configure (must be between 1 and 4).
            probe (float): The probe ratio to set. Must be one of the supported values:
                0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5,
                1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000.

        Raises:
            AssertionError: If the channel is not between 1 and 4, or if the probe ratio is not valid.

        Example:
            set_channel_probe(1, 10)  # Sets channel 1 to use a 10:1 probe ratio
        """
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
        self.__set_parameter_float(f"CHANnel{channel}", "PROBe", probe)

    @tester._member_logger
    def set_channel_units(self, channel: int, units: Units):
        """
        Sets the amplitude display unit for a specified analog channel.

        Args:
            channel (int): The analog channel number (must be between 1 and 4).
            units (Units): The unit to set for the channel's amplitude display. Must be a member of the Units enum.

        Raises:
            AssertionError: If the channel is not between 1 and 4.
            AssertionError: If units is not a valid Units enum value.
        """
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert units in MSO5000.Units, "Units must be one of the Units enum values."
        self.__set_parameter_str(f"CHANnel{channel}", "UNITs", units.value)

    @tester._member_logger
    def set_channel_vernier(self, channel: int, vernier: bool):
        """
        Enables or disables the fine (vernier) adjustment of the vertical scale for a specified analog channel.

        Args:
            channel (int): The analog channel number (must be between 1 and 4).
            vernier (bool): If True, enables fine adjustment; if False, disables it.

        Raises:
            AssertionError: If the channel number is not between 1 and 4.
        """
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        self.__set_parameter_bool(f"CHANnel{channel}", "VERNier", vernier)

    @tester._member_logger
    def set_channel_position(self, channel: int, position: float):
        """
        Sets the vertical position (offset) of the specified analog channel.

        Args:
            channel (int): The channel number to set the position for (must be between 1 and 4).
            position (float): The vertical offset value to set, in the range -100 to 100.

        Raises:
            AssertionError: If the channel is not between 1 and 4, or if the position is not between -100 and 100.

        This method is typically used to calibrate the zero point of an analog channel by adjusting its vertical offset.
        """
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert (
            position >= -100 and position <= 100
        ), "Position must be between -100 and 100."
        self.__set_parameter_float(f"CHANnel{channel}", "POSition", position)

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
        """
        Configures various settings for a specified oscilloscope channel.

        Parameters:
            channel (int): The channel number to configure.
            bandwidth_limit (BandwidthLimit, optional): Sets the bandwidth limit for the channel. Defaults to BandwidthLimit.Off.
            coupling (Coupling, optional): Sets the input coupling mode (e.g., DC, AC). Defaults to Coupling.DC.
            display (bool, optional): Whether to display the channel on the oscilloscope. Defaults to False.
            invert (bool, optional): Whether to invert the channel signal. Defaults to False.
            offset (float, optional): Sets the vertical offset for the channel in volts. Defaults to 0.
            delay_calibration_time (float, optional): Sets the delay calibration time for the channel. Defaults to 0.
            scale (float, optional): Sets the vertical scale (volts/div) for the channel. Defaults to 100e-3.
            probe (float, optional): Sets the probe attenuation factor. Defaults to 1.
            units (Units, optional): Sets the measurement units for the channel. Defaults to Units.Voltage.
            vernier (bool, optional): Enables or disables vernier adjustment for the channel. Defaults to False.
            position (float, optional): Sets the vertical position of the channel trace. Defaults to 0.

        This method applies all specified settings to the given channel by calling the corresponding setter methods.
        """
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
        """
        Clears all status registers of the oscilloscope by sending the standard SCPI *CLS command.

        This method resets the oscilloscope's error queue and status registers, ensuring that any previous errors or status messages are cleared before proceeding with further operations.
        """
        self.__write("*CLS")

    @tester._member_logger
    def get_standard_event_register_enable(self) -> BYTE:
        """
        Queries the enable register bit of the standard event register set.

        Sends the SCPI command '*ESE?' to the device to retrieve the current value of the Standard Event Status Enable register.
        Returns:
            BYTE: The value of the enable register as a BYTE.
        """
        _response = self.__query("*ESE?")
        return BYTE(int(_response))

    @tester._member_logger
    def set_standard_event_register_enable(self, bits: BYTE):
        """
        Sets the enable register bits of the standard event status register (ESE).

        Args:
            bits (BYTE): Bitmask specifying which standard event status register bits to enable.

        This method sends the SCPI command '*ESE' followed by the provided bitmask to configure
        which events will be reported in the standard event status register.
        """
        self.__write(f"*ESE {bits}")

    @tester._member_logger
    def get_standard_event_register_event(self) -> BYTE:
        """
        Queries the standard event status register (*ESR?) of the device, clears it, and returns its value as a BYTE.

        Returns:
            BYTE: The value of the standard event status register after querying and clearing it.
        """
        _response = self.__query("*ESR?")
        return BYTE(int(_response))

    @tester._member_logger
    def get_identity(self) -> str:
        """
        Retrieves the identification string of the instrument.

        Returns:
            str: The identification string returned by the instrument in response to the "*IDN?" SCPI command.
        """
        return self.__query("*IDN?")

    @tester._member_logger
    def get_operation_complete(self) -> bool:
        """
        Queries the device to determine if the current operation is complete.

        Returns:
            bool: True if the current operation is finished, False otherwise.
        """
        _response = self.__query("*OPC?")
        return bool(int(_response))

    @tester._member_logger
    def set_operation_complete(self, state: bool):
        """
        Sets the Operation Complete (*OPC) bit in the standard event status register.

        Args:
            state (bool): If True, sets the *OPC bit to 1 after the current operation is finished;
                          if False, sets it to 0.

        This method sends the *OPC command to the device, indicating whether the operation is complete.
        """
        self.__write(f"*OPC {int(state)}")

    @tester._member_logger
    def save(self, register: int):
        """
        Saves the current oscilloscope settings to a specified register.

        Args:
            register (int): The register number (between 0 and 49) where the current settings will be saved.

        Raises:
            AssertionError: If the register number is not between 0 and 49 (inclusive).
        """
        assert register >= 0 and register <= 49, "Register must be between 0 and 49."
        self.__write(f"*SAVe {register}")

    @tester._member_logger
    def recall(self, register: int):
        """
        Recalls the oscilloscope settings from the specified register.

        Args:
            register (int): The register number to recall settings from. Must be between 0 and 49.

        Raises:
            AssertionError: If the register is not between 0 and 49 (inclusive).

        This method sends a command to the oscilloscope to recall its settings from the given register.
        """
        assert register >= 0 and register <= 49, "Register must be between 0 and 49."
        self.__write(f"*RCL {register}")

    @tester._member_logger
    def reset(self):
        """
        Restores the instrument to its factory default settings.

        Sends the '*RST' command to the instrument and waits for the operation to complete.
        """
        self.__write("*RST")
        time.sleep(1)
        # self.__instrument.clear()

    @tester._member_logger
    def get_status_byte_register_enable(self) -> BYTE:
        """
        Queries the enable register bit of the status byte register set.

        Sends the SCPI command '*SRE?' to the device to retrieve the current value of the Status Byte Register Enable (SRE) register.
        Returns:
            BYTE: The value of the SRE register as a BYTE object.
        """
        _response = self.__query("*SRE?")
        return BYTE(int(_response))

    @tester._member_logger
    def set_status_byte_register_enable(self, bits: BYTE):
        """
        Sets the enable register bits of the status byte register.

        This method configures which bits in the status byte register are enabled by writing to the Standard Event Status Enable Register (SRE) of the device.

        Args:
            bits (BYTE): A bitmask specifying which status byte register bits to enable.
        """
        self.__write(f"*SRE {bits}")

    @tester._member_logger
    def get_status_byte_register_event(self) -> BYTE:
        """
        Queries the instrument for the current value of the status byte register event and clears the event register.

        Returns:
            BYTE: The value of the status byte register event as a BYTE object.
        """
        _response = self.__query("*STB?")
        return BYTE(int(_response))

    @tester._member_logger
    def self_test(self) -> str:
        """
        Performs a self-test on the device and returns the result as a string.

        Returns:
            str: The result of the self-test as returned by the device.
        """
        _response = self.__query("*TST?")
        return _response

    @tester._member_logger
    def wait(self):
        """
        Waits for all pending operations on the device to complete before allowing further commands.

        This method sends the SCPI *WAI command to the device, ensuring that all previously issued
        operations are finished before proceeding. It is useful for synchronizing command execution
        and preventing command overlap or race conditions.

        Raises:
            DeviceCommunicationError: If communication with the device fails.
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
    class MeasureItem(StrEnum):
        """
        Enumeration of measurement items for the MSO5000 device.
        This enum represents the 10 most recently enabled measurement items, identified as Item1 through Item10.
        The order reflects the sequence in which the items were activated. Removing one or more items does not
        affect the order of the remaining items. The 'All' member can be used to refer to all measurement items.
        Members:
            Item1 - The first measurement item.
            Item2 - The second measurement item.
            Item3 - The third measurement item.
            Item4 - The fourth measurement item.
            Item5 - The fifth measurement item.
            Item6 - The sixth measurement item.
            Item7 - The seventh measurement item.
            Item8 - The eighth measurement item.
            Item9 - The ninth measurement item.
            Item10 - The tenth measurement item.
            All - Represents all measurement items.
        """

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
        """
        Sets the measurement source channel for the current measurement parameter.

        Args:
            channel (int): The channel number to set as the measurement source (must be between 1 and 4).
            source (Source): The source to use, must be a member of the MSO5000.Source enum.

        Raises:
            AssertionError: If the channel is not between 1 and 4.
            AssertionError: If the source is not a valid member of the MSO5000.Source enum.
        """
        assert source in MSO5000.Source, "Source must be one of the Source enum values."
        self.__set_parameter_str("MEASure", "SOURce", source.value)

    @tester._member_logger
    def clear_measurement(self, item: MeasureItem):
        """
        Clears a specific measurement item from the oscilloscope.

        Args:
            item (MeasureItem): The measurement item to clear. Must be a member of the MeasureItem enum.

        Raises:
            AssertionError: If the provided item is not a valid MeasureItem enum value.

        This method sends a command to the device to clear the specified measurement item.
        """
        assert (
            item in MSO5000.MeasureItem
        ), "Item must be one of the MeasureItem enum values."
        self.__set_parameter_str("MEASure", "CLEar", item.value)

    @tester._member_logger
    def set_measure_threshold_source(self, source: Source):
        """
        Sets the measurement threshold source for the device.

        Parameters:
            source (Source): The source to use for the measurement threshold.
                Must be one of the following:
                    - MSO5000.Source.Channel1
                    - MSO5000.Source.Channel2
                    - MSO5000.Source.Channel3
                    - MSO5000.Source.Channel4
                    - MSO5000.Source.Math1
                    - MSO5000.Source.Math2
                    - MSO5000.Source.Math3
                    - MSO5000.Source.Math4

        Raises:
            AssertionError: If the provided source is not a valid option.
        """
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
        self.__set_parameter_str("MEASure", "THReshold:SOURce", source.value)

    @tester._member_logger
    def set_measure_threshold_default(self):
        """
        Sets the measurement threshold to the default value.

        This method sends the SCPI command to reset the measurement threshold
        to its default configuration on the oscilloscope.
        """
        self.__write(":MEASure:THReshold:DEFault")

    class MeasureMode(StrEnum):
        Normal = "NORMal"
        Precision = "PRECision"

    @tester._member_logger
    def set_measure_mode(self, mode: MeasureMode):
        self.__set_parameter_str("MEASure", "MODE", mode.value)

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
        """
        Enumeration representing the available options for the length of CSV data to save from the device.

        Attributes:
            Display: Save only the data currently displayed ("DISP").
            Maximum: Save the maximum available data ("MAX").
        """

        Display = "DISP"
        Maximum = "MAX"

    class SaveCsvChannel(StrEnum):
        """
        Enumeration representing the available channels and pods for saving CSV data on the MSO5000 device.

        Attributes:
            Channel1: Represents analog channel 1 ("CHAN1").
            Channel2: Represents analog channel 2 ("CHAN2").
            Channel3: Represents analog channel 3 ("CHAN3").
            Channel4: Represents analog channel 4 ("CHAN4").
            Pod1: Represents digital pod 1 ("POD1").
            Pod2: Represents digital pod 2 ("POD2").
        """

        Channel1 = "CHAN1"
        Channel2 = "CHAN2"
        Channel3 = "CHAN3"
        Channel4 = "CHAN4"
        Pod1 = "POD1"
        Pod2 = "POD2"

    class ImageType(StrEnum):
        """
        Enumeration of supported image file formats for device output.

        Attributes:
            Bitmap: 24-bit Bitmap image format ("BMP24").
            Jpeg: JPEG image format ("JPEG").
            Png: Portable Network Graphics image format ("PNG").
            Tiff: Tagged Image File Format ("TIFF").
        """

        Bitmap = "BMP24"
        Jpeg = "JPEG"
        Png = "PNG"
        Tiff = "TIFF"

    class ImageColor(StrEnum):
        """
        Enumeration representing the color settings available for saved images.
        Attributes:
            Color: Represents a colored image ("COL").
            Gray: Represents a grayscale image ("GRAY").
        """

        Color = "COL"
        Gray = "GRAY"

    @tester._member_logger
    def set_save_csv_length(self, length: SaveCsvLength):
        """
        Sets the data length type for saving CSV files.

        Args:
            length (SaveCsvLength): The desired data length type, must be a member of the SaveCsvLength enum.

        Raises:
            AssertionError: If the provided length is not a valid SaveCsvLength enum value.

        This method configures the instrument to use the specified data length type when saving data to a "*.csv" file.
        """
        assert (
            length in MSO5000.SaveCsvLength
        ), "Length must be one of the SaveCsvLength enum values."
        self.__set_parameter_str("SAVE", "CSV:LENGth", length.value)

    @tester._member_logger
    def set_save_csv_channel(self, channel: SaveCsvChannel, state: bool):
        """
        Sets the on/off status for saving CSV data for a specific channel.

        Args:
            channel (SaveCsvChannel): The channel to configure, must be a member of the SaveCsvChannel enum.
            state (bool): True to enable saving CSV data for the channel, False to disable.

        Raises:
            AssertionError: If the provided channel is not a valid SaveCsvChannel enum value.
        """
        assert (
            channel in MSO5000.SaveCsvChannel
        ), "Channel must be one of the SaveCsvChannel enum values."
        self.__set_parameter_str("SAVE", "CSV:CHANnel", f"{channel.value},{int(state)}")

    @tester._member_logger
    def save_csv(
        self,
        filename: str,
        length: SaveCsvLength = SaveCsvLength.Display,
    ):
        """
        Saves the waveform data currently displayed on the screen to a CSV file.

        Args:
            filename (str): The path and name of the file where the CSV data will be saved.
            length (SaveCsvLength, optional): Specifies the amount of waveform data to save.
                Defaults to SaveCsvLength.Display.

        Raises:
            ValueError: If the filename is invalid or saving fails.

        Note:
            The file can be saved to either internal or external memory.
        """
        self.set_save_csv_length(length)
        self.__set_parameter_str("SAVE", "CSV", filename)

    @tester._member_logger
    def save_image_type(self, type_: ImageType):
        """
        Sets the image type for saving images on the device.

        Args:
            type_ (ImageType): The desired image type, must be a member of the ImageType enum.

        Raises:
            AssertionError: If type_ is not a valid ImageType enum value.
        """
        assert (
            type_ in MSO5000.ImageType
        ), "Type must be one of the ImageType enum values."
        self.__set_parameter_str("SAVE", "IMAGe:TYPE", type_.value)

    @tester._member_logger
    def save_image_invert(self, invert: bool):
        """
        Enables or disables the invert function when saving an image.

        Args:
            invert (bool): If True, the image will be saved with inverted colors; if False, the image will be saved normally.

        Returns:
            None
        """
        self.__set_parameter_bool("SAVE", "IMAGe:INVert", invert)

    @tester._member_logger
    def save_image_color(self, color: ImageColor):
        """
        Sets the color mode for saving images.

        Args:
            color (ImageColor): The desired color mode for the saved image.
                Should be an instance of the ImageColor enum, such as Color or Gray.

        Raises:
            ValueError: If the provided color is not a valid ImageColor enum member.

        Note:
            This method configures the device to save images in the specified color mode.
        """
        self.__set_parameter_str("SAVE", "COLor", color.value)

    @tester._member_logger
    def save_image(
        self,
        path: str,
        type_: ImageType,
        invert: bool = False,
        color: ImageColor = ImageColor.Color,
    ):
        """
        Saves the current screen contents as an image file.

        Args:
            path (str): The file path where the image will be saved.
            type_ (ImageType): The format/type of the image to save (e.g., PNG, BMP).
            invert (bool, optional): Whether to invert the image colors. Defaults to False.
            color (ImageColor, optional): The color mode for the image (e.g., Color, Grayscale). Defaults to ImageColor.Color.

        Raises:
            ValueError: If an invalid image type or color mode is specified.

        Note:
            The image is stored in the specified path, which can be on internal or external memory.
        """
        self.save_image_type(type_)
        self.save_image_invert(invert)
        self.save_image_color(color)
        self.__set_parameter_str("SAVE", "IMAGe", path)

    @tester._member_logger
    def save_setup(self, path: str):
        """
        Saves the current oscilloscope setup parameters to the specified file path.

        Args:
            path (str): The file path where the setup parameters will be saved. This can be an internal or external memory location.

        Raises:
            ValueError: If the provided path is invalid or inaccessible.
            DeviceCommunicationError: If there is an error communicating with the oscilloscope.

        Example:
            oscilloscope.save_setup("D:/setups/my_setup.stp")
        """
        self.__set_parameter_str("SAVE", "SETup", path)

    @tester._member_logger
    def save_waveform(self, path: str):
        """
        Saves the current waveform data to the specified file path.

        Args:
            path (str): The destination file path where the waveform data will be saved. This can be a path to internal or external memory.

        Raises:
            ValueError: If the provided path is invalid or inaccessible.
            DeviceCommunicationError: If there is an error communicating with the device during the save operation.

        Note:
            The file format and supported storage locations depend on the device's capabilities.
        """
        self.__set_parameter_str("SAVE", "WAVeform", path)

    @tester._member_logger
    def get_save_status(self) -> bool:
        """
        Queries and returns the saving status of the internal memory or external USB storage device.

        Returns:
            bool: True if a save operation is currently in progress, False otherwise.
        """
        return self.__get_parameter_bool("SAVE", "STATus")

    @tester._member_logger
    def load_setup(self, filename: str):
        """
        Loads an oscilloscope setup file from the specified filename.

        Args:
            filename (str): The path to the setup file to be loaded onto the oscilloscope.

        Raises:
            Any exceptions raised by the underlying communication or file handling methods.

        Note:
            The filename should be accessible to the oscilloscope device.
        """
        self.__write(f":LOAD:SETup {filename}")

    # The :SEARch commands are used to set the relevant parameters of the search function.

    # The [:SOURce [<n>]] commands are used to set the relevant parameters of the built in function arbitrary
    # waveform generator. <n> can set to 1 or 2, which indicates the corresponding built in function/arbitrary
    # waveform generator channel. When <n> or :SOURce[<n>] is omitted, by default, the operations are
    # carried out on AWG GI.
    class SourceFunction(StrEnum):
        """
        Enumeration of available source waveform functions for the MSO5000 device.

        Attributes:
            Sinusoid: Represents a sinusoidal waveform ("SIN").
            Square: Represents a square waveform ("SQU").
            Ramp: Represents a ramp (sawtooth) waveform ("RAMP").
            Pulse: Represents a pulse waveform ("PULS").
            Noise: Represents a noise waveform ("NOIS").
            Dc: Represents a direct current (DC) level ("DC").
            Sinc: Represents a sinc waveform ("SINC").
            ExponentialRise: Represents an exponential rise waveform ("EXPR").
            ExponentialFall: Represents an exponential fall waveform ("EXPF").
            Ecg: Represents an electrocardiogram (ECG) waveform ("ECG").
            Guass: Represents a Gaussian waveform ("GUAS").
            Lorentz: Represents a Lorentzian waveform ("LOR").
            Haversine: Represents a haversine waveform ("HAV").
            Arbitrary: Represents an arbitrary user-defined waveform ("ARB").
        """

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
        """
        Enumeration of possible source types for the MSO5000 device.

        Attributes:
            _None: Represents no source type ("NONE").
            Modulated: Represents a modulated source type ("MOD").
            Sweep: Represents a sweep source type ("SWE").
            Burst: Represents a burst source type ("BUR").
        """

        _None = "NONE"
        Modulated = "MOD"
        Sweep = "SWE"
        Burst = "BUR"

    class SourceModulation(StrEnum):
        """
        Enumeration of source modulation types.

        Attributes:
            AmplitudeModulation: Represents amplitude modulation ("AM").
            FrequencyModulation: Represents frequency modulation ("FM").
            FrequencyShiftKey: Represents frequency shift keying ("FSK").
        """

        AmplitudeModulation = "AM"
        FrequencyModulation = "FM"
        FrequencyShiftKey = "FSK"

    class SourceSweepType(StrEnum):
        """
        Enumeration of sweep types for a signal source.

        Attributes:
            Linear: Linear sweep type, represented by "LIN".
            Log: Logarithmic sweep type, represented by "LOG".
            Step: Step sweep type, represented by "STEP".
        """

        Linear = "LIN"
        Log = "LOG"
        Step = "STEP"

    class SourceBurstType(StrEnum):
        """
        Enumeration of burst source types for the MSO5000 device.

        Attributes:
            Ncycle: Represents a burst with a specified number of cycles ("NCYCL").
            Infinite: Represents an infinite burst ("INF").
        """

        Ncycle = "NCYCL"
        Infinite = "INF"

    class SourceOutputImpedance(StrEnum):
        """
        Enumeration representing the possible output impedance settings for a signal source.

        Attributes:
            Omeg: Represents an output impedance of high resistance (open or infinite, often labeled as "OMEG").
            Fifty: Represents an output impedance of 50 ohms (labeled as "FIFT").
        """

        Omeg = "OMEG"
        Fifty = "FIFT"

    @tester._member_logger
    def function_generator_state(self, channel: int, state: bool):
        """
        Enables or disables the function generator output for a specified channel.

        Args:
            channel (int): The channel number to control (must be 1 or 2).
            state (bool): True to enable the output, False to disable it.

        Raises:
            AssertionError: If the channel is not 1 or 2.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        self.__set_parameter_bool(f"SOURce{channel}", f"OUTPut{channel}:STATe", state)

    @tester._member_logger
    def set_source_function(self, channel: int, function: SourceFunction):
        """
        Sets the waveform function for the specified function generator channel.

        Args:
            channel (int): The function generator channel to configure (must be 1 or 2).
            function (SourceFunction): The waveform function to set, must be a member of MSO5000.SourceFunction.

        Raises:
            AssertionError: If the channel is not 1 or 2, or if the function is not a valid SourceFunction.

        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            function in MSO5000.SourceFunction
        ), "Function must be one of the Waveform enum values."
        self.__set_parameter_str(f"SOURce{channel}", "FUNCtion", function.value)

    @tester._member_logger
    def set_source_type(self, channel: int, type_: SourceType):
        """
        Sets the signal type for the specified function generator channel.

        Args:
            channel (int): The output channel number (must be 1 or 2).
            type_ (SourceType): The type of signal to set, as a member of the SourceType enum.

        Raises:
            AssertionError: If the channel is not 1 or 2, or if type_ is not a valid SourceType.

        Example:
            set_source_type(1, SourceType.SINE)
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert type in MSO5000.SourceType, "Type must be one of the Type enum values."
        self.__set_parameter_str(f"SOURce{channel}", "TYPE", type_.value)

    @tester._member_logger
    def set_source_frequency(self, channel: int, frequency: float):
        """
        Sets the frequency of the function generator for the specified channel.

        Args:
            channel (int): The output channel to set the frequency on (must be 1 or 2).
            frequency (float): The desired frequency in Hz (must be between 0.01 and 25,000,000 Hz).

        Raises:
            AssertionError: If the channel is not 1 or 2.
            AssertionError: If the frequency is not within the valid range (0.01 < frequency < 25,000,000 Hz).
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            frequency > 0.01 and frequency < 25000000
        ), "Frequency must be between 0.1 and 25000000 Hz."
        self.__set_parameter_float(f"SOURce{channel}", "FREQuency", frequency)

    @tester._member_logger
    def set_source_phase(self, channel: int, phase: float):
        """
        Sets the phase of the function generator for the specified channel.

        Parameters:
            channel (int): The output channel to set the phase on (must be 1 or 2).
            phase (float): The phase value to set, in degrees (must be between 0 and 360).

        Raises:
            AssertionError: If the channel is not 1 or 2, or if the phase is not between 0 and 360 degrees.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert phase >= 0 and phase <= 360, "Phase must be between 0 and 360 degrees."
        self.__set_parameter_float(f"SOURce{channel}", "PHASe", phase)

    @tester._member_logger
    def set_source_amplitude(self, channel: int, amplitude: float):
        """
        Set the amplitude of the function generator for a specified channel.

        Parameters:
            channel (int): The output channel to set the amplitude for (must be 1 or 2).
            amplitude (float): The desired amplitude in Vpp (must be between 0.02 and 5).

        Raises:
            AssertionError: If the channel is not 1 or 2, or if the amplitude is not within 0.02 to 5 Vpp.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            amplitude >= 0.02 and amplitude <= 5
        ), "Amplitude must be between 0.02 and 5 Vpp."
        self.__set_parameter_float(
            f"SOURce{channel}", "VOLTage:LEVel:IMMediate:AMPLitude", amplitude
        )

    @tester._member_logger
    def set_source_offset(self, channel: int, offset: float):
        """
        Sets the DC offset voltage for the specified function generator channel.

        Parameters:
            channel (int): The channel number to set the offset for (must be 1 or 2).
            offset (float): The desired offset voltage in volts (must be between -2.5 and 2.5 V).

        Raises:
            AssertionError: If the channel is not 1 or 2, or if the offset is outside the allowed range.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            offset >= -2.5 and offset <= 2.5
        ), "Offset must be between -2.5 and 2.5 V."
        self.__set_parameter_float(
            f"SOURce{channel}", "VOLTage:LEVel:IMMediate:OFFSet", offset
        )

    @tester._member_logger
    def phase_align(self, channel: int):
        """
        Initiates phase alignment for the specified function generator channel.

        Args:
            channel (int): The function generator channel to align (must be 1 or 2).

        Raises:
            AssertionError: If the channel is not 1 or 2.

        This method sends a command to the device to initiate phase alignment on the specified channel.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        self.__write(f"SOURce{channel}:PHASe:INITiate")

    @tester._member_logger
    def set_source_output_impedance(
        self, channel: int, impedance: SourceOutputImpedance
    ):
        """
        Sets the output impedance of the function generator for the specified channel.

        Args:
            channel (int): The output channel number (must be 1 or 2).
            impedance (SourceOutputImpedance): The desired output impedance, specified as a member of the SourceOutputImpedance enum.

        Raises:
            AssertionError: If the channel is not 1 or 2.
            AssertionError: If the impedance is not a valid SourceOutputImpedance enum value.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            impedance in MSO5000.SourceOutputImpedance
        ), "Output impedance must be one of the OutputImpedance enum values."
        self.__set_parameter_str(
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
        """
        Configures the function generator to output a sinusoidal waveform on the specified channel.

        Parameters:
            channel (int): The output channel of the function generator.
            frequency (float, optional): Frequency of the sinusoid in Hz. Defaults to 1000.
            phase (float, optional): Phase of the sinusoid in degrees. Defaults to 0.
            amplitude (float, optional): Peak-to-peak amplitude of the sinusoid in volts. Defaults to 0.5.
            offset (float, optional): DC offset of the sinusoid in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): Output impedance setting. Defaults to SourceOutputImpedance.Omeg.

        Returns:
            None
        """
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
        """
        Configures the function generator to output a square wave on the specified channel.

        Parameters:
            channel (int): The output channel to configure.
            frequency (float, optional): Frequency of the square wave in Hz. Defaults to 1000.
            phase (float, optional): Phase offset of the square wave in degrees. Defaults to 0.
            amplitude (float, optional): Amplitude of the square wave in volts. Defaults to 0.5.
            offset (float, optional): DC offset of the square wave in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): Output impedance setting. Defaults to SourceOutputImpedance.Omeg.

        This method disables the output, sets the waveform to square, and applies the specified parameters.
        """
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
        """
        Sets the symmetry percentage of the ramp waveform for the specified function generator channel.

        Parameters:
            channel (int): The output channel number (must be 1 or 2).
            symmetry (float): The symmetry of the ramp waveform in percent (must be between 1 and 100).

        Raises:
            AssertionError: If the channel is not 1 or 2, or if symmetry is not between 1 and 100.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert symmetry >= 1 and symmetry <= 100, "Symmetry must be between 1 and 100%."
        self.__set_parameter_float(
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
        """
        Configures the function generator to output a ramp waveform on the specified channel with the given parameters.

        Args:
            channel (int): The output channel to configure.
            frequency (float, optional): Frequency of the ramp waveform in Hz. Defaults to 1000.
            phase (float, optional): Phase offset of the waveform in degrees. Defaults to 0.
            symmetry (float, optional): Symmetry of the ramp waveform in percent (0-100). Defaults to 50.
            amplitude (float, optional): Peak-to-peak amplitude of the waveform in volts. Defaults to 0.5.
            offset (float, optional): DC offset of the waveform in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): Output impedance setting. Defaults to SourceOutputImpedance.Omeg.

        Returns:
            None
        """
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
        """
        Sets the duty cycle for the pulse function of the specified function generator channel.

        Args:
            channel (int): The output channel to set the duty cycle for (must be 1 or 2).
            duty_cycle (float): The desired duty cycle percentage (must be between 10 and 90).

        Raises:
            AssertionError: If the channel is not 1 or 2.
            AssertionError: If the duty cycle is not between 10 and 90 percent.

        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            duty_cycle >= 10 and duty_cycle <= 90
        ), "Duty cycle must be between 10 and 90%."
        self.__set_parameter_float(f"SOURce{channel}", "PULSe:DCYCle", duty_cycle)

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
        """
        Configures the function generator to output a pulse waveform on the specified channel.

        Parameters:
            channel (int): The output channel to configure.
            frequency (float, optional): The frequency of the pulse waveform in Hz. Defaults to 1000.
            phase (float, optional): The phase offset of the pulse waveform in degrees. Defaults to 0.
            duty_cycle (float, optional): The duty cycle of the pulse waveform as a percentage. Defaults to 20.
            amplitude (float, optional): The amplitude of the pulse waveform in volts. Defaults to 0.5.
            offset (float, optional): The DC offset of the pulse waveform in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): The output impedance setting. Defaults to SourceOutputImpedance.Omeg.

        This method disables the function generator output, sets the waveform to pulse, and applies the specified parameters.
        """
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
        """
        Configures the function generator to output a noise signal on the specified channel.

        Parameters:
            channel (int): The output channel of the function generator to configure.
            amplitude (float, optional): The amplitude of the noise signal in volts. Defaults to 0.5.
            offset (float, optional): The DC offset to apply to the noise signal in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): The output impedance setting for the channel. Defaults to SourceOutputImpedance.Omeg.

        This method disables the function generator output, sets the output function to noise, and applies the specified amplitude, offset, and output impedance.
        """
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
        """
        Configures the function generator to output a DC signal on the specified channel.

        Args:
            channel (int): The output channel to configure.
            offset (float, optional): The DC offset voltage to set. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): The output impedance setting. Defaults to SourceOutputImpedance.Omeg.

        This method disables the function generator output, sets the function to DC, applies the specified offset, and configures the output impedance.
        """
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
        """
        Configures the function generator to output a sinc waveform on the specified channel.

        Parameters:
            channel (int): The output channel of the function generator.
            frequency (float, optional): Frequency of the sinc waveform in Hz. Defaults to 1000.
            phase (float, optional): Phase offset of the waveform in degrees. Defaults to 0.
            amplitude (float, optional): Peak-to-peak amplitude of the waveform in volts. Defaults to 0.5.
            offset (float, optional): DC offset of the waveform in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): Output impedance setting. Defaults to SourceOutputImpedance.Omeg.

        This method disables the output, sets the waveform to sinc, and applies the specified parameters.
        """
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
        """
        Disables the function generator output and sets the source type to None for the specified channel.

        Args:
            channel (int): The channel number for which to disable the function generator output.

        This method turns off the function generator for the given channel and resets its source type to None.
        """
        self.function_generator_state(channel, False)
        self.set_source_type(channel, MSO5000.SourceType._None)

    # Function Generator Type: Modulation
    @tester._member_logger
    def set_source_mod_type(self, channel: int, mod_type: SourceModulation):
        """
        Sets the modulation type for the specified function generator channel.

        Args:
            channel (int): The output channel number (must be 1 or 2).
            mod_type (SourceModulation): The modulation type to set, must be a member of the SourceModulation enum.

        Raises:
            AssertionError: If the channel is not 1 or 2.
            AssertionError: If mod_type is not a valid SourceModulation enum value.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            mod_type in MSO5000.SourceModulation
        ), "Modulation type must be one of the Modulation enum values."
        self.__set_parameter_str(f"SOURce{channel}", "MODulation:TYPE", mod_type.value)

    @tester._member_logger
    def set_source_mod_am_depth(self, channel: int, depth: float):
        """
        Sets the amplitude modulation (AM) depth for the specified function generator channel.

        Parameters:
            channel (int): The output channel to configure (must be 1 or 2).
            depth (float): The desired modulation depth as a percentage (0 to 120).

        Raises:
            AssertionError: If the channel is not 1 or 2, or if the depth is not between 0 and 120.

        This method configures the AM depth of the function generator, controlling the extent of amplitude modulation applied to the output signal.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            depth >= 0 and depth <= 120
        ), "Modulation amplitude depth must be between 0 and 120%."
        self.__set_parameter_float(f"SOURce{channel}", "MOD:DEPTh", depth)

    @tester._member_logger
    def set_source_mod_am_freq(self, channel: int, frequency: float):
        """
        Sets the amplitude modulation (AM) frequency for the function generator on the specified channel.

        Parameters:
            channel (int): The output channel to configure (must be 1 or 2).
            frequency (float): The desired AM modulation frequency in Hz (must be between 1 and 50 Hz).

        Raises:
            AssertionError: If the channel is not 1 or 2, or if the frequency is not between 1 and 50 Hz.

        This method configures the internal AM modulation frequency for the specified channel.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            frequency >= 1 and frequency <= 50
        ), "Modulation frequency must be between 1 and 50 Hz."
        self.__set_parameter_float(
            f"SOURce{channel}", "MOD:AM:INTernal:FREQuency", frequency
        )

    @tester._member_logger
    def set_source_mod_fm_freq(self, channel: int, frequency: float):
        """
        Sets the frequency of frequency modulation (FM) for the function generator on the specified channel.

        Parameters:
            channel (int): The output channel to configure (must be 1 or 2).
            frequency (float): The modulation frequency in Hz (must be between 1 and 50 Hz).

        Raises:
            AssertionError: If the channel is not 1 or 2, or if the frequency is not between 1 and 50 Hz.

        This method configures the internal FM modulation frequency for the specified channel.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            frequency >= 1 and frequency <= 50
        ), "Modulation frequency must be between 1 and 50 Hz."
        self.__set_parameter_float(
            f"SOURce{channel}", "MOD:FM:INTernal:FREQuency", frequency
        )

    @tester._member_logger
    def set_source_mod_am_function(self, channel: int, function: SourceFunction):
        """
        Sets the modulation function for amplitude modulation (AM) on the specified function generator channel.

        Parameters:
            channel (int): The output channel number (must be 1 or 2).
            function (SourceFunction): The modulation waveform type. Must be one of:
                - MSO5000.SourceFunction.SINusoid
                - MSO5000.SourceFunction.SQUare
                - MSO5000.SourceFunction.RAMP
                - MSO5000.SourceFunction.NOISe

        Raises:
            AssertionError: If the channel is not 1 or 2, or if the function is not a supported modulation type.

        This method configures the internal modulation function used for amplitude modulation on the specified channel.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert function in [
            MSO5000.SourceFunction.SINusoid,
            MSO5000.SourceFunction.SQUare,
            MSO5000.SourceFunction.RAMP,
            MSO5000.SourceFunction.NOISe,
        ], "Modulation function must be one of SINusoid, SQUare, RAMP, NOISe."
        self.__set_parameter_str(
            f"SOURce{channel}", "MOD:AM:INTernal:FUNCtion", function.value
        )

    @tester._member_logger
    def set_source_mod_fm_function(self, channel: int, function: SourceFunction):
        """
        Sets the modulation function for frequency modulation (FM) on the specified function generator channel.

        Args:
            channel (int): The output channel number (must be 1 or 2).
            function (SourceFunction): The modulation waveform function. Must be one of:
                - MSO5000.SourceFunction.SINusoid
                - MSO5000.SourceFunction.SQUare
                - MSO5000.SourceFunction.RAMP
                - MSO5000.SourceFunction.NOISe

        Raises:
            AssertionError: If the channel is not 1 or 2.
            AssertionError: If the function is not a supported modulation function.

        This method configures the internal modulation waveform used for FM modulation on the specified channel.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert function in [
            MSO5000.SourceFunction.SINusoid,
            MSO5000.SourceFunction.SQUare,
            MSO5000.SourceFunction.RAMP,
            MSO5000.SourceFunction.NOISe,
        ], "Modulation function must be one of SINusoid, SQUare, RAMP, NOISe."
        self.__set_parameter_str(
            f"SOURce{channel}", "MOD:FM:INTernal:FUNCtion", function.value
        )

    @tester._member_logger
    def set_source_mod_fm_deviation(self, channel: int, deviation: float):
        """
        Sets the frequency deviation for FM modulation on the specified function generator channel.

        Args:
            channel (int): The output channel number (must be 1 or 2).
            deviation (float): The desired frequency deviation in Hz (must be >= 0).

        Raises:
            AssertionError: If the channel is not 1 or 2, or if the deviation is negative.

        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            deviation >= 0
        ), "Modulation frequency deviation must be greater than or equal to 0 Hz."
        self.__set_parameter_float(f"SOURce{channel}", "MOD:FM:DEViation", deviation)

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
        """
        Configures the modulation settings for the function generator on the specified channel.

        Parameters:
            channel (int): The output channel to configure.
            type_ (SourceModulation, optional): The type of modulation to apply. Defaults to SourceModulation.AmplitudeModulation.
            am_depth (float, optional): Amplitude modulation depth (percentage). Used only if type_ is AM. Defaults to 100.
            frequency (float, optional): Modulation frequency in Hz. Used for both AM and FM. Defaults to 1000.
            function (SourceFunction, optional): The waveform function used for modulation. Defaults to SourceFunction.Sinusoid.
            fm_deviation (float, optional): Frequency deviation for FM modulation in Hz. Used only if type_ is FM. Defaults to 1000.

        Behavior:
            - Disables the function generator output before applying new settings.
            - Sets the source type to modulated.
            - Configures modulation parameters based on the selected modulation type (AM or FM).
        """
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
        """
        Sets the sweep type for the specified function generator channel.

        Args:
            channel (int): The function generator channel to configure (must be 1 or 2).
            type_ (SourceSweepType): The desired sweep type, as a member of the SourceSweepType enum.

        Raises:
            AssertionError: If the channel is not 1 or 2, or if type_ is not a valid SourceSweepType.

        This method sends the appropriate command to set the sweep type for the given channel.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            type_ in MSO5000.SourceSweepType
        ), "Sweep type must be one of the SweepType enum values."
        self.__set_parameter_str(f"SOURce{channel}", "SWEep:TYPE", type_.value)

    @tester._member_logger
    def set_source_sweep_sweep_time(self, channel: int, time: int):
        """
        Sets the sweep time for the specified function generator channel.

        Parameters:
            channel (int): The function generator channel to configure (must be 1 or 2).
            time (int): The sweep time in seconds (must be between 1 and 500).

        Raises:
            AssertionError: If the channel is not 1 or 2, or if the time is not between 1 and 500 seconds.

        This method sends the appropriate command to set the sweep time for the given channel.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            time >= 1 and time <= 500
        ), "Sweep time must be between 1 and 500 seconds."
        self.__set_parameter_int(f"SOURce{channel}", "SWEep:STIMe", time)

    @tester._member_logger
    def set_source_sweep_return_time(self, channel: int, time: int):
        """
        Sets the sweep return time for the specified source channel.

        Parameters:
            channel (int): The source channel number (must be 1 or 2).
            time (int): The sweep return time in seconds (must be between 1 and 500).

        Raises:
            AssertionError: If the channel is not 1 or 2, or if the time is not between 1 and 500 seconds.

        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            time >= 1 and time <= 500
        ), "Return time must be between 1 and 500 seconds."
        self.__set_parameter_int(f"SOURce{channel}", "SWEep:BTIMe", time)

    @tester._member_logger
    def function_generator_sweep(
        self,
        channel: int,
        type_: SourceSweepType = SourceSweepType.Linear,
        sweep_time: int = 1,
        return_time: int = 0,
    ):
        """
        Configures the sweep function of the function generator for a specified channel.

        Args:
            channel (int): The output channel of the function generator to configure.
            type_ (SourceSweepType, optional): The type of sweep to use (e.g., linear, logarithmic). Defaults to SourceSweepType.Linear.
            sweep_time (int, optional): The duration of the sweep in seconds. Defaults to 1.
            return_time (int, optional): The return time after the sweep in seconds. Defaults to 0.

        This method disables the function generator output, sets the source type to sweep, configures the sweep type, sweep time, and return time for the specified channel.
        """
        self.function_generator_state(channel, False)
        self.set_source_type(channel, MSO5000.SourceType.Sweep)
        self.set_source_sweep_type(channel, type_)
        self.set_source_sweep_sweep_time(channel, sweep_time)
        self.set_source_sweep_return_time(channel, return_time)

    # Function Generator Type: Burst
    @tester._member_logger
    def set_source_burst_type(self, channel: int, type_: SourceBurstType):
        """
        Sets the burst type for the specified source channel.

        Args:
            channel (int): The source channel number (must be 1 or 2).
            type_ (SourceBurstType): The burst type to set, must be a member of the SourceBurstType enum.

        Raises:
            AssertionError: If the channel is not 1 or 2, or if the burst type is not valid.

        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            type_ in MSO5000.SourceBurstType
        ), "Burst type must be one of the BurstType enum values."
        self.__set_parameter_str(f"SOURce{channel}", "BURSt:TYPE", type_.value)

    @tester._member_logger
    def set_source_burst_cycles(self, channel: int, cycles: int):
        """
        Sets the number of burst cycles for the specified function generator channel.

        Args:
            channel (int): The function generator channel to configure (1 or 2).
            cycles (int): The number of burst cycles to set (must be between 1 and 1,000,000).

        Raises:
            AssertionError: If the channel is not 1 or 2.
            AssertionError: If cycles is not between 1 and 1,000,000 (inclusive).
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            cycles >= 1 and cycles <= 1000000
        ), "Burst cycles must be between 1 and 1000000."
        self.__set_parameter_int(f"SOURce{channel}", "BURSt:CYCLes", cycles)

    @tester._member_logger
    def set_source_burst_delay(self, channel: int, delay: int):
        """
        Sets the burst delay for the specified source channel.

        Args:
            channel (int): The source channel number (must be 1 or 2).
            delay (int): The burst delay value in microseconds (must be between 1 and 1,000,000).

        Raises:
            AssertionError: If the channel is not 1 or 2.
            AssertionError: If the delay is not between 1 and 1,000,000.

        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            delay >= 1 and delay <= 1000000
        ), "Burst delay must be between 1 and 1000000."
        self.__set_parameter_int(f"SOURce{channel}", "BURSt:DELay", delay)

    @tester._member_logger
    def function_generator_burst(
        self,
        channel: int,
        type_: SourceBurstType = SourceBurstType.Ncycle,
        cycles: int = 1,
        delay: int = 0,
    ):
        """
        Configures the burst mode settings for the function generator on the specified channel.

        Parameters:
            channel (int): The output channel of the function generator to configure.
            type_ (SourceBurstType, optional): The burst type to set (default is SourceBurstType.Ncycle).
            cycles (int, optional): Number of cycles per burst (default is 1).
            delay (int, optional): Delay before the burst starts, in appropriate units (default is 0).

        This method disables the function generator output, sets the source type to Sweep, and applies the specified burst type, cycle count, and delay.
        """
        self.function_generator_state(channel, False)
        self.set_source_type(channel, MSO5000.SourceType.Sweep)
        self.set_source_burst_type(channel, type_)
        self.set_source_burst_cycles(channel, cycles)
        self.set_source_burst_delay(channel, delay)

    # The :SYSTem commands are used to set sound, language, and other relevant system settings.
    @tester._member_logger
    def get_system_error(self) -> str:
        """
        Queries the instrument for the next system error message and clears it from the error queue.

        Returns:
            str: The latest system error message, or "0,No error" if no errors are present.
        """
        return self.__get_parameter_str("SYSTem", "ERRor:NEXT")

    # The :TIMebase commands are used to set the horizontal system. For example, enable the delayed sweep,
    # set the horizontal time base mode, etc.
    class TimebaseMode(StrEnum):
        """
        Enumeration of available timebase modes for the device.

        Attributes:
            Main: Standard main timebase mode.
            Xy: XY display mode, typically used for Lissajous figures.
            Roll: Roll mode, used for slow signal acquisition and display.
        """

        Main = "MAIN"
        Xy = "XY"
        Roll = "ROLL"

    class HrefMode(StrEnum):
        """
        Enumeration of horizontal reference (Href) modes for the MSO5000 device.

        Attributes:
            Center: Horizontal reference is set to the center ("CENT").
            Lb: Horizontal reference is set to the left border ("LB").
            Rb: Horizontal reference is set to the right border ("RB").
            Trigger: Horizontal reference is set to the trigger position ("TRIG").
            User: Horizontal reference is set to a user-defined position ("USER").
        """

        Center = "CENT"
        Lb = "LB"
        Rb = "RB"
        Trigger = "TRIG"
        User = "USER"

    @tester._member_logger
    def set_timebase_delay_enable(self, enable: bool):
        """
        Enables or disables the delayed sweep mode on the oscilloscope timebase.

        Args:
            enable (bool): If True, enables the delayed sweep; if False, disables it.
        """
        self.__set_parameter_bool("TIMebase", "DELay:ENABle", enable)

    @tester._member_logger
    def set_timebase_delay_offset(self, offset: float):
        """
        Sets the offset for the delayed time base of the oscilloscope.

        Args:
            offset (float): The offset value to set, in seconds.

        Raises:
            ValueError: If the provided offset is not a valid float.

        Note:
            The default unit for the offset is seconds (s).
        """
        self.__set_parameter_float("TIMebase", "DELay:OFFSet", offset)

    @tester._member_logger
    def set_timebase_delay_scale(self, scale: float):
        """
        Sets the scale (seconds per division) for the delayed time base of the oscilloscope.

        Args:
            scale (float): The desired scale for the delayed time base, in seconds per division (s/div).

        Raises:
            ValueError: If the provided scale is not a positive float.

        Note:
            The delayed time base allows for detailed analysis of a specific portion of the main time base.
        """
        self.__set_parameter_float("TIMebase", "DELay:SCALe", scale)

    @tester._member_logger
    def timebase_delay(
        self, enable: bool = False, offset: float = 0, scale: float = 500e-9
    ):
        """
        Configures the timebase delay settings for the device.

        Args:
            enable (bool, optional): If True, enables the timebase delay. Defaults to False.
            offset (float, optional): The offset value for the timebase delay in seconds. Defaults to 0.
            scale (float, optional): The scale value for the timebase delay in seconds per division. Defaults to 500e-9.

        Returns:
            None
        """
        self.set_timebase_delay_enable(enable)
        self.set_timebase_delay_offset(offset)
        self.set_timebase_delay_scale(scale)

    @tester._member_logger
    def set_timebase_offset(self, offset: float):
        """
        Sets the offset of the main time base.

        Args:
            offset (float): The offset value to set for the main time base, in seconds.

        Raises:
            ValueError: If the provided offset is not a valid float.

        Note:
            The default unit for the offset is seconds (s).
        """
        self.__set_parameter_float("TIMebase", "MAIN:OFFSet", offset)

    @tester._member_logger
    def set_timebase_scale(self, scale: float):
        """
        Sets the timebase scale of the oscilloscope.

        Args:
            scale (float): The desired timebase scale value to set, typically in seconds/division.

        Raises:
            ValueError: If the provided scale is not a valid float or out of acceptable range.

        Note:
            This method sends the scale parameter to the device using the internal __set_parameter_float method.
        """
        self.__set_parameter_float("TIMebase", "MAIN:SCALe", scale)

    @tester._member_logger
    def set_timebase_mode(self, mode: TimebaseMode):
        """
        Sets the timebase mode of the MSO5000 device.

        Args:
            mode (TimebaseMode): The desired timebase mode, must be a member of the TimebaseMode enum.

        Raises:
            AssertionError: If the provided mode is not a valid TimebaseMode enum value.

        """
        assert (
            mode in MSO5000.TimebaseMode
        ), "Timebase mode must be one of the TimebaseMode enum values."
        self.__set_parameter_str("TIMebase", "MODE", mode.value)

    @tester._member_logger
    def set_timebase_href_mode(self, mode: HrefMode):
        """
        Sets the horizontal reference (HREF) mode of the oscilloscope's timebase.

        Args:
            mode (HrefMode): The desired horizontal reference mode. Must be a member of the HrefMode enum.

        Raises:
            AssertionError: If the provided mode is not a valid HrefMode enum value.

        This method configures the oscilloscope to use the specified horizontal reference mode for the timebase.
        """
        assert (
            mode in MSO5000.HrefMode
        ), "Href mode must be one of the HrefMode enum values."
        self.__set_parameter_str("TIMebase", "HREFerence:MODE", mode.value)

    @tester._member_logger
    def set_timebase_position(self, position: int):
        """
        Sets the horizontal reference position of the oscilloscope's timebase.

        This method defines the user-specified reference position for the waveform display
        when the timebase is expanded or compressed horizontally. The position determines
        where the reference point appears on the screen.

        Args:
            position (int): The horizontal reference position, must be between -500 and 500.

        Raises:
            AssertionError: If the position is not within the valid range (-500 to 500).
        """
        assert (
            position >= -500 and position <= 500
        ), "Horizontal reference position must be between -500 to 500."
        self.__set_parameter_int("TIMebase", "HREFerence:POSition", position)

    @tester._member_logger
    def set_timebase_vernier(self, vernier: bool):
        """
        Enables or disables the fine adjustment (vernier) function of the oscilloscope's horizontal timebase scale.

        Args:
            vernier (bool): If True, enables the fine adjustment (vernier) mode for the timebase. If False, disables it.

        Raises:
            Any exceptions raised by the underlying __set_parameter_bool method.

        Example:
            device.set_timebase_vernier(True)  # Enables fine adjustment
        """
        self.__set_parameter_bool("TIMebase", "VERNier", vernier)

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
        """
        Configures the oscilloscope's timebase settings.

        Parameters:
            offset (float, optional): The horizontal offset (in seconds) for the timebase. Defaults to 0.
            scale (float, optional): The timebase scale (in seconds/division). Defaults to 1e-6.
            mode (TimebaseMode, optional): The timebase mode (e.g., Main, Window, XY). Defaults to TimebaseMode.Main.
            href_mode (HrefMode, optional): The horizontal reference mode (e.g., Center, Left, Right). Defaults to HrefMode.Center.
            position (float, optional): The horizontal position (in divisions or seconds). Defaults to 0.
            vernier (bool, optional): Whether to enable fine adjustment (vernier) of the timebase. Defaults to False.

        Returns:
            None
        """
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
        """
        Enumeration of trigger modes for the MSO5000 device.

        Each member represents a specific trigger mode that can be set on the device:

        - Edge: Trigger on a signal edge.
        - Pulse: Trigger on a pulse width.
        - Slope: Trigger on a signal slope.
        - Video: Trigger on video signals.
        - Pattern: Trigger on a specific pattern.
        - Duration: Trigger based on signal duration.
        - Timeout: Trigger on a timeout event.
        - Runt: Trigger on runt pulses.
        - Window: Trigger when a signal enters or exits a window.
        - Delay: Trigger after a specified delay.
        - Setup: Trigger on setup/hold violations.
        - Nedge: Trigger on a specified number of edges.
        - RS232: Trigger on RS232 protocol events.
        - IIC: Trigger on I2C protocol events.
        - SPI: Trigger on SPI protocol events.
        - CAN: Trigger on CAN protocol events.
        - Flexray: Trigger on FlexRay protocol events.
        - LIN: Trigger on LIN protocol events.
        - IIS: Trigger on IIS protocol events.
        - M1553: Trigger on MIL-STD-1553 protocol events.
        """

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
        """
        Enumeration representing the trigger coupling modes for the device.

        Attributes:
            AC: Alternating Current coupling mode.
            DC: Direct Current coupling mode.
            LfReject: Low-frequency reject coupling mode ("LFR").
            HfReject: High-frequency reject coupling mode ("HFR").
        """

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
        _status = self.__get_parameter_str("TRIGger", "STATus")
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
        self.__set_parameter_str("TRIGger", "MODE", mode.value)

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
        self.__set_parameter_str("TRIGger", "COUPling", coupling.value)

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
        self.__set_parameter_str("TRIGger", "SWEep", sweep.value)

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
        self.__set_parameter_float("TRIGger", "HOLDoff", holdoff)

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
        self.__set_parameter_bool("TRIGger", "NREJect", status)

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
        self.__set_parameter_str("TRIGger", "EDGE:SOURce", source.value)

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
        self.__set_parameter_str("TRIGger", "EDGE:SLOPe", slope.value)

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
        self.__set_parameter_float("TRIGger", "EDGE:LEVel", level)

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
            nreject (bool, optional): Enables or disables noise rejection. Defaults to False.
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
        self.__set_parameter_str("TRIGger", "PULSe:SOURce", source.value)

    @tester._member_logger
    def set_trigger_pulse_when(self, when: TriggerWhen):
        """
        Sets the trigger condition for pulse width triggering on the device.

        Args:
            when (TriggerWhen): The trigger condition, must be a value from the MSO5000.TriggerWhen enum.

        Raises:
            AssertionError: If 'when' is not a valid TriggerWhen enum value.

        This method configures the oscilloscope to trigger when the pulse width condition specified by 'when' is met.
        """
        assert (
            when in MSO5000.TriggerWhen
        ), "Trigger pulse when must be one of the TriggerWhen enum values."
        self.__set_parameter_str("TRIGger", "PULSe:WHEN", when.value)

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
        self.__set_parameter_float("TRIGger", "PULSe:UWIDth", width)

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
        self.__set_parameter_float("TRIGger", "PULSe:LWIDth", width)

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
        self.__set_parameter_float("TRIGger", "PULSe:LEVel", level)

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
            coupling (TriggerCoupling): The trigger coupling mode (e.g., DC, AC).
            sweep (TriggerSweep): The trigger sweep mode (e.g., Auto, Normal).
            holdoff (float): The trigger holdoff time in seconds.
            nreject (bool): Whether to enable noise rejection for the trigger.
            pulse_source (TriggerSource): The source channel for the pulse trigger.
            pulse_when (TriggerWhen): The pulse condition (e.g., Greater, Less).
            pulse_upper_width (float): The upper width threshold for the pulse in seconds.
            pulse_lower_width (float): The lower width threshold for the pulse in seconds.
            pulse_level (float): The voltage level at which to trigger on the pulse.

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
        self.__set_parameter_str("TRIGger", "SLOPe:SOURce", source.value)

    @tester._member_logger
    def set_trigger_slope_when(self, when: TriggerWhen):
        """
        Sets the trigger slope condition for the oscilloscope.

        Args:
            when (TriggerWhen): The trigger slope condition to set. Must be a value from the TriggerWhen enum.

        Raises:
            AssertionError: If 'when' is not a valid TriggerWhen enum value.

        """
        assert (
            when in MSO5000.TriggerWhen
        ), "Trigger when must be one of the TriggerWhen enum values."
        self.__set_parameter_str("TRIGger", "SLOPe:WHEN", when.value)

    @tester._member_logger
    def set_trigger_slope_time_upper(self, time: float):
        """
        Sets the upper time limit for the trigger slope.

        Args:
            time (float): The upper time limit in seconds. Must be less than or equal to 10.

        Raises:
            AssertionError: If the provided time is greater than 10 seconds.

        """
        assert time <= 10, "Upper time limit must be less than 10 s."
        self.__set_parameter_float("TRIGger", "SLOPe:TUPPer", time)

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
        self.__set_parameter_float("TRIGger", "SLOPe:TLOWer", time)

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
        self.__set_parameter_str("TRIGger", "SLOPe:WINDow", window.value)

    @tester._member_logger
    def set_trigger_slope_amplitude_upper(self, amplitude: float):
        """
        Sets the upper amplitude limit for the trigger slope on the oscilloscope.

        Args:
            amplitude (float): The upper amplitude threshold to set for the trigger slope.

        Raises:
            ValueError: If the provided amplitude is out of the valid range for the oscilloscope.
        """
        self.__set_parameter_float("TRIGger", "SLOPe:ALEVel", amplitude)

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
        self.__set_parameter_float("TRIGger", "SLOPe:BLEVel", amplitude)

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
        Sets the trigger timeout source for the device.

        Args:
            source (TriggerSource): The trigger source to set. Must not be `TriggerSource.AcLine`.

        Raises:
            AssertionError: If the provided source is `TriggerSource.AcLine`.

        """
        assert (
            source is not MSO5000.TriggerSource.AcLine
        ), "Trigger source cannot be ACLine."
        self.__set_parameter_str("TRIGger", "TIMeout:SOURce", source.value)

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
        self.__set_parameter_str("TRIGger", "TIMeout:SLOPe", slope.value)

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
        self.__set_parameter_float("TRIGger", "TIMeout:TIME", time)

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
        self.__set_parameter_float("TRIGger", "TIMeout:LEVel", level)

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
            source (TriggerSource, optional): The trigger source channel. Defaults to TriggerSource.Channel1.
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
        self.__set_parameter_str("WAVeform", "SOURce", source.value)

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
        self.__set_parameter_str("WAVeform", "MODE", mode.value)

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
        self.__set_parameter_str("WAVeform", "FORMat", format_.value)

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
        self.__set_parameter_int("WAVeform", "POINts", points)

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
        return self.__get_parameter_float("WAVeform", "XINCrement")

    @tester._member_logger
    def get_waveform_xorigin(self) -> float:
        """
        Retrieves the X origin value of the current waveform.

        Returns:
            float: The X origin of the waveform, typically representing the starting point on the X-axis (time axis) in waveform data.
        """
        return self.__get_parameter_float("WAVeform", "XORigin")

    @tester._member_logger
    def get_waveform_xreference(self) -> float:
        """
        Retrieves the X reference value of the current waveform.

        Returns:
            float: The X reference value of the waveform, typically representing the horizontal offset or reference point on the X-axis.
        """
        return self.__get_parameter_float("WAVeform", "XREFerence")

    @tester._member_logger
    def get_waveform_yincrement(self) -> float:
        """
        Retrieves the vertical increment (Y increment) value of the current waveform.

        Returns:
            float: The Y increment value, representing the voltage difference between adjacent data points in the waveform.
        """
        return self.__get_parameter_float("WAVeform", "YINCrement")

    @tester._member_logger
    def get_waveform_yorigin(self) -> float:
        """
        Gets the Y origin value of the current waveform.

        Returns:
            float: The Y origin of the waveform as a floating-point number.
        """
        return self.__get_parameter_float("WAVeform", "YORigin")

    @tester._member_logger
    def get_waveform_yreference(self) -> float:
        """
        Retrieves the Y reference value of the current waveform.

        Returns:
            float: The Y reference value used for scaling the waveform data.
        """
        return self.__get_parameter_float("WAVeform", "YREFerence")

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
        self.__set_parameter_int("WAVeform", "STARt", start)

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
        self.__set_parameter_int("WAVeform", "STOP", stop)

    @tester._member_logger
    def get_waveform_preamble(self) -> str:
        """
        Retrieves the waveform preamble from the device.

        Returns:
            str: The waveform preamble as a string, typically containing information about the waveform format, such as scaling, offset, and other acquisition parameters.
        """
        return self.__get_parameter_str("WAVeform", "PREamble")
