# -*- coding: utf-8 -*-
from tester import (
    _member_logger,
    _get_class_logger,
    __application__,
    __company__,
    __version__,
)
from tester.devices.station import Station
from tester.tests.bearing_test import (
    BearingTestController,
    BearingTestModel,
    BearingTestView,
)
from tester.tests.torque_center_test import (
    TorqueCenterTestController,
    TorqueCenterTestModel,
    TorqueCenterTestView,
)
from datetime import datetime
from fpdf import FPDF
import getpass
import json
import logging
import logging.handlers
from pathlib import Path
from PIL import Image, ImageTk
import re
import socket
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog


class TesterModel:
    """
    Model class for the Automated Scanner Test application.
    This class is responsible for managing the data and logic of the application.
    """

    @_member_logger
    def __init__(self, directory: Path):
        """Initialize the Model with a name."""
        self.__logger = _get_class_logger(self.__class__)
        self.__data = {}
        self.__tests = []
        self.__station = Station()
        self.__directory = directory
        self.__directory.mkdir(parents=True, exist_ok=True)

    def __getattr__(self, name):
        try:
            if not name.startswith("_"):
                return self.__data[name]
        except KeyError:
            raise AttributeError

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self.__data[name] = value

    @_member_logger
    def _data_directory(self) -> Path:
        try:
            _dir = (
                self.__directory
                / self.SerialNumber
                / self.StartTime.strftime("%Y%m%d_%H%M%S")
            )
            _dir.mkdir(parents=True, exist_ok=True)
            return _dir
        except:
            return self.__directory

    @_member_logger
    def _json_path(self) -> Path:
        return self._data_directory() / "data.json"


    @_member_logger
    def _report_path(self) -> Path:
        return self._data_directory() / "report.pdf"

    @_member_logger
    def _get_station(self) -> Station:
        return self.__station

    @_member_logger
    def add_test(self, test_model):
        self.__tests.append(test_model)

    @_member_logger
    def on_open(self, path: str):
        with open(path, "r") as _file:
            _data = json.load(_file)
            for _key, _value in _data:
                if _key == "Tests":
                    for _test in self.__tests:
                        if _test.Name in _value:
                            _test.load_data(_value[_test.Name])
                else:
                    self.__data[_key] = _value

    @_member_logger
    def on_save(self, path: str = None):
        _data = self.__data
        _test_data = {}
        for _test in self.__tests:
            _test_data[_test.Name] = _test.get_data()
        _data["Tests"] = _test_data
        if path is None:
            _path = self._json_path()
        else:
            _path = path
        def _json_serial(object):
            if isinstance(object, datetime):
                return object.isoformat()
            raise TypeError(f"Type {type(object)} not serializable")
        with open(_path, "w") as _file:
            json.dump(_data, _file, indent=4, default=_json_serial)

    @_member_logger
    def on_generate_report(self, path: str = None):  
           _pdf = FPDF()  
           _pdf.set_auto_page_break(auto=True, margin=15)  
           _pdf.add_page()  
           _pdf.set_font("Helvetica", size=12)  

           # Add logo  
           logo_path = "./asset/logo.png"  
           _pdf.image(logo_path, x=10, y=8, w=30)  
           _pdf.ln(20)  

           # Add title  
           _pdf.set_font("Helvetica", style="B", size=16)  
           _pdf.cell(400, 10, txt="Automated Scanner Test Report", ln=True, align="C")  
           _pdf.ln(10)  

           # Add metadata  
           _pdf.set_font("Helvetica", size=12)  
           _pdf.cell(400, 10, txt=f"Serial Number: {self.SerialNumber}", ln=True)  
           _pdf.cell(400, 10, txt=f"Date: {self.StartTime.strftime('%Y-%m-%d')}", ln=True)  
           _pdf.cell(  
               400,  
               10,  
               txt=f"Start Time: {self.StartTime.strftime('%H:%M:%S')}",  
               ln=True,  
           )  
           _pdf.cell(  
               400,  
               10,  
               txt=f"End Time: {self.EndTime.strftime('%H:%M:%S')}",  
               ln=True,  
           )  
           _pdf.cell(400, 10, txt=f"Duration: {self.Duration} ms", ln=True)  
           if self.Status:  
               _pdf.cell(400, 10, txt="Status: Pass", ln=True)  
           else:  
               _pdf.cell(400, 10, txt="Status: Fail", ln=True)  
           _pdf.ln(10)  

           for _test in self.__tests:  
               _test.append_report(_pdf)  

           # Save PDF  
           if path is None:  
               _path = self._report_path()
           else:  
               _path = path  
           _pdf.output(_path)  
           self.__logger.info(f"PDF report generated: {_path}")


