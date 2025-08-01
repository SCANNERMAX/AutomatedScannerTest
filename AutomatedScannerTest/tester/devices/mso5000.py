# -*- coding: utf-8 -*-
from PySide6 import QtCore
from ctypes.wintypes import BYTE
from enum import StrEnum
import pyvisa

from tester.devices import Device


class MSO5000(Device):
    __cache = {}

    def __init__(self):
        """
        Initializes a new instance of the MSO5000 device class.
        """
        super().__init__("MSO5000")
        self.__instrument = None

    def __getattr__(self, name):
        inst = self.__instrument
        if inst is not None:
            try:
                return getattr(inst, name)
            except AttributeError:
                pass
        cache = self.__cache
        if name in cache:
            return cache[name]
        raise AttributeError(f"Attribute {name} not found.")

    def __query(self, message: str) -> str:
        _message = message.strip()
        assert _message, "Message cannot be empty."
        QtCore.qDebug(f"[MSO5000] Query: {_message}")
        for _ in range(5):
            try:
                _response = self.__instrument.query(_message).rstrip()
                if _response:
                    return _response
            except pyvisa.errors.VisaIOError:
                QtCore.qWarning("[MSO5000] VISA IO error, retrying query...")
                QtCore.QThread.msleep(100)
        QtCore.qCritical("[MSO5000] Failed to get response after retries.")
        raise AssertionError("Failed to get response.")

    def __write(self, message: str):
        _message = message.strip()
        assert _message, "Message cannot be empty."
        for _ in range(5):
            try:
                QtCore.qDebug(f"[MSO5000] Write: {_message}")
                self.__instrument.write(_message)
                return
            except pyvisa.errors.VisaIOError:
                QtCore.qWarning("[MSO5000] VISA IO error, retrying write...")
                QtCore.QThread.msleep(100)
        QtCore.qCritical("[MSO5000] Failed to write after retries.")

    def __get_names(self, channel: str, parameter: str):
        # Avoid unnecessary string operations
        if channel.startswith(':'):
            _parameter = f"{channel}:{parameter}"
        else:
            _parameter = f":{channel}:{parameter}"
        # Use f-string and .replace only once
        _attribute = _parameter.replace(":", "_").lower()
        return _attribute, _parameter

    def _get_parameter(self, channel: str, parameter: str, default=None):
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        cache = self.__cache
        if _attribute in cache:
            return cache[_attribute]
        _query_result = self.__query(f"{_parameter}?")
        if default is not None:
            try:
                _value = type(default)(_query_result)
            except Exception:
                _value = default
        else:
            _value = _query_result
        cache[_attribute] = _value
        return _value

    def _set_parameter(self, channel: str, parameter: str, value):
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        cache = self.__cache
        if cache.get(_attribute) == value:
            return
        self.__write(f"{_parameter} {value}")
        cache[_attribute] = value

    @QtCore.Slot()
    def onSettingsModified(self):
        QtCore.qInfo("[MSO5000] Settings modified, updating device settings.")

    class Source(StrEnum):
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
        QtCore.qInfo("[MSO5000] Searching for instrument...")
        _resource_manager = pyvisa.ResourceManager()
        found = False
        for _resource_name in _resource_manager.list_resources():
            try:
                QtCore.qInfo(f"[MSO5000] Found device: {_resource_name}")
                _instrument = _resource_manager.open_resource(_resource_name)
                idn = _instrument.query("*IDN?").strip()
                if "RIGOL" in idn and "MSO5" in idn:
                    QtCore.qInfo(f"[MSO5000] Found MSO5000 oscilloscope: {_resource_name}")
                    self.__instrument = _instrument
                    found = True
                    break
            except Exception as e:
                QtCore.qWarning(f"[MSO5000] Error opening resource {_resource_name}: {e}")
        if not found:
            QtCore.qCritical("[MSO5000] No oscilloscope found.")
            raise AssertionError("No oscilloscope found.")
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
            QtCore.qWarning(f"[MSO5000] Error parsing IDN: {e}")
        QtCore.qInfo(f"[MSO5000] Connected to {getattr(self, 'model_name', 'Unknown')} oscilloscope.")

    def autoscale(self):
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

    def set_acquire_averages(self, averages: int):
        if averages < 2 or averages > 65536 or (averages & (averages - 1)) != 0:
            QtCore.qWarning("[MSO5000] Averages must be a power of two between 2 and 65536.")
            raise AssertionError("Averages must be a power of two between 2 and 65536.")
        self._set_parameter("ACQuire", "AVERages", averages)

    def set_acquire_memory_depth(self, depth: MemoryDepth):
        assert depth in MSO5000.MemoryDepth, "Memory depth must be one of the MemoryDepth enum values."
        self._set_parameter("ACQuire", "MDEPth", depth.value)

    def set_acquire_type(self, type_: AcquireType):
        assert type_ in MSO5000.AcquireType, "Acquire type must be one of the AcquireType enum values."
        self._set_parameter("ACQuire", "TYPE", type_.value)

    def get_sample_rate(self) -> float:
        return self._get_parameter("ACQuire", "SRATe", 0.0)

    def get_digital_sample_rate(self) -> float:
        return self._get_parameter("ACQuire", "LA:SRATe", 0.0)

    def get_digital_memory_depth(self) -> float:
        return self._get_parameter("ACQuire", "LA:MDEPth", 0.0)

    def set_acquire_antialiasing(self, state: bool):
        self._set_parameter("ACQuire", "AALias", state)

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

    def set_channel_bandwidth_limit(self, channel: int, limit: BandwidthLimit):
        assert 1 <= channel <= 4, "Channel must be between 1 and 4."
        if getattr(self, "model_name", None) == "MSO5354":
            _valid = MSO5000.BandwidthLimit.__members__.values()
        elif getattr(self, "model_name", None) == "MSO5204":
            _valid = [
                MSO5000.BandwidthLimit.Off,
                MSO5000.BandwidthLimit._20M,
                MSO5000.BandwidthLimit._100M,
            ]
        else:
            _valid = [MSO5000.BandwidthLimit.Off, MSO5000.BandwidthLimit._20M]
        assert limit in _valid, "Bandwidth limit must be one of the BandwidthLimit enum values."
        self._set_parameter(f"CHANnel{channel}", "BWLimit", limit.value)

    def set_channel_coupling(self, channel: int, coupling: Coupling):
        assert 1 <= channel <= 4, "Channel must be between 1 and 4."
        assert coupling in MSO5000.Coupling, "Coupling must be one of the Coupling enum values."
        self._set_parameter(f"CHANnel{channel}", "COUPling", coupling.value)

    def set_channel_display(self, channel: int, display: bool):
        assert 1 <= channel <= 4, "Channel must be between 1 and 4."
        self._set_parameter(f"CHANnel{channel}", "DISPlay", display)

    def set_channel_invert(self, channel: int, invert: bool):
        assert 1 <= channel <= 4, "Channel must be between 1 and 4."
        self._set_parameter(f"CHANnel{channel}", "INVert", invert)

    def set_channel_offset(self, channel: int, offset: float):
        assert 1 <= channel <= 4, "Channel must be between 1 and 4."
        _minimum, _maximum = -10, 100
        assert _minimum <= offset <= _maximum, f"Offset must be between {_minimum} and {_maximum}."
        self._set_parameter(f"CHANnel{channel}", "OFFSet", offset)

    def set_channel_calibration_time(self, channel: int, time: float):
        assert 1 <= channel <= 4, "Channel must be between 1 and 4."
        assert -100e-9 <= time <= 100e-9, "Delay calibration time must be between -100e-9 and 100e-9 seconds."
        self._set_parameter(f"CHANnel{channel}", "TCALibrate", time)

    def set_channel_scale(self, channel: int, scale: float):
        assert 1 <= channel <= 4, "Channel must be between 1 and 4."
        _minimum, _maximum = 500e-6, 10
        assert _minimum <= scale <= _maximum, f"Scale must be between {_minimum} and {_maximum}."
        self._set_parameter(f"CHANnel{channel}", "SCALe", scale)

    def set_channel_probe(self, channel: int, probe: float):
        assert 1 <= channel <= 4, "Channel must be between 1 and 4."
        _valid = {
            0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100,
            200, 500, 1000, 2000, 5000, 10000, 20000, 50000,
        }
        assert probe in _valid, "Probe must be one of the valid values."
        self._set_parameter(f"CHANnel{channel}", "PROBe", probe)

    def set_channel_units(self, channel: int, units: Units):
        assert 1 <= channel <= 4, "Channel must be between 1 and 4."
        assert units in MSO5000.Units, "Units must be one of the Units enum values."
        self._set_parameter(f"CHANnel{channel}", "UNITs", units.value)

    def set_channel_vernier(self, channel: int, vernier: bool):
        assert 1 <= channel <= 4, "Channel must be between 1 and 4."
        self._set_parameter(f"CHANnel{channel}", "VERNier", vernier)

    def set_channel_position(self, channel: int, position: float):
        assert 1 <= channel <= 4, "Channel must be between 1 and 4."
        assert -100 <= position <= 100, "Position must be between -100 and 100."
        self._set_parameter(f"CHANnel{channel}", "POSition", position)

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
        QtCore.QThread.msleep(1000)
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

    def set_measure_source(self, source: Source):
        assert source in MSO5000.Source, "Source must be one of the Source enum values."
        self._set_parameter("MEASure", "SOURce", source.value)

    def clear_measurement(self, item: MeasureItem):
        assert item in MSO5000.MeasureItem, "Item must be one of the MeasureItem enum values."
        self._set_parameter("MEASure", "CLEar", item.value)

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

    def set_measure_threshold_default(self):
        self.__write(":MEASure:THReshold:DEFault")

    class MeasureMode(StrEnum):
        Normal = "NORMal"
        Precision = "PRECision"

    def set_measure_mode(self, mode: MeasureMode):
        self._set_parameter("MEASure", "MODE", mode.value)

    def set_measure_item(self, measurement: Measurement, source: Source):
        self.__write(f":MEASure:ITEM {measurement.value},{source.value}")

    def get_measure_item(self, measurement: Measurement, source: Source):
        return float(self.__query(f":MEASure:ITEM? {measurement.value},{source.value}"))

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

    def set_save_csv_length(self, length: SaveCsvLength):
        assert length in MSO5000.SaveCsvLength, "Length must be one of the SaveCsvLength enum values."
        self._set_parameter("SAVE", "CSV:LENGth", length.value)

    def set_save_csv_channel(self, channel: SaveCsvChannel, state: bool):
        assert channel in MSO5000.SaveCsvChannel, "Channel must be one of the SaveCsvChannel enum values."
        self._set_parameter("SAVE", "CSV:CHANnel", f"{channel.value},{int(state)}")

    def save_csv(
        self,
        filename: str,
        length: SaveCsvLength = SaveCsvLength.Display,
    ):
        self.set_save_csv_length(length)
        self._set_parameter("SAVE", "CSV", filename)

    def save_image_type(self, type_: ImageType):
        assert type_ in MSO5000.ImageType, "Type must be one of the ImageType enum values."
        self._set_parameter("SAVE", "IMAGe:TYPE", type_.value)

    def save_image_invert(self, invert: bool):
        self.__set_parameter("SAVE", "IMAGe:INVert", invert)

    def save_image_color(self, color: ImageColor):
        self._set_parameter("SAVE", "COLor", color.value)

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

    def save_setup(self, path: str):
        self._set_parameter("SAVE", "SETup", path)

    def save_waveform(self, path: str):
        self._set_parameter("SAVE", "WAVeform", path)

    def get_save_status(self) -> bool:
        return self._get_parameter("SAVE", "STATus")

    def load_setup(self, filename: str):
        self.__write(f":LOAD:SETup {filename}")

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

    
    def set_trigger_pulse_when(self, when: TriggerWhen):
        """
        Sets the trigger pulse condition for pulse width triggering on the device.

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

    
    def set_trigger_pulse_upper_width(self, width: float):
        """
        Sets the upper width for the trigger pulse.

        Args:
            width (float): The upper width of the trigger pulse in seconds. Must be less than or equal to 10.

        Raises:
            AssertionError: If the specified width is greater than 10 seconds.

        """
        assert width <= 10, "Trigger pulse upper width must be less than 10s."
        self._set_parameter("TRIGger", "PULSe:UWIDth", width)

    
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

    
    def set_trigger_slope_amplitude_upper(self, amplitude: float):
        """
        Sets the upper amplitude limit for the trigger slope on the oscilloscope.

        Args:
            amplitude (float): The upper amplitude threshold to set for the trigger slope.

        Raises:
            ValueError: If the provided amplitude is out of the valid range for the oscilloscope.
        """
        self._set_parameter("TRIGger", "SLOPe:ALEVel", amplitude)

    
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
            coupling (TriggerCoupling, optional): The trigger coupling mode (e.g., DC, AC). Defaults to TriggerCoupling.DC.
            sweep (TriggerSweep, optional): The trigger sweep mode (e.g., Auto, Normal). Defaults to TriggerSweep.Auto.
            holdoff (float, optional): The trigger holdoff time in seconds. Defaults to 8e-9.
            nreject (bool, optional): Whether to enable noise rejection. Defaults to False.
            source (TriggerSource, optional): The trigger source channel. Defaults to TriggerSource.Channel1.
            when (TriggerWhen, optional): The trigger condition (e.g., Greater, Less). Defaults to TriggerWhen.Greater.
            time_upper (float, optional): The upper time threshold for the slope trigger in seconds. Defaults to 1e-6.
            time_lower (float, optional): The lower time threshold for the slope trigger in seconds. Defaults to 1e-6.
            window (TriggerWindow, optional): The trigger window type. Defaults to TriggerWindow.TA.
            amplitude_upper (float, optional): The upper amplitude threshold for the slope trigger. Defaults to 0.
            amplitude_lower (float, optional): The lower amplitude threshold for the slope trigger. Defaults to 0.

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

    
    def get_waveform_xincrement(self) -> float:
        """
        Retrieves the horizontal (X-axis) increment value of the current waveform.

        Returns:
            float: The time interval between consecutive data points in the waveform.
        """
        return self._get_parameter("WAVeform", "XINCrement")

    
    def get_waveform_xorigin(self) -> float:
        """
        Retrieves the X origin value of the current waveform.

        Returns:
            float: The X origin of the waveform, typically representing the starting point on the X-axis (time axis) in waveform data.
        """
        return self._get_parameter("WAVeform", "XORigin")

    
    def get_waveform_xreference(self) -> float:
        """
        Retrieves the X reference value of the current waveform.

        Returns:
            float: The X reference value of the waveform, typically representing the horizontal offset or reference point on the X-axis.
        """
        return self._get_parameter("WAVeform", "XREFerence")

    
    def get_waveform_yincrement(self) -> float:
        """
        Retrieves the vertical increment (Y-axis increment) of the current waveform.

        Returns:
            float: The change in voltage per unit time for the waveform.
        """
        return self._get_parameter("WAVeform", "YINCrement")

    
    def get_waveform_yorigin(self) -> float:
        """
        Gets the Y origin value of the current waveform.

        Returns:
            float: The Y origin of the waveform as a floating-point number.
        """
        return self._get_parameter("WAVeform", "YORigin")

    
    def get_waveform_yreference(self) -> float:
        """
        Retrieves the Y reference value of the current waveform.

        Returns:
            float: The Y reference value used for scaling the waveform data.
        """
        return self._get_parameter("WAVeform", "YREFerence")

    
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

    
    def get_waveform_preamble(self) -> str:
        """
        Retrieves the waveform preamble from the device.

        Returns:
            str: The waveform preamble as a string, typically containing information about the waveform format, such as scaling, offset, and other acquisition parameters.
        """
        return self._get_parameter("WAVeform", "PREamble")
