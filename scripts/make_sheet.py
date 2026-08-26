from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math
from scripts.generate_markers import generate_markers, MARKERS, OUTPUT_DIR
import os

INPUT_DIR = Path(__file__).resolve().parent / "aruco_markers"

# Dimensions A4 à 300 DPI
DPI = 300
A4_W = round(210 / 25.4 * DPI)
A4_H = round(297 / 25.4 * DPI)

# Mise en page
MARGIN = round(10 / 25.4 * DPI)       # 10 mm
GAP = round(5 / 25.4 * DPI)          # 5 mm


def generate_sheet(marker_size, DPI=300):
    """
    Génère une planche A4 avec les marqueurs ArUco.

    marker_size : taille du marqueur en mm
    DPI : résolution en points par pouce
    """

    output_pdf = OUTPUT_DIR / "aruco_sheet.pdf"

    if output_pdf.exists():
        os.remove(output_pdf)

    # ========================================================
    # DIMENSIONS
    # ========================================================

    marker_px = round(marker_size / 25.4 * DPI)

    # Texte avec une taille minimale
    # Le texte ne devient donc pas microscopique
    FONT_SIZE_MM = 3.5
    font_size = max(
        10,
        round(FONT_SIZE_MM / 25.4 * DPI)
    )

    font_id = ImageFont.load_default(font_size)
    font_name = ImageFont.load_default(font_size)

    # Espace entre le marqueur et son ID
    ID_GAP = round(2 / 25.4 * DPI)

    # Hauteur réservée à la légende
    LEGEND_HEIGHT = round(35 / 25.4 * DPI)

    # ========================================================
    # FICHIERS
    # ========================================================

    files = sorted(
        INPUT_DIR.glob("*.png"),
        key=lambda p: int(p.stem)
    )

    # ========================================================
    # DIMENSIONS DES CELLULES
    # ========================================================

    # L'ID est placé à droite du marqueur
    text_width = round(20 / 25.4 * DPI)

    cell_width = (
        marker_px
        + ID_GAP
        + text_width
    )

    cell_height = marker_px

    # ========================================================
    # MISE EN PAGE
    # ========================================================

    available_width = (
        A4_W
        - 2 * MARGIN
    )

    available_height = (
        A4_H
        - 2 * MARGIN
        - LEGEND_HEIGHT
    )

    cols = max(
        1,
        math.floor(
            (available_width + GAP)
            / (cell_width + GAP)
        )
    )

    rows = math.ceil(
        len(files) / cols
    )

    required_height = (
        rows * cell_height
        + (rows - 1) * GAP
    )

    if required_height > available_height:
        raise ValueError(
            f"Les marqueurs ne tiennent pas sur une page A4. "
            f"Il faudrait "
            f"{(
                required_height
                + LEGEND_HEIGHT
                + 2 * MARGIN
            ) / DPI * 25.4:.1f} mm "
            f"de hauteur."
        )

    # ========================================================
    # CRÉATION DE LA PAGE
    # ========================================================

    sheet = Image.new(
        "RGB",
        (A4_W, A4_H),
        "white"
    )

    draw = ImageDraw.Draw(sheet)

    # ========================================================
    # MARQUEURS
    # ========================================================

    for i, path in enumerate(files):

        try:
            marker_id = int(path.stem)
        except ValueError:
            print(
                f"Nom de fichier ignoré : {path}"
            )
            continue

        body_part = MARKERS.get(
            marker_id,
            "Unknown"
        )

        marker = Image.open(
            path
        ).convert("RGB")

        marker = marker.resize(
            (marker_px, marker_px),
            Image.Resampling.NEAREST
        )

        row = i // cols
        col = i % cols

        x = (
            MARGIN
            + col * (cell_width + GAP)
        )

        y = (
            MARGIN
            + row * (cell_height + GAP)
        )

        # ----------------------------------------------------
        # Marqueur
        # ----------------------------------------------------

        sheet.paste(
            marker,
            (x, y)
        )

        # ----------------------------------------------------
        # ID à droite
        # ----------------------------------------------------

        id_text = f"ID {marker_id}"

        bbox = draw.textbbox(
            (0, 0),
            id_text,
            font=font_id
        )

        id_width = (
            bbox[2] - bbox[0]
        )

        id_height = (
            bbox[3] - bbox[1]
        )

        id_x = (
            x
            + marker_px
            + ID_GAP
        )

        id_y = (
            y
            + marker_px / 2
            - id_height / 2
        )

        draw.text(
            (id_x, id_y),
            id_text,
            fill="black",
            font=font_id
        )

    # ========================================================
    # LÉGENDE
    # ========================================================

    legend_y = (
        MARGIN
        + rows * cell_height
        + (rows - 1) * GAP
        + round(8 / 25.4 * DPI)
    )

    # Ligne séparatrice
    draw.line(
        (
            MARGIN,
            legend_y,
            A4_W - MARGIN,
            legend_y
        ),
        fill="black",
        width=2
    )

    legend_y += round(
        4 / 25.4 * DPI
    )

    # Titre
    title = "Légende des marqueurs"

    draw.text(
        (MARGIN, legend_y),
        title,
        fill="black",
        font=font_id
    )

    legend_y += round(
        7 / 25.4 * DPI
    )

    # --------------------------------------------------------
    # Légende sur plusieurs colonnes
    # --------------------------------------------------------

    legend_columns = 2

    legend_items = [
        (
            marker_id,
            MARKERS[marker_id]
        )
        for marker_id in sorted(MARKERS)
    ]

    items_per_column = math.ceil(
        len(legend_items)
        / legend_columns
    )

    legend_col_width = (
        A4_W - 2 * MARGIN
    ) // legend_columns

    for i, (marker_id, body_part) in enumerate(
        legend_items
    ):

        column = i // items_per_column
        row = i % items_per_column

        x = (
            MARGIN
            + column * legend_col_width
        )

        y = (
            legend_y
            + row * round(
                5 / 25.4 * DPI
            )
        )

        text = (
            f"ID {marker_id} : "
            f"{body_part}"
        )

        draw.text(
            (x, y),
            text,
            fill="black",
            font=font_name
        )

    # ========================================================
    # PDF
    # ========================================================

    sheet.save(
        output_pdf,
        "PDF",
        resolution=DPI
    )

    print(
        f"Planche créée : {output_pdf}"
    )

import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Génère une planche de marqueurs ArUco."
    )

    parser.add_argument(
        "--size",
        type=float,
        default=20,
        help="Taille d'un marqueur en mm (défaut : 20 mm)."
    )

    args = parser.parse_args()

    if (
        not INPUT_DIR.exists()
        or not any(INPUT_DIR.glob("*.png"))
        or len(list(INPUT_DIR.glob("*.png"))) < len(MARKERS)
    ):
        generate_markers()

    generate_sheet(
        marker_size=args.size,
        DPI=DPI
    )