class TesterView:

    @property
    def ComputerName(self):
        return self.__computer_name.get()

    @ComputerName.setter
    def ComputerName(self, computer_name):
        """Set the name of the computer."""
        self.__computer_name.set(computer_name)

    @property
    def Duration(self):
        return self.__duration.get()

    @Duration.setter
    def Duration(self, duration):
        try:
            self.__duration.set(str(duration))
        except:
            self.__duration.set("")

    @property
    def EndTime(self) -> str:
        return self.__end_time.get()

    @EndTime.setter
    def EndTime(self, end_time):
        try:
            self.__end_time.set(end_time.strftime("%m/%d/%Y %H:%M:%S"))
        except:
            self.__end_time.set("")

    @property
    def SerialNumber(self):
        """Return the serial number of the device."""
        return self.__serial_number.get()

    @SerialNumber.setter
    def SerialNumber(self, serial_number):
        """Set the serial number of the device."""
        self.__serial_number.set(serial_number)

    @property
    def StartTime(self):
        return self.__start_time.get()

    @StartTime.setter
    def StartTime(self, start_time):
        try:
            self.__start_time.set(start_time.strftime("%m/%d/%Y %H:%M:%S"))
        except:
            self.__start_time.set("")

    @property
    def Status(self):
        return self.__status.get()

    @Status.setter
    def Status(self, status):
        if status is None:
            self.__status.set("Pending")
        if status:
            self.__status.set("Pass")
        else:
            self.__status.set("Fail")

    @property
    def Subtitle(self):
        """Return the subtitle of the window"""
        return self.__subtitle.get()

    @Subtitle.setter
    def Subtitle(self, subtitle):
        self.__subtitle.set(subtitle)

    @property
    def Title(self):
        """Return the title of the window."""
        return self.__title.get()

    @Title.setter
    def Title(self, title):
        """Set the title of the main window."""
        self.__master.title(title)
        self.__title.set(title)

    @property
    def Username(self):
        """Return the name of the user."""
        return self.__user_name.get()

    @Username.setter
    def Username(self, username):
        """Set the name of the user."""
        self.__user_name.set(username)

    @_member_logger
    def __init__(self, master):
        super().__init__()
        self.__logger = _get_class_logger(self.__class__)
        self.__tests = []
        self.__follow = True
        self.__master = master

        # Create string variables
        self.__computer_name = tk.StringVar(master)
        self.__date_time = tk.StringVar(master)
        self.__duration = tk.StringVar(master)
        self.__end_time = tk.StringVar(master)
        self.__serial_number = tk.StringVar(master)
        self.__start_time = tk.StringVar(master)
        self.__status = tk.StringVar(master)
        self.__subtitle = tk.StringVar(master)
        self.__title = tk.StringVar(master)
        self.__user_name = tk.StringVar(master)

        # Set up the application window
        self.__logger.debug("Initializing the main application window")
        master.iconbitmap("asset/Pangolin.ico")
        master.geometry("800x600")  # Default size of the window
        master.minsize(800, 600)
        master.resizable(True, True)  # Allow resizing in both directions
        master.configure(bg="white")
        master.protocol("WM_DELETE_WINDOW", master.quit)

        # Set up the style
        _style = ttk.Style(master)
        _bgt = (173, 216, 230, 255)
        _bgh = f"#{_bgt[0]:02x}{_bgt[1]:02x}{_bgt[2]:02x}"
        _style.configure("TopFrame.TFrame", background=_bgh)
        _style.configure("TopFrame.TLabel", background=_bgh, font=("Helvetica", 8))

        # Create a menu bar
        self.__menu_bar = tk.Menu(master)
        master.config(menu=self.__menu_bar)

        # Add File menu
        self.__file_menu = tk.Menu(self.__menu_bar, tearoff=0)
        self.__file_menu.add_command(
            label="Open", state="disabled", command=self.on_open
        )
        self.__file_menu.add_command(
            label="Save", state="disabled", command=self.on_save
        )
        self.__file_menu.add_separator()
        self.__file_menu.add_command(label="Exit", command=master.quit)
        self.__menu_bar.add_cascade(label="File", menu=self.__file_menu)

        # Add Test menu
        self.__test_menu = tk.Menu(self.__menu_bar, tearoff=0)
        self.__test_menu.add_command(label="Start Test", command=self.on_start_test)
        self.__test_menu.add_command(
            label="Stop Test", state="disabled", command=self.on_stop_test
        )
        self.__test_menu.add_separator()
        self.__test_menu.add_command(
            label="Generate Report", state="disabled", command=self.on_generate_report
        )
        self.__menu_bar.add_cascade(label="Test", menu=self.__test_menu)

        # Add Help menu
        self.__help_menu = tk.Menu(self.__menu_bar, tearoff=0)
        self.__help_menu.add_command(label="About", command=self.on_about)
        self.__menu_bar.add_cascade(label="Help", menu=self.__help_menu)

        # Add top frame with light blue background
        _top_frame = ttk.Frame(master, height=60)
        _top_frame.pack(side=tk.TOP, fill=tk.X)
        _top_frame.configure(style="TopFrame.TFrame")

        # Add logo image to the left of the title frame
        _logo_image = Image.open("./asset/logo.png")
        _new_image = Image.new("RGBA", _logo_image.size, _bgt)
        _new_image.paste(_logo_image, (0, 0), _logo_image)
        _photo = ImageTk.PhotoImage(_new_image)
        _image_label = ttk.Label(_top_frame, image=_photo)
        _image_label.pack(side=tk.LEFT, padx=5)

        # Add computer info to the right of the frame
        _comp_info = ttk.Frame(_top_frame, width=200)
        _comp_info.pack(side=tk.RIGHT, padx=5)
        _comp_info.configure(style="TopFrame.TFrame")
        _comp_label = ttk.Label(_comp_info, textvariable=self.__computer_name)
        _comp_label.pack(side=tk.TOP, anchor=tk.E)
        _comp_label.configure(style="TopFrame.TLabel")
        _user_label = ttk.Label(_comp_info, textvariable=self.__user_name)
        _user_label.pack(side=tk.TOP, anchor=tk.E)
        _user_label.configure(style="TopFrame.TLabel")
        _date_label = ttk.Label(_comp_info, textvariable=self.__date_time)
        _date_label.pack(side=tk.TOP, anchor=tk.E)
        _date_label.configure(style="TopFrame.TLabel")

        # Add titles to the center of the top frame
        _title_frame = ttk.Frame(_top_frame)
        _title_frame.pack(side=tk.LEFT, expand=True)
        _title_frame.configure(style="TopFrame.TFrame")
        _title_label = ttk.Label(_title_frame, textvariable=self.__title)
        _title_label.pack(side=tk.TOP, expand=True)
        _title_label.configure(style="TopFrame.TLabel")
        _title_label["font"] = ("Helvetica", 18)
        _title_label["justify"] = "center"
        _subtitle = ttk.Label(_title_frame, textvariable=self.__subtitle)
        _subtitle.pack(side=tk.TOP, expand=True)
        _subtitle.configure(style="TopFrame.TLabel")
        _subtitle["font"] = ("Helvetica", 14)
        _subtitle["justify"] = "center"

        # Add a status bar at the bottom of the window filled in by the logger
        _status_bar = ttk.Label(
            master,
            text="Status: Ready",
            relief=tk.SUNKEN,
            anchor=tk.W,
        )
        _status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        class StatusBarHandler(logging.Handler):
            def __init__(self, status_bar):
                super().__init__()
                self.status_bar = status_bar

            def emit(self, record):
                log_entry = self.format(record)
                self.status_bar.config(text=f"Status: {log_entry}")

        _status_bar_handler = StatusBarHandler(_status_bar)
        _status_bar_handler.setLevel(logging.INFO)
        logging.root.addHandler(_status_bar_handler)

        # Add test status bar
        _test_info_frame = ttk.Frame(master)
        _test_info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        _serial_number_textbox = ttk.Entry(
            _test_info_frame, textvariable=self.__serial_number, width=20
        )
        _serial_number_textbox.pack(side=tk.LEFT, expand=True, padx=5, pady=5)
        _start_time_textbox = ttk.Entry(
            _test_info_frame, textvariable=self.__start_time, width=20
        )
        _start_time_textbox.pack(side=tk.LEFT, expand=True, padx=5, pady=5)
        _end_time_textbox = ttk.Entry(
            _test_info_frame, textvariable=self.__end_time, width=20
        )
        _end_time_textbox.pack(side=tk.LEFT, expand=True, padx=5, pady=5)
        _duration_textbox = ttk.Entry(
            _test_info_frame, textvariable=self.__duration, width=20
        )
        _duration_textbox.pack(side=tk.LEFT, expand=True, padx=5, pady=5)

        # Assign all the variables
        self.Title = __application__
        self.Subtitle = "Initializing"
        self.ComputerName = socket.gethostname()
        self.Username = getpass.getuser()
        self.__logger.info("Application GUI initialized")
        self.update_time()

        # Add a left frame for the test sequence control
        _left_frame = ttk.Frame(master, width=300)
        _left_frame.pack(side=tk.LEFT, fill=tk.Y)
        _left_frame.pack_propagate(False)

        self.__test_list = ttk.Treeview(
            _left_frame, columns=("TestName", "Status"), show="headings"
        )
        self.__test_list.heading("TestName", text="Test Name")
        self.__test_list.heading("Status", text="Status")
        self.__test_list.column("TestName", width=225)
        self.__test_list.column("Status", width=75)
        self.__test_list.pack(fill=tk.BOTH, expand=True)

        self.__test_views = ttk.Notebook(master)
        self.__test_views.pack(side="top", fill="both", expand=True)

    def update_time(self):
        """Update the date and time label."""
        self.__date_time.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.__master.after(1000, self.update_time)

    @_member_logger
    def set_controller(self, controller):
        """Set the controller for the view."""
        self.__controller = controller

    @_member_logger
    def add_test(self, test_view):
        self.__tests.append(test_view)
        test_view.configure_gui(self.__test_views)
        self.__test_list.insert("", "end", values=(test_view.Name, test_view.Status))

    @_member_logger
    def on_open(self):
        """Handle the Open menu action."""
        self.__logger.info("Open menu clicked")
        _path = filedialog.askopenfilename(
            title="Test data log", filetypes=(("Json data file", "*.json"))
        )
        self.__controller.on_open(_path)

    @_member_logger
    def on_save(self):
        """Handle the Save menu action."""
        self.__logger.info("Save menu clicked")
        _path = filedialog.asksaveasfilename(
            title="Test data log", filetypes=(("Json data file", "*.json"))
        )
        self.__controller.on_save(_path)

    @_member_logger
    def on_start_test(self):
        """Handle the Start Test menu action."""
        self.__logger.info("Start Test menu clicked")
        _serial_number = simpledialog.askstring(
            "Input", "Enter galvo serial number (q to quit):"
        )
        if not re.match(r"^[A-Z]{2}[0-9]{6}$", _serial_number):
            self.__logger.error("Invalid serial number format.")
        self.__test_menu.entryconfig("Start Test", state="disabled")
        self.__test_menu.entryconfig("Stop Test", state="normal")
        self.__controller.on_start_test(_serial_number)

    @_member_logger
    def on_stop_test(self):
        """Handle the Stop Test menu action."""
        self.__logger.info("Stop Test menu clicked")
        self.__controller.on_stop_test()

    @_member_logger
    def on_generate_report(self):
        """Handle the Generate Report menu action."""
        self.__logger.info("Generate Report menu clicked")
        _path = filedialog.asksaveasfilename(
            title="Save file name", filetypes=(("Adobe PDF", "*.pdf"))
        )
        self.__controller.on_generate_report(_path)

    @_member_logger
    def on_about(self):
        """Handle the About menu action."""
        self.__logger.info("About menu clicked")
        tk.messagebox.showinfo(
            "About",
            f"{__application__}\nVersion {__version__}\nDeveloped by {__company__}",
        )

    @_member_logger
    def test_finished(self, status):
        self.__logger.info(f"All tests are complete with status {status}")
        self.__test_menu.entryconfig("Start Test", state="normal")
        self.__test_menu.entryconfig("Stop Test", state="disabled")
        self.__test_menu.entryconfig("Generate Report", state="normal")
        self.Status = status


