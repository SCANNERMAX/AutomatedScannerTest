from Tester import UnitUnderTest
from Tester import BaseStation

class BaseTest():
    _parameters = dict()
    _results = dict()
    Station = None
    Target = None

    def __init__(self):
        self.setup_test()

    def setup_test(self, station: BaseStation, target: UnitUnderTest):
        """Setup the test for the station and scanner model."""
        self.Station = station
        self.Target = target
        self.load_parameters(target.get_name())
        station.initialize_for_test(target)

    def load_parameters(self, target_name: str):
        """Load the test parameters for the scanner model."""
        pass

    def run_test(self, station: BaseStation):
        """Run the test for the scanner model."""
        pass

    def analyze_results(self):
        """Analyze the results of the test."""
        pass

    def save_results(self):
        """Save the results of the test."""
        pass
