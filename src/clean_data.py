from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter


# ============================================================
# PARAMÈTRES
# ============================================================

CONF_THRESHOLD = 0.5

# Nombre maximum de frames consécutives pouvant être interpolées
MAX_INTERPOLATION_GAP = 10

# Paramètres du filtre Savitzky-Golay
SMOOTHING_WINDOW = 11
SMOOTHING_POLYORDER = 2

# Distance maximale autorisée entre deux frames.
# Elle sera multipliée par la taille du corps.
MAX_MOVEMENT_RATIO = 0.25


# ============================================================
# OUTILS
# ============================================================

def calculate_body_scale(group):
    """
    Estime la taille du bébé dans l'image à partir des hanches
    et des épaules.
    """

    points = {
        row["keypoint"]: (row["x"], row["y"])
        for _, row in group.iterrows()
    }

    required = [
        "Left Shoulder",
        "Right Shoulder",
        "Left Hip",
        "Right Hip",
    ]

    if not all(k in points for k in required):
        return np.nan

    left_shoulder = np.array(points["Left Shoulder"])
    right_shoulder = np.array(points["Right Shoulder"])

    left_hip = np.array(points["Left Hip"])
    right_hip = np.array(points["Right Hip"])

    shoulder_width = np.linalg.norm(
        left_shoulder - right_shoulder
    )

    hip_width = np.linalg.norm(
        left_hip - right_hip
    )

    scale = np.nanmedian([
        shoulder_width,
        hip_width
    ])

    return scale


def clean_keypoint_trajectory(
    trajectory,
    confidence,
    max_interpolation_gap=10
):
    """
    Nettoie une trajectoire 1D :
    1. supprime les points de faible confiance
    2. interpole les petits trous
    3. lisse les données valides
    """

    values = np.asarray(
        trajectory,
        dtype=float
    ).copy()

    # --------------------------------------------------------
    # 1. Faible confiance
    # --------------------------------------------------------

    values[confidence < CONF_THRESHOLD] = np.nan

    # --------------------------------------------------------
    # 2. Interpolation
    # --------------------------------------------------------

    series = pd.Series(values)

    series = series.interpolate(
        method="linear",
        limit=max_interpolation_gap,
        limit_area="inside"
    )

    values = series.to_numpy()

    # --------------------------------------------------------
    # 3. Vérification
    # --------------------------------------------------------

    valid = ~np.isnan(values)

    # Pas assez de données pour filtrer
    if valid.sum() < 5:
        return values

    # --------------------------------------------------------
    # 4. Lissage
    # --------------------------------------------------------

    # On ne peut pas donner de NaN à savgol_filter.
    # On ne filtre donc que les parties valides.

    first = np.where(valid)[0][0]
    last = np.where(valid)[0][-1]

    segment = values[first:last + 1]

    # S'il reste des NaN à l'intérieur, on les interpole
    segment = (
        pd.Series(segment)
        .interpolate(method="linear")
        .ffill()
        .bfill()
        .to_numpy()
    )

    # Nombre de points disponibles
    n = len(segment)

    if n < SMOOTHING_POLYORDER + 2:
        values[first:last + 1] = segment
        return values

    # Fenêtre impaire
    window = min(
        SMOOTHING_WINDOW,
        n if n % 2 == 1 else n - 1
    )

    # La fenêtre doit être > polyorder
    if window <= SMOOTHING_POLYORDER:
        values[first:last + 1] = segment
        return values

    # --------------------------------------------------------
    # 5. Savitzky-Golay
    # --------------------------------------------------------

    smoothed = savgol_filter(
        segment,
        window_length=window,
        polyorder=SMOOTHING_POLYORDER
    )

    values[first:last + 1] = smoothed

    return values


# ============================================================
# NETTOYAGE
# ============================================================

