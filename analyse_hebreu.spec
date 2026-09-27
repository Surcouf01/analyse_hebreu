# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller pour analyse_hebreu.

Builds :
    pyinstaller analyse_hebreu.spec            # GUI onedir (recommandé)
    pyinstaller analyse_hebreu.spec --         # identique (défaut)

Variables d'environnement :
    SPEC_TARGET=gui|cli        cible (défaut : gui)
    SPEC_MODE=onedir|onefile   mode (défaut : onedir, démarrage plus rapide
                               et moins lourd pour l'antivirus)
    SPEC_BHSA_DIR=CHEMIN       embarque la base BHSA (dossier tf/c des
                               features, ~150-240 Mo) dans l'exécutable :
                               aucune installation manuelle n'est alors
                               nécessaire. Défaut : non embarquée.

Notes :
    analyse_hebreu.py (CLI) est inclus comme module importable, ce qui
    permet au GUI packagé de rester focalisé sur l'interface ; le CLI peut
    être reconstruit séparément avec SPEC_TARGET=cli.
"""

import os

import PyInstaller.utils.hooks as hooks

target = os.environ.get("SPEC_TARGET", "gui")
mode = os.environ.get("SPEC_MODE", "onedir")
onefile = mode == "onefile"
bhsa_dir = os.environ.get("SPEC_BHSA_DIR")

# Text-Fabric charge des données depuis son paquet (tf/*) : on embarque
# tout le paquet tf pour garantir la disponibilité des resources.
tf_datas = hooks.collect_data_files("tf", include_py_files=False)

datas = [
    ("bhsa_grammar/*.json", "bhsa_grammar"),
    ("data", "data"),
    ("icone.png", "."),
    ("icone.ico", "."),
    ("gui.properties", "."),
] + tf_datas

# Base BHSA embarquée : les features tf/c sont installées sous
# bhsa_data/tf/c dans le bundle, où loader.py les trouve automatiquement.
if bhsa_dir:
    if not os.path.isfile(os.path.join(bhsa_dir, "otype.tf")):
        raise SystemExit(
            "SPEC_BHSA_DIR=%s ne contient pas otype.tf (attendu : dossier "
            "tf/c du clone ETCBC/bhsa)" % bhsa_dir
        )
    datas.append((bhsa_dir, "bhsa_data/tf/c"))

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
]

a = Analysis(
    ["gui_hebreu.py" if target == "gui" else "analyse_hebreu.py"],
    pathex=[os.path.abspath(".")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "pandas", "scipy", "pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

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
        icon="icone.ico" if os.path.exists("icone.ico") else None,
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
        icon="icone.ico" if os.path.exists("icone.ico") else None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name="analyse_hebreu" + ("" if target == "gui" else "-cli"),
    )
