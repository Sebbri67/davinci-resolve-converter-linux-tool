import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkFont
import libs.libtools as libtools
import config.style as customstyle

def create_princ():
    root = tk.Tk()
    root.title("Convertisseur vidéo pour Davinci Resolve")
    root.geometry("900x600")
    root.configure(bg=customstyle.bg_global)

    bold_font = tkFont.Font(family="Helvetica", size=10, weight="bold")
    
    input_files = tk.Variable(value=[])
    output_dir = tk.StringVar()

    # Création des onglets
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # --- Cadre : Boutons de fermeture ---
    frame_princ = tk.LabelFrame(root, bg=customstyle.bg_frame, padx=10, pady=10)
    frame_princ.pack(pady=10, fill="x", padx=10)
    
    close_button = tk.Button(frame_princ, text="Fermer", command=lambda: close_app(root),
        width=20, bg=customstyle.bg_button_close, fg="white", state=tk.NORMAL)
    close_button.pack(side="right", padx=10)

    return root, notebook, input_files, output_dir, bold_font

def create_files_tab(notebook, input_files, output_dir):
    #### ONGLET FICHIERS

    file_tab = customstyle.gen_tab(notebook, "Fichiers")

    input_files = tk.Variable(value=[])

    # --- Cadre : Sélection des fichiers ---
    frame_files = tk.LabelFrame(file_tab, text=" Sélection des fichiers ", bg=customstyle.bg_frame, padx=10, pady=10)
    frame_files.pack(pady=10, fill="x", padx=10)

    frame_buttons = tk.Frame(frame_files, bg=customstyle.bg_global)
    frame_buttons.pack(fill="x")

    select_button = tk.Button(frame_buttons, text="Vidéos...", width=18,
        command=lambda: libtools.select_files(input_files, files_list), bg=customstyle.bg_button_files, fg="white")
    select_button.pack(side="left")

    remove_button = tk.Button(frame_buttons, text="Supprimer sélection", width=18,
        command=lambda: libtools.remove_selected(input_files, files_list), bg=customstyle.bg_button_remove, fg="white")
    remove_button.pack(side="left", padx=5)

    clear_button = tk.Button(frame_buttons, text="Tout effacer", width=14,
        command=lambda: libtools.clear_all(input_files, files_list), bg=customstyle.bg_button_clear, fg="white")
    clear_button.pack(side="left")

    # detect_button = tk.Button(frame_buttons, text="Détecter H.264/H.265", width=20,
    #     command=lambda: libtools.detect_and_convert_h264_h265(input_files, files_list, conversion_option),
    #     bg=customstyle.bg_button_detect, fg="black")
    # detect_button.pack(side="left", padx=5)

    frame_list = tk.Frame(frame_files, bg=customstyle.bg_global)
    frame_list.pack(fill="x", pady=5)
    scrollbar = tk.Scrollbar(frame_list, orient="vertical")
    scrollbar.pack(side="right", fill="y")
    files_list = tk.Listbox(frame_list, width=80, height=8, relief="flat", yscrollcommand=scrollbar.set)
    files_list.pack(side="left", fill="x", expand=True)
    scrollbar.config(command=files_list.yview)

    tk.Label(frame_files, text="Les fichiers H.264/H.265 sont marqués en rouge.", fg="red", bg=customstyle.bg_frame).pack()
    tk.Label(frame_files, text="ATTENTION : toutes les vidéos sélectionnées seront traitées avec le mème format de conversion sélectionné dans l'onglet Options.", fg=customstyle.fg_global, bg=customstyle.bg_frame).pack()
    tk.Label(frame_files, text="Choisir, donc, des vidéos qui ont le même format.", fg=customstyle.fg_global, bg=customstyle.bg_frame).pack()

    # --- Cadre : Répertoire de sortie ---
    frame_output = tk.LabelFrame(file_tab, text=" Répertoire de sortie ", bg=customstyle.bg_frame, padx=10, pady=10)
    frame_output.pack(pady=10, fill="x", padx=10)

    output_dir = tk.StringVar()
    output_dir.set(libtools.load_param("dest_dir", default=""))

    output_button = tk.Button(frame_output, text="Destination...", width=20,
                              command=lambda: libtools.select_output_dir(output_dir), bg=customstyle.bg_button_output, fg="white")
    output_button.pack(side="left")

    tk.Entry(frame_output, textvariable=output_dir, width=40, relief="flat").pack(side="left", padx=5)

    return files_list, input_files, select_button, remove_button, clear_button, output_button, output_dir

