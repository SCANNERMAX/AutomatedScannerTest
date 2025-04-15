import BaseDevice

class BaseStation():
    """Base class to define the equipment used to perform testing"""
    _devices = list()
    _name = None
    _stationType = None

    def __init__(self, stationType: str, name: str):
        self._stationType = stationType
        self._name = name

    @property
    def stationType(self) -> str:
        return self._stationType

    @stationType.setter
    def stationType(self, value: str):
        self._stationType = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    def addDevice(self, device: BaseDevice):
        self._devices.append(device)

    def getDevices(self):
        return self._devices

    def __str__(self):
        return self._name

    def __repr__(self):
        return self._name