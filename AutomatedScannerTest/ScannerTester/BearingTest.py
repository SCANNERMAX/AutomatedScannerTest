import pathlib
from Tester import BaseTest
import ScannerTester.ScannerTestStation as ScannerTestStation

class BearingTest(BaseTest):
    def __init__(self):
        super().__init__()

    @property
    def MaximumSeparation(self) -> float:
        return self._parameters["MaximumSeparation"]

    @MaximumSeparation.setter
    def MaximumSeparation(self, value: float):
        self._parameters["MaximumSeparation"] = value

    @property
    def MinimumSeparation(self) -> float:
        return self._parameters["MinimumSeparation"]

    @MinimumSeparation.setter
    def MinimumSeparation(self, value: float):
        self._parameters["MinimumSeparation"] = value

    @property
    def MinimumSpikeAmplitude(self) -> float:
        return self._parameters["MinimumSpikeAmplitude"]

    @MinimumSpikeAmplitude.setter
    def MinimumSpikeAmplitude(self, value: float):
        self._parameters["MinimumSpikeAmplitude"] = value

    @property
    def MaximumSpikeAmplitude(self) -> float:
        return self._parameters["MaximumSpikeAmplitude"]

    @MaximumSpikeAmplitude.setter
    def MaximumSpikeAmplitude(self, value: float):
        self._parameters["MaximumSpikeAmplitude"] = value

    @property
    def MaximumSlopeMismatch(self) -> float:
        return self._parameters["MaximumSlopeMismatch"]

    @MaximumSlopeMismatch.setter
    def MaximumSlopeMismatch(self, value: float):
        self._parameters["MaximumSlopeMismatch"] = value

    @property
    def MaximumFrictionMismatch(self) -> float:
        return self._parameters["MaximumFrictionMismatch"]

    @MaximumFrictionMismatch.setter
    def MaximumFrictionMismatch(self, value: float):
        self._parameters["MaximumFrictionMismatch"] = value

    @property
    def FrictionPlot(self):
        return self._results["FrictionPlot"]

    @FrictionPlot.setter
    def FrictionPlot(self, value):
        self._results["FrictionPlot"] = value

    @property
    def PositiveSideSpikeMaximumAmplitude(self) -> float:
        return self._results["PositiveSideSpikeMaximumAmplitude"]

    @PositiveSideSpikeMaximumAmplitude.setter
    def PositiveSideSpikeMaximumAmplitude(self, value: float):
        self._results["PositiveSideSpikeMaximumAmplitude"] = value

    @property
    def NegativeSideSpikeMaximumAmplitude(self) -> float:
        return self._results["NegativeSideSpikeMaximumAmplitude"]

    @NegativeSideSpikeMaximumAmplitude.setter
    def NegativeSideSpikeMaximumAmplitude(self, value: float):
        self._results["NegativeSideSpikeMaximumAmplitude"] = value

    @property
    def SlopeMismatch(self) -> float:
        return self._results["SlopeMismatch"]

    @SlopeMismatch.setter
    def SlopeMismatch(self, value: float):
        self._results["SlopeMismatch"] = value

    @property
    def Separation(self) -> float:
        return self._results["Separation"]

    @Separation.setter
    def Separation(self, value: float):
        self._results["Separation"] = value

    @property
    def MaximumSpikeMismatch(self) -> float:
        return self._results["MaximumSpikeMismatch"]

    @MaximumSpikeMismatch.setter
    def MaximumSpikeMismatch(self, value: float):
        self._results["MaximumSpikeMismatch"] = value

    @property
    def PositiveSideSpikePass(self) -> bool:
        return self._results["PositiveSideSpikePass"]

    @PositiveSideSpikePass.setter
    def PositiveSideSpikePass(self, value: bool):
        self._results["PositiveSideSpikePass"] = value

    @property
    def NegativeSideSpikePass(self) -> bool:
        return self._results["NegativeSideSpikePass"]

    @NegativeSideSpikePass.setter
    def NegativeSideSpikePass(self, value: bool):
        self._results["NegativeSideSpikePass"] = value

    @property
    def SlopeMismatchPass(self) -> bool:
        return self._results["SlopeMismatchPass"]

    @SlopeMismatchPass.setter
    def SlopeMismatchPass(self, value: bool):
        self._results["SlopeMismatchPass"] = value

    @property
    def SeparationPass(self) -> bool:
        return self._results["SeparationPass"]

    @SeparationPass.setter
    def SeparationPass(self, value: bool):
        self._results["SeparationPass"] = value

    @property
    def MaximumSpikeMismatchPass(self) -> bool:
        return self._results["MaximumSpikeMismatchPass"]

    @MaximumSpikeMismatchPass.setter
    def MaximumSpikeMismatchPass(self, value: bool):
        self._results["MaximumSpikeMismatchPass"] = value

    @property
    def DataFile(self) -> str:
        pathlib.Path(self._parameters["DataFile"]).mkdir(parents=True, exist_ok=True)

    def run_test(self):
        super().run_test()
        self.Station.aquire_friction_plot()
        self.Station.generate_waveform("Triangle", 0.5, self.Target.Field, -90)
        self.Station.save_waveform(DataFile)

    def analyze_results(self):
        super().analyze_results()
