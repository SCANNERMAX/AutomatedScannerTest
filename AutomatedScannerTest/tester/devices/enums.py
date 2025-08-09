from enum import StrEnum


class Source(StrEnum):
    """
    Enumeration of possible signal sources for the MSO5000 device.

    Members:
        D0-D15: Digital channels 0 through 15.
        Channel1-Channel4: Analog channels 1 through 4.
        Math1-Math4: Math function channels 1 through 4.
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
    Enumeration of memory depth settings for waveform acquisition.

    Members:
        Auto: Automatic memory depth selection.
        _1K, _10K, _100K, _1M, _10M, _25M, _50M, _100M, _200M: Fixed memory depth values.
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
    Enumeration of acquisition types for waveform data.

    Members:
        Normal: Standard acquisition.
        Averages: Averaged acquisition.
        Peak: Peak detection.
        HighResolution: High resolution acquisition.
    """
    Normal = "NORM"
    Averages = "AVER"
    Peak = "PEAK"
    HighResolution = "HRES"

class BandwidthLimit(StrEnum):
    """
    Enumeration of bandwidth limit settings for input channels.

    Members:
        Off: No bandwidth limit.
        Auto: Automatic bandwidth limit.
        _20M, _100M, _200M: Fixed bandwidth limits.
    """
    Off = "OFF"
    Auto = "AUTO"
    _20M = "20M"
    _100M = "100M"
    _200M = "200M"

class Coupling(StrEnum):
    """
    Enumeration of coupling types for input channels.

    Members:
        AC: AC coupling.
        DC: DC coupling.
        Ground: Ground reference.
    """
    AC = "AC"
    DC = "DC"
    Ground = "GND"

class Units(StrEnum):
    """
    Enumeration of measurement units.

    Members:
        Voltage: Volts.
        Watt: Watts.
        Ampere: Amperes.
        Unknown: Unknown unit.
    """
    Voltage = "VOLT"
    Watt = "WATT"
    Ampere = "AMP"
    Unknown = "UNKN"

