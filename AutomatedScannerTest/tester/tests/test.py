# -*- coding: utf-8 -*-
from tester import _get_class_logger, _member_logger
from datetime import datetime
from fpdf import FPDF
from pathlib import Path
from PIL.Image import fromarray
import threading
import tkinter as tk
from tkinter import ttk


class TestModel:
    """Model used a base for all tests."""

    @_member_logger
    def __init__(self):
        """Initialize the test model with a name and directory."""
        self.__logger = _get_class_logger(self.__class__)
        self.__data = {}

    def __getattr__(self, name):
        if not name.startswith("_"):
            return self.__data.get(name, None)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self.__data[name] = value

    @_member_logger
    def get_attrs(self):
        return self.__data.items()

    @_member_logger
    def load_data(self, data):
        for _key, _value in data.items():
            self.__data[_key] = _value

    @_member_logger
    def get_data(self):
        return dict(self.__data)

    @_member_logger
    def setup_test(self, station, target):
        """Setup the test for the scanner model."""
        station.osc.reset()

    @_member_logger
    def run_test(self, station, target):
        """Run the test for the scanner model."""
        pass

    @_member_logger
    def analyze_results(self, target):
        """Analyze the results of the test."""
        pass

    @_member_logger
    def append_report(self, report: FPDF):
        """Append the report of the test."""
        report.add_page()

        # Add title
        report.set_font("Helvetica", style="B", size=16)
        report.cell(400, 10, txt=self.Name, ln=True, align="C")
        report.ln(10)


class TestView:
    """View used as a base for all tests."""

    @_member_logger
    def __init__(self):
        self.__logger = _get_class_logger(self.__class__)

    @_member_logger
    def configure_gui(self, parent):
        self.parent = ttk.Frame(parent)
        parent.add(self.parent, text=f" {self.Name} ")

    @_member_logger
    def set_controller(self, controller):
        self._controller = controller


class TestController:
    """Controller used as a base for all tests."""

    @_member_logger
    def __init__(self, model_class, view_class, name):
        self.__logger = _get_class_logger(self.__class__)
        self._model = model_class()
        self._view = view_class()
        self._view.set_controller(self)
        self.Name = name
        self.Status = "Initialized"

    def __getattr__(self, name):
        if not name.startswith("_"):
            return getattr(self._model, name)

    def __setattr__(self, name, value):
        if not name.startswith("_"):
            setattr(self._model, name, value)
            setattr(self._view, name, value)
        else:
            super().__setattr__(name, value)

    @_member_logger
    def set_data_directory(self, root_directory: Path):
        self._data_directory = root_directory / self.Name
        self._data_directory.mkdir(parents=True, exist_ok=True)
        self._model._data_directory = self._data_directory
        self._view._data_directory = self._data_directory

    @_member_logger
    def execute(self, station, target):
        """Execute the test for the scanner model."""

        # Initialize parameters and setup test
        self.StartTime = datetime.now()
        self.EndTime = None
        self.Duration = None
        self.Status = None
        self._model.setup_test(station, target)

        # Run test and analyze results
        self._model.run_test(station, target)
        self._model.analyze_results(target)
        for _attr, _value in self._model.get_attrs():
            setattr(self._view, _attr, _value)
        self.EndTime = datetime.now()
        self.Duration = (self.EndTime - self.StartTime).total_seconds()
        return self.Status
