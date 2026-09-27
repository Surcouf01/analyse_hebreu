"""Résolution de chemins compatible à la fois avec une exécution depuis les
sources et depuis un exécutable PyInstaller (onefile ou onedir).

PyInstaller extrait ou installe les données à un emplacement qui n'est pas
celui du script compilé : pour les fichiers embarqués, le dossier de
référence est ``sys._MEIPASS`` ; pour les données modifiables ou volumineuses
qui restent à côté de l'exécutable (base BHSA, clone git), c'est le dossier
de l'exécutable lui-même.
"""

import os
import sys


def resource_dir():
    """Dossier des ressources embarquées (données en lecture seule).

    En exécution normale : dossier du paquet ``bhsa_grammar``.
    Sous PyInstaller : ``sys._MEIPASS`` (dossier d'extraction temporaire en
    mode onefile, dossier ``_internal`` en mode onedir), où le .spec recrée
    l'arborescence ``bhsa_grammar/`` et ``data/``.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def app_dir():
    """Dossier de l'application (exécutable ou sources).

    C'est l'emplacement attendu pour les données externes que l'utilisateur
    fournit ou modifie : ``bhsa_repo/``, ``bhsa_data/``, ``gui.properties``
    surchargé, etc.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
