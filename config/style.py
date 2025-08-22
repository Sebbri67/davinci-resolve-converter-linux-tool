import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkFont

from click import style
from distro import name

bg_global = "#f0f0f0"
bg_frame = "#f0f0f0"
bg_tab1="#f8debd"
bg_tab2="#b3f0bd"
bg_tab3="#c9e1ff"
bg_tab4="#ffcef8"
bg_tab5="#f0f0f0"
bg_tab=bg_tab5

fg_global = "black"
fg_recommended = "green"

bg_button_files = "#ec9129"
bg_button_remove = "#d9534f"
bg_button_clear = "#6c757d"
bg_button_detect = "#5bc0de"
bg_button_output = "#5bc0de"
bg_button_convert = "#1aa02c"
bg_button_cancel = "#b43546"
bg_button_close = "#6c757d"

def gen_tab(notebook, name):
  
        style = ttk.Style()
        style.theme_use("default")

        style.configure("TNotebook", background=bg_frame)
        style.configure("TNotebook.Tab", background=bg_tab)
        style.map("TNotebook.Tab",
                background=[("selected", "white")],
                foreground=[("selected", "black")])

        tab = ttk.Frame(notebook, style="TNotebook")
        notebook.add(tab, text=name)

        return tab  