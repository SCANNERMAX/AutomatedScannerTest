# -*- coding: utf-8 -*-
from PySide6 import QtCore
from ctypes.wintypes import BYTE
from enum import StrEnum
import logging
import pyvisa
import time

from tester.devices import Device

logger = logging.getLogger(__name__)


class Source(StrEnum):
    """
    Enumeration representing possible signal sources for the MSO5000 device.

    Members:
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
    """
    Enumeration representing possible memory depth settings for the MSO5000 oscilloscope.

    Members:
        Auto: Automatically selects the memory depth based on acquisition settings.
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
    Enumeration representing the acquisition types for the MSO5000 oscilloscope.

    Members:
        Normal: Standard acquisition mode.
        Averages: Acquisition mode with averaging enabled.
        Peak: Peak detection acquisition mode.
        HighResolution: High resolution acquisition mode.
    """
    Normal = "NORM"
    Averages = "AVER"
    Peak = "PEAK"
    HighResolution = "HRES"

class BandwidthLimit(StrEnum):
    """
    Enumeration representing possible bandwidth limit settings for the MSO5000 oscilloscope.

    Members:
        Off: Disables bandwidth limiting.
        Auto: Automatically selects bandwidth limit based on device configuration.
        _20M: Limits bandwidth to 20 MHz.
        _100M: Limits bandwidth to 100 MHz.
        _200M: Limits bandwidth to 200 MHz.
    """
    Off = "OFF"
    Auto = "AUTO"
    _20M = "20M"
    _100M = "100M"
    _200M = "200M"

class Coupling(StrEnum):
    """
    Enumeration representing the coupling modes for the MSO5000 oscilloscope channels.

    Members:
        AC: Alternating Current coupling mode.
        DC: Direct Current coupling mode.
        Ground: Ground coupling mode.
    """
    AC = "AC"
    DC = "DC"
    Ground = "GND"

class Units(StrEnum):
    """
    Enumeration representing the measurement units for the MSO5000 oscilloscope channels.

    Members:
        Voltage: Unit for voltage measurements ("VOLT").
        Watt: Unit for power measurements ("WATT").
        Ampere: Unit for current measurements ("AMP").
        Unknown: Unknown or unspecified unit ("UNKN").
    """
    Voltage = "VOLT"
    Watt = "WATT"
    Ampere = "AMP"
    Unknown = "UNKN"

class MeasureItem(StrEnum):
    """
    Enumeration representing the available measurement item slots for the MSO5000 oscilloscope.

    Members:
        Item1-Item10: Individual measurement item slots ("ITEM1" to "ITEM10").
        All: Represents all measurement items ("ALL").
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
    """
    Enumeration representing measurement types available on the MSO5000 oscilloscope.

    Members:
        VoltageMaximum: Maximum voltage value ("VMAX").
        VoltageMinimum: Minimum voltage value ("VMIN").
        VoltagePeakToPeak: Peak-to-peak voltage ("VPP").
        VoltageTOP: Top voltage value ("VTOP").
        VoltageBase: Base voltage value ("VBASe").
        VoltageAmplitude: Amplitude of the voltage ("VAMP").
        VoltageAverage: Average voltage value ("VAVG").
        VoltageRms: Root mean square voltage ("VRMS").
        Overshoot: Overshoot value ("OVERshoot").
        Preshoot: Preshoot value ("PREShoot").
        MARea: Measurement area ("MARea").
        MPARea: Measurement positive area ("MPARea").
        Period: Signal period ("PERiod").
        Frequency: Signal frequency ("FREQuency").
        RiseTime: Signal rise time ("RTIMe").
        FallTime: Signal fall time ("FTIMe").
        PositivePulseWidth: Width of positive pulse ("PWIDth").
        NegativePulseWidth: Width of negative pulse ("NWIDth").
        PositiveDuty: Positive duty cycle ("PDUTy").
        NegativeDuty: Negative duty cycle ("NDUTy").
        TVMAX: Maximum value in TV mode ("TVMAX").
        TVMIN: Minimum value in TV mode ("TVMIN").
        PositiveSlewrate: Positive slew rate ("PSLewrate").
        NegativeSlewrate: Negative slew rate ("NSLewrate").
        VUPPer: Upper voltage value ("VUPPer").
        VMID: Middle voltage value ("VMID").
        VLOWer: Lower voltage value ("VLOWer").
        VARiance: Variance of the measurement ("VARiance").
        PVRMs: Peak value RMS ("PVRMs").
        PPULses: Number of positive pulses ("PPULses").
        NPULses: Number of negative pulses ("NPULses").
        PEDGes: Number of positive edges ("PEDGes").
        NEDGes: Number of negative edges ("NEDGes").
        RRDelay: Rising-to-rising delay ("RRDelay").
        RFDelay: Rising-to-falling delay ("RFDelay").
        FRDelay: Falling-to-rising delay ("FRDelay").
        FFDelay: Falling-to-falling delay ("FFDelay").
        RRPHase: Rising-to-rising phase ("RRPHase").
        RFPHase: Rising-to-falling phase ("RFPHase").
        FRPHase: Falling-to-rising phase ("FRPHase").
        FFPHase: Falling-to-falling phase ("FFPHase").
    """
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

class SaveCsvLength(StrEnum):
    """
    Enumeration representing the possible CSV save length options for the MSO5000 oscilloscope.

    Members:
        Display: Save only the data currently displayed on the oscilloscope ("DISP").
        Maximum: Save the maximum available data points ("MAX").
    """
    Display = "DISP"
    Maximum = "MAX"

class SaveCsvChannel(StrEnum):
    """
    Enumeration representing the available channels for saving CSV data on the MSO5000 oscilloscope.

    Members:
        Channel1: Analog channel 1 ("CHAN1").
        Channel2: Analog channel 2 ("CHAN2").
        Channel3: Analog channel 3 ("CHAN3").
        Channel4: Analog channel 4 ("CHAN4").
        Pod1: Digital pod 1 ("POD1").
        Pod2: Digital pod 2 ("POD2").
    """
    Channel1 = "CHAN1"
    Channel2 = "CHAN2"
    Channel3 = "CHAN3"
    Channel4 = "CHAN4"
    Pod1 = "POD1"
    Pod2 = "POD2"

class ImageType(StrEnum):
    """
    Enumeration representing supported image file types for saving oscilloscope screenshots.

    Members:
        Bitmap: 24-bit bitmap image format ("BMP24").
        Jpeg: JPEG image format ("JPEG").
        Png: PNG image format ("PNG").
        Tiff: TIFF image format ("TIFF").
    """
    Bitmap = "BMP24"
    Jpeg = "JPEG"
    Png = "PNG"
    Tiff = "TIFF"

class ImageColor(StrEnum):
    """
    Enumeration representing supported color modes for saving oscilloscope screenshots.

    Members:
        Color: Save the image in color mode ("COL").
        Gray: Save the image in grayscale mode ("GRAY").
    """
    Color = "COL"
    Gray = "GRAY"

class SourceFunction(StrEnum):
    """
    Enumeration representing the available function types for the MSO5000 arbitrary waveform generator.

    Members:
        Sinusoid: Sine wave output ("SIN").
        Square: Square wave output ("SQU").
        Ramp: Ramp (triangle) wave output ("RAMP").
        Pulse: Pulse wave output ("PULS").
        Noise: Noise output ("NOIS").
        Dc: DC output ("DC").
        Sinc: Sinc function output ("SINC").
        ExponentialRise: Exponential rise waveform ("EXPR").
        ExponentialFall: Exponential fall waveform ("EXPF").
        Ecg: ECG (electrocardiogram) waveform ("ECG").
        Guass: Gaussian waveform ("GUAS").
        Lorentz: Lorentzian waveform ("LOR").
        Haversine: Haversine waveform ("HAV").
        Arbitrary: Arbitrary waveform ("ARB").
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
    Enumeration representing the available source types for the MSO5000 arbitrary waveform generator.

    Members:
        _None: No source type selected ("NONE").
        Modulated: Modulation source type ("MOD").
        Sweep: Sweep source type ("SWE").
        Burst: Burst source type ("BUR").
    """
    _None = "NONE"
    Modulated = "MOD"
    Sweep = "SWE"
    Burst = "BUR"

class SourceModulation(StrEnum):
    """
    Enumeration representing the modulation types available for the MSO5000 arbitrary waveform generator.

    Members:
        AmplitudeModulation: Amplitude modulation ("AM").
        FrequencyModulation: Frequency modulation ("FM").
        FrequencyShiftKey: Frequency shift keying ("FSK").
    """
    AmplitudeModulation = "AM"
    FrequencyModulation = "FM"
    FrequencyShiftKey = "FSK"

class SourceSweepType(StrEnum):
    """
    Enumeration representing the sweep types available for the MSO5000 arbitrary waveform generator.

    Members:
        Linear: Linear sweep type ("LIN").
        Log: Logarithmic sweep type ("LOG").
        Step: Step sweep type ("STEP").
    """
    Linear = "LIN"
    Log = "LOG"
    Step = "STEP"

class SourceBurstType(StrEnum):
    """
    Enumeration representing the burst types available for the MSO5000 arbitrary waveform generator.

    Members:
        Ncycle: Burst mode with a specified number of cycles ("NCYCL").
        Infinite: Continuous burst mode ("INF").
    """
    Ncycle = "NCYCL"
    Infinite = "INF"

class SourceOutputImpedance(StrEnum):
    """
    Enumeration representing the output impedance options for the MSO5000 arbitrary waveform generator.

    Members:
        Omeg: High impedance output ("OMEG").
        Fifty: 50 Ohm output impedance ("FIFT").
    """
    Omeg = "OMEG"
    Fifty = "FIFT"

class TimebaseMode(StrEnum):
    """
    Enumeration representing the horizontal timebase modes for the MSO5000 oscilloscope.

    Members:
        Main: Standard timebase mode for regular waveform acquisition ("MAIN").
        Xy: XY display mode for plotting one channel against another ("XY").
        Roll: Roll mode for slow signal acquisition, displaying data as it is acquired ("ROLL").
    """
    Main = "MAIN"
    Xy = "XY"
    Roll = "ROLL"

class HrefMode(StrEnum):
    """
    Enumeration representing the horizontal reference modes for the MSO5000 oscilloscope.

    Members:
        Center: Center reference mode ("CENT").
        Lb: Left boundary reference mode ("LB").
        Rb: Right boundary reference mode ("RB").
        Trigger: Trigger reference mode ("TRIG").
        User: User-defined reference mode ("USER").
    """
    Center = "CENT"
    Lb = "LB"
    Rb = "RB"
    Trigger = "TRIG"
    User = "USER"

class TriggerMode(StrEnum):
    """
    Enumeration representing the available trigger modes for the MSO5000 oscilloscope.

    Members:
        Edge: Edge trigger mode ("EDGE").
        Pulse: Pulse trigger mode ("PULS").
        Slope: Slope trigger mode ("SLOP").
        Video: Video trigger mode ("VID").
        Pattern: Pattern trigger mode ("PATT").
        Duration: Duration trigger mode ("DUR").
        Timeout: Timeout trigger mode ("TIM").
        Runt: Runt trigger mode ("RUNT").
        Window: Window trigger mode ("WIND").
        Delay: Delay trigger mode ("DEL").
        Setup: Setup and hold trigger mode ("SET").
        Nedge: Nth edge trigger mode ("NEDG").
        RS232: RS232 serial trigger mode ("RS232").
        IIC: I2C serial trigger mode ("IIC").
        SPI: SPI serial trigger mode ("SPI").
        CAN: CAN bus trigger mode ("CAN").
        Flexray: FlexRay bus trigger mode ("FLEX").
        LIN: LIN bus trigger mode ("LIN").
        IIS: IIS bus trigger mode ("IIS").
        M1553: MIL-STD-1553 bus trigger mode ("M1553").
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
    Enumeration representing the trigger coupling modes for the MSO5000 oscilloscope.

    Members:
        AC: AC coupling ("AC").
        DC: DC coupling ("DC").
        LfReject: Low frequency reject coupling ("LFR").
        HfReject: High frequency reject coupling ("HFR").
    """
    AC = "AC"
    DC = "DC"
    LfReject = "LFR"
    HfReject = "HFR"

class TriggerStatus(StrEnum):
    """
    Enumeration representing the possible trigger statuses for the MSO5000 oscilloscope.

    Members:
        TD: Triggered and data acquisition is complete ("TD").
        Wait: Waiting for a trigger event ("WAIT").
        Run: Actively running and acquiring data ("RUN").
        Auto: Automatically triggering when no trigger event occurs ("AUTO").
        Stop: Stopped, no data acquisition in progress ("STOP").
    """
    TD = "TD"
    Wait = "WAIT"
    Run = "RUN"
    Auto = "AUTO"
    Stop = "STOP"

class TriggerSweep(StrEnum):
    """
    Enumeration representing the available trigger sweep modes for the MSO5000 oscilloscope.

    Members:
        Auto: Automatic sweep mode ("AUTO").
        Normal: Normal sweep mode ("NORM").
        Single: Single sweep mode ("SING").
    """
    Auto = "AUTO"
    Normal = "NORM"
    Single = "SING"