def create_options_tab(notebook, bold_font):
    cuda_available = libtools.check_cuda()

    #### ONGLET OPTIONS
    option_tab = customstyle.gen_tab(notebook, "Options")

    # --- Cadre : Options de conversion ---
    frame_mode = tk.LabelFrame(option_tab, text=" Options de conversion ", bg=customstyle.bg_frame, padx=10, pady=10)
    frame_mode.pack(pady=10, fill="x", padx=10)

    # Frame pour les options Davinci Resolve (à gauche)
    frame_davinci_in = tk.Frame(frame_mode, bg=customstyle.bg_frame)
    frame_davinci_in.pack(side="left", padx=10, fill="y")

    # Frame pour les options de sortie de Davinci Resolve (au centre)
    frame_davinci_out = tk.Frame(frame_mode, bg=customstyle.bg_frame)
    frame_davinci_out.pack(side="left", padx=10, fill="y")

    # Frame pour les autres options (à droite)
    frame_other = tk.Frame(frame_mode, bg=customstyle.bg_frame)
    frame_other.pack(side="right", padx=10, fill="y")

    # Label pour les options d'entrée pour Davinci Resolve
    tk.Label(frame_davinci_in, text="Pour import Davinci Resolve :", font=bold_font, bg=customstyle.bg_frame).pack(anchor="w", pady=(0, 10))

    # Options d'entrée pour Davinci Resolve
    davinci_in_conversions = [
        ("H.264/H.265 → ProRes 422 HQ", "H.264/H.265 → ProRes 422 HQ (pour Davinci Resolve)"),
        ("H.264/H.265 → DNxHR HQX", "H.264/H.265 → DNxHR HQX (pour Davinci Resolve)"),
        ("H.264/H.265 → MJPEG", "H.264/H.265 → MJPEG (pour Davinci Resolve)")
    ]

    conversion_option = tk.StringVar(value="H.264/H.265 → ProRes 422 HQ (pour Davinci Resolve)")
    for text, mode in davinci_in_conversions:
        fg_spec = customstyle.fg_global
        if text == "H.264/H.265 → ProRes 422 HQ":
            fg_spec = customstyle.fg_recommended
        tk.Radiobutton(frame_davinci_in, text=text, variable=conversion_option, value=mode,
                       bg=customstyle.bg_frame, fg=fg_spec, bd=0, relief="flat", highlightthickness=0).pack(anchor='w', pady=2)

    # Label pour les options de sortie de Davinci Resolve
    tk.Label(frame_davinci_out, text="Après export Davinci Resolve :", font=bold_font, bg=customstyle.bg_frame).pack(anchor="w", pady=(0, 10))

    # Options de sortie de Davinci Resolve
    davinci_out_conversions = [
        ("ProRes/DNxHR → H.264 (Web)", "ProRes/DNxHR → H.264 (pour le Web)"),
        ("ProRes/DNxHR → H.264 (YouTube)", "ProRes/DNxHR → H.264 (pour YouTube)"),
        ("ProRes/DNxHR → H.265 (Web/YouTube)", "ProRes/DNxHR → H.265 (pour Web/YouTube)")
    ]

    for text, mode in davinci_out_conversions:
        fg_spec = customstyle.fg_global
        if text == "ProRes/DNxHR → H.264 (YouTube)":
            fg_spec = customstyle.fg_recommended
        tk.Radiobutton(frame_davinci_out, text=text, variable=conversion_option, value=mode,
                       bg=customstyle.bg_frame, fg=fg_spec, bd=0, relief="flat", highlightthickness=0).pack(anchor='w', pady=2)

    # Label pour les autres options
    tk.Label(frame_other, text="Autres options :", font=bold_font, bg=customstyle.bg_frame).pack(anchor="w", pady=(0, 10))

    # Autres options
    other_conversions = [
        # ("H.264 → MJPEG", "H.264 → MJPEG")
    ]

    if cuda_available:
        other_conversions.extend([
            ("MJPEG → H.264 (NVIDIA QP)", "MJPEG → H.264 (NVIDIA QP)"),
            ("MJPEG → H.264 (NVIDIA Bitrate)", "MJPEG → H.264 (NVIDIA Bitrate)"),
            ("Optimisé YouTube (H.264 NVIDIA QP)", "Optimisé YouTube (H.264 NVIDIA QP)"),
            ("Optimisé YouTube (H.264 NVIDIA Bitrate)", "Optimisé YouTube (H.264 NVIDIA Bitrate)")
        ])

    other_conversions.extend([
        ("MJPEG → H.264 (libx264 CPU)", "MJPEG → H.264 (libx264 CPU)"),
        ("MJPEG → H.265 (libx265 CPU)", "MJPEG → H.265 (libx265 CPU)"),
        ("Optimisé YouTube (H.264 CPU libx264)", "Optimisé YouTube (H.264 CPU libx264)")
    ])

    for text, mode in other_conversions:
        fg_spec = customstyle.fg_global
        tk.Radiobutton(frame_other, text=text, variable=conversion_option, value=mode,
                       bg=customstyle.bg_frame, fg=fg_spec, bd=0, relief="flat", highlightthickness=0).pack(anchor='w', pady=2)

    frame_help = tk.LabelFrame(option_tab, text=" Aide", bg=customstyle.bg_frame, padx=10, pady=10)
    frame_help.pack(pady=10, fill="x", padx=10)
    tk.Label(frame_help, text="Les options recommandées sont en vert", fg=customstyle.fg_recommended, bg=customstyle.bg_frame).pack()

    # --- Cadre : Nombre de threads ---
    frame_threads = tk.LabelFrame(option_tab, text=" Nombre de threads ", bg=customstyle.bg_frame, padx=10, pady=10)
    frame_threads.pack(pady=10, fill="x", padx=10)

    tk.Label(frame_threads, text="Nombre de threads (0 = auto) :", bg=customstyle.bg_frame).pack(side="left")
    num_threads = tk.StringVar(value="0")
    tk.Entry(frame_threads, textvariable=num_threads, width=5).pack(side="left", padx=5)

    return conversion_option, num_threads

