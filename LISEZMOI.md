# ReelsOff : dépôt F-Droid perso (sans Linux)

## Contenu
- `repo/com.neo.reelsoff_1.apk` : APK de release signé avec la clé locale.

## Clé de signature
- Fichier : `C:\Users\coupa\.reelsoff\reelsoff-release.jks` (hors du projet, hors git).
- Empreinte SHA-256 : 0aeec84b511468ae446417f6fae31279c2ccacaa762f34fb7e7cf4d520f988fe
- Ne jamais perdre ce fichier : sans lui, impossible de mettre l'app à jour.

## Ce qui manque
- Un index F-Droid signé (`index-v1.jar`) à côté de l'APK. L'outil officiel (`fdroidserver`) tourne sous Linux, donc on ne l'utilise pas ici.
- Un hébergement HTTPS public pour le dossier `repo/`.

## Installation sur le téléphone (une fois le dépôt prêt)
1. Désinstaller la version debug de ReelsOff (signature différente).
2. Dans F-Droid : Paramètres > Dépôts > + > ajouter l'URL du dépôt.
3. Installer ReelsOff depuis F-Droid, puis activer le service d'accessibilité.
