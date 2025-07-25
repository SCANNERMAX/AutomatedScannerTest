# -*- coding: utf-8 -*-
import sys

from tester.gui.app import TesterApp
from tester.gui.gui import TesterWindow

def main():
    """
    Main entry point for the GUI tester application.

    Initializes the TesterApp with command-line arguments and creates the main TesterWindow.
    Starts the application event loop and exits with the returned exit code.

    Returns:
        int: The exit code from the application.
    """
    app = TesterApp(sys.argv)
    window = TesterWindow()
    window.start_application()
    sys.exit(app.exec())

if __name__ == "__main__":
    """
    If this module is run as the main program, execute the main function.
    """
    main()
