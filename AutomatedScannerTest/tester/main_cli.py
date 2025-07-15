# -*- coding: utf-8 -*-
import logging
import re
import sys

from tester.gui.gui import TesterApp
from tester.manager.test_sequence import TestSequence


def main():
    """
    Main entry point for the CLI tester application.
    Configures logging to output INFO level messages to standard output, parses command-line arguments,
    and executes actions based on the provided options. Supports listing available tests, running a test
    sequence (with serial number validation and user prompt), and displaying help information.
    Workflow:
    - Sets up logging.
    - Parses command-line arguments, adding default options for demonstration.
    - If 'list' option is set, prints available tests and exits.
    - If 'run' option is set, validates the serial number (prompting user if invalid), then starts the test sequence.
    - If 'help' option is set, displays help and exits.
    """
    # Send all info logging to standard output
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)

    options = sys.argv
    options.extend(["-r", "-s", "PS501861", "-m", "Saturn 5"])
    app = TesterApp(options)
    ts = TestSequence()
    args = ts.get_command_line_parser(app)
    if args.isSet("list"):
        ts.print_test_list()
        sys.exit(0)
    if args.isSet("run"):
        logging.info("Running test sequence...")
        _serial_number = args.value("serial")
        for _attempt in range(3):
            if re.match(r"^[A-Z]{2}[0-9]{6}$", _serial_number):
                break
            elif _attempt == 2:
                logging.exception("Invalid serial number format. Exiting.")
                sys.exit(1)
            else:
                _serial_number = input(
                    "Please enter the serial number for the test sequence: "
                ).strip()
        ts.on_start_test(
            _serial_number, model_name=args.value("model"), test=args.value("test")
        )
        logging.info("Test sequence completed.")
    if args.isSet("help"):
        args.showHelp()
        sys.exit(0)


if __name__ == "__main__":
    main()