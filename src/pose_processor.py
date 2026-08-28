from pathlib import Path
import csv
import torch
from ultralytics import YOLO
import cv2


BODY_KEYPOINTS = {
    0: "Nose",
    1: "Left Eye",
    2: "Right Eye",
    3: "Left Ear",
    4: "Right Ear",
    5: "Left Shoulder",
    6: "Right Shoulder",
    7: "Left Elbow",
    8: "Right Elbow",
    9: "Left Wrist",
    10: "Right Wrist",
    11: "Left Hip",
    12: "Right Hip",
    13: "Left Knee",
    14: "Right Knee",
    15: "Left Ankle",
    16: "Right Ankle",
}

SUPPORTED_EXTENSIONS = (".mp4", ".avi", ".mov", ".mkv")

PROJECT_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = PROJECT_DIR / "models" / "yolo26x-pose.pt"
RESULTS_DIR = PROJECT_DIR / "results"
VIDEOS_DIR = PROJECT_DIR / "videos"

DEVICE = 0 if torch.cuda.is_available() else "cpu"

def process_video(
    video_path,
    results_dir=RESULTS_DIR,
    model_path=MODEL_PATH,
    progress_callback=None
):
    video_path = Path(video_path)
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Nombre total de frames
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    model = YOLO(model_path)
    model.to(DEVICE)
    
    output_dir = results_dir / video_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    output_dir = results_dir / video_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    output_csv = output_dir / f"{video_path.stem}.csv"

    # stream=True = résultats fournis frame par frame
    results = model.track(
        str(video_path),
        persist=True,
        save=True,
        verbose=False,
        stream=True,
        project=str(results_dir),
        name=video_path.stem,
        exist_ok=True
    )

    with open(output_csv, "w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow([
            "frame",
            "person_id",
            "keypoint",
            "x",
            "y",
            "confidence"
        ])

        for frame, result in enumerate(results):

            if result.keypoints is not None:

                keypoints = result.keypoints.xy.cpu().numpy()

                confidences = result.keypoints.conf

                if confidences is not None:
                    confidences = confidences.cpu().numpy()

                if result.boxes.id is not None:
                    ids = result.boxes.id.cpu().numpy()
                else:
                    ids = [-1] * len(keypoints)

                for person_idx, person_keypoints in enumerate(keypoints):

                    person_id = ids[person_idx]

                    for kp_idx, (x, y) in enumerate(person_keypoints):

                        conf = (
                            confidences[person_idx][kp_idx]
                            if confidences is not None
                            else None
                        )

                        writer.writerow([
                            frame,
                            int(person_id),
                            BODY_KEYPOINTS.get(kp_idx, "Unknown"),
                            float(x),
                            float(y),
                            float(conf) if conf is not None else None
                        ])

            # Mise à jour de la progression
            if progress_callback and total_frames > 0:

                progress = ((frame + 1) / total_frames) * 100

                progress_callback(progress)

    return output_csv