def close_app(root: tk.Tk) -> None:
    """Ferme l'application."""
    root.destroy()

def create_processing_tab(root, notebook, input_files, output_dir, files_list,
                                select_button, remove_button, clear_button, output_button,
                                conversion_option, num_threads):
    #### ONGLET TRAITEMENT
    process_tab = customstyle.gen_tab(notebook, "Traitement")

    # --- Cadre : Progression ---
    frame_progress = tk.LabelFrame(process_tab, text=" Progression ", bg=customstyle.bg_frame, padx=10, pady=10)
    frame_progress.pack(pady=10, fill="x", padx=10)

    progress_bar = ttk.Progressbar(frame_progress, length=700)
    progress_bar.pack(pady=5)
    progress_label = tk.Label(frame_progress, text="En attente...", bg=customstyle.bg_frame)
    progress_label.pack()

    # --- Cadre : Boutons de commande ---
    frame_command = tk.LabelFrame(process_tab, text=" Commandes ", bg=customstyle.bg_frame, padx=10, pady=10)
    frame_command.pack(pady=10, fill="x", padx=10)

    convert_button = tk.Button(frame_command, text="Convertir",
        command=lambda: libtools.convert(input_files, conversion_option, output_dir,
            progress_bar, progress_label, files_list, root,
            convert_button, cancel_button, select_button,
            remove_button, clear_button, output_button, close_button, num_threads),
        width=20, bg=customstyle.bg_button_convert, fg="white")
    convert_button.pack(side="left")

    cancel_button = tk.Button(frame_command, text="Annuler", command=lambda: libtools.cancel_conversion(),
        width=20, bg=customstyle.bg_button_cancel, fg="white", state=tk.DISABLED)
    cancel_button.pack(side="left", padx=5)

def create_debug_tab(notebook):
    debug_tab = customstyle.gen_tab(notebook, "Débogage")

    debug_text = tk.Text(debug_tab, height=15, width=80)
    debug_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    clear_button = tk.Button(debug_tab, text="Vider les logs", width=14,
            command=lambda: debug_text.delete(1.0, tk.END), bg=customstyle.bg_button_clear, fg="white")
    clear_button.pack(pady=5)

    # Rediriger les logs vers cette zone de texte
    class TextHandler(libtools.logging.Handler):
        def __init__(self, text_widget):
            super().__init__()
            self.text_widget = text_widget

        def emit(self, record):
            self.text_widget.insert(tk.END, self.format(record) + "\n")
            self.text_widget.see(tk.END)

    text_handler = TextHandler(debug_text)
    text_handler.setFormatter(libtools.logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    libtools.logging.getLogger().addHandler(text_handler)

    return debug_tab

def create_help_tab(notebook, bold_font):
    #### ONGLET AIDE
    help_tab = customstyle.gen_tab(notebook, "Aide")

    # --- Cadre : Aide ---
    frame_help = tk.LabelFrame(help_tab, text=" Aide ", bg=customstyle.bg_frame, relief="flat", bd=0, padx=10, pady=10)
    frame_help.pack(pady=10, fill="x", padx=10)

    tk.Label(frame_help, text="⚠️ Pour Davinci Resolve (version gratuite sous Linux) :", font=bold_font, bg=customstyle.bg_frame).pack(anchor="w")
    tk.Label(frame_help, text="• Utilisez ProRes ou DNxHD pour une compatibilité optimale.", bg=customstyle.bg_frame).pack(anchor="w")
    tk.Label(frame_help, text="• Les fichiers H.264 et H.265 doivent être convertis avant import dasn Davinci Resolve.", bg=customstyle.bg_frame).pack(anchor="w")
    tk.Label(frame_help, text=f"• CUDA {'est disponible' if libtools.check_cuda() else 'n\'est pas disponible'} sur ce système.", bg=customstyle.bg_frame).pack(anchor="w")