import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
from typing import List, Optional
import logging
import os
import json
import re
import threading
import config.lang as customlang

current_process = None

def save_param(key, value, filename="/tmp/dvtool.json"):
    """Sauvegarde un paramètre dans un fichier JSON sous /tmp"""
    params = {}

    # Charger le fichier existant si présent
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                params = json.load(f)
            except json.JSONDecodeError:
                params = {}

    # Mettre à jour le paramètre
    params[key] = value

    # Sauvegarder
    with open(filename, "w") as f:
        json.dump(params, f, indent=2)

def load_param(key, filename="/tmp/dvtool.json", default=None):
    """Charge un paramètre depuis le fichier JSON sous /tmp"""
    if not os.path.exists(filename):
        return default
    
    with open(filename, "r") as f:
        try:
            params = json.load(f)
        except json.JSONDecodeError:
            return default

    return params.get(key, default)       

def setup_logging():
    """Configure le logging pour l'application."""
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
        messagebox.showerror(customlang.get("error_label"), customlang.get("error_ffmpeg"))
        return False

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
    
# def check_cuda() -> bool:
#     """Vérifie si CUDA et NVENC sont disponibles et fonctionnels."""
#     try:
#         result = subprocess.run(
#             ["ffmpeg", "-hide_banner", "-f", "lavfi", "-i", "testsrc=size=160x160:rate=1", "-c:v", "h264_nvenc",
#              "-f", "null", "-"],
#             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
#         )
#         # return True
#         return result.returncode == 0
#     except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
#         return False

