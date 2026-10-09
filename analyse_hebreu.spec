# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller pour analyse_hebreu.

Builds :
    pyinstaller analyse_hebreu.spec            # GUI onedir (recommandé)
    pyinstaller analyse_hebreu.spec --         # identique (défaut)

Variables d'environnement :
    SPEC_TARGET=gui|cli        cible (défaut : gui)
    SPEC_MODE=onedir|onefile   mode (défaut : onedir, démarrage plus rapide
                               et moins lourd pour l'antivirus)
    SPEC_BHSA_DIR=none         N'embarque PAS la base BHSA (build léger,
                               ~50 Mo de moins ; la base devra être
                               installée à côté de l'exécutable ou
                               chargée en ligne).

Comportement par défaut : la base BHSA (features tf/c, ~240 Mo) est
automatiquement clonée depuis ETCBC/bhsa (branche data2021, clone sparse)
si elle n'est pas déjà présente en local (bhsa_repo/tf/c ou BHSA_DATA),
puis embarquée dans l'exécutable — l'utilisateur final n'a rien à
installer et rien à télécharger au lancement. SPEC_BHSA_DIR peut aussi
pointer vers un dossier tf/c existant pour fournir une base précise.

Notes :
    analyse_hebreu.py (CLI) est inclus comme module importable, ce qui
    permet au GUI packagé de rester focalisé sur l'interface ; le CLI peut
    être reconstruit séparément avec SPEC_TARGET=cli.
