import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkFont

bg_global = "#f0f0f0"
bg_frame = "#f0f0f0"
bg_tab1="#f0f0f0"
bg_tab2="#f0f0f0"
bg_tab3="#f0f0f0"
bg_tab4="#f0f0f0"
bg_tab5="#f0f0f0"

bg_button_files = "orange"
bg_button_remove = "#d9534f"
bg_button_clear = "#6c757d"
bg_button_detect = "#5bc0de"
bg_button_output = "#5bc0de"
bg_button_convert = "green"
bg_button_cancel = "red"
bg_button_close = "#6c757d"

def gen_tab(notebook, name, bg_color):

    style = ttk.Style()
    style.theme_use("clam")

    # Personnaliser les onglets du Notebook
    style.configure("TNotebook", background=bg_frame)      # arrière-plan global
    style.configure("TNotebook.Tab", background=bg_color)  # onglets
    style.map("TNotebook.Tab",
            background=[("selected", "white")],           # couleur si sélectionné
            foreground=[("selected", "black")])
    
    tab = ttk.Frame(notebook, style="TNotebook")
    notebook.add(tab, text=name)

    return tab  