def check_cuda() -> bool:
    """Vérifie si CUDA et NVENC sont disponibles et fonctionnels."""
    try:
        result = subprocess.run(
            ["nvcc", "--version"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, check=True
        )
        # return "cuda" in result.stdout.lower()
        # Fonction désactivée pour le moment. Elle retourne toujours False
        return False
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
  
# def detect_and_convert_h264_h265(input_files: tk.Variable, files_list: tk.Listbox, conversion_option: tk.StringVar) -> None:
#     """Détecte les fichiers H.264/H.265 et propose une conversion automatique."""
#     files = input_files.get()
#     h264_h265_files = []
#     for f in files:
#         codec = get_video_codec(f)
#         if codec in ["h264", "hevc"]:
#             h264_h265_files.append(f)

#     if h264_h265_files:
#         if messagebox.askyesno(customlang.get("quest_recommanded"),
#                                f"{len(h264_h265_files)} fichier(s) H.264/H.265 détecté(s). Voulez-vous les convertir vers ProRes pour Davinci Resolve ?"):
#             conversion_option.set("H.264/H.265 → ProRes 422 HQ (pour Davinci Resolve)")

# def select_files(input_files: tk.Variable, files_list: tk.Listbox) -> None:
#     """Ouvre une boîte de dialogue pour sélectionner des fichiers vidéo."""
#     file_paths = filedialog.askopenfilenames(
#         title=customlang.get("title_selection_file"),
#         initialdir=os.path.expanduser(load_param("last_dir", default="~")),
#         filetypes=[(customlang.get("title_video_files"), "*.mp4 *.mkv *.avi *.mov *.flv *.wmv"), ("Tous les fichiers", "*")]
#     )
#     if file_paths:
#         save_param("last_dir",os.path.dirname(file_paths[0]))
#         input_files.set(list(file_paths))
#         files_list.delete(0, tk.END)
#         for f in file_paths:
#             files_list.insert(tk.END, f)
#             codec = get_video_codec(f)
#             if codec in ["h264", "hevc"]:
#                 index = files_list.size() - 1
#                 files_list.itemconfig(index, {'fg': 'red'})

def select_files(input_files: tk.Variable, files_list: tk.Listbox) -> None:
    """Ouvre une boîte de dialogue pour sélectionner des fichiers vidéo et les ajoute à la liste existante."""
    file_paths = filedialog.askopenfilenames(
        title=customlang.get("title_selection_file"),
        initialdir=os.path.expanduser(load_param("last_dir", default="~")),
        filetypes=[(customlang.get("title_video_files"), "*.mp4 *.mkv *.avi *.mov *.flv *.wmv"), ("Tous les fichiers", "*")]
    )
    if file_paths:
        save_param("last_dir", os.path.dirname(file_paths[0]))
        
        # Récupère les fichiers déjà présents
        current_files = list(input_files.get())
        
        # Ajoute seulement les nouveaux fichiers (évite doublons)
        for f in file_paths:
            if f not in current_files:
                current_files.append(f)
                files_list.insert(tk.END, f)
                codec = get_video_codec(f)
                if codec in ["h264", "hevc"]:
                    index = files_list.size() - 1
                    files_list.itemconfig(index, {'fg': 'red'})
        
        input_files.set(current_files)

def select_output_dir(output_dir: tk.StringVar) -> None:
    """Ouvre une boîte de dialogue pour sélectionner le répertoire de destination."""
    last = load_param("dest_dir", default="~")
    initial=os.path.expanduser(last) if last else os.path.expanduser("~")
    
    dir_path = filedialog.askdirectory(
        title=customlang.get("title_select_output"),
        initialdir=initial
    )
    
    if dir_path:
        output_dir.set(dir_path)
        save_param("dest_dir",dir_path)

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
    if messagebox.askyesno("Confirmation", customlang.get("confirmation_remove_label")):
        input_files.set([])
        files_list.delete(0, tk.END)

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

def build_ffmpeg_command(file_path: str, mode: str, out_file: str, num_threads: int = 0, cuda_available: bool = False) -> List[str]:
    """Construit la commande FFmpeg avec support multi-cœurs et options pour Davinci Resolve."""
    base_cmd = ["ffmpeg", "-i", file_path, "-y"]
    cuda_available = check_cuda()

    if any(codec in mode for codec in ["libx264", "libx265", "prores_ks"]):
        if num_threads > 0:
            base_cmd.extend(["-threads", str(num_threads)])

    # --- OPTIONS POUR DAVINCI RESOLVE (ENTRÉE) ---
    if mode == "H.264/H.265 → ProRes 422 HQ (Davinci Resolve)":
        return base_cmd + [
            "-c:v", "prores_ks", "-profile:v", "3", "-qscale:v", "11",
            "-vendor", "ap10", "-pix_fmt", "yuv422p10le",
            "-acodec", "pcm_s16le", out_file
        ]
    elif mode == "H.264/H.265 → DNxHR HQX (Davinci Resolve)":
        return base_cmd + [
            "-c:v", "dnxhd", "-vf", "scale=3840:2160,fps=60,format=yuv422p10le",
            "-b:v", "440M", "-profile:v", "dnxhr_hqx",
            "-pix_fmt", "yuv422p10le", "-acodec", "pcm_s16le", out_file
        ]
    elif mode == "H.264/H.265 → MJPEG (Davinci Resolve)":
        return base_cmd + [
            "-c:v", "mjpeg", "-q:v", "2", "-pix_fmt", "yuvj422p",
            "-acodec", "pcm_s16le", out_file
        ]

    # --- OPTIONS POUR SORTIE DE DAVINCI RESOLVE (ProRes/DNxHD → H.264/H.265) ---
    elif mode == "ProRes/DNxHR → H.264 (Web)":
        if cuda_available:
            return [
                "ffmpeg", "-hide_banner", "-y",
                "-hwaccel", "cuda", "-hwaccel_device", "0",
                "-i", file_path,
                "-vf", "format=yuv420p",  # conversion 10-bit → 8-bit
                "-c:v", "h264_nvenc", "-preset", "slow", "-profile:v", "high", "-level", "5.1",
                "-rc", "vbr", "-cq", "18",
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
    elif mode == "ProRes/DNxHR → H.264 (YouTube)":
        if cuda_available:
            return [
            "ffmpeg", "-hide_banner", "-y",
            "-hwaccel", "cuda", "-hwaccel_device", "0",
            "-i", file_path,
            "-vf", "format=yuv420p",  # conversion 10-bit → 8-bit
            "-c:v", "h264_nvenc", "-preset", "slow", "-profile:v", "high", "-level", "5.1",
            "-rc", "vbr", "-cq", "18",
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
 
    elif mode == "ProRes/DNxHR → H.265 (Web/YouTube)":
        return base_cmd + [
            "-c:v", "libx265", "-preset", "slow", "-crf", "22",
            "-pix_fmt", "yuv420p", "-tag:v", "hvc1",
            "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
            "-movflags", "+faststart", out_file
        ]
    
    # --- AUTRES OPTIONS ---
#     elif mode == "H.264 → MJPEG":
#         return base_cmd + [
#             "-hwaccel", "cuda" if cuda_available else "none", "-hwaccel_device", "0" if cuda_available else "none",
#             "-vcodec", "mjpeg", "-q:v", "2",
#             "-acodec", "pcm_s16be", "-q:a", "0", "-f", "mov", out_file
#         ]
#     elif mode == "MJPEG → H.264 (NVIDIA QP)" and cuda_available:
#         return base_cmd + [
#             "-hwaccel", "cuda", "-hwaccel_device", "0",
#             "-vf", "yadif", "-codec:v", "h264_nvenc", "-preset", "slow", "-profile:v", "high", "-level", "4.0",
#             "-pix_fmt", "yuv420p", "-rc", "vbr", "-cq", "18",
#             "-codec:a", "aac", "-b:a", "384k", "-ar", "48000",
#             "-movflags", "faststart", out_file
#         ]
#     elif mode == "MJPEG → H.264 (NVIDIA Bitrate)" and cuda_available:
#         return base_cmd + [
#             "-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
#             "-c:a", "copy", "-c:v", "h264_nvenc", "-preset", "slow", "-profile:v", "high", "-level", "4.0",
#             "-pix_fmt", "yuv420p", "-b:v", "10M", "-rc", "vbr",
#             "-movflags", "faststart", out_file
#         ]
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
#     elif mode == "Optimisé YouTube (H.264 NVIDIA QP)" and cuda_available:
#         return base_cmd + [
#             "-hwaccel", "cuda", "-hwaccel_device", "0",
#             "-c:v", "h264_nvenc", "-preset", "slow", "-profile:v", "high", "-level", "4.0",
#             "-pix_fmt", "yuv420p", "-rc", "vbr", "-cq", "18",
#             "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
#             "-movflags", "+faststart", out_file
#         ]
#     elif mode == "Optimisé YouTube (H.264 NVIDIA Bitrate)" and cuda_available:
#         return base_cmd + [
#             "-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
#             "-c:v", "h264_nvenc", "-preset", "slow", "-profile:v", "high", "-level", "4.0",
#             "-pix_fmt", "yuv420p", "-b:v", "20M", "-rc", "vbr",
#             "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
#             "-movflags", "+faststart", out_file
#         ]
    else:
        raise ValueError(f"{customlang.get("cuda_unknown")} : {mode}")
    
def cancel_conversion():
    """Annule la conversion en cours."""
    global current_process
    logging.debug(f"Command FFmpeg : " + str(current_process.pid) + " canceled")  # Log de la commande FFmpeg
    if current_process:
        current_process.terminate()
        current_process = None

def convert(input_files: tk.Variable, conversion_option: tk.StringVar, output_dir: tk.StringVar,
           progress_bar: ttk.Progressbar, progress_label: tk.Label, files_list: tk.Listbox,
           root: tk.Tk, convert_button: tk.Button, cancel_button: tk.Button,
           select_button: tk.Button, remove_button: tk.Button, clear_button: tk.Button,
           output_button: tk.Button, close_button: tk.Button, num_threads: tk.StringVar) -> None:
    
    global current_process
    
    files = input_files.get()
    mode = conversion_option.get()
    dest_dir = output_dir.get()

    if not files:
        messagebox.showerror(customlang.get("error_label"), customlang.get("error_nofiles"))
        return
    if not dest_dir:
        messagebox.showerror(customlang.get("error_label"), customlang.get("error_nodest"))
        return
    
    progress_bar["value"] = 0
    progress_label.config(text=customlang.get("conversion_inprogress"))

    def start_batch():
        set_ui_state("processing", convert_button, cancel_button, select_button, remove_button, clear_button, output_button, close_button)
        for f in files:
            process = run_ffmpeg(f, mode, dest_dir, progress_bar, progress_label, root, int(num_threads.get()))
            if process is None:
                break
            process.wait()  # Attendre la fin de la conversion
            if current_process is None:  # Si annulé
                break
        messagebox.showinfo(customlang.get("end_batch"), customlang.get("end_batch_notice"))
        progress_bar["value"] = 0
        progress_label.config(text=customlang.get("label_inwait"))
        set_ui_state("idle", convert_button, cancel_button, select_button, remove_button, clear_button, output_button, close_button)

    threading.Thread(target=start_batch, daemon=True).start()

def run_ffmpeg(file_path: str, mode: str, dest_dir: str, progress_bar: ttk.Progressbar,
               progress_label: tk.Label, root: tk.Tk, num_threads: int) -> Optional[subprocess.Popen]:
    
    """Exécute FFmpeg et met à jour la progression. Retourne le processus."""

    global current_process

    base_name = os.path.splitext(os.path.basename(file_path))[0]

    # Détermine l'extension de sortie en fonction du mode
    if "ProRes" in mode and "Davinci Resolve" in mode:
        out_file = os.path.join(dest_dir, f"{base_name}_ProRes_DV.mov")
    elif "DNxHR" in mode and "Davinci Resolve" in mode:
        out_file = os.path.join(dest_dir, f"{base_name}_DNxHR_DV.mov")
    elif "MJPEG (Davinci Resolve)" in mode:
        out_file = os.path.join(dest_dir, f"{base_name}_MJPEG_DV.mov")
    elif mode == "H.264 → MJPEG":
        out_file = os.path.join(dest_dir, f"{base_name}_mjpeg.mov")
    elif "H.265" in mode:
        out_file = os.path.join(dest_dir, f"{base_name}_h265.mp4")
    elif "Web" in mode:
        out_file = os.path.join(dest_dir, f"{base_name}_Web.mp4")
    elif "YouTube" in mode:
        out_file = os.path.join(dest_dir, f"{base_name}_YT.mp4")
    else:
        out_file = os.path.join(dest_dir, f"{base_name}_h264.mp4")

    total_duration = get_duration(file_path)
    if not total_duration:
        messagebox.showerror(customlang.get("error_label"), f"{customlang.get("error_read_time")} : {file_path}")
        return None

    cmd = build_ffmpeg_command(file_path, mode, out_file, num_threads)

    logging.debug(f"Command FFmpeg : {' '.join(cmd)}")  # Log de la commande FFmpeg

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
                progress_label.config(text=f"Conversion {mode}... ({os.path.basename(file_path)}) {percent:.1f}%")
                root.update_idletasks()
        
        if errors:
            logging.error("Errors FFmpeg :\n" + "\n".join(errors))
    
    threading.Thread(target=update_progress, daemon=True).start()

    return current_process
