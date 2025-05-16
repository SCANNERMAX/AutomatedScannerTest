# -*- coding: utf-8 -*-
from tester import _get_class_logger, _member_logger
from tester.tester import TesterModel, TesterView, TesterController
from datetime import datetime
import logging
import os
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk

# Set up the logger
_data_directory = Path("C:/") / "Test Data" / "Automated Scanner Test"
_data_directory.mkdir(parents=True, exist_ok=True)
logfile = _data_directory / ("log_" + datetime.today().strftime("%Y%m%d") + ".log")
handler = logging.handlers.RotatingFileHandler(
    logfile, maxBytes=(1048576 * 5), backupCount=7
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logging.root.addHandler(handler)
logging.root.setLevel(logging.DEBUG)


class App(tk.Tk):
    """Main application class that initializes the GUI and its components."""

    @_member_logger
    def __init__(self):
        """Initialize the main application window."""
        super().__init__()
        self.__logger = _get_class_logger(self.__class__)

        # create a model
        model = TesterModel(_data_directory)

        # create a view and place it on the root window
        view = TesterView(self)

        # create a controller
        controller = TesterController(model, view)

        # set the controller to view
        view.set_controller(controller)


if __name__ == "__main__":
    app = App()
    app.mainloop()