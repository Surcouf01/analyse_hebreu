"""Vérifie que tous les imports externes des points d'entrée sont résolus.

Utilisé par le workflow CI (build-executables.yml) avant le build PyInstaller
pour échouer tôt si une dépendance (ex. PIL, pywin32) manque dans
requirements.txt. Sort avec un code non nul et liste les modules manquants.

Usage : python scripts/check_imports.py [fichier1 fichier2 ...]
Sans argument, vérifie les points d'entrée par défaut du projet.
"""

import ast
import importlib.util
import sys
from pathlib import Path

# Modules graphiques/Win32 fournis par l'interpréteur ou optionnels selon la
# plateforme : non vérifiés par find_spec (tkinter est inclus dans l'install
# Windows/macOS de Python ; win32* sont couverts par pywin32 sous Windows).
SKIPPED_PREFIXES = ("tkinter", "win32con", "win32gui", "win32ui")

# Modules locaux du dépôt : résolus relativement au répertoire racine du
# projet (cwd du script), pas via site-packages.
LOCAL_PACKAGES = ("bhsa_grammar", "bidi_display", "verse_audio", "curation")

DEFAULT_TARGETS = (
    "gui_hebreu.py",
    "analyse_hebreu.py",
    "verse_audio.py",
    "bidi_display.py",
)


def iter_imports(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module


def main(argv):
    targets = argv[1:] or list(DEFAULT_TARGETS)
    missing = []
    for target in targets:
        for module in iter_imports(target):
            top = module.split(".")[0]
            if top in SKIPPED_PREFIXES or top in LOCAL_PACKAGES:
                continue
            try:
                found = importlib.util.find_spec(module) is not None
            except ModuleNotFoundError:
                found = False
            if not found:
                missing.append((target, module))
    if missing:
        print("Imports manquants:", sorted(set(missing)))
        return 1
    print("Tous les imports externes sont resolus.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
