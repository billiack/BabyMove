# Analyse de mouvements du nourrisson

Application permettant d'analyser une vidéo avec YOLO26 Pose et de générer les positions des keypoints dans un fichier CSV.

## 1. Installation

Python 3.10 ou supérieur est recommandé.

Créer un environnement virtuel :

```sh
python -m venv .venv
```

Activer l'environnement :

Windows :

```sh
.venv\Scripts\activate
```

Installer les dépendances :

```sh
pip install -r requirements.txt
```

## 3. Lancer l'application

Depuis le dossier principal du projet :

```sh
python app.py
```

L'interface permet ensuite de sélectionner une vidéo dans `videos/` ou de la glisser-déposer dans l'application.

Une fois l'analyse terminée, les résultats sont enregistrés dans `results/`.

## 4. Modèle YOLO

L'application utilise actuellement YOLO26 Pose pour détecter les 17 keypoints humains.

Les modèles YOLO sont placés dans `models/` par défaut. Le chemin du modèle peut être modifié dans `.env` en modifiant `MODEL_PATH`. 
Le modèle sera automatiquement téléchargé si le fichier n'existe pas.

## 5. Marqueurs ArUco

Pour générer la planche de marqueurs ArUco avec une taille par défaut de 20 mm :

```sh
python -m scripts.make_sheet
```

Pour choisir la taille des marqueurs en millimètres :

```sh
python -m scripts.make_sheet --size 10
```