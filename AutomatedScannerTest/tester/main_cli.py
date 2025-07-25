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
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s - %(message)s",
            stream=sys.stdout
        )

    app = TesterApp(sys.argv)
    ts = TestSequence()
    args = ts.get_command_line_parser(app)

    if args.isSet("list"):
        """
        Handle the 'list' command-line option.

        Prints the list of available tests and exits the application.
        """
        ts.print_test_list()
        sys.exit(0)

    if args.isSet("run"):
        """
        Handle the 'run' command-line option.

        Prompts the user for a valid serial number (up to three attempts) and starts the test sequence
        with the provided serial number, model, and test. Exits if the serial number is invalid.
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
        return

    if args.isSet("help"):
        """
        Handle the 'help' command-line option.

        Displays help information and exits the application.
        """
        args.showHelp()
        sys.exit(0)

if __name__ == "__main__":
    """
    Main execution block.

    Calls the main() function to start the CLI tester application.
    """
    main()