class TriggerSource(StrEnum):
    """
    Enumeration of possible trigger sources for the MSO5000 oscilloscope.

    Members:
        D0-D15: Digital channels 0 through 15 ("D0" to "D15").
        Channel1-Channel4: Analog channels 1 through 4 ("CHAN1" to "CHAN4").
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
    Enumeration representing the possible trigger slope types for the MSO5000 oscilloscope.

    Members:
        Positive: Trigger on a positive slope ("POS").
        Negative: Trigger on a negative slope ("NEG").
        RFall: Trigger on a rapid falling edge ("RFAL").
    """
    Positive = "POS"
    Negative = "NEG"
    RFall = "RFAL"

class TriggerWhen(StrEnum):
    """
    Enumeration representing trigger conditions for the MSO5000 oscilloscope.

    Members:
        Greater: Trigger when the value is greater than a specified threshold ("GRE").
        Less: Trigger when the value is less than a specified threshold ("LESS").
        Gless: Trigger when the value is greater or less than a specified threshold ("GLES").
    """
    Greater = "GRE"
    Less = "LESS"
    Gless = "GLES"

class TriggerWindow(StrEnum):
    """
    Enumeration representing the available trigger windows for the MSO5000 oscilloscope.

    Members:
        TA: Trigger window A ("TA").
        TB: Trigger window B ("TB").
        TAB: Trigger window A and B combined ("TAB").
    """
    TA = "TA"
    TB = "TB"
    TAB = "TAB"

class WaveformMode(StrEnum):
    """
    Enumeration of available waveform acquisition modes for the MSO5000 device.

    This enumeration defines the supported modes for waveform data acquisition:

    Attributes:
        Normal (str): Standard acquisition mode, typically used for regular waveform capture.
        Maximum (str): Acquires waveform data at the maximum available rate or resolution.
        Raw (str): Captures raw, unprocessed waveform data directly from the device.
    """
    Normal = "NORM"
    Maximum = "MAX"
    Raw = "RAW"

class WaveformFormat(StrEnum):
    """
    Enumeration of supported waveform data formats for the MSO5000 oscilloscope.

    This enumeration defines the available formats for waveform data returned by the device.

    Attributes:
        Word (str): Represents waveform data in 16-bit word format ("WORD").
        Byte (str): Represents waveform data in 8-bit byte format ("BYTE").
        Ascii (str): Represents waveform data in ASCII format ("ASC").
    """

    Word = "WORD"
    Byte = "BYTE"
    Ascii = "ASC"

