"""Génère l'index F-Droid v2 (index-v2.json + entry.json + entry.jar) et l'index v1 signé,
sous Windows, sans Linux. Reprend la structure écrite par fdroidserver (make_v2, convert_version,
v2_repo, package_metadata, signindex.sign_index).

Usage : python make_index_v2.py
"""
import base64
import hashlib
import json
import subprocess
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE / "repo"
APK = REPO / "com.neo.reelsoff_1.apk"
ICON = REPO / "icon.png"
KEYSTORE = Path(r"C:\Users\coupa\.reelsoff\reelsoff-release.jks")
KEYALIAS = "reelsoff"
PROPS = Path(r"C:\Users\coupa\OneDrive\Desktop\claude\ReelsOff\keystore.properties")
JDK = Path(r"C:\Program Files\Android\Android Studio\jbr\bin")
KEYTOOL = JDK / "keytool.exe"
JARSIGNER = JDK / "jarsigner.exe"
SCRATCH = HERE / ".build"

PKG = "com.neo.reelsoff"
VERSION_CODE = 1
VERSION_NAME = "1.0"
MIN_SDK = 26
TARGET_SDK = 34
REPO_ADDRESS = "https://neocpt.github.io/reelsoff-fdroid/repo"
REPO_VERSION = 22
LOCALE = "en-US"


def store_password() -> str:
    for line in PROPS.read_text(encoding="utf-8").splitlines():
        if line.startswith("storePassword="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("storePassword introuvable")


def cert_der(password: str) -> bytes:
    SCRATCH.mkdir(exist_ok=True)
    pem = SCRATCH / "cert.pem"
    subprocess.run(
        [str(KEYTOOL), "-exportcert", "-rfc", "-alias", KEYALIAS, "-keystore", str(KEYSTORE),
         "-storepass", password, "-file", str(pem)],
        check=True, capture_output=True,
    )
    body = "".join(line for line in pem.read_text().splitlines() if not line.startswith("-----"))
    return base64.b64decode(body)


def file_entry(path: Path, name: str) -> dict:
    data = path.read_bytes()
    return {"name": name, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def sign_jar(jar: Path, password: str, old_algs: bool) -> None:
    if old_algs:
        sig = ["-sigalg", "SHA1withRSA", "-digestalg", "SHA1"]
    else:
        sig = ["-sigalg", "SHA256withRSA", "-digestalg", "SHA-256"]
    subprocess.run(
        [str(JARSIGNER), "-keystore", str(KEYSTORE), "-storepass", password, "-keypass", password,
         *sig, str(jar), KEYALIAS],
        check=True, capture_output=True,
    )


def main() -> None:
    if not APK.exists() or not ICON.exists():
        raise SystemExit("APK ou icône manquant dans repo/")

    password = store_password()
    der = cert_der(password)
    now_ms = int(time.time() * 1000)
    signer = hashlib.sha256(der).hexdigest()

    apk_entry = file_entry(APK, f"/{APK.name}")
    icon_entry = file_entry(ICON, "/icon.png")

    repo = {
        "name": {LOCALE: "ReelsOff"},
        "description": {LOCALE: "Dépôt personnel de ReelsOff (coupe les Reels, Shorts et Spotlight)."},
        "icon": {LOCALE: icon_entry},
        "address": REPO_ADDRESS,
        "timestamp": now_ms,
        "version": REPO_VERSION,
    }

    metadata = {
        "added": now_ms,
        "lastUpdated": now_ms,
        "license": "MIT",
        "categories": ["System"],
        "name": {LOCALE: "ReelsOff"},
        "summary": {LOCALE: "Coupe les Reels Instagram, les Shorts YouTube et le Spotlight Snapchat."},
        "description": {LOCALE: "Quitte l'onglet Reels d'Instagram, ferme le lecteur Shorts de YouTube "
                                "et quitte le Spotlight de Snapchat. Aucune donnée n'est envoyée."},
        "icon": {LOCALE: file_entry(ICON, "/icon.png")},
        "preferredSigner": signer,
    }

    version = {
        "added": now_ms,
        "file": apk_entry,
        "manifest": {
            "versionName": VERSION_NAME,
            "versionCode": VERSION_CODE,
            "usesSdk": {"minSdkVersion": MIN_SDK, "targetSdkVersion": TARGET_SDK},
            "signer": {"sha256": [signer]},
        },
    }

    index_v2 = {
        "repo": repo,
        "packages": {PKG: {"metadata": metadata, "versions": {apk_entry["sha256"]: version}}},
    }
    index_v2_path = REPO / "index-v2.json"
    index_v2_path.write_text(json.dumps(index_v2, ensure_ascii=False, indent=2), encoding="utf-8")

    # entry.json : décrit l'index v2 (taille et hash), puis entry.jar signé
    entry = {
        "timestamp": now_ms,
        "version": REPO_VERSION,
        "index": {
            "name": "/index-v2.json",
            "sha256": hashlib.sha256(index_v2_path.read_bytes()).hexdigest(),
            "size": index_v2_path.stat().st_size,
            "numPackages": 1,
        },
        "diffs": {},
    }
    entry_json = REPO / "entry.json"
    entry_json.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    entry_jar = REPO / "entry.jar"
    entry_jar.unlink(missing_ok=True)
    with zipfile.ZipFile(entry_jar, "w", zipfile.ZIP_DEFLATED) as jar:
        jar.write(entry_json, "entry.json")
    sign_jar(entry_jar, password, old_algs=False)

    # index-v1 : même contenu d'app, format v1, signé en SHA-1 comme le fait fdroidserver
    index_v1 = {
        "repo": {
            "name": "ReelsOff",
            "description": "Dépôt personnel de ReelsOff (coupe les Reels, Shorts et Spotlight).",
            "address": REPO_ADDRESS,
            "icon": "icon.png",
            "version": 21,
            "timestamp": now_ms,
        },
        "requests": {"install": [], "uninstall": []},
        "apps": [{
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
        }],
        "packages": {PKG: [{
            "apkName": APK.name,
            "hash": apk_entry["sha256"],
            "hashType": "sha256",
            "packageName": PKG,
            "versionName": VERSION_NAME,
            "versionCode": VERSION_CODE,
            "size": apk_entry["size"],
            "sig": hashlib.md5(der).hexdigest(),
            "signer": signer,
            "minSdkVersion": MIN_SDK,
            "targetSdkVersion": TARGET_SDK,
            "added": now_ms,
        }]},
    }
    index_v1_json = SCRATCH / "index-v1.json"
    SCRATCH.mkdir(exist_ok=True)
    index_v1_json.write_text(json.dumps(index_v1, ensure_ascii=False, indent=2), encoding="utf-8")
    index_v1_jar = REPO / "index-v1.jar"
    index_v1_jar.unlink(missing_ok=True)
    with zipfile.ZipFile(index_v1_jar, "w", zipfile.ZIP_DEFLATED) as jar:
        jar.write(index_v1_json, "index-v1.json")
    sign_jar(index_v1_jar, password, old_algs=True)

    print("Index v2, entry.jar et index-v1.jar générés dans repo/")


if __name__ == "__main__":
    main()