class TesterController:
    """
    The Controller class is responsible for managing the flow of the application.
    It coordinates between the model, view, and other components to ensure smooth operation.
    """

    @_member_logger
    def __init__(self, model, view):
        """Initializes the Controller instance."""
        self.__logger = _get_class_logger(self.__class__)
        self.__logger.debug("Tester controller initializing.")
        self.__model = model
        self.__view = view
        self.__tests = []
        self.Name = __application__
        self.add_test(BearingTestController)
        self.add_test(TorqueCenterTestController)

    def __getattr__(self, name):
        if not name.startswith("_"):
            return getattr(self.__model, name)

    def __setattr__(self, name, value):
        if not name.startswith("_"):
            setattr(self.__model, name, value)
            setattr(self.__view, name, value)
        else:
            super().__setattr__(name, value)

    @_member_logger
    def add_test(self, test_class):
        """Adds a test to the list of tests."""
        _controller = test_class()
        self.__model.add_test(_controller._model)
        self.__view.add_test(_controller._view)
        self.__tests.append(_controller)

    @_member_logger
    def on_open(self, path: str):
        self.__model.on_open(path)

    @_member_logger
    def on_save(self, path: str):
        self.__model.on_save(path=path)

    @_member_logger
    def on_start_test(self, target: str):
        self.SerialNumber = target
        self.StartTime = datetime.now()
        self.EndTime = None
        self.Duration = None
        self.Status = None
        _data_directory = self.__model._data_directory()
        _station = self.__model._get_station()
        for _test in self.__tests:
            _test.set_data_directory(_data_directory)
            _test.execute(_station, target)
        self.EndTime = datetime.now()
        self.Duration = (self.EndTime - self.StartTime).total_seconds()
        self.Status = all([test.Status for test in self.__tests])
        self.__view.test_finished(self.Status)
        self.__model.on_save()
        self.__model.on_generate_report()

    @_member_logger
    def on_stop_test(self):
        pass

    @_member_logger
    def on_generate_report(self, path: str):
        self.__model.on_generate_report(self, path)
