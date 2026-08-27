import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import subprocess
import sys

from tkinterdnd2 import DND_FILES, TkinterDnD

from src.pose_processor import process_video, SUPPORTED_EXTENSIONS
from src.id_selection_window import IDSelectionWindow
from src.clean_data import clean_csv
from src.visualize_clean import create_visualization

import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

VIDEOS_DIR = BASE_DIR / "videos"
RESULTS_DIR = BASE_DIR / "results"

MODELS = {
    "YOLO26 Nano": "yolo26n-pose.pt",
    "YOLO26 Small": "yolo26s-pose.pt",
    "YOLO26 Medium": "yolo26m-pose.pt",
    "YOLO26 Large": "yolo26l-pose.pt",
    "YOLO26 XLarge": "yolo26x-pose.pt",
}

# Allow custom model path via .env file
load_dotenv(BASE_DIR / ".env")
MODELS_DIR = os.getenv("MODEL_DIR", BASE_DIR / "models")

VIDEOS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

def show_video(video_path):
    video_path = Path(video_path).resolve()

    if sys.platform == "win32":
        os.startfile(video_path)
    elif sys.platform == "darwin":
        subprocess.run(["open", str(video_path)])
    else:
        subprocess.run(["xdg-open", str(video_path)])

class PoseApp(TkinterDnD.Tk):

    def __init__(self):

        super().__init__()

        self.title("Analyse de mouvements")
        self.geometry("700x500")
        self.minsize(600, 500)

        self.video_path = None
        self.processing = False

        self.create_widgets()

    def create_widgets(self):

        # ========================================================
        # Configuration de la fenêtre
        # ========================================================

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ========================================================
        # Conteneur principal
        # ========================================================

        main_frame = tk.Frame(self)

        main_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=20,
            pady=15
        )

        main_frame.grid_columnconfigure(
            0,
            weight=1
        )

        # ========================================================
        # Titre
        # ========================================================

        title = tk.Label(
            main_frame,
            text="Analyse de mouvements du nourrisson",
            font=("Arial", 20, "bold")
        )

        title.grid(
            row=0,
            column=0,
            pady=(10, 5)
        )

        # ========================================================
        # Sous-titre
        # ========================================================

        subtitle = tk.Label(
            main_frame,
            text="Sélectionnez une vidéo pour lancer l'analyse.",
            font=("Arial", 11)
        )

        subtitle.grid(
            row=1,
            column=0,
            pady=(0, 15)
        )

        # ========================================================
        # Zone drag & drop
        # ========================================================

        self.drop_zone = tk.Label(
            main_frame,
            text="Glissez-déposez une vidéo ici",
            relief="solid",
            borderwidth=2,
            font=("Arial", 13)
        )

        self.drop_zone.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=30,
            pady=10,
            ipady=25
        )

        self.drop_zone.drop_target_register(DND_FILES)

        self.drop_zone.dnd_bind(
            "<<Drop>>",
            self.on_drop
        )

        self.drop_zone.bind(
            "<Button-1>",
            lambda event: self.select_video()
        )

        # ========================================================
        # Bouton sélection vidéo
        # ========================================================

        self.select_button = tk.Button(
            main_frame,
            text="Sélectionner une vidéo",
            command=self.select_video,
            width=25,
            height=2
        )

        self.select_button.grid(
            row=3,
            column=0,
            pady=10
        )

        # ========================================================
        # Vidéo sélectionnée
        # ========================================================

        self.video_label = tk.Label(
            main_frame,
            text="Aucune vidéo sélectionnée",
            font=("Arial", 10),
            anchor="center"
        )

        self.video_label.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=10
        )

        # ========================================================
        # Modèle YOLO
        # ========================================================

        tk.Label(
            main_frame,
            text="Modèle :"
        ).grid(
            row=5,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.model_variable = tk.StringVar(
            value="YOLO26 Small"
        )

        self.model_combobox = ttk.Combobox(
            main_frame,
            textvariable=self.model_variable,
            values=list(MODELS.keys()),
            state="readonly"
        )

        self.model_combobox.grid(
            row=5,
            column=0,
            sticky="e",
            padx=5,
            pady=5
        )

        # ========================================================
        # Progression
        # ========================================================
        
        progress_frame = tk.Frame(main_frame)
        
        progress_frame.grid(
            row=6,
            column=0,
            sticky="ew",
            pady=(15, 5)
        )
        
        progress_frame.grid_columnconfigure(
            0,
            weight=1
        )
        
        self.progress = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            mode="determinate"
        )
        
        self.progress.grid(
            row=0,
            column=0,
            sticky="ew"
        )
        
        self.progress_label = tk.Label(
            progress_frame,
            text="En attente",
            font=("Arial", 10)
        )
        
        self.progress_label.grid(
            row=1,
            column=0,
            pady=(5, 0)
        )

        # ========================================================
        # Bouton lancement
        # ========================================================

        self.start_button = tk.Button(
            main_frame,
            text="Lancer l'analyse",
            command=self.start_processing,
            width=25,
            height=2,
            state="disabled"
        )

        self.start_button.grid(
            row=7,
            column=0,
            pady=15
        )

        # ========================================================
        # Status
        # ========================================================

        self.status_label = tk.Label(
            main_frame,
            text="",
            font=("Arial", 12)
        )

        self.status_label.grid(
            row=8,
            column=0,
            pady=5
        )

    def is_valid_video(self, path):

        return (
            Path(path).suffix.lower()
            in SUPPORTED_EXTENSIONS
        )

    def set_video(self, path):

        path = Path(path)

        if not self.is_valid_video(path):

            messagebox.showerror(
                "Format non supporté",
                (
                    "Veuillez sélectionner une vidéo "
                    "(.mp4, .avi, .mov ou .mkv)."
                )
            )

            return

        self.video_path = path
        self.video_label.config(text=f"Vidéo sélectionnée : {path.name}")
        self.start_button.config(state="normal")
        self.status_label.config(text="Vidéo prête à être analysée.")

    def on_drop(self, event):

        paths = self.tk.splitlist(event.data)

        if paths:
            self.set_video(paths[0])

    def select_video(self):

        path = filedialog.askopenfilename(
            title="Sélectionner une vidéo",
            initialdir=VIDEOS_DIR,
            filetypes=[
                (
                    "Vidéos",
                    "*.mp4 *.avi *.mov *.mkv"
                ),
                (
                    "Tous les fichiers",
                    "*.*"
                )
            ]
        )

        if path:
            self.set_video(path)

    def start_processing(self):

        if self.video_path is None:
            return

        if self.processing:
            return

        output_dir = RESULTS_DIR / self.video_path.stem
        baby_csv = output_dir / f"baby_{self.video_path.stem}.csv"

        if output_dir.exists():

            answer = messagebox.askyesno(
                "Vidéo déjà analysée",
                (
                    "Cette vidéo a déjà été analysée.\n\n"
                    "Voulez-vous relancer l'analyse ?"
                )
            )

            if not answer:

                video_path = output_dir / f"visualization_{self.video_path.stem}.avi"

                if video_path.exists():
                    self.after(
                        0,
                        lambda: show_video(video_path)
                    )
                    return
                
                if baby_csv.exists():
                    self.after(
                        0,
                        lambda: self.process_baby_data(baby_csv)
                    )
                    return
                else:
                    messagebox.showwarning(
                        "CSV du bébé introuvable",
                        (
                            "La vidéo a déjà été analysée, "
                            "mais le fichier CSV du bébé est introuvable.\n\n"
                            "L'analyse YOLO va être relancée."
                        )
                    )
        
        self.processing = True

        self.select_button.config(
            state="disabled"
        )

        self.start_button.config(
            state="disabled"
        )

        self.progress["value"] = 0

        self.progress_label.config(
            text="0 %"
        )

        self.status_label.config(
            text="Analyse YOLO en cours..."
        )

        thread = threading.Thread(
            target=self.run_processing,
            daemon=True
        )

        thread.start()

    def update_progress(self, value):

        self.after(
            0,
            lambda: self._update_progress(value)
        )

    def _update_progress(self, value):

        self.progress["value"] = value

        self.progress_label.config(
            text=f"{value:.0f} %"
        )

    def run_processing(self):
        """
        Exécute le traitement de la vidéo.
        """
        
        try:
            all_csv = process_video(
                self.video_path,
                results_dir=RESULTS_DIR,
                model_path=Path(MODELS_DIR) / MODELS[self.model_variable.get()],
                progress_callback=self.update_progress
            )

            self.after(
                0,
                lambda: self.processing_finished(
                    all_csv
                )
            )
        except Exception as error:

            self.after(
                0,
                lambda error=error: self.processing_failed(
                    error
                )
            )

    def processing_finished(self, all_csv):
        """
        Affiche la fenêtre de sélection des IDs après la fin du traitement.
        """

        self.processing = False

        self.select_button.config(state="normal")
        self.progress["value"] = 100
        self.progress_label.config(text="100 %")
        self.status_label.config(text="Analyse YOLO terminée.")

        output_dir = RESULTS_DIR / self.video_path.stem

        # Vidéo générée par YOLO
        generated_video = output_dir / f"{self.video_path.stem}.mp4"

        # Nouveau nom
        output_video = (
            output_dir /
            f"{self.video_path.stem}_annotated.mp4"
        )

        # Vérifier que la vidéo existe
        if not generated_video.exists():

            self.start_button.config(state="normal")

            messagebox.showerror(
                "Vidéo introuvable",
                (
                    "L'analyse YOLO est terminée, "
                    "mais la vidéo annotée n'a pas été trouvée.\n\n"
                    f"Fichier attendu :\n{generated_video}"
                )
            )

            return

        # Renommer la vidéo
        try:
            generated_video.rename(output_video)

        except OSError as error:

            self.start_button.config(state="normal")

            messagebox.showerror(
                "Erreur",
                f"Impossible de renommer la vidéo :\n\n{error}"
            )

            return

        annotated_video = output_video

        # Ouvre la fenêtre de sélection des IDs
        self.status_label.config(
            text="Sélectionnez maintenant les IDs du bébé."
        )

        IDSelectionWindow(
            self,
            annotated_video,
            all_csv,
            output_dir,
            on_validate=self.process_baby_data
        )

    def process_baby_data(self, baby_csv):
        """
        Nettoie les données et génère la vidéo de visualisation.
        """

        self.status_label.config(
            text="Traitement des données en cours..."
        )

        self.start_button.config(state="disabled")
        self.select_button.config(state="disabled")

        thread = threading.Thread(
            target=self._run_baby_processing,
            args=(baby_csv,),
            daemon=True
        )

        thread.start()

    def _run_baby_processing(self, baby_csv):

        try:

            self.after(
                0,
                lambda: self.status_label.config(
                    text="Nettoyage des données..."
                )
            )

            self.progress.config(mode="indeterminate")
            self.progress.start(10)

            clean_csv(
                baby_csv
            )

            self.after(
                0,
                lambda: self.status_label.config(
                    text="Génération de la vidéo..."
                )
            )

            video_path = create_visualization(
                input_folder=baby_csv.parent.name,
            )

            self.progress.stop()
            self.progress.config(
                mode="determinate",
                value=100
            )

            self.after(
                0,
                lambda: show_video(
                    video_path
                )
            )

        except Exception as error:

            self.after(
                0,
                lambda error=error: self.processing_failed(
                    error
                )
            )

    def processing_failed(self, error):
        """
        Affiche un message d'erreur si le traitement échoue.
        """

        self.processing = False

        self.select_button.config(state="normal")
        self.start_button.config(state="normal")
        self.status_label.config(text="Une erreur est survenue.")

        messagebox.showerror(
            "Erreur",
            (
                "L'analyse n'a pas pu être terminée.\n\n"
                f"{error}"
            )
        )

if __name__ == "__main__":

    app = PoseApp()
    app.mainloop()