"""

import os

import PyInstaller.utils.hooks as hooks

# SPECPATH est injecté par PyInstaller (dossier du .spec) : tous les chemins
# du projet y sont ancrés pour que le build soit identique quel que soit le
# répertoire courant d'appel de pyinstaller. Sans cela, icone.ico résolu
# relativement au répertoire courant peut rester introuvable et PyInstaller
# embarque alors son icône par défaut (la plume).
spec_dir = globals().get("SPECPATH") or os.path.abspath(".")

target = os.environ.get("SPEC_TARGET", "gui")
mode = os.environ.get("SPEC_MODE", "onedir")
onefile = mode == "onefile"
bhsa_dir = os.environ.get("SPEC_BHSA_DIR", "")


def _locate_bhsa():
    """Renvoie le dossier tf/c des features BHSA, ou None si l'utilisateur
    a explicitement demandé un build sans base (SPEC_BHSA_DIR=none).

    Ordre de résolution :
      1. SPEC_BHSA_DIR (chemin explicite ou "none") ;
      2. un dossier tf/c déjà présent localement : BHSA_DATA, bhsa_repo/ ;
      3. clonage automatique (clone sparse de ETCBC/bhsa, branche data2021)
         dans bhsa_repo/ à côté du spec — la dernière version de la base
         est ainsi embarquée à chaque build.
    """
    bhsa = bhsa_dir
    if bhsa.lower() == "none":
        return None
    if bhsa:
        if not os.path.isabs(bhsa):
            bhsa = os.path.join(spec_dir, bhsa)
        if not os.path.isfile(os.path.join(bhsa, "otype.tf")):
            raise SystemExit(
                "SPEC_BHSA_DIR=%s ne contient pas otype.tf (attendu : dossier "
                "tf/c du clone ETCBC/bhsa)" % bhsa
            )
        return bhsa
    candidates = [
        os.environ.get("BHSA_DATA"),
        os.path.join(spec_dir, "bhsa_repo", "tf", "c"),
    ]
    for cand in candidates:
        if cand and os.path.isfile(os.path.join(cand, "otype.tf")):
            return cand
    import subprocess
    repo = "https://github.com/ETCBC/bhsa.git"
    dest = os.path.join(spec_dir, "bhsa_repo")
    print("[spec] BHSA absente : clonage sparse de %s (branche data2021)..." % repo)
    subprocess.check_call(
        ["git", "clone", "--branch", "data2021", "--depth", "1",
         "--filter=blob:none", "--sparse", repo, dest]
    )
    subprocess.check_call(["git", "-C", dest, "sparse-checkout", "set", "tf/c"])
    tfc = os.path.join(dest, "tf", "c")
    if not os.path.isfile(os.path.join(tfc, "otype.tf")):
        raise SystemExit("Clonage de la BHSA échoué : %s incomplet" % tfc)
    return tfc


bhsa_tf_dir = _locate_bhsa()

# Text-Fabric charge des données depuis son paquet (tf/*) : on embarque
# tout le paquet tf pour garantir la disponibilité des resources.
tf_datas = hooks.collect_data_files("tf", include_py_files=False)

# Version du projet : lue depuis le fichier VERSION à la racine des sources.
# Elle est embarquée dans le bundle (le GUI/CLI l'affichent via
# bhsa_grammar.__version__) et sert de ressource de version Windows pour
# l'exécutable (Propriétés → Détails).
version = ""
version_path = os.path.join(spec_dir, "VERSION")
if os.path.isfile(version_path):
    with open(version_path, encoding="utf-8") as fh:
        version = fh.read().strip()


def _version_tuple(v):
    """"1.0" -> (1, 0, 0, 0) : parties numériques de la version,
    complétées à 4 chiffres pour la ressource Windows."""
    parts = []
    for chunk in v.replace("-", ".").split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


datas = [
    ("bhsa_grammar/*.json", "bhsa_grammar"),
    ("data", "data"),
    ("icone.ico", "."),
    ("gui.properties", "."),
] + tf_datas
# icone.png (source de l'icône) : embarqué seulement s'il est présent —
# le spec n'échoue pas s'il a été retiré du dépôt (icone.ico reste la
# référence pour la fenêtre, la barre des tâches et l'exe).
if os.path.isfile(os.path.join(spec_dir, "icone.png")):
    datas.append((os.path.join(spec_dir, "icone.png"), "."))
if version:
    datas.append((version_path, "."))

# Base BHSA embarquée : les features tf/c sont installées sous
# bhsa_data/tf/c dans le bundle, où loader.py les trouve automatiquement.
if bhsa_tf_dir:
    datas.append((bhsa_tf_dir, "bhsa_data/tf/c"))

hiddenimports = [
    "tf",
    "tf.app",
    "tf.fabric",
    "tf.core",
    "tf.convert",
    "tf.core.api",
    "tf.core.nodefeature",
    "tf.core.helpers",
    "tf.convert.walker",
    "tf.parameters",
    "tf.core.timestamp",
    "win32com",
    "win32com.client",
    "pythoncom",
]

a = Analysis(
    ["gui_hebreu.py" if target == "gui" else "analyse_hebreu.py"],
    pathex=[spec_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "pandas", "scipy", "pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

# Ressource de version Windows : visible dans les Propriétés → Détails de
# l'exécutable (explorateur). Construite uniquement sous Windows (les
# utilitaires PyInstaller de gestion des ressources Win32 exigent win32api).
exe_version_resource = None
if version and os.name == "nt":
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo,
        StringFileInfo,
        StringStruct,
        StringTable,
        VarFileInfo,
        VarStruct,
        VSVersionInfo,
    )

    vtuple = _version_tuple(version)
    exe_version_resource = VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=vtuple,
            prodvers=vtuple,
            mask=0x3F,
            flags=0x0,
            OS=0x40004,
            fileType=0x1,
        ),
        kids=[
            StringFileInfo([
                StringTable("040904B0", [
                    StringStruct("CompanyName", "Surcouf01"),
                    StringStruct("FileDescription", "Analyseur grammatical de l'hébreu biblique"),
                    StringStruct("FileVersion", version),
                    StringStruct("InternalName", "analyse_hebreu"),
                    StringStruct("LegalCopyright", ""),
                    StringStruct("OriginalFilename", "analyse_hebreu.exe"),
                    StringStruct("ProductName", "Analyseur grammatical de l'hébreu biblique"),
                    StringStruct("ProductVersion", version),
                ]),
            ]),
            VarFileInfo([VarStruct("Translation", [0x0409, 1200])]),
        ],
    )


icon_path=os.path.join(spec_dir, "icone.ico") if os.path.isfile(os.path.join(spec_dir, "icone.ico")) else None

if onefile:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="analyse_hebreu" + ("" if target == "gui" else "-cli"),
        debug=False,
        strip=False,
        upx=False,
        console=False if target == "gui" else True,
        icon=icon_path,
        version=exe_version_resource,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="analyse_hebreu" + ("" if target == "gui" else "-cli"),
        debug=False,
        strip=False,
        upx=False,
        console=False if target == "gui" else True,
        icon=icon_path,
        version=exe_version_resource,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name="analyse_hebreu" + ("" if target == "gui" else "-cli"),
    )


# --- Post-build (GUI uniquement) --------------------------------------------
# À côté de l'exécutable GUI : copie du README.md et génération d'un
# gui.properties avec les valeurs par défaut (l'utilisateur peut y
# personnaliser polices et traductions ; le GUI le lit à côté de l'exécutable
# avant les ressources internes). Puis zip du bundle GUI complet en
# analyse_hebreu-<mode>-<plateforme>.zip.
#
# onedir : l'exécutable et ses ressources vivent dans dist/analyse_hebreu/,
#          le zip reprend tout ce répertoire (racine analyse_hebreu/).
# onefile : l'exécutable est seul dans dist/, README.md et gui.properties
#          sont copiés à côté de lui et zippés avec lui.
if target == "gui":
    import platform
    import shutil
    import zipfile

    dist_dir = DISTPATH if onefile else os.path.join(DISTPATH, "analyse_hebreu")

    readme_src = os.path.join(spec_dir, "README.md")
    if os.path.isfile(readme_src):
        shutil.copy2(readme_src, os.path.join(dist_dir, "README.md"))

    default_props = """# Propriétés d'affichage de l'interface graphique (gui_hebreu.py).