def clean_dataframe(df, progress_callback=None):

    if progress_callback is not None:
        progress_callback(0)

    df = df.copy()

    # Colonnes supplémentaires
    df["is_outlier"] = False
    df["x_clean"] = df["x"]
    df["y_clean"] = df["y"]

    # --------------------------------------------------------
    # 1. Faible confiance
    # --------------------------------------------------------

    low_confidence = (
        df["confidence"] < CONF_THRESHOLD
    )

    df.loc[
        low_confidence,
        "is_outlier"
    ] = True

    df.loc[
        low_confidence,
        ["x_clean", "y_clean"]
    ] = np.nan

    # --------------------------------------------------------
    # 2. Traitement personne par personne / keypoint
    # --------------------------------------------------------

    grouped = df.groupby(
        ["person_id", "keypoint"],
        sort=False
    )

    total_groups = grouped.ngroups

    for group_index, ((person_id, keypoint), group) in enumerate(grouped):

        group = group.sort_values("frame")

        indices = group.index.to_numpy()

        x = group["x_clean"].to_numpy()
        y = group["y_clean"].to_numpy()

        confidence = group["confidence"].to_numpy()

        # ----------------------------------------------------
        # Détection des gros sauts
        # ----------------------------------------------------

        for i in range(1, len(group)):

            if np.isnan(x[i]) or np.isnan(y[i]):
                continue

            if np.isnan(x[i - 1]) or np.isnan(y[i - 1]):
                continue

            dx = x[i] - x[i - 1]
            dy = y[i] - y[i - 1]

            distance = np.sqrt(
                dx ** 2 + dy ** 2
            )

            current_frame = df[
                df["frame"] == group.iloc[i]["frame"]
            ]

            body_scale = calculate_body_scale(
                current_frame
            )

            if np.isnan(body_scale):
                continue

            max_distance = (
                MAX_MOVEMENT_RATIO *
                body_scale
            )

            if distance > max_distance:

                idx = indices[i]

                df.loc[
                    idx,
                    "is_outlier"
                ] = True

                df.loc[
                    idx,
                    ["x_clean", "y_clean"]
                ] = np.nan

        # ----------------------------------------------------
        # Interpolation + lissage
        # ----------------------------------------------------

        cleaned_x = clean_keypoint_trajectory(
            df.loc[
                indices,
                "x_clean"
            ].to_numpy(),
            confidence
        )

        cleaned_y = clean_keypoint_trajectory(
            df.loc[
                indices,
                "y_clean"
            ].to_numpy(),
            confidence
        )

        df.loc[
            indices,
            "x_clean"
        ] = cleaned_x

        df.loc[
            indices,
            "y_clean"
        ] = cleaned_y

        # ----------------------------------------------------
        # Progression
        # ----------------------------------------------------

        if progress_callback is not None:

            progress = (
                (group_index + 1)
                / total_groups
                * 100
            )

            progress_callback(progress)

    return df

def clean_csv(input_csv, progress_callback=None):

    df = pd.read_csv(input_csv)

    clean_df = clean_dataframe(df, progress_callback=progress_callback)

    output_csv = (
        Path(input_csv).parent /
        f"{Path(input_csv).stem}_clean.csv"
    )

    clean_df.to_csv(
        output_csv,
        index=False
    )

    print(
        f"Clean data saved to: {output_csv}"
    )

    print(
        f"Outliers detected: "
        f"{clean_df['is_outlier'].sum()}"
    )

    return output_csv

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    FOLDER = "Cut_Crawli1_BB006_0_blur_cut"

    RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

    # À modifier selon ton dossier
    folder = FOLDER

    input_file = (
        RESULTS_DIR /
        folder /
        f"baby_{folder}.csv"
    )

    output_file = (
        RESULTS_DIR /
        folder /
        f"baby_{folder}_clean.csv"
    )

    print(f"Reading: {input_file}")

    df = pd.read_csv(input_file)

    print(
        f"{len(df)} keypoints loaded"
    )

    clean_df = clean_dataframe(df)

    clean_df.to_csv(
        output_file,
        index=False
    )

    print(
        f"Clean data saved to: {output_file}"
    )

    print(
        f"Outliers detected: "
        f"{clean_df['is_outlier'].sum()}"
    )