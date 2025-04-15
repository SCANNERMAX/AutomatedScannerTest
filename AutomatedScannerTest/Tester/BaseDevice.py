class BaseDevice:
    """Base class for all devices"""
    _name: str = ""

    def __init__(self, name: str = ""):
        self._name = name

    @property
    def Name(self) -> str:
        return self._name

    def __str__(self):
        return f"Device: {self._name}"

    def __repr__(self):
        return f"Device(Name={self._name!r})"