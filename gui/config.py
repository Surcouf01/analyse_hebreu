"""Configuration du GUI : propriétés, polices, constantes.

Extrait de gui_hebreu.py (refactorisation en paquet gui/) : le
chargement de gui.properties, les polices dérivées, la géométrie et
les réglages d'impression sauvegardés, les constantes d'onglets.
"""

import json
import os
import re
import sys
import tempfile

TRANSLATIONS = (
    ("fr", "Louis Segond 1910 (fr)"),
    ("rab", "Bible du Rabbinat 1899 (fr)"),
    ("en", "King James Version 1611 (en)"),
    ("es", "Torres Amat 1823 (es)"),
    ("it", "Riveduta Luzzi 1927 (it)"),
)


def _resource_dir():
    """Dossier des ressources embarquées (PyInstaller ``sys._MEIPASS``) ;
    en développement, la racine du projet (au-dessus du paquet gui/)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return _properties_home()


def _app_dir():
    """Dossier de l'exécutable (données modifiables à côté du binaire) ;
    en développement, la racine du projet (au-dessus du paquet gui/)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return _properties_home()


def _properties_home():
    """Dossier de gui.properties : le répertoire du paquet gui/ en
    développement, la racine de l'application une fois figé par
    PyInstaller (les ressources restent à côté de l'exécutable)."""
    here = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        return here
    return os.path.dirname(here)


def _load_properties():
    """Charge les tailles de police depuis gui.properties (à côté du script).

    En cas d'absence ou d'erreur, retombe sur les valeurs par défaut.
    """
    defaults = {
        "font.input.family": "DejaVu Sans",
        "font.input.size": "14",
        "font.output.family": "DejaVu Sans",
        "font.output.size": "24",
    }
    path = os.path.join(_properties_home(), "gui.properties")
    if not os.path.isfile(path):
        for alt in (_resource_dir(), _app_dir()):
            path = os.path.join(alt, "gui.properties")
            if os.path.isfile(path):
                break
    defaults["_path"] = path
    try:
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                defaults[key.strip()] = value.strip()
    except OSError:
        pass
    return defaults


_PROPS = _load_properties()

# Géométrie par défaut de la fenêtre principale.
DEFAULT_GEOMETRY = "1200x1000"

# Réglages d'impression des binyanim (aperçu avant impression) : pages
# par feuille (1 ou 2) et taille de police du document (pourcentage des
# tailles de base), persistés dans gui.properties.
PRINT_PER_SHEET_DEFAULT = "1"
PRINT_FONT_SCALE_DEFAULT = "100"


def _saved_print_settings():
    """Réglages d'impression sauvegardés (pages/feuille, taille police)."""
    per_sheet = _PROPS.get("print.pages.per.sheet",
                           PRINT_PER_SHEET_DEFAULT).strip()
    if per_sheet not in ("1", "2"):
        per_sheet = PRINT_PER_SHEET_DEFAULT
    try:
        font_scale = int(float(_PROPS.get("print.font.scale",
                                          PRINT_FONT_SCALE_DEFAULT)))
    except ValueError:
        font_scale = int(PRINT_FONT_SCALE_DEFAULT)
    if not 60 <= font_scale <= 200:
        font_scale = int(PRINT_FONT_SCALE_DEFAULT)
    return per_sheet == "2", font_scale


def _saved_geometry():
    """Géométrie sauvegardée dans gui.properties, si elle est valide.

    Formats acceptés : « largeurxhauteur » ou « largeurxhauteur+X+Y »
    (coordonnées éventuellement négatives, écran multi-moniteurs).
    """
    geo = _PROPS.get("window.geometry", "").strip()
    if re.fullmatch(r"\d+x\d+(?:[+-]-?\d+[+-]-?\d+)?", geo):
        return geo
    return ""


