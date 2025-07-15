# -*- coding: utf-8 -*-
from tester.gui.gui import TesterWindow
from tester.gui.gui import TesterApp


def main():
    """
    Entry point for the application. Initializes the TesterApp with command-line arguments,
    creates and displays the main TesterWindow, and starts the application's event loop.
    """
    import sys

    app = TesterApp(sys.argv)
    window = TesterWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()