# Format : clé = valeur, encodage UTF-8. Les tailles sont en points.
# Ce fichier, placé à côté de l'exécutable, personnalise l'affichage sans
# toucher aux ressources internes ; il est réécrit à la fermeture pour
# mémoriser la géométrie de la fenêtre.

# Police de saisie de l'hébreu (champs Mot et Phrase).
font.input.family = DejaVu Sans
font.input.size = 14

# Police de la zone de résultat.
font.output.family = DejaVu Sans
font.output.size = 24

# Police des titres d'onglets (binyanim).
font.tabs.family = DejaVu Sans
font.tabs.size = 20

# Traductions affichées par défaut dans l'onglet Livre (true/false).
translation.fr = true
translation.en = true
translation.es = true
"""
    props_path = os.path.join(dist_dir, "gui.properties")
    if not os.path.isfile(props_path):
        with open(props_path, "w", encoding="utf-8") as fh:
            fh.write(default_props)

    zip_name = "analyse_hebreu-%s-%s.zip" % (mode, platform.system().lower())
    zip_path = os.path.join(DISTPATH, zip_name)
    # Liste des fichiers avant création du zip : en mode onefile le zip est
    # écrit dans le même répertoire que celui parcouru, il ne doit pas
    # s'inclure lui-même.
    entries = []
    for folder, _dirs, files in os.walk(dist_dir):
        for fname in files:
            fpath = os.path.join(folder, fname)
            if onefile and fname not in (
                "README.md", "gui.properties", "analyse_hebreu",
                "analyse_hebreu.exe",
            ):
                continue
            arcname = os.path.join(
                "analyse_hebreu", os.path.relpath(fpath, dist_dir)
            )
            entries.append((fpath, arcname))
    if os.path.isfile(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath, arcname in entries:
            zf.write(fpath, arcname)
    print("[spec] Post-build : README.md et gui.properties copiés ; zip -> %s"
          % zip_path)
