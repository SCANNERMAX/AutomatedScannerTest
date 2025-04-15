import platform
from Tester import BaseStation
import ScannerTester.mso5000 as mso5000
import ScannerTester.MachDSP as MachDSP

class ScannerTestStation(BaseStation):
    """Station for testing completed scanners"""
    _mso5000 = None
    _machDSP = None

    def __init__(self):
        """Initialize the station with a name and a scanner"""
        super(ScannerTestStation, self).__init__(
            "Scanner Test Station", platform.node()
        )
        self.AddDevice(mso5000())
        self.AddDevice(MachDSP())