def _save_properties(root, updates):
    """Écrit des paires clé/valeur dans gui.properties (géométrie de la
    fenêtre, traductions affichées…). Préserve le reste du fichier
    (commentaires, polices). En cas d'erreur d'E/S, l'échec est
    silencieux : la préférence est perdue mais l'application continue.
    """
    path = _PROPS.get("_path")
    if not path:
        return
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        lines = []
    written = set()
    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, _ = line.partition("=")
        if k.strip() in updates:
            lines[i] = f"{k.strip()} = {updates[k.strip()]}\n"
            written.add(k.strip())
    # Clés absentes du fichier : ajoutées en fin, avec commentaire de
    # section si nécessaire.
    missing = {k: v for k, v in updates.items() if k not in written}
    if missing:
        if lines and lines[-1].strip():
            lines.append("\n")
        if "window.geometry" in missing:
            lines.append("# Position et taille de la fenêtre principale "
                         "(sauvegardées à la fermeture).\n")
        if any(k.startswith("translation.") for k in missing):
            lines.append("# Traductions affichées par défaut dans l'onglet "
                         "Verset (true/false).\n")
        if "audio.speed" in missing:
            lines.append("# Vitesse de lecture du verset (0.5 à 2.0 ; "
                         "1.0 = normale).\n")
        if "audio.voice" in missing:
            lines.append("# Voix de lecture du verset (shaul ou michael).\n")
        if any(k.startswith("print.") for k in missing):
            lines.append("# Aperçu avant impression des binyanim : pages par "
                         "feuille (1 ou 2) et taille de police du "
                         "document (60 à 200, en pourcentage).\n")
        if any(k.startswith("binyanim.") for k in missing):
            lines.append("# Onglet Binyanim : signaler les binyanim "
                         "mishnaïques (Sefaria) et modernes (Pealim) "
                         "(true/false).\n")
        for k, v in missing.items():
            lines.append(f"{k} = {v}\n")
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.writelines(lines)
    except OSError:
        return
    # Écriture réussie : répercuter en mémoire (_PROPS est chargé une
    # seule fois au démarrage ; sans ça, une relecture dans la même
    # session — ex. réouverture de l'aperçu d'impression — verrait les
    # anciennes valeurs).
    _PROPS.update(updates)


def _github_slug(text):
    """Ancre GitHub d'un titre markdown (cf. scripts/generate_toc.py) :
    minuscules, ponctuation supprimée, espaces remplacées par des
    traits d'union. Utilisée pour faire correspondre les liens du
    sommaire aux titres rendus dans l'onglet README."""
    slug = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE)
    slug = re.sub(r"\s+", "-", slug).strip("-")
    return slug


def _font(prop_family, prop_size):
    try:
        size = int(_PROPS[prop_size])
    except (ValueError, KeyError):
        size = 14
    family = _PROPS.get(prop_family, "DejaVu Sans")
    return (family, size)


# Polices : saisie de l'hébreu (Mot/Phrase) et zone de résultat.
# Configurables via gui.properties (famille + taille en points).
HEBREW_FONT = _font("font.input.family", "font.input.size")
HEBREW_FONT_MONO = _font("font.output.family", "font.output.size")
# Police du clavier virtuel : reprend la police/ taille de sortie (output).
KEYBOARD_FONT = HEBREW_FONT_MONO
# Police des touches de voyelles (nikkud/dagesh/ratafim) : reprend la police/
# taille de sortie, touche plus grande que les consonnes. La rangée des
# voyelles est répartie sur deux lignes afin de tenir sur une largeur
# d'écran ordinaire.
_v_fam, _v_size = KEYBOARD_FONT
KEYBOARD_FONT_VOWELS = (_v_fam, _v_size)
# Police des touches de consonnes : 5 points plus petite que celle des
# voyelles.
KEYBOARD_FONT_CONSONANTS = (_v_fam, max(6, _v_size - 5))

# Police des titres d'onglets (binyanim) : configurable via gui.properties
# (clés font.tabs.family / font.tabs.size), avec repli sur la police de
# saisie si les clés sont absentes.
def _tab_font():
    try:
        size = int(_PROPS["font.tabs.size"])
    except (KeyError, ValueError):
        size = HEBREW_FONT[1]
    family = _PROPS.get("font.tabs.family", HEBREW_FONT[0])
    return (family, size)


BINYAN_TAB_FONT = _tab_font()

# Onglet « Livre » : corpus disponibles.
CORPUS_BIBLE = "Bible (BHSA)"
CORPUS_MISHNA = "Mishna (Sefaria)"
