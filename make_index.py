"""Génère l'index F-Droid v1 signé (index-v1.jar) pour le dossier repo/, sous Windows.

Usage : python make_index.py
Pré-requis : l'APK est dans repo/, la clé est dans C:\\Users\\coupa\\.reelsoff\\, et jarsigner
(JDK d'Android Studio) est trouvé au chemin ci-dessous.
"""
import base64
import hashlib
import json
import os
import subprocess
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE / "repo"
APK = REPO / "com.neo.reelsoff_1.apk"
KEYSTORE = Path(r"C:\Users\coupa\.reelsoff\reelsoff-release.jks")
KEYALIAS = "reelsoff"
JDK = Path(r"C:\Program Files\Android\Android Studio\jbr\bin")
KEYTOOL = JDK / "keytool.exe"
JARSIGNER = JDK / "jarsigner.exe"

PKG = "com.neo.reelsoff"
VERSION_CODE = 1
VERSION_NAME = "1.0"
MIN_SDK = 26
TARGET_SDK = 34
REPO_ADDRESS = "https://neocpt.github.io/reelsoff-fdroid/repo"
SCRATCH = HERE / ".build"


def read_store_password() -> str:
    props = Path(r"C:\Users\coupa\OneDrive\Desktop\claude\ReelsOff\keystore.properties")
    for line in props.read_text(encoding="utf-8").splitlines():
        if line.startswith("storePassword="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("storePassword introuvable dans keystore.properties")


def cert_der(password: str) -> bytes:
    SCRATCH.mkdir(exist_ok=True)
    pem_path = SCRATCH / "cert.pem"
    subprocess.run(
        [str(KEYTOOL), "-exportcert", "-rfc", "-alias", KEYALIAS, "-keystore", str(KEYSTORE),
         "-storepass", password, "-file", str(pem_path)],
        check=True, capture_output=True,
    )
    body = "".join(line for line in pem_path.read_text().splitlines() if not line.startswith("-----"))
    return base64.b64decode(body)


def main() -> None:
    if not APK.exists():
        raise SystemExit(f"APK introuvable : {APK}")

    apk_bytes = APK.read_bytes()
    apk_sha256 = hashlib.sha256(apk_bytes).hexdigest()
    der = cert_der(read_store_password())
    now_ms = int(time.time() * 1000)

    repo = {
        "name": "ReelsOff",
        "description": "Dépôt personnel de ReelsOff (coupe les Reels, Shorts et Spotlight).",
        "address": REPO_ADDRESS,
        "version": 21,
        "timestamp": now_ms,
    }

    app = {
        "packageName": PKG,
        "name": "ReelsOff",
        "summary": "Coupe les Reels Instagram, les Shorts YouTube et le Spotlight Snapchat.",
        "description": "Quitte l'onglet Reels d'Instagram, ferme le lecteur Shorts de YouTube "
                       "et quitte le Spotlight de Snapchat. Aucune donnée n'est envoyée.",
        "license": "MIT",
        "categories": ["System"],
        "suggestedVersionName": VERSION_NAME,
        "suggestedVersionCode": str(VERSION_CODE),
        "added": now_ms,
        "lastUpdated": now_ms,
    }

    package = {
        "apkName": APK.name,
        "hash": apk_sha256,
        "hashType": "sha256",
        "packageName": PKG,
        "versionName": VERSION_NAME,
        "versionCode": VERSION_CODE,
        "size": len(apk_bytes),
        "sig": hashlib.md5(der).hexdigest(),
        "signer": hashlib.sha256(der).hexdigest(),
        "minSdkVersion": MIN_SDK,
        "targetSdkVersion": TARGET_SDK,
        "added": now_ms,
    }

    index = {
        "repo": repo,
        "requests": {"install": [], "uninstall": []},
        "apps": [app],
        "packages": {PKG: [package]},
    }

    SCRATCH.mkdir(exist_ok=True)
    json_path = SCRATCH / "index-v1.json"
    json_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    jar_path = REPO / "index-v1.jar"
    if jar_path.exists():
        jar_path.unlink()
    with zipfile.ZipFile(jar_path, "w", zipfile.ZIP_DEFLATED) as jar:
        jar.write(json_path, arcname="index-v1.json")

    password = read_store_password()
    subprocess.run(
        [str(JARSIGNER), "-keystore", str(KEYSTORE), "-storepass", password, "-keypass", password,
         "-sigalg", "SHA256withRSA", "-digestalg", "SHA-256", str(jar_path), KEYALIAS],
        check=True,
    )
    print(f"Index généré : {jar_path}")
    print(f"APK sha256 : {apk_sha256}")


if __name__ == "__main__":
    main()