class MSO5000(Device):
    __cache = {}

    def __init__(self):
        """
        Initializes the MSO5000 device instance.

        Args:
            settings (QSettings): The application settings used for device configuration.

        Side Effects:
            Calls the base Device class initializer with the device name "MSO5000" and the provided settings.
            Initializes the internal instrument reference to None.
        """
        super().__init__("MSO5000")
        self.__instrument = None

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
        logger.debug(f"[MSO5000] Sending query: \"{_message}\"")
        for attempt in range(5):
            try:
                logger.debug(f"[MSO5000] Attempt {attempt+1}: Querying instrument with \"{_message}\"")
                _response = self.__instrument.query(_message)
                logger.debug(f"[MSO5000] Received response: \"{_response}\"")
                if _response:
                    logger.debug(f"[MSO5000] Query successful: \"{_message}\" -> \"{_response.rstrip()}\"")
                    return _response.rstrip()
                else:
                    logger.warning(f"[MSO5000] Empty response for query \"{_message}\" on attempt {attempt+1}")
            except pyvisa.errors.VisaIOError as e:
                logger.error(f"[MSO5000] VISA IO Error on query \"{_message}\" (attempt {attempt+1}): {e}")
                logging.debug("retrying...")
                time.sleep(0.1)
        msg = f'Failed to get response for query \"{_message}\" after 5 attempts'
        logger.critical(f"[MSO5000] {msg}")
        raise AssertionError(msg)

    def __write(self, message: str):
        """
        Sends a SCPI command to the MSO5000 instrument.

        This method attempts to send the specified command string to the instrument up to 5 times,
        handling transient VISA IO errors by retrying after a short delay. It logs each attempt and
        the outcome, including errors and successful transmissions.

        Args:
            message (str): The SCPI command string to send to the instrument.

        Raises:
            AssertionError: If the message is empty or if the command fails to send after 5 attempts.
            pyvisa.errors.VisaIOError: If a VISA IO error occurs during communication.

        Side Effects:
            - Logs the command being sent and any retries to the device logger.
            - Waits 0.1 seconds between retries if a VISA IO error occurs.
            - Raises a critical log if the command cannot be sent after 5 attempts.
        """
        _message = message.strip()
        assert _message, "Message cannot be empty."
        logger.debug(f"[MSO5000] Preparing to send command: \"{_message}\"")
        for attempt in range(5):
            try:
                if attempt == 0:
                    logger.debug(f"[MSO5000] Sending command (attempt {attempt+1}): \"{_message}\"")
                else:
                    logger.warning(f"[MSO5000] Retrying command (attempt {attempt+1}): \"{_message}\"")
                self.__instrument.write(_message)
                logger.debug(f"[MSO5000] Command sent successfully: \"{_message}\"")
                return
            except pyvisa.errors.VisaIOError as e:
                logger.error(f"[MSO5000] VISA IO Error on write \"{_message}\" (attempt {attempt+1}): {e}")
                if attempt < 4:
                    logger.debug(f"[MSO5000] Waiting 0.1s before retrying command: \"{_message}\"")
                    time.sleep(0.1)
        msg = f'Failed to send command \"{_message}\" after 5 attempts'
        logger.critical(f"[MSO5000] {msg}")
        raise AssertionError(msg)

    def __get_names(self, channel: str, parameter: str):
        """
        Generates the SCPI parameter string and corresponding cache attribute name for a given channel and parameter.

        Args:
            channel (str): The channel identifier (e.g., "CHANnel1", "ACQuire").
            parameter (str): The parameter name to query or set (e.g., "SCALe", "TYPE").

        Returns:
            tuple: A tuple containing:
                - _attribute (str): The cache attribute name, formatted as "_<channel>_<parameter>" in lowercase with colons replaced by underscores.
                - _parameter (str): The SCPI parameter string, formatted as ":<channel>:<parameter>" or "<channel>:<parameter>" if channel starts with \":\".

        Side Effects:
            Logs detailed debug information about the construction of the parameter and attribute names for traceability.

        Example:
            >>> self.__get_names("CHANnel1", "SCALe")
            ("_channel1_scale", ":CHANnel1:SCALe")
        """
        logger.debug(f"[MSO5000] __get_names called with channel=\"{channel}\", parameter=\"{parameter}\"")
        # Fast path: avoid repeated string operations
        if not channel.startswith(":"):
            _parameter = f":{channel}:{parameter}"
            logger.debug(f"[MSO5000] Channel does not start with \":\", constructed _parameter=\"{_parameter}\"")
        else:
            _parameter = f"{channel}:{parameter}"
            logger.debug(f"[MSO5000] Channel starts with \":\", constructed _parameter=\"{_parameter}\"")
        # Use str.translate for fast colon-to-underscore replacement and .lower() in one step
        _attribute = "_" + _parameter.replace(":", "_").lower()
        logger.debug(f"[MSO5000] Constructed _attribute=\"{_attribute}\" from _parameter=\"{_parameter}\"")
        return _attribute, _parameter

    def __get_parameter(self, channel: str, parameter: str, default=None):
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
        logger.debug(f"[MSO5000] __get_parameter called with channel=\"{channel}\", parameter=\"{parameter}\", default=\"{default}\"")
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        logger.debug(f"[MSO5000] Computed cache attribute=\"{_attribute}\", SCPI parameter=\"{_parameter}\"")
        _cache = self.__cache
        _value = _cache.get(_attribute)
        if _value is not None:
            logger.debug(f"[MSO5000] Cache hit for attribute=\"{_attribute}\", returning value=\"{_value}\"")
            return _value
        logger.debug(f"[MSO5000] Cache miss for attribute=\"{_attribute}\", querying instrument with \"{_parameter}?\"")
        try:
            _query_result = self.__query(f"{_parameter}?")
            logger.debug(f"[MSO5000] Received query result=\"{_query_result}\" for parameter=\"{_parameter}\"")
        except Exception as e:
            logger.error(f"[MSO5000] Exception during query for parameter=\"{_parameter}\": {e}")
            raise
        if default is not None:
            try:
                if isinstance(default, bool):
                    _value = _query_result.strip() in ("1", "ON", "TRUE")
                    logger.debug(f"[MSO5000] Interpreted boolean value=\"{_value}\" from query result=\"{_query_result}\"")
                else:
                    _value = type(default)(_query_result)
                    logger.debug(f"[MSO5000] Casted query result=\"{_query_result}\" to type=\"{type(default).__name__}\", value=\"{_value}\"")
            except Exception as e:
                logger.warning(f"[MSO5000] Failed to cast query result=\"{_query_result}\" to type=\"{type(default).__name__}\": {e}. Using default=\"{default}\"")
                _value = default
        else:
            _value = _query_result
            logger.debug(f"[MSO5000] No default provided, using raw query result=\"{_value}\"")
        _cache[_attribute] = _value
        logger.debug(f"[MSO5000] Cached value for attribute=\"{_attribute}\": \"{_value}\"")
        return _value

    def __set_parameter(self, channel: str, parameter: str, value):
        """
        Sets a device parameter for the specified channel and caches the value.

        Args:
            channel (str): The channel identifier (e.g., "CHANnel1", "ACQuire").
            parameter (str): The parameter name to set (e.g., "SCALe", "TYPE").
            value (Any): The value to set for the parameter.

        Returns:
            None

        Raises:
            AssertionError: If \"channel\" or \"parameter\" is empty.

        Side Effects:
            Sends a command to the instrument to set the parameter.
            Updates the internal cache with the new value.
            Skips sending the command if the cached value matches the new value.
        """
        logger.debug(f"[MSO5000] __set_parameter called with channel=\"{channel}\", parameter=\"{parameter}\", value=\"{value}\"")
        assert channel, "Channel cannot be empty."
        assert parameter, "Parameter cannot be empty."
        _attribute, _parameter = self.__get_names(channel, parameter)
        logger.debug(f"[MSO5000] Computed cache attribute=\"{_attribute}\", SCPI parameter=\"{_parameter}\"")
        _cache = self.__cache
        _cached_value = _cache.get(_attribute)
        logger.debug(f"[MSO5000] Cached value for attribute=\"{_attribute}\": \"{_cached_value}\"")
        # Fast path: avoid unnecessary str conversion if types match and are simple
        if _cached_value is not None:
            if type(_cached_value) == type(value) and _cached_value == value:
                logger.debug(f"[MSO5000] Skipping set for \"{_parameter}\" as cached value matches new value: \"{value}\"")
                return
            # For float comparison, use a tolerance to avoid precision issues
            if isinstance(_cached_value, float) and isinstance(value, float):
                if abs(_cached_value - value) < 1e-9:
                    logger.debug(f"[MSO5000] Skipping set for \"{_parameter}\" as cached float value matches new value within tolerance: \"{value}\"")
                    return
            # For bool comparison, allow int equivalence
            if isinstance(_cached_value, bool) and isinstance(value, (bool, int)):
                if bool(_cached_value) == bool(value):
                    logger.debug(f"[MSO5000] Skipping set for \"{_parameter}\" as cached bool value matches new value: \"{value}\"")
                    return
            # Fallback to string comparison for other types
            if str(_cached_value) == str(value):
                logger.debug(f"[MSO5000] Skipping set for \"{_parameter}\" as cached string value matches new value: \"{value}\"")
                return
        logger.debug(f"[MSO5000] Sending command to instrument: \"{_parameter} {value}\"")
        self.__write(f"{_parameter} {value}")
        logger.debug(f"[MSO5000] Updating cache for attribute=\"{_attribute}\" with value=\"{value}\"")
        _cache[_attribute] = value

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
                logging.debug(f"Found device: {_resource_name}")
                _instrument = _resource_manager.open_resource(_resource_name)
                idn = _instrument.query("*IDN?").strip()
                # Example IDN: "RIGOL TECHNOLOGIES,MSO5074,DS5A123456789,00.01.01"
                if "RIGOL" in idn and "MSO5" in idn:
                    logging.debug(f"Found MSO5000 oscilloscope: {_resource_name}")
                    self.__instrument = _instrument
                    found = True
                    break
            except Exception as e:
                logging.debug(f"Error opening resource {_resource_name}: {e}")
        assert found, "No oscilloscope found."
        # Copy all public members of self.__instrument to self
        try:
            for attr in (
                "manufacturer_name",
                "model_name",
                "serial_number",
                "model_code",
                "manufacturer_id",
            ):
                try:
                    setattr(self, attr, getattr(self.__instrument, attr))
                    self._set_setting(attr, getattr(self.__instrument, attr))
                except Exception as e:
                    logging.debug(f"Error copying attribute {attr}: {e}")
        except Exception as e:
            logging.debug(f"Error copying instrument members: {e}")
        logging.info(
            f"Connected to {getattr(self, 'model_name', 'Unknown')} oscilloscope."
        )

    # The device command system

    def autoscale(self):
        """
        Executes the autoscale command on the MSO5000 oscilloscope.

        This method sends the "AUToscale" SCPI command to the instrument, which automatically adjusts
        the vertical and horizontal settings to optimally display the input signal.

        Side Effects:
            - Logs the execution of the autoscale command.
            - Sends the "AUToscale" command to the oscilloscope.

        Example:
            >>> device.autoscale()
        """
        logging.debug("[MSO5000] Executing autoscale command.")
        self.__write("AUToscale")

    def clear(self):
        """
        Clears the oscilloscope's display and resets measurement results.

        This method sends the "CLEar" SCPI command to the MSO5000 instrument, which clears the current display and resets any measurement results or status indicators.

        Side Effects:
            - Logs the execution of the clear command.
            - Sends the "CLEar" command to the oscilloscope.

        Example:
            >>> device.clear()
        """
        logging.debug("[MSO5000] Executing clear command.")
        self.__write("CLEar")

    def run(self):
        """
        Starts continuous data acquisition on the MSO5000 oscilloscope.

        This method sends the ":RUN" SCPI command to the instrument, initiating continuous waveform acquisition.

        Side Effects:
            - Logs the execution of the run command.
            - Sends the ":RUN" command to the oscilloscope.

        Example:
            >>> device.run()
        """
        logging.debug("[MSO5000] Executing run command.")
        self.__write(":RUN")

    def stop(self):
        """
        Stops data acquisition on the MSO5000 oscilloscope.

        This method sends the ":STOP" SCPI command to the instrument, halting waveform acquisition.

        Side Effects:
            - Logs the execution of the stop command.
            - Sends the ":STOP" command to the oscilloscope.

        Example:
            >>> device.stop()
        """
        logging.debug("[MSO5000] Executing stop command.")
        self.__write(":STOP")

    def single(self):
        """
        Initiates a single acquisition cycle on the MSO5000 oscilloscope.

        This method sends the ":SINGle" SCPI command to the instrument, causing it to acquire a single waveform and then stop.

        Side Effects:
            - Logs the execution of the single command.
            - Sends the ":SINGle" command to the oscilloscope.

        Example:
            >>> device.single()
        """
        logging.debug("[MSO5000] Executing single command.")
        self.__write(":SINGle")

    def force_trigger(self):
        """
        Forces a trigger event on the MSO5000 oscilloscope.

        This method sends the ":TFORce" SCPI command to the instrument, manually triggering data acquisition regardless of the current trigger conditions.

        Side Effects:
            - Logs the execution of the force trigger command.
            - Sends the ":TFORce" command to the oscilloscope.

        Example:
            >>> device.force_trigger()
        """
        logging.debug("[MSO5000] Executing force trigger command.")
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
            AssertionError: If averages is not a power of two between 2 and 65536.

        Side Effects:
            Updates the acquisition averaging setting on the oscilloscope.
        """
        logging.debug(f"[MSO5000] Setting acquire averages: {averages}")
        if not (2 <= averages <= 65536 and averages & (averages - 1) == 0):
            logger.error(f"[MSO5000] Invalid averages value: {averages}")
            raise AssertionError("Averages must be a power of two between 2 and 65536.")
        self.__set_parameter("ACQuire", "AVERages", averages)

    def set_acquire_memory_depth(self, depth: MemoryDepth):
        """
        Sets the memory depth for waveform acquisition on the MSO5000 oscilloscope.

        Args:
            depth (MemoryDepth): The desired memory depth, must be a member of the MemoryDepth enum.

        Raises:
            AssertionError: If depth is not a valid MemoryDepth enum value.

        Side Effects:
            Updates the acquisition memory depth setting on the oscilloscope.
        """
        logging.debug(f"[MSO5000] Setting acquire memory depth: {depth}")
        if depth not in MemoryDepth:
            logger.error(f"[MSO5000] Invalid memory depth: {depth}")
            raise AssertionError("Memory depth must be one of the MemoryDepth enum values.")
        self.__set_parameter("ACQuire", "MDEPth", depth.value)

    def set_acquire_type(self, type_: AcquireType):
        """
        Sets the acquisition type for the MSO5000 oscilloscope.

        Args:
            type_ (AcquireType): The acquisition type to set, must be a member of the AcquireType enum.

        Raises:
            AssertionError: If type_ is not a valid AcquireType enum value.

        Side Effects:
            Updates the acquisition type setting on the oscilloscope.
        """
        logging.debug(f"[MSO5000] Setting acquire type: {type_}")
        if type_ not in AcquireType:
            logger.error(f"[MSO5000] Invalid acquire type: {type_}")
            raise AssertionError("Acquire type must be one of the AcquireType enum values.")
        self.__set_parameter("ACQuire", "TYPE", type_.value)

    def get_sample_rate(self) -> float:
        """
        Retrieves the current analog sample rate from the MSO5000 oscilloscope.

        Returns:
            float: The analog sample rate in samples per second.
        """
        logging.debug("[MSO5000] Getting sample rate")
        return self.__get_parameter("ACQuire", "SRATe", 0.0)

    def get_digital_sample_rate(self) -> float:
        """
        Retrieves the current digital sample rate from the MSO5000 oscilloscope.

        Returns:
            float: The digital sample rate in samples per second.
        """
        logging.debug("[MSO5000] Getting digital sample rate")
        return self.__get_parameter("ACQuire", "LA:SRATe", 0.0)

    def get_digital_memory_depth(self) -> float:
        """
        Retrieves the current digital memory depth from the MSO5000 oscilloscope.

        Returns:
            float: The digital memory depth in points.
        """
        logging.debug("[MSO5000] Getting digital memory depth")
        return self.__get_parameter("ACQuire", "LA:MDEPth", 0.0)

    def set_acquire_antialiasing(self, state: bool):
        """
        Enables or disables antialiasing for waveform acquisition on the MSO5000 oscilloscope.

        Args:
            state (bool): True to enable antialiasing, False to disable.

        Side Effects:
            Updates the antialiasing setting on the oscilloscope.
        """
        logging.debug(f"[MSO5000] Setting acquire antialiasing: {state}")
        self.__set_parameter("ACQuire", "AALias", state)

    def acquire_settings(
        self,
        averages: int = 2,
        memory_depth: MemoryDepth = MemoryDepth.Auto,
        type_: AcquireType = AcquireType.Normal,
        antialiasing: bool = False,
    ):
        """
        Applies a set of acquisition settings to the MSO5000 oscilloscope.

        Args:
            averages (int, optional): Number of averages (used if type_ is AcquireType.Averages). Default is 2.
            memory_depth (MemoryDepth, optional): Memory depth setting. Default is MemoryDepth.Auto.
            type_ (AcquireType, optional): Acquisition type. Default is AcquireType.Normal.
            antialiasing (bool, optional): Enable or disable antialiasing. Default is False.

        Side Effects:
            Updates the oscilloscope acquisition settings.
        """
        logging.debug(f"[MSO5000] Applying acquire settings: averages={averages}, memory_depth={memory_depth}, type_={type_}, antialiasing={antialiasing}")
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
        """
        Sets the bandwidth limit for a specified analog channel on the MSO5000 oscilloscope.

        The valid bandwidth limits depend on the oscilloscope model:
            - MSO5354: All BandwidthLimit enum values are valid.
            - MSO5204: Only Off, 20M, and 100M are valid.
            - Other models: Only Off and 20M are valid.

        Args:
            channel (int): The analog channel number (1-4).
            limit (BandwidthLimit): The desired bandwidth limit, must be a member of BandwidthLimit.

        Raises:
            AssertionError: If channel is not in [1, 4] or limit is not valid for the model.

        Side Effects:
            Updates the bandwidth limit setting for the specified channel.
        """
        logger.debug(f"[MSO5000] set_channel_bandwidth_limit called with channel={channel}, limit={limit}")
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        if getattr(self, "model_name", None) == "MSO5354":
            _valid = list(BandwidthLimit)
            logger.debug(f"[MSO5000] Model MSO5354 detected, valid limits: {_valid}")
        elif getattr(self, "model_name", None) == "MSO5204":
            _valid = [
                BandwidthLimit.Off,
                BandwidthLimit._20M,
                BandwidthLimit._100M,
            ]
            logger.debug(f"[MSO5000] Model MSO5204 detected, valid limits: {_valid}")
        else:
            _valid = [BandwidthLimit.Off, BandwidthLimit._20M]
            logger.debug(f"[MSO5000] Default model detected, valid limits: {_valid}")
        assert (
            limit in _valid
        ), "Bandwidth limit must be one of the BandwidthLimit enum values."
        logger.debug(f"[MSO5000] Setting bandwidth limit for channel {channel} to {limit.value}")
        self.__set_parameter(f"CHANnel{channel}", "BWLimit", limit.value)

        def set_channel_coupling(self, channel: int, coupling: Coupling):
            """
            Sets the coupling mode for a specified analog channel.

            Args:
                channel (int): The analog channel number (1-4).
                coupling (Coupling): The desired coupling mode, must be a member of Coupling.

            Raises:
                AssertionError: If channel is not in [1, 4] or coupling is not valid.

            Side Effects:
                Updates the coupling setting for the specified channel.
            """
            logger.debug(f"[MSO5000] set_channel_coupling called with channel={channel}, coupling={coupling}")
            assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
            assert (
                coupling in Coupling
            ), "Coupling must be one of the Coupling enum values."
            logger.debug(f"[MSO5000] Setting coupling for channel {channel} to {coupling.value}")
            self.__set_parameter(f"CHANnel{channel}", "COUPling", coupling.value)

        def set_channel_display(self, channel: int, display: bool):
            """
            Sets the display state for a specified analog channel.

            Args:
                channel (int): The analog channel number (1-4).
                display (bool): True to display the channel, False to hide.

            Raises:
                AssertionError: If channel is not in [1, 4].

            Side Effects:
                Updates the display state for the specified channel.
            """
            logger.debug(f"[MSO5000] set_channel_display called with channel={channel}, display={display}")
            assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
            logger.debug(f"[MSO5000] Setting display for channel {channel} to {display}")
            self.__set_parameter(f"CHANnel{channel}", "DISPlay", display)

        def set_channel_invert(self, channel: int, invert: bool):
            """
            Sets the invert state for a specified analog channel.

            Args:
                channel (int): The analog channel number (1-4).
                invert (bool): True to invert the channel signal, False otherwise.

            Raises:
                AssertionError: If channel is not in [1, 4].

            Side Effects:
                Updates the invert state for the specified channel.
            """
            logger.debug(f"[MSO5000] set_channel_invert called with channel={channel}, invert={invert}")
            assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
            logger.debug(f"[MSO5000] Setting invert for channel {channel} to {invert}")
            self.__set_parameter(f"CHANnel{channel}", "INVert", invert)

        def set_channel_offset(self, channel: int, offset: float):
            """
            Sets the vertical offset for a specified analog channel.

            Args:
                channel (int): The analog channel number (1-4).
                offset (float): The offset value in volts, must be between -10 and 100.

            Raises:
                AssertionError: If channel is not in [1, 4] or offset is out of range.

            Side Effects:
                Updates the offset setting for the specified channel.
            """
            logger.debug(f"[MSO5000] set_channel_offset called with channel={channel}, offset={offset}")
            assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
            _minimum = -10
            _maximum = 100
            assert (
                offset >= _minimum and offset <= _maximum
            ), f"Offset must be between {_minimum} and {_maximum}."
            logger.debug(f"[MSO5000] Setting offset for channel {channel} to {offset}")
            self.__set_parameter(f"CHANnel{channel}", "OFFSet", offset)

        def set_channel_calibration_time(self, channel: int, time: float):
            """
            Sets the delay calibration time for a specified analog channel.

            Args:
                channel (int): The analog channel number (1-4).
                time (float): The calibration time in seconds, must be between -100e-9 and 100e-9.

            Raises:
                AssertionError: If channel is not in [1, 4] or time is out of range.

            Side Effects:
                Updates the calibration time for the specified channel.
            """
            logger.debug(f"[MSO5000] set_channel_calibration_time called with channel={channel}, time={time}")
            assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
            assert (
                time >= -100e-9 and time <= 100e-9
            ), "Delay calibration time must be between -100e-9 and 100e-9 seconds."
            logger.debug(f"[MSO5000] Setting calibration time for channel {channel} to {time}")
            self.__set_parameter(f"CHANnel{channel}", "TCALibrate", time)

        def set_channel_scale(self, channel: int, scale: float):
            """
            Sets the vertical scale for a specified analog channel.

            Args:
                channel (int): The analog channel number (1-4).
                scale (float): The scale value in volts/div, must be between 500e-6 and 10.

            Raises:
                AssertionError: If channel is not in [1, 4] or scale is out of range.

            Side Effects:
                Updates the scale setting for the specified channel.
            """
            logger.debug(f"[MSO5000] set_channel_scale called with channel={channel}, scale={scale}")
            assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
            _minimum = 500e-6
            _maximum = 10
            assert (
                scale >= _minimum and scale <= _maximum
            ), f"Scale must be between {_minimum} and {_maximum}."
            logger.debug(f"[MSO5000] Setting scale for channel {channel} to {scale}")
            self.__set_parameter(f"CHANnel{channel}", "SCALe", scale)

        def set_channel_probe(self, channel: int, probe: float):
            """
            Sets the probe attenuation factor for a specified analog channel.

            Args:
                channel (int): The analog channel number (1-4).
                probe (float): The probe attenuation factor, must be one of the valid values.

            Raises:
                AssertionError: If channel is not in [1, 4] or probe is not valid.

            Side Effects:
                Updates the probe setting for the specified channel.
            """
            logger.debug(f"[MSO5000] set_channel_probe called with channel={channel}, probe={probe}")
            assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
            _valid_probes = [
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
            ]
            assert probe in _valid_probes, "Probe must be one of the valid values."
            logger.debug(f"[MSO5000] Setting probe for channel {channel} to {probe}")
            self.__set_parameter(f"CHANnel{channel}", "PROBe", probe)

        def set_channel_units(self, channel: int, units: Units):
            """
            Sets the measurement units for a specified analog channel.

            Args:
                channel (int): The analog channel number (1-4).
                units (Units): The desired measurement units, must be a member of Units.

            Raises:
                AssertionError: If channel is not in [1, 4] or units is not valid.

            Side Effects:
                Updates the units setting for the specified channel.
            """
            logger.debug(f"[MSO5000] set_channel_units called with channel={channel}, units={units}")
            assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
            assert units in Units, "Units must be one of the Units enum values."
            logger.debug(f"[MSO5000] Setting units for channel {channel} to {units.value}")
            self.__set_parameter(f"CHANnel{channel}", "UNITs", units.value)

        def set_channel_vernier(self, channel: int, vernier: bool):
            """
            Sets the vernier mode for a specified analog channel.

            Args:
                channel (int): The analog channel number (1-4).
                vernier (bool): True to enable vernier mode, False otherwise.

            Raises:
                AssertionError: If channel is not in [1, 4].

            Side Effects:
                Updates the vernier setting for the specified channel.
            """
            logger.debug(f"[MSO5000] set_channel_vernier called with channel={channel}, vernier={vernier}")
            assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
            logger.debug(f"[MSO5000] Setting vernier for channel {channel} to {vernier}")
            self.__set_parameter(f"CHANnel{channel}", "VERNier", vernier)

        def set_channel_position(self, channel: int, position: float):
            """
            Sets the vertical position for a specified analog channel.

            Args:
                channel (int): The analog channel number (1-4).
                position (float): The position value, must be between -100 and 100.

            Raises:
                AssertionError: If channel is not in [1, 4] or position is out of range.

            Side Effects:
                Updates the position setting for the specified channel.
            """
            logger.debug(f"[MSO5000] set_channel_position called with channel={channel}, position={position}")
            assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
            assert (
                position >= -100 and position <= 100
            ), "Position must be between -100 and 100."
            logger.debug(f"[MSO5000] Setting position for channel {channel} to {position}")
            self.__set_parameter(f"CHANnel{channel}", "POSition", position)

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
            Applies a set of configuration settings to a specified analog channel.

            Args:
                channel (int): The analog channel number (1-4).
                bandwidth_limit (BandwidthLimit, optional): Bandwidth limit setting.
                coupling (Coupling, optional): Coupling mode.
                display (bool, optional): Display state.
                invert (bool, optional): Invert state.
                offset (float, optional): Vertical offset.
                delay_calibration_time (float, optional): Delay calibration time.
                scale (float, optional): Vertical scale.
                probe (float, optional): Probe attenuation factor.
                units (Units, optional): Measurement units.
                vernier (bool, optional): Vernier mode.
                position (float, optional): Vertical position.

            Raises:
                AssertionError: If any parameter is out of valid range.

            Side Effects:
                Updates all specified settings for the channel.
            """
            logger.debug(f"[MSO5000] channel_settings called with channel={channel}, bandwidth_limit={bandwidth_limit}, coupling={coupling}, display={display}, invert={invert}, offset={offset}, delay_calibration_time={delay_calibration_time}, scale={scale}, probe={probe}, units={units}, vernier={vernier}, position={position}")
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
            logger.debug(f"[MSO5000] Setting position for channel {channel} to {position}")
            self.set_channel_position(channel, position)

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
        """
        Clears the oscilloscope's registers using the SCPI *CLS command.

        This method sends the "*CLS" command to the instrument, which clears the status registers and event registers.

        Side Effects:
            - Sends the "*CLS" command to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Clearing registers with *CLS command.")
        self.__write("*CLS")

    def get_standard_event_register_enable(self) -> BYTE:
        """
        Queries the standard event register enable mask from the oscilloscope.

        Returns:
            BYTE: The enable mask for the standard event register.

        Side Effects:
            - Sends the "*ESE?" query to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Querying standard event register enable (*ESE?).")
        _response = self.__query("*ESE?")
        logger.debug(f"[MSO5000] Received standard event register enable: {_response}")
        return BYTE(int(_response))

    def set_standard_event_register_enable(self, bits: BYTE):
        """
        Sets the standard event register enable mask on the oscilloscope.

        Args:
            bits (BYTE): The enable mask to set.

        Side Effects:
            - Sends the "*ESE <bits>" command to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Setting standard event register enable to {bits}.")
        self.__write(f"*ESE {bits}")

    def get_standard_event_register_event(self) -> BYTE:
        """
        Queries the standard event register event value from the oscilloscope.

        Returns:
            BYTE: The event value of the standard event register.

        Side Effects:
            - Sends the "*ESR?" query to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Querying standard event register event (*ESR?).")
        _response = self.__query("*ESR?")
        logger.debug(f"[MSO5000] Received standard event register event: {_response}")
        return BYTE(int(_response))

    def get_identity(self) -> str:
        """
        Queries the oscilloscope's identity string.

        Returns:
            str: The identity string returned by the "*IDN?" command.

        Side Effects:
            - Sends the "*IDN?" query to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Querying device identity (*IDN?).")
        return self.__query("*IDN?")

    def get_operation_complete(self) -> bool:
        """
        Queries the operation complete status from the oscilloscope.

        Returns:
            bool: True if the last operation is complete, False otherwise.

        Side Effects:
            - Sends the "*OPC?" query to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Querying operation complete status (*OPC?).")
        _response = self.__query("*OPC?")
        logger.debug(f"[MSO5000] Received operation complete status: {_response}")
        return bool(int(_response))

    def set_operation_complete(self, state: bool):
        """
        Sets the operation complete flag on the oscilloscope.

        Args:
            state (bool): The state to set (True or False).

        Side Effects:
            - Sends the "*OPC <state>" command to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Setting operation complete to {state}.")
        self.__write(f"*OPC {int(state)}")

    def save(self, register: int):
        """
        Saves the current oscilloscope setup to a specified register.

        Args:
            register (int): The register number (0-49) to save to.

        Raises:
            AssertionError: If register is not between 0 and 49.

        Side Effects:
            - Sends the "*SAVe <register>" command to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Saving to register {register}.")
        assert register >= 0 and register <= 49, "Register must be between 0 and 49."
        self.__write(f"*SAVe {register}")

    def recall(self, register: int):
        """
        Recalls a previously saved oscilloscope setup from a specified register.

        Args:
            register (int): The register number (0-49) to recall from.

        Raises:
            AssertionError: If register is not between 0 and 49.

        Side Effects:
            - Sends the "*RCL <register>" command to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Recalling from register {register}.")
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
        logger.debug(f"[MSO5000] Resetting device with *RST command and clearing cache.")
        self.__write("*RST")
        self.__cache.clear()

    def get_status_byte_register_enable(self) -> BYTE:
        """
        Queries the status byte register enable mask from the oscilloscope.

        Returns:
            BYTE: The enable mask for the status byte register.

        Side Effects:
            - Sends the "*SRE?" query to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Querying status byte register enable (*SRE?).")
        _response = self.__query("*SRE?")
        logger.debug(f"[MSO5000] Received status byte register enable: {_response}")
        return BYTE(int(_response))

    def set_status_byte_register_enable(self, bits: BYTE):
        """
        Sets the status byte register enable mask on the oscilloscope.

        Args:
            bits (BYTE): The enable mask to set.

        Side Effects:
            - Sends the "*SRE <bits>" command to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Setting status byte register enable to {bits}.")
        self.__write(f"*SRE {bits}")

    def get_status_byte_register_event(self) -> BYTE:
        """
        Queries the status byte register event value from the oscilloscope.

        Returns:
            BYTE: The event value of the status byte register.

        Side Effects:
            - Sends the "*STB?" query to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Querying status byte register event (*STB?).")
        _response = self.__query("*STB?")
        logger.debug(f"[MSO5000] Received status byte register event: {_response}")
        return BYTE(int(_response))

    def self_test(self) -> str:
        """
        Runs the oscilloscope's self-test routine.

        Returns:
            str: The result of the self-test as returned by "*TST?".

        Side Effects:
            - Sends the "*TST?" query to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Running self test (*TST?).")
        _response = self.__query("*TST?")
        logger.debug(f"[MSO5000] Self test result: {_response}")
        return _response

    def wait(self):
        """
        Waits for the oscilloscope to complete all pending operations.

        This method sends the "*WAI" command to the instrument, causing it to wait until all operations are finished.

        Side Effects:
            - Sends the "*WAI" command to the oscilloscope.
            - Logs the operation.
        """
        logger.debug(f"[MSO5000] Waiting for device (*WAI).")
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

    def set_channel_coupling(self, channel: int, coupling: Coupling):
        """
        Sets the coupling mode for a specified analog channel.

        Args:
            channel (int): The analog channel number (1-4).
            coupling (Coupling): The desired coupling mode, must be a member of Coupling.

        Raises:
            AssertionError: If channel is not in [1, 4] or coupling is not valid.

        Side Effects:
            Updates the coupling setting for the specified channel.
        """
        logger.debug(f"[MSO5000] set_channel_coupling called with channel={channel}, coupling={coupling}")
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        assert (
            coupling in Coupling
        ), "Coupling must be one of the Coupling enum values."
        logger.debug(f"[MSO5000] Setting coupling for channel {channel} to {coupling.value}")
        self.__set_parameter(f"CHANnel{channel}", "COUPling", coupling.value)

    def set_channel_display(self, channel: int, display: bool):
        """
        Sets the display state for a specified analog channel.

        Args:
            channel (int): The analog channel number (1-4).
            display (bool): True to display the channel, False to hide.

        Raises:
            AssertionError: If channel is not in [1, 4].

        Side Effects:
            Updates the display state for the specified channel.
        """
        logger.debug(f"[MSO5000] set_channel_display called with channel={channel}, display={display}")
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        logger.debug(f"[MSO5000] Setting display for channel {channel} to {display}")
        self.__set_parameter(f"CHANnel{channel}", "DISPlay", display)

    def set_channel_invert(self, channel: int, invert: bool):
        """
        Sets the invert state for a specified analog channel.

        Args:
            channel (int): The analog channel number (1-4).
            invert (bool): True to invert the channel signal, False otherwise.

        Raises:
            AssertionError: If channel is not in [1, 4].

        Side Effects:
            Updates the invert state for the specified channel.
        """
        logger.debug(f"[MSO5000] set_channel_invert called with channel={channel}, invert={invert}")
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        logger.debug(f"[MSO5000] Setting invert for channel {channel} to {invert}")
        self.__set_parameter(f"CHANnel{channel}", "INVert", invert)

    def set_channel_offset(self, channel: int, offset: float):
        """
        Sets the vertical offset for a specified analog channel.

        Args:
            channel (int): The analog channel number (1-4).
            offset (float): The offset value in volts, must be between -10 and 100.

        Raises:
            AssertionError: If channel is not in [1, 4] or offset is out of range.

        Side Effects:
            Updates the offset setting for the specified channel.
        """
        logger.debug(f"[MSO5000] set_channel_offset called with channel={channel}, offset={offset}")
        assert channel >= 1 and channel <= 4, "Channel must be between 1 and 4."
        _minimum = -10
        _maximum = 100
        assert (
            offset >= _minimum and offset <= _maximum
        ), f"Offset must be between {_minimum} and {_maximum}."
        logger.debug(f"[MSO5000] Setting offset for channel {channel} to {offset}")
        self.__set_parameter(f"CHANnel{channel}", "OFFSet", offset)

    # The :POWer commands are used to set the relevant parameters of the power supply module.

    # The :QUICk command is used to set and query the relevant parameters for shortcut keys.

    # The :RECOrd commands are used to set the relevant parameters of the record function.

    # The :REFerence commands are used to set relevant parameters for reference waveforms.

    # The :SAVE commands are used to save data or settings from the oscilloscope.
    def set_save_csv_length(self, length: SaveCsvLength):
        """
        Sets the CSV save length option for the MSO5000 oscilloscope.

        Args:
            length (SaveCsvLength): The desired CSV save length, must be a member of SaveCsvLength enum.

        Raises:
            AssertionError: If length is not a valid SaveCsvLength enum value.

        Side Effects:
            Updates the CSV save length setting on the oscilloscope.
        """
        logger.debug(f"[MSO5000] set_save_csv_length called with length={length}")
        assert (
            length in SaveCsvLength
        ), "Length must be one of the SaveCsvLength enum values."
        self.__set_parameter("SAVE", "CSV:LENGth", length.value)

    def set_save_csv_channel(self, channel: SaveCsvChannel, state: bool):
        """
        Sets the CSV save channel and its state for the MSO5000 oscilloscope.

        Args:
            channel (SaveCsvChannel): The channel to save, must be a member of SaveCsvChannel enum.
            state (bool): True to enable saving for the channel, False to disable.

        Raises:
            AssertionError: If channel is not a valid SaveCsvChannel enum value.

        Side Effects:
            Updates the CSV save channel setting on the oscilloscope.
        """
        logger.debug(f"[MSO5000] set_save_csv_channel called with channel={channel}, state={state}")
        assert (
            channel in SaveCsvChannel
        ), "Channel must be one of the SaveCsvChannel enum values."
        self.__set_parameter("SAVE", "CSV:CHANnel", f"{channel.value},{int(state)}")

    def save_csv(
        self,
        filename: str,
        length: SaveCsvLength = SaveCsvLength.Display,
    ):
        """
        Saves waveform data to a CSV file on the MSO5000 oscilloscope.

        Args:
            filename (str): The file path to save the CSV data.
            length (SaveCsvLength, optional): The CSV save length option. Defaults to SaveCsvLength.Display.

        Side Effects:
            Sets the CSV save length and saves the data to the specified file.
        """
        logger.debug(f"[MSO5000] save_csv called with filename={filename}, length={length}")
        self.set_save_csv_length(length)
        self.__set_parameter("SAVE", "CSV", filename)

    def save_image_type(self, type_: ImageType):
        """
        Sets the image file type for saving screenshots on the MSO5000 oscilloscope.

        Args:
            type_ (ImageType): The image type to set, must be a member of ImageType enum.

        Raises:
            AssertionError: If type_ is not a valid ImageType enum value.

        Side Effects:
            Updates the image type setting on the oscilloscope.
        """
        logger.debug(f"[MSO5000] save_image_type called with type_={type_}")
        assert (
            type_ in ImageType
        ), "Type must be one of the ImageType enum values."
        self.__set_parameter("SAVE", "IMAGe:TYPE", type_.value)

    def save_image_invert(self, invert: bool):
        """
        Sets the invert option for saving images on the MSO5000 oscilloscope.

        Args:
            invert (bool): True to invert the image colors, False otherwise.

        Side Effects:
            Updates the image invert setting on the oscilloscope.
        """
        logger.debug(f"[MSO5000] save_image_invert called with invert={invert}")
        self.__set_parameter("SAVE", "IMAGe:INVert", invert)

    def save_image_color(self, color: ImageColor):
        """
        Sets the color mode for saving images on the MSO5000 oscilloscope.

        Args:
            color (ImageColor): The color mode to set, must be a member of ImageColor enum.

        Side Effects:
            Updates the image color mode setting on the oscilloscope.
        """
        logger.debug(f"[MSO5000] save_image_color called with color={color}")
        self.__set_parameter("SAVE", "COLor", color.value)

    def save_image(
        self,
        path: str,
        type_: ImageType,
        invert: bool = False,
        color: ImageColor = ImageColor.Color,
    ):
        """
        Saves a screenshot image to the specified path on the MSO5000 oscilloscope.

        Args:
            path (str): The file path to save the image.
            type_ (ImageType): The image file type.
            invert (bool, optional): Whether to invert the image colors. Defaults to False.
            color (ImageColor, optional): The color mode. Defaults to ImageColor.Color.

        Side Effects:
            Sets image type, invert, color, and saves the image to the specified path.
        """
        logger.debug(f"[MSO5000] save_image called with path={path}, type_={type_}, invert={invert}, color={color}")
        self.save_image_type(type_)
        self.save_image_invert(invert)
        self.save_image_color(color)
        self.__set_parameter("SAVE", "IMAGe", path)

    def save_setup(self, path: str):
        """
        Saves the current oscilloscope setup to the specified file path.

        Args:
            path (str): The file path to save the setup.

        Side Effects:
            Saves the setup to the specified path on the oscilloscope.
        """
        logger.debug(f"[MSO5000] save_setup called with path={path}")
        self.__set_parameter("SAVE", "SETup", path)

    def save_waveform(self, path: str):
        """
        Saves the current waveform data to the specified file path.

        Args:
            path (str): The file path to save the waveform data.

        Side Effects:
            Saves the waveform data to the specified path on the oscilloscope.
        """
        logger.debug(f"[MSO5000] save_waveform called with path={path}")
        self.__set_parameter("SAVE", "WAVeform", path)

    def get_save_status(self) -> bool:
        """
        Retrieves the status of the last save operation on the MSO5000 oscilloscope.

        Returns:
            bool: True if the last save operation was successful, False otherwise.
        """
        logger.debug(f"[MSO5000] get_save_status called")
        return self.__get_parameter("SAVE", "STATus")

    def load_setup(self, filename: str):
        """
        Loads a previously saved oscilloscope setup from the specified file.

        Args:
            filename (str): The file path of the setup to load.

        Side Effects:
            Loads the setup from the specified file on the oscilloscope.
        """
        logger.debug(f"[MSO5000] load_setup called with filename={filename}")
        self.__write(f":LOAD:SETup {filename}")

    # The :SEARch commands are used to set the relevant parameters of the search function.

    # The [:SOURce [<n>]] commands are used to set the relevant parameters of the built in function arbitrary
    # waveform generator. <n> can set to 1 or 2, which indicates the corresponding built in function/arbitrary
    # waveform generator channel. When <n> or :SOURce[<n>] is omitted, by default, the operations are
    # carried out on AWG GI.

    # The [:SOURce [<n>]] commands are used to set the relevant parameters of the built in function arbitrary
    # waveform generator. <n> can set to 1 or 2, which indicates the corresponding built in function/arbitrary
    # waveform generator channel. When <n> or :SOURce[<n>] is omitted, by default, the operations are
    # carried out on AWG GI.

    def function_generator_state(self, channel: int, state: bool):
        """
        Enables or disables the function generator output for the specified channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            state (bool): True to enable output, False to disable.

        Raises:
            AssertionError: If channel is not 1 or 2.

        Side Effects:
            Sends the output enable/disable command to the instrument.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        self.__set_parameter(f"SOURce{channel}", "OUTPut", state)

    def set_source_function(self, channel: int, function: SourceFunction):
        """
        Sets the waveform function type for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            function (SourceFunction): The waveform function type to set.

        Raises:
            AssertionError: If channel is not 1 or 2, or function is not a valid SourceFunction.

        Side Effects:
            Sends the function type command to the instrument.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert function in SourceFunction, "Function must be one of the SourceFunction enum values."
        self.__set_parameter(f"SOURce{channel}", "FUNCtion", function.value)

    def set_source_frequency(self, channel: int, frequency: float):
        """
        Sets the output frequency for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            frequency (float): The output frequency in Hz.

        Raises:
            AssertionError: If channel is not 1 or 2, or frequency is not positive.

        Side Effects:
            Sends the frequency command to the instrument.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert frequency > 0, "Frequency must be positive."
        self.__set_parameter(f"SOURce{channel}", "FREQuency", frequency)

    def set_source_phase(self, channel: int, phase: float):
        """
        Sets the output phase for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            phase (float): The output phase in degrees.

        Raises:
            AssertionError: If channel is not 1 or 2.

        Side Effects:
            Sends the phase command to the instrument.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        self.__set_parameter(f"SOURce{channel}", "PHASe", phase)

    def set_source_amplitude(self, channel: int, amplitude: float):
        """
        Sets the output amplitude for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            amplitude (float): The output amplitude in volts.

        Raises:
            AssertionError: If channel is not 1 or 2, or amplitude is not positive.

        Side Effects:
            Sends the amplitude command to the instrument.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert amplitude > 0, "Amplitude must be positive."
        self.__set_parameter(f"SOURce{channel}", "AMPLitude", amplitude)

    def set_source_offset(self, channel: int, offset: float):
        """
        Sets the output offset voltage for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            offset (float): The output offset voltage in volts.

        Raises:
            AssertionError: If channel is not 1 or 2.

        Side Effects:
            Sends the offset command to the instrument.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        self.__set_parameter(f"SOURce{channel}", "OFFSet", offset)

    def set_source_output_impedance(self, channel: int, impedance: SourceOutputImpedance):
        """
        Sets the output impedance for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            impedance (SourceOutputImpedance): The output impedance setting.

        Raises:
            AssertionError: If channel is not 1 or 2, or impedance is not a valid SourceOutputImpedance.

        Side Effects:
            Sends the output impedance command to the instrument.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert impedance in SourceOutputImpedance, "Impedance must be one of the SourceOutputImpedance enum values."
        self.__set_parameter(f"SOURce{channel}", "IMPedance", impedance.value)

    def set_source_type(self, channel: int, type_: SourceType):
        """
        Sets the source type (None, Modulated, Sweep, Burst) for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            type_ (SourceType): The source type to set.

        Raises:
            AssertionError: If channel is not 1 or 2, or type_ is not a valid SourceType.

        Side Effects:
            Sends the source type command to the instrument.
        """
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert type_ in SourceType, "Type must be one of the SourceType enum values."
        self.__set_parameter(f"SOURce{channel}", "TYPE", type_.value)
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
        """
        Configures the function generator to output a sinusoidal waveform on the specified channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            frequency (float, optional): Output frequency in Hz. Defaults to 1000.
            phase (float, optional): Output phase in degrees. Defaults to 0.
            amplitude (float, optional): Output amplitude in volts. Defaults to 0.5.
            offset (float, optional): Output offset voltage in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): Output impedance setting. Defaults to Omeg (high impedance).

        Side Effects:
            Disables output, sets waveform type, frequency, phase, amplitude, offset, and output impedance for the channel.
        """
        logger.debug(f"[MSO5000] function_generator_sinusoid called with channel={channel}, frequency={frequency}, phase={phase}, amplitude={amplitude}, offset={offset}, output_impedance={output_impedance}")
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.Sinusoid)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

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
        Configures the function generator to output a square waveform on the specified channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            frequency (float, optional): Output frequency in Hz. Defaults to 1000.
            phase (float, optional): Output phase in degrees. Defaults to 0.
            amplitude (float, optional): Output amplitude in volts. Defaults to 0.5.
            offset (float, optional): Output offset voltage in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): Output impedance setting. Defaults to Omeg (high impedance).

        Side Effects:
            Disables output, sets waveform type, frequency, phase, amplitude, offset, and output impedance for the channel.
        """
        logger.debug(f"[MSO5000] function_generator_square called with channel={channel}, frequency={frequency}, phase={phase}, amplitude={amplitude}, offset={offset}, output_impedance={output_impedance}")
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.Square)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    def set_source_function_ramp_symmetry(self, channel: int, symmetry: float):
        """
        Sets the symmetry for the ramp waveform on the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            symmetry (float): Symmetry percentage (1-100).

        Raises:
            AssertionError: If channel is not 1 or 2, or symmetry is not in [1, 100].

        Side Effects:
            Updates the ramp symmetry setting for the channel.
        """
        logger.debug(f"[MSO5000] set_source_function_ramp_symmetry called with channel={channel}, symmetry={symmetry}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert symmetry >= 1 and symmetry <= 100, "Symmetry must be between 1 and 100%."
        self.__set_parameter(f"SOURce{channel}", "FUNCtion:RAMP:SYMMetry", symmetry)

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
        Configures the function generator to output a ramp waveform on the specified channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            frequency (float, optional): Output frequency in Hz. Defaults to 1000.
            phase (float, optional): Output phase in degrees. Defaults to 0.
            symmetry (float, optional): Ramp symmetry percentage (1-100). Defaults to 50.
            amplitude (float, optional): Output amplitude in volts. Defaults to 0.5.
            offset (float, optional): Output offset voltage in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): Output impedance setting. Defaults to Omeg (high impedance).

        Side Effects:
            Disables output, sets waveform type, frequency, phase, symmetry, amplitude, offset, and output impedance for the channel.
        """
        logger.debug(f"[MSO5000] function_generator_ramp called with channel={channel}, frequency={frequency}, phase={phase}, symmetry={symmetry}, amplitude={amplitude}, offset={offset}, output_impedance={output_impedance}")
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.Ramp)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_function_ramp_symmetry(channel, symmetry)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    def set_source_duty_cycle(self, channel: int, duty_cycle: float):
        """
        Sets the duty cycle for the pulse waveform on the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            duty_cycle (float): Duty cycle percentage (10-90).

        Raises:
            AssertionError: If channel is not 1 or 2, or duty_cycle is not in [10, 90].

        Side Effects:
            Updates the pulse duty cycle setting for the channel.
        """
        logger.debug(f"[MSO5000] set_source_duty_cycle called with channel={channel}, duty_cycle={duty_cycle}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            duty_cycle >= 10 and duty_cycle <= 90
        ), "Duty cycle must be between 10 and 90%."
        self.__set_parameter(f"SOURce{channel}", "PULSe:DCYCle", duty_cycle)

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

        Args:
            channel (int): The function generator channel (1 or 2).
            frequency (float, optional): Output frequency in Hz. Defaults to 1000.
            phase (float, optional): Output phase in degrees. Defaults to 0.
            duty_cycle (float, optional): Duty cycle percentage (10-90). Defaults to 20.
            amplitude (float, optional): Output amplitude in volts. Defaults to 0.5.
            offset (float, optional): Output offset voltage in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): Output impedance setting. Defaults to Omeg (high impedance).

        Side Effects:
            Disables output, sets waveform type, frequency, phase, duty cycle, amplitude, offset, and output impedance for the channel.
        """
        logger.debug(f"[MSO5000] function_generator_pulse called with channel={channel}, frequency={frequency}, phase={phase}, duty_cycle={duty_cycle}, amplitude={amplitude}, offset={offset}, output_impedance={output_impedance}")
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.Pulse)
        self.set_source_frequency(channel, frequency)
        self.set_source_phase(channel, phase)
        self.set_source_duty_cycle(channel, duty_cycle)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    def function_generator_noise(
        self,
        channel: int,
        amplitude: float = 0.5,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        """
        Configures the function generator to output a noise waveform on the specified channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            amplitude (float, optional): Output amplitude in volts. Defaults to 0.5.
            offset (float, optional): Output offset voltage in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): Output impedance setting. Defaults to Omeg (high impedance).

        Side Effects:
            Disables output, sets waveform type, amplitude, offset, and output impedance for the channel.
        """
        logger.debug(f"[MSO5000] function_generator_noise called with channel={channel}, amplitude={amplitude}, offset={offset}, output_impedance={output_impedance}")
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.Noise)
        self.set_source_amplitude(channel, amplitude)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

    def function_generator_dc(
        self,
        channel: int,
        offset: float = 0,
        output_impedance: SourceOutputImpedance = SourceOutputImpedance.Omeg,
    ):
        """
        Configures the function generator to output a DC waveform on the specified channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            offset (float, optional): Output offset voltage in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): Output impedance setting. Defaults to Omeg (high impedance).

        Side Effects:
            Disables output, sets waveform type, offset, and output impedance for the channel.
        """
        logger.debug(f"[MSO5000] function_generator_dc called with channel={channel}, offset={offset}, output_impedance={output_impedance}")
        self.function_generator_state(channel, False)
        self.set_source_function(channel, SourceFunction.DC)
        self.set_source_offset(channel, offset)
        self.set_source_output_impedance(channel, output_impedance)

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

        Args:
            channel (int): The function generator channel (1 or 2).
            frequency (float, optional): Output frequency in Hz. Defaults to 1000.
            phase (float, optional): Output phase in degrees. Defaults to 0.
            amplitude (float, optional): Output amplitude in volts. Defaults to 0.5.
            offset (float, optional): Output offset voltage in volts. Defaults to 0.
            output_impedance (SourceOutputImpedance, optional): Output impedance setting. Defaults to Omeg (high impedance).

        Side Effects:
            Disables output, sets waveform type, frequency, phase, amplitude, offset, and output impedance for the channel.
        """
        logger.debug(f"[MSO5000] function_generator_sinc called with channel={channel}, frequency={frequency}, phase={phase}, amplitude={amplitude}, offset={offset}, output_impedance={output_impedance}")
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
        """
        Disables modulation for the function generator on the specified channel.

        Args:
            channel (int): The function generator channel (1 or 2).

        Side Effects:
            Disables output and sets the source type to None for the channel.
        """
        logger.debug(f"[MSO5000] function_generator_no_modulation called with channel={channel}")
        self.function_generator_state(channel, False)
        self.set_source_type(channel, SourceType._None)

    # Function Generator Type: Modulation

    def set_source_mod_type(self, channel: int, mod_type: SourceModulation):
        """
        Sets the modulation type for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            mod_type (SourceModulation): The modulation type to set.

        Raises:
            AssertionError: If channel is not 1 or 2, or mod_type is not a valid SourceModulation.

        Side Effects:
            Sends the modulation type command to the instrument.
        """
        logger.debug(f"[MSO5000] set_source_mod_type called with channel={channel}, mod_type={mod_type}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            mod_type in SourceModulation
        ), "Modulation type must be one of the Modulation enum values."
        self.__set_parameter(f"SOURce{channel}", "MODulation:TYPE", mod_type.value)

    def set_source_mod_am_depth(self, channel: int, depth: float):
        """
        Sets the amplitude modulation depth for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            depth (float): Modulation depth percentage (0-120).

        Raises:
            AssertionError: If channel is not 1 or 2, or depth is not in [0, 120].

        Side Effects:
            Updates the amplitude modulation depth for the channel.
        """
        logger.debug(f"[MSO5000] set_source_mod_am_depth called with channel={channel}, depth={depth}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            depth >= 0 and depth <= 120
        ), "Modulation amplitude depth must be between 0 and 120%."
        self.__set_parameter(f"SOURce{channel}", "MOD:DEPTh", depth)

    def set_source_mod_am_freq(self, channel: int, frequency: float):
        """
        Sets the amplitude modulation frequency for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            frequency (float): Modulation frequency in Hz (1-50).

        Raises:
            AssertionError: If channel is not 1 or 2, or frequency is not in [1, 50].

        Side Effects:
            Updates the amplitude modulation frequency for the channel.
        """
        logger.debug(f"[MSO5000] set_source_mod_am_freq called with channel={channel}, frequency={frequency}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            frequency >= 1 and frequency <= 50
        ), "Modulation frequency must be between 1 and 50 Hz."
        self.__set_parameter(f"SOURce{channel}", "MOD:AM:INTernal:FREQuency", frequency)

    def set_source_mod_fm_freq(self, channel: int, frequency: float):
        """
        Sets the frequency modulation frequency for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            frequency (float): Modulation frequency in Hz (1-50).

        Raises:
            AssertionError: If channel is not 1 or 2, or frequency is not in [1, 50].

        Side Effects:
            Updates the frequency modulation frequency for the channel.
        """
        logger.debug(f"[MSO5000] set_source_mod_fm_freq called with channel={channel}, frequency={frequency}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            frequency >= 1 and frequency <= 50
        ), "Modulation frequency must be between 1 and 50 Hz."
        self.__set_parameter(f"SOURce{channel}", "MOD:FM:INTernal:FREQuency", frequency)

    def set_source_mod_am_function(self, channel: int, function: SourceFunction):
        """
        Sets the internal function for amplitude modulation on the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            function (SourceFunction): The waveform function type for modulation.

        Raises:
            AssertionError: If channel is not 1 or 2, or function is not a valid modulation function.

        Side Effects:
            Updates the internal function for amplitude modulation.
        """
        logger.debug(f"[MSO5000] set_source_mod_am_function called with channel={channel}, function={function}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert function in [
            SourceFunction.SINusoid,
            SourceFunction.SQUare,
            SourceFunction.RAMP,
            SourceFunction.NOISe,
        ], "Modulation function must be one of SINusoid, SQUare, RAMP, NOISe."
        self.__set_parameter(
            f"SOURce{channel}", "MOD:AM:INTernal:FUNCtion", function.value
        )

    def set_source_mod_fm_function(self, channel: int, function: SourceFunction):
        """
        Sets the internal function for frequency modulation on the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            function (SourceFunction): The waveform function type for modulation.

        Raises:
            AssertionError: If channel is not 1 or 2, or function is not a valid modulation function.

        Side Effects:
            Updates the internal function for frequency modulation.
        """
        logger.debug(f"[MSO5000] set_source_mod_fm_function called with channel={channel}, function={function}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert function in [
            SourceFunction.SINusoid,
            SourceFunction.SQUare,
            SourceFunction.RAMP,
            SourceFunction.NOISe,
        ], "Modulation function must be one of SINusoid, SQUare, RAMP, NOISe."
        self.__set_parameter(
            f"SOURce{channel}", "MOD:FM:INTernal:FUNCtion", function.value
        )

    def set_source_mod_fm_deviation(self, channel: int, deviation: float):
        """
        Sets the frequency deviation for frequency modulation on the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            deviation (float): Frequency deviation in Hz (>= 0).

        Raises:
            AssertionError: If channel is not 1 or 2, or deviation is negative.

        Side Effects:
            Updates the frequency deviation for frequency modulation.
        """
        logger.debug(f"[MSO5000] set_source_mod_fm_deviation called with channel={channel}, deviation={deviation}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            deviation >= 0
        ), "Modulation frequency deviation must be greater than or equal to 0 Hz."
        self.__set_parameter(f"SOURce{channel}", "MOD:FM:DEViation", deviation)

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
        Configures the function generator to output a modulated waveform on the specified channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            type_ (SourceModulation, optional): Modulation type (AM, FM, FSK). Defaults to AmplitudeModulation.
            am_depth (float, optional): Amplitude modulation depth (0-120%). Defaults to 100.
            frequency (float, optional): Modulation frequency in Hz. Defaults to 1000.
            function (SourceFunction, optional): Modulation waveform function. Defaults to Sinusoid.
            fm_deviation (float, optional): Frequency deviation for FM in Hz. Defaults to 1000.

        Side Effects:
            Disables output, sets modulation type, and configures modulation parameters for the channel.
        """
        logger.debug(f"[MSO5000] function_generator_modulation called with channel={channel}, type_={type_}, am_depth={am_depth}, frequency={frequency}, function={function}, fm_deviation={fm_deviation}")
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
        """
        Sets the sweep type for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            type_ (SourceSweepType): The sweep type to set.

        Raises:
            AssertionError: If channel is not 1 or 2, or type_ is not a valid SourceSweepType.

        Side Effects:
            Updates the sweep type for the channel.
        """
        logger.debug(f"[MSO5000] set_source_sweep_type called with channel={channel}, type_={type_}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            type_ in SourceSweepType
        ), "Sweep type must be one of the SweepType enum values."
        self.__set_parameter(f"SOURce{channel}", "SWEep:TYPE", type_.value)

    def set_source_sweep_sweep_time(self, channel: int, time: int):
        """
        Sets the sweep time for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            time (int): Sweep time in seconds (1-500).

        Raises:
            AssertionError: If channel is not 1 or 2, or time is not in [1, 500].

        Side Effects:
            Updates the sweep time for the channel.
        """
        logger.debug(f"[MSO5000] set_source_sweep_sweep_time called with channel={channel}, time={time}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            time >= 1 and time <= 500
        ), "Sweep time must be between 1 and 500 seconds."
        self.__set_parameter(f"SOURce{channel}", "SWEep:STIMe", time)

    def set_source_sweep_return_time(self, channel: int, time: int):
        """
        Sets the return time for the sweep function on the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            time (int): Return time in seconds (1-500).

        Raises:
            AssertionError: If channel is not 1 or 2, or time is not in [1, 500].

        Side Effects:
            Updates the return time for the channel.
        """
        logger.debug(f"[MSO5000] set_source_sweep_return_time called with channel={channel}, time={time}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            time >= 1 and time <= 500
        ), "Return time must be between 1 and 500 seconds."
        self.__set_parameter(f"SOURce{channel}", "SWEep:BTIMe", time)

    def function_generator_sweep(
        self,
        channel: int,
        type_: SourceSweepType = SourceSweepType.Linear,
        sweep_time: int = 1,
        return_time: int = 0,
    ):
        """
        Configures the function generator to output a sweep waveform on the specified channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            type_ (SourceSweepType, optional): Sweep type (Linear, Log, Step). Defaults to Linear.
            sweep_time (int, optional): Sweep time in seconds (1-500). Defaults to 1.
            return_time (int, optional): Return time in seconds (1-500). Defaults to 0.

        Side Effects:
            Disables output, sets sweep type, sweep time, and return time for the channel.
        """
        logger.debug(f"[MSO5000] function_generator_sweep called with channel={channel}, type_={type_}, sweep_time={sweep_time}, return_time={return_time}")
        self.function_generator_state(channel, False)
        self.set_source_type(channel, SourceType.Sweep)
        self.set_source_sweep_type(channel, type_)
        self.set_source_sweep_sweep_time(channel, sweep_time)
        self.set_source_sweep_return_time(channel, return_time)

    # Function Generator Type: Burst

    def set_source_burst_type(self, channel: int, type_: SourceBurstType):
        """
        Sets the burst type for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            type_ (SourceBurstType): The burst type to set.

        Raises:
            AssertionError: If channel is not 1 or 2, or type_ is not a valid SourceBurstType.

        Side Effects:
            Updates the burst type for the channel.
        """
        logger.debug(f"[MSO5000] set_source_burst_type called with channel={channel}, type_={type_}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            type_ in SourceBurstType
        ), "Burst type must be one of the BurstType enum values."
        self.__set_parameter(f"SOURce{channel}", "BURSt:TYPE", type_.value)

    def set_source_burst_cycles(self, channel: int, cycles: int):
        """
        Sets the number of burst cycles for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            cycles (int): Number of burst cycles (1-1000000).

        Raises:
            AssertionError: If channel is not 1 or 2, or cycles is not in [1, 1000000].

        Side Effects:
            Updates the burst cycles for the channel.
        """
        logger.debug(f"[MSO5000] set_source_burst_cycles called with channel={channel}, cycles={cycles}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            cycles >= 1 and cycles <= 1000000
        ), "Burst cycles must be between 1 and 1000000."
        self.__set_parameter(f"SOURce{channel}", "BURSt:CYCLes", cycles)

    def set_source_burst_delay(self, channel: int, delay: int):
        """
        Sets the burst delay for the function generator channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            delay (int): Burst delay in microseconds (1-1000000).

        Raises:
            AssertionError: If channel is not 1 or 2, or delay is not in [1, 1000000].

        Side Effects:
            Updates the burst delay for the channel.
        """
        logger.debug(f"[MSO5000] set_source_burst_delay called with channel={channel}, delay={delay}")
        assert channel >= 1 and channel <= 2, "Channel must be between 1 and 2."
        assert (
            delay >= 1 and delay <= 1000000
        ), "Burst delay must be between 1 and 1000000."
        self.__set_parameter(f"SOURce{channel}", "BURSt:DELay", delay)

    def function_generator_burst(
        self,
        channel: int,
        type_: SourceBurstType = SourceBurstType.Ncycle,
        cycles: int = 1,
        delay: int = 0,
    ):
        """
        Configures the function generator to output a burst waveform on the specified channel.

        Args:
            channel (int): The function generator channel (1 or 2).
            type_ (SourceBurstType, optional): Burst type (Ncycle, Infinite). Defaults to Ncycle.
            cycles (int, optional): Number of burst cycles (1-1000000). Defaults to 1.
            delay (int, optional): Burst delay in microseconds (1-1000000). Defaults to 0.

        Side Effects:
            Disables output, sets burst type, cycles, and delay for the channel.
        """
        logger.debug(f"[MSO5000] function_generator_burst called with channel={channel}, type_={type_}, cycles={cycles}, delay={delay}")
        self.function_generator_state(channel, False)
        self.set_source_type(channel, SourceType.Sweep)
        self.set_source_burst_type(channel, type_)
        self.set_source_burst_cycles(channel, cycles)
        self.set_source_burst_delay(channel, delay)

    # The :SYSTem commands are used to set sound, language, and other relevant system settings.

    def get_system_error(self) -> str:
        """
        Retrieves the next system error message from the MSO5000 oscilloscope.

        Returns:
            str: The next error message from the system error queue, or an empty string if no error is present.

        Side Effects:
            - Logs the operation.
            - Queries the device for the next error message.
        """
        logger.debug(f"[MSO5000] get_system_error called")
        return self.__get_parameter("SYSTem", "ERRor:NEXT")

    def set_timebase_delay_enable(self, enable: bool):
        """
        Enables or disables the delayed sweep timebase on the MSO5000 oscilloscope.

        Args:
            enable (bool): True to enable delayed sweep, False to disable.

        Side Effects:
            - Logs the operation.
            - Sets the delayed sweep enable parameter on the device.
        """
        logger.debug(f"[MSO5000] set_timebase_delay_enable called with enable={enable}")
        self.__set_parameter("TIMebase", "DELay:ENABle", enable)

    def set_timebase_delay_offset(self, offset: float):
        """
        Sets the delay offset for the timebase on the MSO5000 oscilloscope.

        Args:
            offset (float): The delay offset value in seconds.

        Side Effects:
            - Logs the operation.
            - Sets the delay offset parameter on the device.
        """
        logger.debug(f"[MSO5000] set_timebase_delay_offset called with offset={offset}")
        self.__set_parameter("TIMebase", "DELay:OFFSet", offset)

    def set_timebase_delay_scale(self, scale: float):
        """
        Sets the delay scale for the timebase on the MSO5000 oscilloscope.

        Args:
            scale (float): The delay scale value in seconds/div.

        Side Effects:
            - Logs the operation.
            - Sets the delay scale parameter on the device.
        """
        logger.debug(f"[MSO5000] set_timebase_delay_scale called with scale={scale}")
        self.__set_parameter("TIMebase", "DELay:SCALe", scale)

    def timebase_delay(
        self, enable: bool = False, offset: float = 0, scale: float = 500e-9
    ):
        """
        Configures the delayed sweep timebase settings on the MSO5000 oscilloscope.

        Args:
            enable (bool, optional): Enable or disable delayed sweep. Defaults to False.
            offset (float, optional): Delay offset in seconds. Defaults to 0.
            scale (float, optional): Delay scale in seconds/div. Defaults to 500e-9.

        Side Effects:
            - Logs the operation.
            - Applies the delayed sweep settings to the device.
        """
        logger.debug(f"[MSO5000] timebase_delay called with enable={enable}, offset={offset}, scale={scale}")
        self.set_timebase_delay_enable(enable)
        self.set_timebase_delay_offset(offset)
        self.set_timebase_delay_scale(scale)

    def set_timebase_offset(self, offset: float):
        """
        Sets the main timebase horizontal offset on the MSO5000 oscilloscope.

        Args:
            offset (float): The horizontal offset value in seconds.

        Side Effects:
            - Logs the operation.
            - Sets the main timebase offset parameter on the device.
        """
        logger.debug(f"[MSO5000] set_timebase_offset called with offset={offset}")
        self.__set_parameter("TIMebase", "MAIN:OFFSet", offset)

    def set_timebase_scale(self, scale: float):
        """
        Sets the main timebase scale on the MSO5000 oscilloscope.

        Args:
            scale (float): The timebase scale value in seconds/div.

        Side Effects:
            - Logs the operation.
            - Sets the main timebase scale parameter on the device.
        """
        logger.debug(f"[MSO5000] set_timebase_scale called with scale={scale}")
        self.__set_parameter("TIMebase", "MAIN:SCALe", scale)

    def set_timebase_mode(self, mode: TimebaseMode):
        """
        Sets the horizontal timebase mode on the MSO5000 oscilloscope.

        Args:
            mode (TimebaseMode): The desired timebase mode (Main, Xy, Roll).

        Raises:
            AssertionError: If mode is not a valid TimebaseMode enum value.

        Side Effects:
            - Logs the operation.
            - Sets the timebase mode parameter on the device.
        """
        logger.debug(f"[MSO5000] set_timebase_mode called with mode={mode}")
        assert (
            mode in TimebaseMode
        ), "Timebase mode must be one of the TimebaseMode enum values."
        self.__set_parameter("TIMebase", "MODE", mode.value)

    def set_timebase_href_mode(self, mode: HrefMode):
        """
        Sets the horizontal reference mode for the timebase on the MSO5000 oscilloscope.

        Args:
            mode (HrefMode): The desired horizontal reference mode.

        Raises:
            AssertionError: If mode is not a valid HrefMode enum value.

        Side Effects:
            - Logs the operation.
            - Sets the horizontal reference mode parameter on the device.
        """
        logger.debug(f"[MSO5000] set_timebase_href_mode called with mode={mode}")
        assert (
            mode in HrefMode
        ), "Href mode must be one of the HrefMode enum values."
        self.__set_parameter("TIMebase", "HREFerence:MODE", mode.value)

    def set_timebase_position(self, position: int):
        """
        Sets the horizontal reference position for the timebase on the MSO5000 oscilloscope.

        Args:
            position (int): The reference position value, must be between -500 and 500.

        Raises:
            AssertionError: If position is not within the valid range.

        Side Effects:
            - Logs the operation.
            - Sets the horizontal reference position parameter on the device.
        """
        logger.debug(f"[MSO5000] set_timebase_position called with position={position}")
        assert (
            position >= -500 and position <= 500
        ), "Horizontal reference position must be between -500 to 500."
        self.__set_parameter("TIMebase", "HREFerence:POSition", position)

    def set_timebase_vernier(self, vernier: bool):
        """
        Enables or disables vernier mode for the timebase on the MSO5000 oscilloscope.

        Args:
            vernier (bool): True to enable vernier mode, False to disable.

        Side Effects:
            - Logs the operation.
            - Sets the vernier mode parameter on the device.
        """
        logger.debug(f"[MSO5000] set_timebase_vernier called with vernier={vernier}")
        self.__set_parameter("TIMebase", "VERNier", vernier)

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
        Applies a set of horizontal timebase settings to the MSO5000 oscilloscope.

        Args:
            offset (float, optional): Horizontal offset in seconds. Defaults to 0.
            scale (float, optional): Timebase scale in seconds/div. Defaults to 1e-6.
            mode (TimebaseMode, optional): Timebase mode. Defaults to Main.
            href_mode (HrefMode, optional): Horizontal reference mode. Defaults to Center.
            position (float, optional): Reference position. Defaults to 0.
            vernier (bool, optional): Enable vernier mode. Defaults to False.

        Side Effects:
            - Logs the operation.
            - Applies all specified timebase settings to the device.
        """
        logger.debug(f"[MSO5000] timebase_settings called with offset={offset}, scale={scale}, mode={mode}, href_mode={href_mode}, position={position}, vernier={vernier}")
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
        logger.debug(f"[MSO5000] get_trigger_status called")
        _status = self.__get_parameter("TRIGger", "STATus")
        logger.debug(f"[MSO5000] Trigger status response: {_status}")
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
        logger.debug(f"[MSO5000] set_trigger_mode called with mode={mode}")
        assert (
            mode in TriggerMode
        ), "Trigger mode must be one of the TriggerMode enum values."
        self.__set_parameter("TRIGger", "MODE", mode.value)

    def set_trigger_coupling(self, coupling: TriggerCoupling):
        """
        Sets the trigger coupling mode for the device.

        Args:
            coupling (TriggerCoupling): The desired trigger coupling mode. Must be a member of the TriggerCoupling enum.

        Raises:
            AssertionError: If the provided coupling is not a valid TriggerCoupling enum value.

        """
        logger.debug(f"[MSO5000] set_trigger_coupling called with coupling={coupling}")
        assert (
            coupling in TriggerCoupling
        ), "Trigger coupling must be one of the TriggerCoupling enum values."
        self.__set_parameter("TRIGger", "COUPling", coupling.value)

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
        logger.debug(f"[MSO5000] set_trigger_sweep called with sweep={sweep}")
        assert (
            sweep in TriggerSweep
        ), "Trigger sweep must be one of the TriggerSweep enum values."
        self.__set_parameter("TRIGger", "SWEep", sweep.value)

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
        logger.debug(f"[MSO5000] set_trigger_holdoff called with holdoff={holdoff}")
        assert (
            holdoff >= 8e-9 and holdoff <= 10
        ), "Trigger holdoff must be between 8ns and 10s."
        self.__set_parameter("TRIGger", "HOLDoff", holdoff)

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
        logger.debug(f"[MSO5000] set_trigger_noise_reject called with status={status}")
        self.__set_parameter("TRIGger", "NREJect", status)

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
        logger.debug(f"[MSO5000] set_trigger_edge_source called with source={source}")
        assert (
            source in TriggerSource
        ), "Trigger edge source must be one of the TriggerSource enum values."
        self.__set_parameter("TRIGger", "EDGE:SOURce", source.value)

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
        logger.debug(f"[MSO5000] set_trigger_edge_slope called with slope={slope}")
        assert (
            slope in TriggerSlope
        ), "Trigger edge slope must be one of the TriggerEdgeSlope enum values."
        self.__set_parameter("TRIGger", "EDGE:SLOPe", slope.value)

    def set_trigger_edge_level(self, level: float):
        """
        Sets the trigger edge level for the device.

        Args:
            level (float): The voltage level to set for the trigger edge, in volts.
                Must be between -15 and 15 (inclusive).

        Raises:
            AssertionError: If the provided level is outside the valid range [-15, 15].

        """
        logger.debug(f"[MSO5000] set_trigger_edge_level called with level={level}")
        assert (
            level >= -15 and level <= 15
        ), "Trigger edge level must be between -15 and 15 V."
        self.__set_parameter("TRIGger", "EDGE:LEVel", level)

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
        logger.debug(f"[MSO5000] trigger_edge called with coupling={coupling}, sweep={sweep}, holdoff={holdoff}, nreject={nreject}, edge_source={edge_source}, edge_slope={edge_slope}, edge_level={edge_level}")
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
        logger.debug(f"[MSO5000] set_trigger_pulse_source called with source={source}")
        assert (
            source in TriggerSource
        ), "Trigger pulse source must be one of the TriggerSource enum values."
        self.__set_parameter("TRIGger", "PULSe:SOURce", source.value)

    def set_trigger_pulse_when(self, when: TriggerWhen):
        """
        Sets the trigger pulse condition for the oscilloscope.

        Args:
            when (TriggerWhen): The trigger condition to set. Must be a value from the TriggerWhen enum.

        Raises:
            AssertionError: If the provided when is not a valid TriggerWhen enum value.

        """
        logger.debug(f"[MSO5000] set_trigger_pulse_when called with when={when}")
        assert (
            when in TriggerWhen
        ), "Trigger when must be one of the TriggerWhen enum values."
        self.__set_parameter("TRIGger", "PULSe:WHEN", when.value)

    def set_trigger_pulse_upper_width(self, width: float):
        """
        Sets the upper width for the trigger pulse.

        Parameters:
            width (float): The upper width of the trigger pulse in seconds. Must be less than or equal to 10.

        Raises:
            AssertionError: If the specified width is greater than 10 seconds.

        """
        logger.debug(f"[MSO5000] set_trigger_pulse_upper_width called with width={width}")
        assert width <= 10, "Trigger pulse upper width must be less than 10s."
        self.__set_parameter("TRIGger", "PULSe:UWIDth", width)

    def set_trigger_pulse_lower_width(self, width: float):
        """
        Sets the lower width threshold for the trigger pulse.

        Args:
            width (float): The lower width of the trigger pulse in seconds.
                Must be greater than or equal to 8 picoseconds (8e-12 s).

        Raises:
            AssertionError: If the specified width is less than 8 picoseconds.

        """
        logger.debug(f"[MSO5000] set_trigger_pulse_lower_width called with width={width}")
        assert width >= 8e-12, "Trigger pulse lower width must be greater than 8 ps."
        self.__set_parameter("TRIGger", "PULSe:LWIDth", width)

    def set_trigger_pulse_level(self, level: float):
        """
        Sets the trigger pulse level for the device.

        Args:
            level (float): The desired trigger pulse level in volts. Must be between -15 and 15.

        Raises:
            AssertionError: If the specified level is not within the range -15 to 15 volts.

        """
        logger.debug(f"[MSO5000] set_trigger_pulse_level called with level={level}")
        assert (
            level >= -15 and level <= 15
        ), "Trigger pulse level must be between -15V and 15V."
        self.__set_parameter("TRIGger", "PULSe:LEVel", level)

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
        logger.debug(f"[MSO5000] trigger_pulse called with coupling={coupling}, sweep={sweep}, holdoff={holdoff}, nreject={nreject}, pulse_source={pulse_source}, pulse_when={pulse_when}, pulse_upper_width={pulse_upper_width}, pulse_lower_width={pulse_lower_width}, pulse_level={pulse_level}")
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
        logger.debug(f"[MSO5000] set_trigger_slope_source called with source={source}")
        assert source in [
            TriggerSource.Channel1,
            TriggerSource.Channel2,
            TriggerSource.Channel3,
            TriggerSource.Channel4,
        ], "Trigger source must be one of Channel 1, Channel 2, Channel 3 or Channel 4."
        self.__set_parameter("TRIGger", "SLOPe:SOURce", source.value)

    def set_trigger_slope_when(self, when: TriggerWhen):
        """
        Sets the trigger slope condition for the oscilloscope.

        Args:
            when (TriggerWhen): The trigger condition to set. Must be a value from the TriggerWhen enum.

        Raises:
            AssertionError: If the provided when is not a valid TriggerWhen enum value.

        """
        logger.debug(f"[MSO5000] set_trigger_slope_when called with when={when}")
        assert (
            when in TriggerWhen
        ), "Trigger when must be one of the TriggerWhen enum values."
        self.__set_parameter("TRIGger", "SLOPe:WHEN", when.value)

    def set_trigger_slope_time_upper(self, time: float):
        """
        Sets the upper time limit for the trigger slope.

        Args:
            time (float): The upper time limit in seconds. Must be less than or equal to 10.

        Raises:
            AssertionError: If the specified time is greater than 10 seconds.

        """
        logger.debug(f"[MSO5000] set_trigger_slope_time_upper called with time={time}")
        assert time <= 10, "Upper time limit must be less than 10 s."
        self.__set_parameter("TRIGger", "SLOPe:TUPPer", time)

    def set_trigger_slope_time_lower(self, time: float):
        """
        Sets the lower time limit for the trigger slope on the oscilloscope.

        Parameters:
            time (float): The lower time limit for the trigger slope, in seconds. Must be greater than or equal to 800 picoseconds (800e-12 s).

        Raises:
            AssertionError: If the provided time is less than 800 picoseconds.

        This method configures the oscilloscope to use the specified lower time limit for the trigger slope, ensuring precise triggering based on signal slope duration.
        """
        logger.debug(f"[MSO5000] set_trigger_slope_time_lower called with time={time}")
        assert time >= 800e-12, "Lower time limit must be greater than 800 ps."
        self.__set_parameter("TRIGger", "SLOPe:TLOWer", time)

    def set_trigger_slope_window(self, window: TriggerWindow):
        """
        Sets the trigger slope window of the oscilloscope.

        Args:
            window (TriggerWindow): The trigger slope window to set. Must be a value from the TriggerWindow enum.

        Raises:
            AssertionError: If the provided window is not a valid TriggerWindow enum value.

        This method configures the oscilloscope to use the specified trigger slope window by sending the appropriate command.
        """
        logger.debug(f"[MSO5000] set_trigger_slope_window called with window={window}")
        assert (
            window in TriggerWindow
        ), "Trigger window must be one of the TriggerWindow enum values."
        self.__set_parameter("TRIGger", "SLOPe:WINDow", window.value)

    def set_trigger_slope_amplitude_upper(self, amplitude: float):
        """
        Sets the upper amplitude limit for the trigger slope on the oscilloscope.

        Args:
            amplitude (float): The upper amplitude threshold to set for the trigger slope.

        Raises:
            ValueError: If the provided amplitude is out of the valid range for the oscilloscope.
        """
        logger.debug(f"[MSO5000] set_trigger_slope_amplitude_upper called with amplitude={amplitude}")
        self.__set_parameter("TRIGger", "SLOPe:ALEVel", amplitude)

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
        logger.debug(f"[MSO5000] set_trigger_slope_amplitude_lower called with amplitude={amplitude}")
        self.__set_parameter("TRIGger", "SLOPe:BLEVel", amplitude)

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
            coupling (TriggerCoupling, optional): The trigger coupling mode (e.g., DC, AC).
            sweep (TriggerSweep, optional): The trigger sweep mode (e.g., Auto, Normal).
            holdoff (float, optional): The trigger holdoff time in seconds.
            nreject (bool, optional): Whether to enable noise rejection.
            source (TriggerSource, optional): The trigger source channel.
            when (TriggerWhen, optional): The trigger condition (e.g., Greater, Less).
            time_upper (float, optional): The upper time threshold for the slope trigger in seconds.
            time_lower (float, optional): The lower time threshold for the slope trigger in seconds.
            window (TriggerWindow, optional): The trigger window type.
            amplitude_upper (float, optional): The upper amplitude threshold for the slope trigger.
            amplitude_lower (float, optional): The lower amplitude threshold for the slope trigger.

        Sets the oscilloscope to slope trigger mode and applies the specified trigger parameters.
        """
        logger.debug(f"[MSO5000] trigger_slope called with coupling={coupling}, sweep={sweep}, holdoff={holdoff}, nreject={nreject}, source={source}, when={when}, time_upper={time_upper}, time_lower={time_lower}, window={window}, amplitude_upper={amplitude_upper}, amplitude_lower={amplitude_lower}")
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
        logger.debug(f"[MSO5000] set_trigger_timeout_source called with source={source}")
        assert (
            source is not TriggerSource.AcLine
        ), "Trigger source cannot be ACLine."
        self.__set_parameter("TRIGger", "TIMeout:SOURce", source.value)

    def set_trigger_timeout_slope(self, slope: TriggerSlope):
        """
        Sets the trigger timeout slope for the device.

        Args:
            slope (TriggerSlope): The desired trigger slope. Must be a member of the TriggerSlope enum.

        Raises:
            AssertionError: If the provided slope is not a valid TriggerSlope enum value.

        """
        logger.debug(f"[MSO5000] set_trigger_timeout_slope called with slope={slope}")
        assert (
            slope in TriggerSlope
        ), "Trigger slope must be one of the TriggerSlope enum values."
        self.__set_parameter("TRIGger", "TIMeout:SLOPe", slope.value)

    def set_trigger_timeout_time(self, time: float):
        """
        Sets the trigger timeout time for the device.

        The trigger timeout time determines how long the device waits for a trigger event before timing out.

        Args:
            time (float): The timeout duration in seconds. Must be between 16 nanoseconds (16e-9) and 10 seconds.

        Raises:
            AssertionError: If the provided time is not within the valid range [16e-9, 10].
        """
        logger.debug(f"[MSO5000] set_trigger_timeout_time called with time={time}")
        assert (
            time >= 16e-9 and time <= 10
        ), "Trigger time must be between 16ns and 10s."
        self.__set_parameter("TRIGger", "TIMeout:TIME", time)

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
        logger.debug(f"[MSO5000] set_trigger_timeout_level called with level={level}")
        assert (
            level >= -15 and level <= 15
        ), "Trigger level must be between -15V and 15V."
        self.__set_parameter("TRIGger", "TIMeout:LEVel", level)

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
        logger.debug(f"[MSO5000] trigger_timeout called with coupling={coupling}, sweep={sweep}, holdoff={holdoff}, nreject={nreject}, source={source}, slope={slope}, time={time}, level={level}")
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
        logger.debug(f"[MSO5000] set_waveform_source called with source={source}")
        assert (
            source in Source
        ), "Waveform source must be one of the WaveformSource enum values."
        self.__set_parameter("WAVeform", "SOURce", source.value)

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
        logger.debug(f"[MSO5000] set_waveform_mode called with mode={mode}")
        assert (
            mode in WaveformMode
        ), "Waveform mode must be one of the WaveformMode enum values."
        self.__set_parameter("WAVeform", "MODE", mode.value)

    def set_waveform_format(self, format_: WaveformFormat):
        """
        Sets the waveform data format for the device.

        Args:
            format_ (WaveformFormat): The desired waveform format, must be a member of the WaveformFormat enum.

        Raises:
            AssertionError: If the provided format_ is not a valid WaveformFormat enum value.

        """
        logger.debug(f"[MSO5000] set_waveform_format called with format_={format_}")
        assert (
            format_ in WaveformFormat
        ), "Waveform format must be one of the WaveformFormat enum values."
        self.__set_parameter("WAVeform", "FORMat", format_.value)

    def set_waveform_points(self, points: int):
        """
        Sets the number of waveform points for the device.

        Args:
            points (int): The number of points to set for the waveform. Must be greater than or equal to 1.

        Raises:
            AssertionError: If points is less than 1.
        """
        logger.debug(f"[MSO5000] set_waveform_points called with points={points}")
        assert points >= 1, "Waveform points must be greater than 1."
        self.__set_parameter("WAVeform", "POINts", points)

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
        logger.debug(f"[MSO5000] get_waveform called with source={source}, format_={format_}, mode={mode}, start={start}, stop={stop}")
        assert start >= 1, "Waveform start must be greater than 1."
        assert stop > start, "Waveform stop must be greater than start."
        self.set_waveform_source(source)
        self.set_waveform_mode(mode)
        self.set_waveform_format(format_)
        _start = start
        _stop = min(start + 100, stop)
        _data = [0] * (stop - start + 1)
        while _start < stop:
            logger.debug(f"[MSO5000] Reading waveform chunk: start={_start}, stop={_stop}")
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
        logger.debug(f"[MSO5000] get_waveform finished, returning {len(_data)} points")
        return _data

    def get_waveform_xincrement(self) -> float:
        """
        Retrieves the horizontal (X-axis) increment value of the current waveform.

        Returns:
            float: The time interval between consecutive data points in the waveform.
        """
        logger.debug(f"[MSO5000] get_waveform_xincrement called")
        return self.__get_parameter("WAVeform", "XINCrement")

    def get_waveform_xorigin(self) -> float:
        """
        Retrieves the X origin value of the current waveform.

        Returns:
            float: The X origin of the waveform, typically representing the starting point on the X-axis (time axis) in waveform data.
        """
        logger.debug(f"[MSO5000] get_waveform_xorigin called")
        return self.__get_parameter("WAVeform", "XORigin")

    def get_waveform_xreference(self) -> float:
        """
        Retrieves the X reference value of the current waveform.

        Returns:
            float: The X reference value of the waveform, typically representing the horizontal offset or reference point on the X-axis.
        """
        logger.debug(f"[MSO5000] get_waveform_xreference called")
        return self.__get_parameter("WAVeform", "XREFerence")

    def get_waveform_yincrement(self) -> float:
        """
        Retrieves the vertical increment (Y-axis increment) value of the current waveform.

        Returns:
            float: The Y increment value, representing the voltage difference between adjacent data points in the waveform.
        """
        logger.debug(f"[MSO5000] get_waveform_yincrement called")
        return self.__get_parameter("WAVeform", "YINCrement")

    def get_waveform_yorigin(self) -> float:
        """
        Gets the Y origin value of the current waveform.

        Returns:
            float: The Y origin of the waveform as a floating-point number.
        """
        logger.debug(f"[MSO5000] get_waveform_yorigin called")
        return self.__get_parameter("WAVeform", "YORigin")

    def get_waveform_yreference(self) -> float:
        """
        Retrieves the Y reference value of the current waveform.

        Returns:
            float: The Y reference value used for scaling the waveform data.
        """
        logger.debug(f"[MSO5000] get_waveform_yreference called")
        return self.__get_parameter("WAVeform", "YREFerence")

    def set_waveform_start(self, start: int):
        """
        Sets the starting point for waveform data acquisition.

        Parameters:
            start (int): The starting index for the waveform data. Must be greater than or equal to 1.

        Raises:
            AssertionError: If 'start' is less than 1.
        """
        logger.debug(f"[MSO5000] set_waveform_start called with start={start}")
        assert start >= 1, "Waveform start must be greater than 1."
        self.__set_parameter("WAVeform", "STARt", start)

    def set_waveform_stop(self, stop: int):
        """
        Sets the stop point for waveform data acquisition.

        Parameters:
            stop (int): The index at which to stop waveform acquisition. Must be greater than or equal to 1.

        Raises:
            AssertionError: If 'stop' is less than 1.
        """
        logger.debug(f"[MSO5000] set_waveform_stop called with stop={stop}")
        assert stop >= 1, "Waveform stop must be greater than 1."
        self.__set_parameter("WAVeform", "STOP", stop)

    def get_waveform_preamble(self) -> str:
        """
        Retrieves the waveform preamble from the device.

        Returns:
            str: The waveform preamble as a string, typically containing information about the waveform format, such as scaling, offset, and other acquisition parameters.
        """
        logger.debug(f"[MSO5000] get_waveform_preamble called")
        return self.__get_parameter("WAVeform", "PREamble")
