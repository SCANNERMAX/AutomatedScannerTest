import os
import platform
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class MainWindow(tk.Tk):
   def __init__(self, name):
       super().__init__()
       self.name = name
       self.title(name)
       self.geometry("800x600")
       self.minsize(800, 600)
       self.iconbitmap("./asset/Pangolin.ico")
       self.create_widgets()

   def create_widgets(self):
       self.computer_name = platform.node()
       self.user_name = os.getlogin()

       self.title_frame = ttk.Frame(self)
       self.title_frame.pack(side=tk.TOP, fill=tk.X)

       self.image = Image.open("./asset/logo.png")
       self.image = self.image.resize((50, 50))
       self.photo = ImageTk.PhotoImage(self.image)
       self.image_label = ttk.Label(self.title_frame, image=self.photo)
       self.image_label.pack(side=tk.LEFT, padx=10)

       self.title_label = ttk.Label(self.title_frame)
       self.title_label["font"] = ("Helvetica", 18)
       self.title_label["justify"] = "center"
       self.title_label.pack(side=tk.LEFT, expand=True)
       self.set_subtitle("Initializing")
       
       self.status_bar = ttk.Label(self, relief=tk.SUNKEN, anchor=tk.W)
       self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
       self.set_status("Ready")
       
       self.left_frame = ttk.Frame(self, width=300)
       self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
       self.left_frame.pack_propagate(False)
       
       self.listbox = ttk.Treeview(self.left_frame, columns=("TestName", "PassFail"), show="headings")
       self.listbox.heading("TestName", text="Test Name")
       self.listbox.heading("PassFail", text="Pass/Fail")
       self.listbox.column("TestName", width=200)
       self.listbox.column("PassFail", width=100)
       self.listbox.pack(fill=tk.BOTH, expand=True)

       self.listbox.insert("", "end", values=("Bearing Test", "Pass"))

   def set_subtitle(self, subtitle: str):
       self.title_label["text"] = self.name + "\n" + subtitle

   def set_status(self, status: str):
       self.status_bar["text"] = "Status: " + status
              
if __name__ == "__main__":
    app = MainWindow("Automated Scanner Test")
    app.mainloop()