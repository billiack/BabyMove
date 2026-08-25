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

Le fichier du modèle `yolo26x-pose.pt` doit être placé dans `models/`
L'application utilise actuellement YOLO26 Pose pour détecter les 17 keypoints humains.

## 5. Marqueurs ArUco

Pour générer la planche de marqueurs ArUco avec une taille par défaut de 20 mm :

```sh
python -m scripts.make_sheet
```

Pour choisir la taille des marqueurs en millimètres :

```sh
python -m scripts.make_sheet --size 10
```