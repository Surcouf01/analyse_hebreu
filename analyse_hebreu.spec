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

datas = [
    ("bhsa_grammar/*.json", "bhsa_grammar"),
    ("data", "data"),
    ("icone.png", "."),
    ("icone.ico", "."),
    ("gui.properties", "."),
] + tf_datas

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
        icon=os.path.join(spec_dir, "icone.ico") if os.path.isfile(os.path.join(spec_dir, "icone.ico")) else None,
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
        icon=os.path.join(spec_dir, "icone.ico") if os.path.isfile(os.path.join(spec_dir, "icone.ico")) else None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name="analyse_hebreu" + ("" if target == "gui" else "-cli"),
    )
