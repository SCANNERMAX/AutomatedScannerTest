from Tester import UnitUnderTest


class ScannerUnderTest(UnitUnderTest):
    def __init__(self, name: str):
        super().__init__(name)

    def get_name(self):
        return "ScannerUnderTest"

    @property
    def Field(self):
        return self._characteristics["Field"]

    @Field.setter
    def Field(self, value: float):
        self._characteristics["Field"] = value