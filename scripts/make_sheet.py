from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math
from scripts.generate_markers import generate_markers, MARKERS, OUTPUT_DIR
import os

INPUT_DIR = Path("aruco_markers")

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

    # Supprimer l'ancienne planche si elle existe
    if output_pdf.exists():
        os.remove(output_pdf)

    # Taille du marqueur en pixels
    marker_px = round(marker_size / 25.4 * DPI)

    # Espace réservé au texte sous chaque marqueur
    text_height = round(12 / 25.4 * DPI)  # 12 mm

    # Taille réelle d'une cellule
    cell_width = marker_px
    cell_height = marker_px + text_height + GAP

    files = sorted(
        INPUT_DIR.glob("*.png"),
        key=lambda p: int(p.stem)
    )

    # Nombre de colonnes et lignes
    cols = math.floor(
        (A4_W - 2 * MARGIN + GAP)
        / (cell_width + GAP)
    )

    rows = math.ceil(len(files) / cols)

    # Vérifier que tout tient sur une page A4
    required_height = (
        2 * MARGIN
        + rows * cell_height
        + (rows - 1) * GAP
    )

    if required_height > A4_H:
        raise ValueError(
            f"Les marqueurs ne tiennent pas sur une page A4. "
            f"Il faudrait {required_height / DPI * 25.4:.1f} mm "
            f"de hauteur."
        )

    sheet = Image.new(
        "RGB",
        (A4_W, A4_H),
        "white"
    )

    draw = ImageDraw.Draw(sheet)

    # Police
    font_id = ImageFont.load_default(round(3 / 25.4 * DPI))
    font_name = ImageFont.load_default(round(3 / 25.4 * DPI))
        

    for i, path in enumerate(files):

        # ID ArUco
        try:
            marker_id = int(path.stem)
        except ValueError:
            print(f"Nom de fichier ignoré : {path}")
            continue

        # Nom de la partie du corps
        body_part = MARKERS.get(
            marker_id,
            "Unknown"
        )

        marker = Image.open(path).convert("RGB")

        # Redimensionnement exact
        marker = marker.resize(
            (marker_px, marker_px),
            Image.Resampling.NEAREST
        )

        row = i // cols
        col = i % cols

        x = MARGIN + col * (cell_width + GAP)

        y = MARGIN + row * cell_height

        # Centrer le marqueur dans sa cellule
        cell_x = x
        marker_x = cell_x

        sheet.paste(
            marker,
            (marker_x, y)
        )

        # -------------------------
        # Texte sous le marqueur
        # -------------------------

        center_x = marker_x + marker_px / 2

        # "ID 5"
        id_text = f"ID {marker_id}"

        bbox = draw.textbbox(
            (0, 0),
            id_text,
            font=font_id
        )

        id_width = bbox[2] - bbox[0]
        id_height = bbox[3] - bbox[1]

        id_x = center_x - id_width / 2
        id_y = y + marker_px + round(1 / 25.4 * DPI)

        draw.text(
            (id_x, id_y),
            id_text,
            fill="black",
            font=font_id
        )

        # "Left Shoulder"
        name_text = body_part.replace("_", " ")

        bbox = draw.textbbox(
            (0, 0),
            name_text,
            font=font_name
        )

        name_width = bbox[2] - bbox[0]

        name_x = center_x - name_width / 2
        name_y = (
            id_y
            + id_height
            + round(0.5 / 25.4 * DPI)
        )

        draw.text(
            (name_x, name_y),
            name_text,
            fill="black",
            font=font_name
        )

    # PDF
    sheet.save(
        output_pdf,
        "PDF",
        resolution=DPI
    )

    print(
        f"Planche créée : {output_pdf}"
    )


if __name__ == "__main__":
    if not INPUT_DIR.exists() or not any(INPUT_DIR.glob("*.png")):
        generate_markers()
    
    generate_sheet(
        marker_size=30,
        DPI=DPI
    )