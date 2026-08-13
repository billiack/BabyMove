import cv2
from pathlib import Path


OUTPUT_DIR = Path("aruco_markers")
OUTPUT_DIR.mkdir(exist_ok=True)

# Dictionnaire ArUco utilisé
ARUCO_DICT = cv2.aruco.DICT_4X4_50

MARKERS = {
    5: "Epaule gauche",
    7: "Coude gauche",
    9: "Poignet gauche",
    11: "Hanche gauche",
    13: "Genou gauche",
    15: "Cheville gauche",
}

SIZE = 500  # pixels


def generate_markers():

    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)

    for marker_id in MARKERS.keys():

        marker = cv2.aruco.generateImageMarker(
            dictionary,
            marker_id,
            SIZE
        )

        filename = OUTPUT_DIR / f"{marker_id}.png"

        cv2.imwrite(str(filename), marker)

    print("\nMarkers generated successfully.")


if __name__ == "__main__":
    generate_markers()