class MeasureItem(StrEnum):
    """
    Enumeration of measurement items.

    Members:
        Item1-Item10: Individual measurement items.
        All: All measurement items.
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
    Enumeration of supported measurement types.

    Members:
        VoltageMaximum, VoltageMinimum, VoltagePeakToPeak, etc.: Various voltage, timing, and pulse measurements.
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

class MeasureMode(StrEnum):
    """
    Enumeration of measurement modes.

    Members:
        Normal: Standard measurement mode.
        Precision: High precision measurement mode.
    """
    Normal = "NORMal"
    Precision = "PRECision"

class SaveCsvLength(StrEnum):
    """
    Enumeration of CSV save length options.

    Members:
        Display: Save data for displayed range.
        Maximum: Save maximum available data.
    """
    Display = "DISP"
    Maximum = "MAX"

class SaveCsvChannel(StrEnum):
    """
    Enumeration of CSV save channel options.

    Members:
        Channel1-Channel4: Analog channels.
        Pod1, Pod2: Digital pods.
    """
    Channel1 = "CHAN1"
    Channel2 = "CHAN2"
    Channel3 = "CHAN3"
    Channel4 = "CHAN4"
    Pod1 = "POD1"
    Pod2 = "POD2"

class ImageType(StrEnum):
    """
    Enumeration of supported image file types.

    Members:
        Bitmap: 24-bit BMP.
        Jpeg: JPEG format.
        Png: PNG format.
        Tiff: TIFF format.
    """
    Bitmap = "BMP24"
    Jpeg = "JPEG"
    Png = "PNG"
    Tiff = "TIFF"

class ImageColor(StrEnum):
    """
    Enumeration of image color modes.

    Members:
        Color: Color image.
        Gray: Grayscale image.
    """
    Color = "COL"
    Gray = "GRAY"

class SourceFunction(StrEnum):
    """
    Enumeration of source waveform functions.

    Members:
        Sinusoid, Square, Ramp, Pulse, Noise, etc.: Various waveform types.
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
    Enumeration of source types.

    Members:
        _None: No source type.
        Modulated: Modulated source.
        Sweep: Sweep source.
        Burst: Burst source.
    """
    _None = "NONE"
    Modulated = "MOD"
    Sweep = "SWE"
    Burst = "BUR"

class SourceModulation(StrEnum):
    """
    Enumeration of source modulation types.

    Members:
        AmplitudeModulation: AM.
        FrequencyModulation: FM.
        FrequencyShiftKey: FSK.
    """
    AmplitudeModulation = "AM"
    FrequencyModulation = "FM"
    FrequencyShiftKey = "FSK"

class SourceSweepType(StrEnum):
    """
    Enumeration of source sweep types.

    Members:
        Linear: Linear sweep.
        Log: Logarithmic sweep.
        Step: Step sweep.
    """
    Linear = "LIN"
    Log = "LOG"
    Step = "STEP"

class SourceBurstType(StrEnum):
    """
    Enumeration of source burst types.

    Members:
        Ncycle: Fixed number of cycles.
        Infinite: Infinite burst.
    """
    Ncycle = "NCYCL"
    Infinite = "INF"

class SourceOutputImpedance(StrEnum):
    """
    Enumeration of source output impedance options.

    Members:
        Omeg: High impedance.
        Fifty: 50 Ohm impedance.
    """
    Omeg = "OMEG"
    Fifty = "FIFT"

class TimebaseMode(StrEnum):
    """
    Enumeration of timebase modes.

    Members:
        Main: Main timebase.
        Xy: XY mode.
        Roll: Roll mode.
    """
    Main = "MAIN"
    Xy = "XY"
    Roll = "ROLL"

class HrefMode(StrEnum):
    """
    Enumeration of horizontal reference modes.

    Members:
        Center: Center reference.
        Lb: Left border.
        Rb: Right border.
        Trigger: Trigger position.
        User: User-defined reference.
    """
    Center = "CENT"
    Lb = "LB"
    Rb = "RB"
    Trigger = "TRIG"
    User = "USER"

class TriggerMode(StrEnum):
    """
    Enumeration of trigger modes.

    Members:
        Edge, Pulse, Slope, Video, Pattern, Duration, Timeout, Runt, Window, Delay, Setup, Nedge, RS232, IIC, SPI, CAN, Flexray, LIN, IIS, M1553:
        Various trigger types for analog and digital signals.
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
    Enumeration of trigger coupling types.

    Members:
        AC: AC coupling.
        DC: DC coupling.
        LfReject: Low frequency reject.
        HfReject: High frequency reject.
    """
    AC = "AC"
    DC = "DC"
    LfReject = "LFR"
    HfReject = "HFR"

class TriggerStatus(StrEnum):
    """
    Enumeration representing the possible trigger statuses for the device.

    Members:
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

    Members:
        Auto: Automatic sweep mode.
        Normal: Normal sweep mode.
        Single: Single sweep mode.
    """
    Auto = "AUTO"
    Normal = "NORM"
    Single = "SING"

class TriggerSource(StrEnum):
    """
    Enumeration of possible trigger sources for the MSO5000 device.

    Members:
        D0-D15: Digital channels 0 through 15.
        Channel1-Channel4: Analog channels 1 through 4.
        AcLine: AC line trigger source.
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

    Members:
        Positive: Trigger on a positive slope.
        Negative: Trigger on a negative slope.
        RFall: Trigger on a rapid falling edge.
    """
    Positive = "POS"
    Negative = "NEG"
    RFall = "RFAL"

class TriggerWhen(StrEnum):
    """
    Enumeration representing trigger conditions for a device.

    Members:
        Greater: Trigger when the value is greater than a specified threshold.
        Less: Trigger when the value is less than a specified threshold.
        Gless: Trigger when the value is greater or less than a specified threshold.
    """
    Greater = "GRE"
    Less = "LESS"
    Gless = "GLES"

class TriggerWindow(StrEnum):
    """
    Enumeration representing the available trigger windows for the device.

    Members:
        TA: Trigger window A.
        TB: Trigger window B.
        TAB: Trigger window A and B combined.
    """
    TA = "TA"
    TB = "TB"
    TAB = "TAB"

class WaveformMode(StrEnum):
    """
    Enumeration of available waveform acquisition modes for the device.

    Members:
        Normal: Standard acquisition mode.
        Maximum: Maximum rate or resolution.
        Raw: Raw, unprocessed waveform data.
    """
    Normal = "NORM"
    Maximum = "MAX"
    Raw = "RAW"

class WaveformFormat(StrEnum):
    """
    Enumeration of supported waveform data formats for the device.

    Members:
        Word: 16-bit word format.
        Byte: 8-bit byte format.
        Ascii: ASCII format.
    """
    Word = "WORD"
    Byte = "BYTE"
    Ascii = "ASC"

