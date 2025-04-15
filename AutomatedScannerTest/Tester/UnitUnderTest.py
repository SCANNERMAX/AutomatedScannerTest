class UnitUnderTest():
    """The production product that is being tested."""
    _characteristics = dict()
    _name = None

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value