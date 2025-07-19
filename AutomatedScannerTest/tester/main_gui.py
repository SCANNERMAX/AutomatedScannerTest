# -*- coding: utf-8 -*-
import sys
from tester.gui.gui import TesterWindow, TesterApp

def main():
    """
    Entry point for the application.

    This function initializes the TesterApp with command-line arguments,
    creates and displays the main TesterWindow, and starts the application's event loop.

    Returns:
        int: The exit status code returned by the application's event loop.
    """
    app = TesterApp(sys.argv)
    window = TesterWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    """
    Main execution block.

    Exits the program with the status code returned by the main() function.
    """
    sys.exit(main())