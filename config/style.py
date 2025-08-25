import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkFont

from click import style
from distro import name

## TODO
# Voir encore la couleur des bordures des boutons

themesel="clear"

theme = {}
theme['clear']={}
theme['clear']['bg_global'] = "#f0f0f0"
theme['clear']['bg_frame'] = "#f0f0f0"
theme['clear']['fg_frame'] = "black"
theme['clear']['bg_tab_nosel']="#d0d0d0"
theme['clear']['bg_tab_sel']="#f0f0f0"
theme['clear']['bg_field'] = "white"
theme['clear']['fg_field'] = "black"
theme['clear']['fg_global'] = "black"
theme['clear']['fg_recommended'] = "green"
theme['clear']['bg_button_files'] = "#ec9129"
theme['clear']['bg_button_remove'] = "#d9534f"
theme['clear']['bg_button_clear'] = "#6c757d"
theme['clear']['bg_button_detect'] = "#5bc0de"
theme['clear']['bg_button_output'] = "#5bc0de"
theme['clear']['bg_button_convert'] = "#1aa02c"
theme['clear']['bg_button_cancel'] = "#b43546"
theme['clear']['bg_button_close'] = "#6c757d"
theme['clear']['bd_color'] = "#6c757d"

theme['dark'] = {}
theme['dark']['bg_global'] = "#202020"
theme['dark']['bg_frame'] = "#202020"
theme['dark']['fg_frame'] = "white"
theme['dark']['bg_tab_nosel']="#333333"
theme['dark']['bg_tab_sel']="#444444"
theme['dark']['bg_field'] = "#474747"
theme['dark']['fg_field'] = "white"
theme['dark']['fg_global'] = "white"
theme['dark']['fg_recommended'] = "green"
theme['dark']['bg_button_files'] = "#ec9129"
theme['dark']['bg_button_remove'] = "#d9534f"
theme['dark']['bg_button_clear'] = "#6c757d"
theme['dark']['bg_button_detect'] = "#5bc0de"
theme['dark']['bg_button_output'] = "#5bc0de"
theme['dark']['bg_button_convert'] = "#1aa02c"
theme['dark']['bg_button_cancel'] = "#b43546"
theme['dark']['bg_button_close'] = "#6c757d"
theme['dark']['bd_color'] = "#6c757d"

bg_global = theme[themesel]['bg_global']
bg_frame = theme[themesel]['bg_frame']
fg_frame = theme[themesel]['fg_frame']
bg_tab = theme[themesel]['bg_tab_nosel']
bg_tab_sel = theme[themesel]['bg_tab_sel']
bg_field = theme[themesel]['bg_field']
fg_field = theme[themesel]['fg_field']
fg_global = theme[themesel]['fg_global']
fg_recommended = theme[themesel]['fg_recommended']
bg_button_files = theme[themesel]['bg_button_files']
bg_button_remove = theme[themesel]['bg_button_remove']
bg_button_clear = theme[themesel]['bg_button_clear']
bg_button_detect = theme[themesel]['bg_button_detect']
bg_button_output = theme[themesel]['bg_button_output']
bg_button_convert = theme[themesel]['bg_button_convert']
bg_button_cancel = theme[themesel]['bg_button_cancel']
bg_button_close = theme[themesel]['bg_button_close']
bd_color = theme[themesel]['bd_color']

def gen_tab(notebook, name):
  
        style = ttk.Style()
        style.theme_use("default")

        style.configure("TNotebook", background=bg_frame)
        style.configure("TNotebook.Tab",
                        background=theme[themesel]['bg_tab_nosel'],
                        foreground=theme[themesel]['fg_frame']
                        )
        style.map("TNotebook.Tab",
                background=[("selected", theme[themesel]['bg_tab_sel'])],
                foreground=[("selected", theme[themesel]['fg_frame'])])

        tab = ttk.Frame(notebook, style="TNotebook")
        notebook.add(tab, text=name)

        return tab  