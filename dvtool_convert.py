#!/usr/bin/python3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkFont
import subprocess
import os
import re
import threading
from typing import List, Optional
import logging


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("debug.log"),  # Écrit les logs dans un fichier
            logging.StreamHandler()           # Affiche les logs dans la console
        ]
    )

setup_logging()

def check_ffmpeg() -> bool:
    """Vérifie si ffmpeg et ffprobe sont installés."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        subprocess.run(["ffprobe", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except FileNotFoundError:
        messagebox.showerror("Erreur", "FFmpeg ou ffprobe n'est pas installé ou n'est pas dans le PATH.")
        return False

def check_cuda() -> bool:
    """Vérifie si CUDA et NVENC sont disponibles et fonctionnels."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-f", "lavfi", "-i", "testsrc=size=128x128:rate=1", "-c:v", "h264_nvenc",
             "-f", "null", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
        )
        # return True
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False

cuda_available = check_cuda()

def select_files(input_files: tk.Variable, files_list: tk.Listbox) -> None:
    """Ouvre une boîte de dialogue pour sélectionner des fichiers vidéo."""
    file_paths = filedialog.askopenfilenames(
        title="Sélectionner des vidéos",
        filetypes=[("Fichiers vidéo", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv"), ("Tous les fichiers", "*")]
    )
    if file_paths:
        input_files.set(list(file_paths))
        files_list.delete(0, tk.END)
        for f in file_paths:
            files_list.insert(tk.END, f)
            codec = get_video_codec(f)
            if codec in ["h264", "hevc"]:
                index = files_list.size() - 1
                files_list.itemconfig(index, {'fg': 'red'})

def get_video_codec(filename: str) -> Optional[str]:
    """Récupère le codec vidéo d'un fichier."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        return result.stdout.strip().lower()
    except Exception:
        return None

def get_duration(filename: str) -> Optional[float]:
    """Récupère la durée de la vidéo en secondes avec ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return None

def detect_and_convert_h264_h265(input_files: tk.Variable, files_list: tk.Listbox, conversion_option: tk.StringVar) -> None:
    """Détecte les fichiers H.264/H.265 et propose une conversion automatique."""
    files = input_files.get()
    h264_h265_files = []
    for f in files:
        codec = get_video_codec(f)
        if codec in ["h264", "hevc"]:
            h264_h265_files.append(f)

    if h264_h265_files:
        if messagebox.askyesno("Conversion recommandée",
                               f"{len(h264_h265_files)} fichier(s) H.264/H.265 détecté(s). Voulez-vous les convertir vers ProRes pour Davinci Resolve ?"):
            conversion_option.set("H.264/H.265 → ProRes 422 HQ (pour Davinci Resolve)")

def build_ffmpeg_command(file_path: str, mode: str, out_file: str, num_threads: int = 0) -> List[str]:
    """Construit la commande FFmpeg avec support multi-cœurs et options pour Davinci Resolve."""
    base_cmd = ["ffmpeg", "-i", file_path, "-y"]

    if any(codec in mode for codec in ["libx264", "libx265", "prores_ks"]):
        if num_threads > 0:
            base_cmd.extend(["-threads", str(num_threads)])

    # --- OPTIONS POUR DAVINCI RESOLVE (ENTRÉE) ---
    if mode == "H.264/H.265 → ProRes 422 HQ (pour Davinci Resolve)":
        return base_cmd + [
            "-c:v", "prores_ks", "-profile:v", "3", "-qscale:v", "11",
            "-vendor", "ap10", "-pix_fmt", "yuv422p10le",
            "-acodec", "pcm_s16le", out_file
        ]
    elif mode == "H.264/H.265 → DNxHR HQX (pour Davinci Resolve)":
        return base_cmd + [
            "-c:v", "dnxhd", "-vf", "scale=3840:2160,fps=60,format=yuv422p10le",
            "-b:v", "440M", "-profile:v", "dnxhr_hqx",
            "-pix_fmt", "yuv422p10le", "-acodec", "pcm_s16le", out_file
        ]
    elif mode == "H.264/H.265 → MJPEG (pour Davinci Resolve)":
        return base_cmd + [
            "-c:v", "mjpeg", "-q:v", "2", "-pix_fmt", "yuvj422p",
            "-acodec", "pcm_s16le", out_file
        ]

    # --- OPTIONS POUR SORTIE DE DAVINCI RESOLVE (ProRes/DNxHD → H.264/H.265) ---
    elif mode == "ProRes/DNxHR → H.264 (pour le Web)":
        if cuda_available:
            return base_cmd + [
                "-hwaccel", "cuda", "-hwaccel_device", "0",
                "-c:v", "h264_nvenc", "-preset", "slow", "-profile:v", "high", "-level", "4.0",
                "-pix_fmt", "yuv420p", "-rc", "vbr", "-cq", "18",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-movflags", "+faststart", out_file
            ]
        else:
            return base_cmd + [
                "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-movflags", "+faststart", out_file
            ]
    elif mode == "ProRes/DNxHR → H.264 (pour YouTube)":
        if cuda_available:
            return base_cmd + [
                "-hwaccel", "cuda", "-hwaccel_device", "0",
                "-c:v", "h264_nvenc", "-preset", "slow", "-profile:v", "high", "-level", "4.0",
                "-pix_fmt", "yuv420p", "-rc", "vbr", "-cq", "18",
                "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
                "-movflags", "+faststart", out_file
            ]
        else:
            return base_cmd + [
                "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0",
                "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
                "-movflags", "+faststart", out_file
            ]
    elif mode == "ProRes/DNxHR → H.265 (pour Web/YouTube)":
        return base_cmd + [
            "-c:v", "libx265", "-preset", "slow", "-crf", "22",
            "-pix_fmt", "yuv420p", "-tag:v", "hvc1",
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
            "-movflags", "+faststart", out_file
        ]

    # --- AUTRES OPTIONS ---
    elif mode == "H.264 → MJPEG":
        return base_cmd + [
            "-hwaccel", "cuda" if cuda_available else "none", "-hwaccel_device", "0" if cuda_available else "none",
            "-vcodec", "mjpeg", "-q:v", "2",
            "-acodec", "pcm_s16be", "-q:a", "0", "-f", "mov", out_file
        ]
    elif mode == "MJPEG → H.264 (NVIDIA QP)" and cuda_available:
        return base_cmd + [
            "-hwaccel", "cuda", "-hwaccel_device", "0",
            "-vf", "yadif", "-codec:v", "h264_nvenc", "-preset", "slow", "-profile:v", "high", "-level", "4.0",
            "-pix_fmt", "yuv420p", "-rc", "vbr", "-cq", "18",
            "-codec:a", "aac", "-b:a", "384k", "-ar", "48000",
            "-movflags", "faststart", out_file
        ]
    elif mode == "MJPEG → H.264 (NVIDIA Bitrate)" and cuda_available:
        return base_cmd + [
            "-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
            "-c:a", "copy", "-c:v", "h264_nvenc", "-preset", "slow", "-profile:v", "high", "-level", "4.0",
            "-pix_fmt", "yuv420p", "-b:v", "10M", "-rc", "vbr",
            "-movflags", "faststart", out_file
        ]
    elif mode == "MJPEG → H.264 (libx264 CPU)":
        return base_cmd + [
            "-vf", "yadif", "-codec:v", "libx264", "-preset", "slow", "-crf", "18",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0",
            "-codec:a", "aac", "-b:a", "384k", "-ar", "48000",
            "-movflags", "faststart", out_file
        ]
    elif mode == "MJPEG → H.265 (libx265 CPU)":
        return base_cmd + [
            "-vf", "yadif", "-c:v", "libx265", "-preset", "slow", "-crf", "22",
            "-pix_fmt", "yuv420p", "-tag:v", "hvc1",
            "-c:a", "aac", "-b:a", "384k", "-ar", "48000",
            "-movflags", "faststart", out_file
        ]
    elif mode == "Optimisé YouTube (H.264 CPU libx264)":
        return base_cmd + [
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0",
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
            "-movflags", "+faststart", out_file
        ]
    elif mode == "Optimisé YouTube (H.264 NVIDIA QP)" and cuda_available:
        return base_cmd + [
            "-hwaccel", "cuda", "-hwaccel_device", "0",
            "-c:v", "h264_nvenc", "-preset", "slow", "-profile:v", "high", "-level", "4.0",
            "-pix_fmt", "yuv420p", "-rc", "vbr", "-cq", "18",
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
            "-movflags", "+faststart", out_file
        ]
    elif mode == "Optimisé YouTube (H.264 NVIDIA Bitrate)" and cuda_available:
        return base_cmd + [
            "-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
            "-c:v", "h264_nvenc", "-preset", "slow", "-profile:v", "high", "-level", "4.0",
            "-pix_fmt", "yuv420p", "-b:v", "20M", "-rc", "vbr",
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
            "-movflags", "+faststart", out_file
        ]
    else:
        raise ValueError(f"Mode inconnu ou non disponible sans CUDA : {mode}")

current_process = None

def run_ffmpeg(file_path: str, mode: str, dest_dir: str, progress_bar: ttk.Progressbar,
               progress_label: tk.Label, root: tk.Tk, num_threads: int) -> Optional[subprocess.Popen]:
    """Exécute FFmpeg et met à jour la progression. Retourne le processus."""
    global current_process
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    # Détermine l'extension de sortie en fonction du mode
    if "ProRes" in mode and "pour Davinci Resolve" in mode:
        out_file = os.path.join(dest_dir, f"{base_name}_ProRes.mov")
    elif "DNxHR" in mode and "pour Davinci Resolve" in mode:
        out_file = os.path.join(dest_dir, f"{base_name}_DNxHR.mov")
    elif "MJPEG (pour Davinci Resolve)" in mode:
        out_file = os.path.join(dest_dir, f"{base_name}_MJPEG_DaVinci.mov")
    elif mode == "H.264 → MJPEG":
        out_file = os.path.join(dest_dir, f"{base_name}_mjpeg.mov")
    elif "H.265" in mode:
        out_file = os.path.join(dest_dir, f"{base_name}_h265.mp4")
    elif "pour le Web" in mode or "pour YouTube" in mode:
        out_file = os.path.join(dest_dir, f"{base_name}_Web.mp4")
    elif "YouTube" in mode:
        out_file = os.path.join(dest_dir, f"{base_name}_YT.mp4")
    else:
        out_file = os.path.join(dest_dir, f"{base_name}_h264.mp4")

    total_duration = get_duration(file_path)
    if not total_duration:
        messagebox.showerror("Erreur", f"Impossible de lire la durée de la vidéo : {file_path}")
        return None

    cmd = build_ffmpeg_command(file_path, mode, out_file, num_threads)
    logging.debug(f"Commande FFmpeg : {' '.join(cmd)}")  # Log de la commande FFmpeg
    current_process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, universal_newlines=True)

    time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")
    def update_progress():
        errors=[]
        for line in current_process.stderr:
            if current_process.poll() is not None:
                break
            if "error" in line.lower():
                errors.append(line) 
            match = time_pattern.search(line)
            if match:
                hours, minutes, seconds = match.groups()
                elapsed = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                percent = (elapsed / total_duration) * 100
                progress_bar["value"] = percent
                progress_label.config(text=f"Conversion... {percent:.1f}% ({os.path.basename(file_path)})")
                root.update_idletasks()
        
        if errors:
            logging.error("Erreurs FFmpeg :\n" + "\n".join(errors))
    
    threading.Thread(target=update_progress, daemon=True).start()
    return current_process

def create_debug_tab(notebook):
    debug_tab = ttk.Frame(notebook)
    notebook.add(debug_tab, text="Débogage")

    debug_text = tk.Text(debug_tab, height=15, width=80)
    debug_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    clear_button = tk.Button(debug_tab, text="Vider les logs", width=14,
            command=lambda: debug_text.delete(1.0, tk.END), bg="#6c757d", fg="white")
    clear_button.pack(pady=5)

    # Rediriger les logs vers cette zone de texte
    class TextHandler(logging.Handler):
        def __init__(self, text_widget):
            super().__init__()
            self.text_widget = text_widget

        def emit(self, record):
            self.text_widget.insert(tk.END, self.format(record) + "\n")
            self.text_widget.see(tk.END)

    text_handler = TextHandler(debug_text)
    text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(text_handler)

    return debug_tab

def cancel_conversion():
    """Annule la conversion en cours."""
    global current_process
    if current_process:
        current_process.terminate()
        current_process = None

def set_ui_state(state: str, convert_button: tk.Button, cancel_button: tk.Button,
                 select_button: tk.Button, remove_button: tk.Button,
                 clear_button: tk.Button, output_button: tk.Button, close_button: tk.Button) -> None:
    """Active ou désactive les boutons en fonction de l'état du traitement."""
    if state == "processing":
        convert_button.config(state=tk.DISABLED)
        cancel_button.config(state=tk.NORMAL)
        select_button.config(state=tk.DISABLED)
        remove_button.config(state=tk.DISABLED)
        clear_button.config(state=tk.DISABLED)
        output_button.config(state=tk.DISABLED)
        close_button.config(state=tk.DISABLED)
    else:
        convert_button.config(state=tk.NORMAL)
        cancel_button.config(state=tk.DISABLED)
        select_button.config(state=tk.NORMAL)
        remove_button.config(state=tk.NORMAL)
        clear_button.config(state=tk.NORMAL)
        output_button.config(state=tk.NORMAL)
        close_button.config(state=tk.NORMAL)

def convert(input_files: tk.Variable, conversion_option: tk.StringVar, output_dir: tk.StringVar,
           progress_bar: ttk.Progressbar, progress_label: tk.Label, files_list: tk.Listbox,
           root: tk.Tk, convert_button: tk.Button, cancel_button: tk.Button,
           select_button: tk.Button, remove_button: tk.Button, clear_button: tk.Button,
           output_button: tk.Button, close_button: tk.Button, num_threads: tk.StringVar) -> None:
    files = input_files.get()
    mode = conversion_option.get()
    dest_dir = output_dir.get()
    if not files:
        messagebox.showerror("Erreur", "Veuillez sélectionner au moins un fichier vidéo.")
        return
    if not dest_dir:
        messagebox.showerror("Erreur", "Veuillez sélectionner un répertoire de destination.")
        return
    progress_bar["value"] = 0
    progress_label.config(text="Conversion en cours...")
    def start_batch():
        set_ui_state("processing", convert_button, cancel_button, select_button, remove_button, clear_button, output_button, close_button)
        for f in files:
            process = run_ffmpeg(f, mode, dest_dir, progress_bar, progress_label, root, int(num_threads.get()))
            if process is None:
                break
            process.wait()  # Attendre la fin de la conversion
            if current_process is None:  # Si annulé
                break
        messagebox.showinfo("Batch terminé", "Toutes les conversions sont terminées !")
        progress_bar["value"] = 0
        progress_label.config(text="En attente...")
        set_ui_state("idle", convert_button, cancel_button, select_button, remove_button, clear_button, output_button, close_button)
    threading.Thread(target=start_batch, daemon=True).start()

def select_output_dir(output_dir: tk.StringVar) -> None:
    """Ouvre une boîte de dialogue pour sélectionner le répertoire de destination."""
    dir_path = filedialog.askdirectory(title="Sélectionner un répertoire de destination")
    if dir_path:
        output_dir.set(dir_path)

def remove_selected(input_files: tk.Variable, files_list: tk.Listbox) -> None:
    """Supprime le fichier sélectionné de la liste."""
    sel = files_list.curselection()
    if not sel:
        return
    idx = sel[0]
    current = list(input_files.get())
    if 0 <= idx < len(current):
        del current[idx]
        input_files.set(current)
    files_list.delete(idx)

def clear_all(input_files: tk.Variable, files_list: tk.Listbox) -> None:
    """Efface tous les fichiers de la liste."""
    if not files_list.size():
        return
    if messagebox.askyesno("Confirmation", "Effacer toute la liste ?"):
        input_files.set([])
        files_list.delete(0, tk.END)

def close_app(root: tk.Tk) -> None:
    """Ferme l'application."""
    root.destroy()

def main() -> None:
    if not check_ffmpeg():
        return
    background = "#f0f0f0"
    root = tk.Tk()
    root.title("Convertisseur vidéo pour Davinci Resolve")
    root.geometry("900x500")
    root.configure(bg=background)
    bold_font = tkFont.Font(family="Helvetica", size=10, weight="bold")
    input_files = tk.Variable(value=[])
    output_dir = tk.StringVar()

    # Création des onglets
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # ONGLET FICHIERS
    file_tab = ttk.Frame(notebook)
    notebook.add(file_tab, text="Fichiers")
    input_files = tk.Variable(value=[])

    # --- Cadre : Sélection des fichiers ---
    frame_files = tk.LabelFrame(file_tab, text=" Sélection des fichiers ", bg=background, padx=10, pady=10)
    frame_files.pack(pady=10, fill="x", padx=10)

    frame_buttons = tk.Frame(frame_files, bg=background)
    frame_buttons.pack(fill="x")
    select_button = tk.Button(frame_buttons, text="Vidéos...", width=18,
        command=lambda: select_files(input_files, files_list), bg="orange", fg="white")
    select_button.pack(side="left")
    remove_button = tk.Button(frame_buttons, text="Supprimer sélection", width=18,
        command=lambda: remove_selected(input_files, files_list), bg="#d9534f", fg="white")
    remove_button.pack(side="left", padx=5)
    clear_button = tk.Button(frame_buttons, text="Tout effacer", width=14,
        command=lambda: clear_all(input_files, files_list), bg="#6c757d", fg="white")
    clear_button.pack(side="left")

    detect_button = tk.Button(frame_buttons, text="Détecter H.264/H.265", width=20,
        command=lambda: detect_and_convert_h264_h265(input_files, files_list, conversion_option),
        bg="#5bc0de", fg="black")
    detect_button.pack(side="left", padx=5)

    frame_list = tk.Frame(frame_files, bg=background)
    frame_list.pack(fill="x", pady=5)
    scrollbar = tk.Scrollbar(frame_list, orient="vertical")
    scrollbar.pack(side="right", fill="y")
    files_list = tk.Listbox(frame_list, width=80, height=8, relief="flat", yscrollcommand=scrollbar.set)
    files_list.pack(side="left", fill="x", expand=True)
    scrollbar.config(command=files_list.yview)

    tk.Label(frame_files, text="Les fichiers H.264/H.265 sont marqués en rouge.", fg="red", bg=background).pack()

    # --- Cadre : Répertoire de sortie ---
    frame_output = tk.LabelFrame(file_tab, text=" Répertoire de sortie ", bg=background, padx=10, pady=10)
    frame_output.pack(pady=10, fill="x", padx=10)

    output_button = tk.Button(frame_output, text="Destination...", width=20,
                              command=lambda: select_output_dir(output_dir), bg="orange", fg="white")
    output_button.pack(side="left")
    tk.Entry(frame_output, textvariable=output_dir, width=40, relief="flat").pack(side="left", padx=5)

    # ONGLET OPTIONS
    option_tab = ttk.Frame(notebook)
    notebook.add(option_tab, text="Options")

    # --- Cadre : Options de conversion ---
    frame_mode = tk.LabelFrame(option_tab, text=" Options de conversion ", bg=background, padx=10, pady=10)
    frame_mode.pack(pady=10, fill="x", padx=10)

    # Frame pour les options Davinci Resolve (à gauche)
    frame_davinci_in = tk.Frame(frame_mode, bg=background)
    frame_davinci_in.pack(side="left", padx=10, fill="y")

    # Frame pour les options de sortie de Davinci Resolve (au centre)
    frame_davinci_out = tk.Frame(frame_mode, bg=background)
    frame_davinci_out.pack(side="left", padx=10, fill="y")

    # Frame pour les autres options (à droite)
    frame_other = tk.Frame(frame_mode, bg=background)
    frame_other.pack(side="right", padx=10, fill="y")

    # Label pour les options d'entrée pour Davinci Resolve
    tk.Label(frame_davinci_in, text="Pour import Davinci Resolve :", font=bold_font, bg=background).pack(anchor="w", pady=(0, 10))

    # Options d'entrée pour Davinci Resolve
    davinci_in_conversions = [
        ("H.264/H.265 → ProRes 422 HQ", "H.264/H.265 → ProRes 422 HQ (pour Davinci Resolve)"),
        ("H.264/H.265 → DNxHR HQX", "H.264/H.265 → DNxHR HQX (pour Davinci Resolve)"),
        ("H.264/H.265 → MJPEG", "H.264/H.265 → MJPEG (pour Davinci Resolve)")
    ]

    conversion_option = tk.StringVar(value="H.264/H.265 → ProRes 422 HQ (pour Davinci Resolve)")
    for text, mode in davinci_in_conversions:
        tk.Radiobutton(frame_davinci_in, text=text, variable=conversion_option, value=mode,
                       bg=background, fg="blue", bd=0, relief="flat", highlightthickness=0).pack(anchor='w', pady=2)

    # Label pour les options de sortie de Davinci Resolve
    tk.Label(frame_davinci_out, text="Après export Davinci Resolve :", font=bold_font, bg=background).pack(anchor="w", pady=(0, 10))

    # Options de sortie de Davinci Resolve
    davinci_out_conversions = [
        ("ProRes/DNxHR → H.264 (Web)", "ProRes/DNxHR → H.264 (pour le Web)"),
        ("ProRes/DNxHR → H.264 (YouTube)", "ProRes/DNxHR → H.264 (pour YouTube)"),
        ("ProRes/DNxHR → H.265 (Web/YouTube)", "ProRes/DNxHR → H.265 (pour Web/YouTube)")
    ]

    for text, mode in davinci_out_conversions:
        tk.Radiobutton(frame_davinci_out, text=text, variable=conversion_option, value=mode,
                       bg=background, fg="blue", bd=0, relief="flat", highlightthickness=0).pack(anchor='w', pady=2)

    # Label pour les autres options
    tk.Label(frame_other, text="Autres options :", font=bold_font, bg=background).pack(anchor="w", pady=(0, 10))

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
        tk.Radiobutton(frame_other, text=text, variable=conversion_option, value=mode,
                       bg=background, fg="blue", bd=0, relief="flat", highlightthickness=0).pack(anchor='w', pady=2)

    # --- Cadre : Nombre de threads ---
    frame_threads = tk.LabelFrame(option_tab, text=" Nombre de threads ", bg=background, padx=10, pady=10)
    frame_threads.pack(pady=10, fill="x", padx=10)

    tk.Label(frame_threads, text="Nombre de threads (0 = auto) :", bg=background).pack(side="left")
    num_threads = tk.StringVar(value="0")
    tk.Entry(frame_threads, textvariable=num_threads, width=5).pack(side="left", padx=5)

    # ONGLET TRAITEMENT
    process_tab = ttk.Frame(notebook)
    notebook.add(process_tab, text="Traitement")

    # --- Cadre : Progression ---
    frame_progress = tk.LabelFrame(process_tab, text=" Progression ", bg=background, padx=10, pady=10)
    frame_progress.pack(pady=10, fill="x", padx=10)

    progress_bar = ttk.Progressbar(frame_progress, length=500)
    progress_bar.pack(pady=5)
    progress_label = tk.Label(frame_progress, text="En attente...", bg=background)
    progress_label.pack()

    # --- Cadre : Boutons de commande ---
    frame_command = tk.LabelFrame(process_tab, text=" Commandes ", bg=background, padx=10, pady=10)
    frame_command.pack(pady=10, fill="x", padx=10)

    convert_button = tk.Button(frame_command, text="Convertir",
        command=lambda: convert(input_files, conversion_option, output_dir,
            progress_bar, progress_label, files_list, root,
            convert_button, cancel_button, select_button,
            remove_button, clear_button, output_button, close_button, num_threads),
        width=20, bg="green", fg="white")
    convert_button.pack(side="left")
    cancel_button = tk.Button(frame_command, text="Annuler", command=lambda: cancel_conversion(),
        width=20, bg="red", fg="white", state=tk.DISABLED)
    cancel_button.pack(side="left", padx=5)

    # --- Cadre : Boutons de fermeture ---
    frame_princ = tk.LabelFrame(root, bg=background, padx=10, pady=10)
    frame_princ.pack(pady=10, fill="x", padx=10)
    
    close_button = tk.Button(frame_princ, text="Fermer", command=lambda: close_app(root),
        width=20, bg="grey", fg="white", state=tk.NORMAL)
    close_button.pack(side="right", padx=10)

    # ONGLET DEBUG
    debug_tab = create_debug_tab(notebook)

    # ONGLET AIDE
    help_tab = ttk.Frame(notebook)
    notebook.add(help_tab, text="Aide/Info")

    # --- Cadre 7 : Aide ---
    frame_help = tk.LabelFrame(help_tab, text=" Aide ", bg=background, relief="flat", bd=0, padx=10, pady=10)
    frame_help.pack(pady=10, fill="x", padx=10)

    tk.Label(frame_help, text="⚠️ Pour Davinci Resolve (version gratuite sous Linux) :", font=bold_font, bg=background).pack(anchor="w")
    tk.Label(frame_help, text="• Utilisez ProRes ou DNxHD pour une compatibilité optimale.", bg=background).pack(anchor="w")
    tk.Label(frame_help, text="• Les fichiers H.264 et H.265 doivent être convertis avant import.", bg=background).pack(anchor="w")
    tk.Label(frame_help, text=f"• CUDA {'est disponible' if cuda_available else 'n\'est pas disponible'} sur ce système.", bg=background).pack(anchor="w")

    root.mainloop()

if __name__ == "__main__":
    main()
