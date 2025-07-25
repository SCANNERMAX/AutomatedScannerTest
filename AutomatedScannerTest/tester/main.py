# -*- coding: utf-8 -*-
from tester.gui.app import TesterApp
from tester.gui.gui import TesterWindow
from tester.manager.test_sequence import TestSequenceModel

import sys

def main() -> int:
    """
    Main entry point for the GUI tester application.

    This function initializes the TesterApp with command-line arguments,
    creates the main TesterWindow, starts the application event loop,
    and returns the exit code from the application.

    Returns:
        int: The exit code from the application event loop.
    """
    app = TesterApp(sys.argv)
    if app.options.isSet("nogui"):
        ts = TestSequenceModel(app.settings)
        return ts.run_nogui()
    else:
        window = TesterWindow()
        window.show()
        return app.exec()

if __name__ == "__main__":
    """
    If this module is run as the main program, execute the main function
    and exit the process with the returned exit code.
    """
    sys.exit(main())
