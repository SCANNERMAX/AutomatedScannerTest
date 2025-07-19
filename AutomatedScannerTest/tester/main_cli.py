# -*- coding: utf-8 -*-
import logging
import re
import sys

from tester.gui.gui import TesterApp
from tester.manager.test_sequence import TestSequence

# Pre-compile the serial number regex for efficiency
_SERIAL_RE = re.compile(r"^[A-Z]{2}[0-9]{6}$")
"""Regular expression to validate serial numbers in the format: two uppercase letters followed by six digits."""

def main():
    """
    Main entry point for the CLI tester application.

    This function configures logging to output INFO level messages to standard output, parses command-line arguments,
    and executes actions based on the provided options. It supports the following actions:
        - Listing available tests.
        - Running a test sequence (with serial number validation and user prompt).
        - Displaying help information.

    The function ensures that the serial number provided for a test sequence matches the required format (AA######).
    If the serial number is invalid, the user is prompted up to three times before the application exits.
    """
    # Configure logging only if not already configured
    if not logging.root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logging.root.addHandler(handler)
        logging.root.setLevel(logging.INFO)

    options = sys.argv  # Exclude script name
    options.append("-s")
    options.append("PS501861")
    options.append("-m")
    options.append("Saturn 5")
    options.append("-r")
    app = TesterApp(options)
    ts = TestSequence()
    args = ts.get_command_line_parser(app)

    if args.isSet("list"):
        """
        If the 'list' option is set, print the list of available tests and exit.
        """
        ts.print_test_list()
        sys.exit(0)

    if args.isSet("run"):
        """
        If the 'run' option is set, prompt for a valid serial number (up to three attempts),
        then start the test sequence with the provided serial number, model, and test.
        """
        logging.info("Running test sequence...")
        _serial_number = args.value("serial")
        for _attempt in range(3):
            if _serial_number and _SERIAL_RE.match(_serial_number):
                break
            if _attempt == 2:
                logging.error("Invalid serial number format. Exiting.")
                sys.exit(1)
            _serial_number = input(
                "Please enter the serial number for the test sequence (format: AA######): "
            ).strip()
        ts.on_start_test(
            _serial_number, model_name=args.value("model"), test=args.value("test")
        )
        logging.info("Test sequence completed.")
        return  # Early return to avoid unnecessary checks

    if args.isSet("help"):
        """
        If the 'help' option is set, display help information and exit.
        """
        args.showHelp()
        sys.exit(0)


if __name__ == "__main__":
    main()