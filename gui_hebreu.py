#!/usr/bin/env python3
"""Interface graphique de l'analyseur grammatical de l'hébreu biblique.

Fenêtre Tkinter à onglets qui reprend chacune des fonctions du programme en
ligne de commande (``analyse_hebreu.py``) :

  - Onglet « Livre »   : sélection du corpus (Bible hébraïque via la base
    BHSA, ou Mishna via l'API Sefaria), puis analyse d'un verset (Bible)
    ou affichage d'une mishna (Mishna) par sélection successive du livre,
    du chapitre puis du verset, au moyen de listes déroulantes bornées aux
    limites réelles de la base BHSA ou du catalogue Mishna.
  - Onglet « Mot »     : analyse d'un mot hébreu isolé, saisie via un clavier
    hébreu virtuel (points-voyelles inclus) en UTF-8.
  - Onglet « Phrase »  : analyse d'une phrase hébreu libre, saisie via le
    même clavier hébreu virtuel.

Lancement :

    python gui_hebreu.py

La base BHSA est chargée en arrière-plan au démarrage (cf. ``bhsa_grammar``).
"""

import ctypes
import os
import queue
import re
import signal
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import tempfile
from PIL import Image
from PIL.ImageWin import Dib

from bidi_display import (
    to_visual,
    to_logical,
    logical_wrap,
    looks_visual,
    clusters,
    visual_caret_offsets,
    logical_boundary_at,
    normalize_query,
    find_line_matches,
    has_hebrew_letters,
)

from bhsa_grammar import (
    __version__,
    load_corpus,
    analyze_verse_by_reference,
    analyze_word,
    analyze_phrase,
    analyze_binyanim,
    format_text,
    format_json,
    format_summary,
    format_word,
    format_word_json,
    format_phrase,
    format_phrase_json,
    format_binyanim,
    format_binyanim_json,
    parse_binyanim_text,
    WEAK_CONJ_RULES,
    book_french,
    DataNotFoundError,
    load_translation,
    get_translation,
    TranslationNotFoundError,
)
from bhsa_grammar.sefaria_client import fetch_mishnah_mishnayot
from bhsa_grammar.mishnah_catalog import SEDARIM, STRUCTURE, SCHWAB_TRACTATES
from bhsa_grammar.mishnah_analyzer import (
    analyze_mishnah_text,
    mishnah_analysis_block,
)
import verse_audio
import binyan_print
from stable_selection import StableSelection
from verse_audio import (
    VersePlayer,
    VersePlayerError,
    synthesize_wav,
    VOICES,
)


# Langues de traduction disponibles, avec leur libellé.
TRANSLATIONS = (
    ("fr", "Louis Segond 1910 (fr)"),
    ("rab", "Bible du Rabbinat 1899 (fr)"),
    ("en", "King James Version 1611 (en)"),
    ("es", "Torres Amat 1823 (es)"),
    ("it", "Riveduta Luzzi 1927 (it)"),
)


def _resource_dir():
    """Dossier des ressources embarquées (PyInstaller ``sys._MEIPASS``)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _app_dir():
    """Dossier de l'exécutable (données modifiables à côté du binaire)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


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
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "gui.properties")
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


# --- Clavier hébreu virtuel ------------------------------------------------
# Points-voyelles (nikkud) et daguesh — marques combinantes UTF-8.
_NIKKUD = {
    "qamats": "\u05B8",      # ָ
    "patach": "\u05B7",      # ַ
    "segol": "\u05B6",       # ֶ
    "tsere": "\u05B5",       # ֵ
    "hireq": "\u05B4",       # ִ
    "holem": "\u05B9",       # ֹ
    "qubuts": "\u05BB",     # ֻ
    "sheva": "\u05B0",       # ְ
    "dagesh": "\u05BC",     # ּ
    "qamats_qatan": "\u05C7",  # ַ (qamats qatan / qamats hatuf)
    # Points de shin/sin (distinguent שׁ shin de שׂ sin).
    "shin_dot": "\u05C1",   # שׁ (shin)
    "sin_dot": "\u05C2",   # שׂ (sin)
    # Ratafim (hateph) : voyelles ultracourtes.
    "hateph_segol": "\u05B1",   # ֱ
    "hateph_patach": "\u05B2",  # ֲ
    "hateph_qamats": "\u05B3",  # ֳ
}

# Libellés des touches de voyelles : glyphes Unicode purs. Les marques
# combinantes (nikkud/dagesh) sont portées par un cercle pointillé (U+25CC ◌),
# convention standard pour afficher un signe diacritique isolé.
_CARRIER = "\u25CC"
# Cependant, selon la police du clavier (font.output.family), le moteur
# de rendu ne sait pas toujours attacher la marque au cercle pointillé :
# il la dessine alors sur son propre cercle de repli, et la touche
# affiche DEUX cercles. Un porteur consonantique hébreu (comme ש pour
# les points shin/sin) est attaché de façon fiable par toute police
# supportant l'hébreu.
_NIKKUD_CARRIER = "\u05D0"   # א
NIKKUD_LABELS = {
    "qamats": _NIKKUD_CARRIER + "\u05B8",
    "patach": _NIKKUD_CARRIER + "\u05B7",
    "segol": _NIKKUD_CARRIER + "\u05B6",
    "tsere": _NIKKUD_CARRIER + "\u05B5",
    "hireq": _NIKKUD_CARRIER + "\u05B4",
    "holem": _NIKKUD_CARRIER + "\u05B9",
    "qubuts": _NIKKUD_CARRIER + "\u05BB",
    "sheva": _NIKKUD_CARRIER + "\u05B0",
    "dagesh": _NIKKUD_CARRIER + "\u05BC",
    "qamats_qatan": _NIKKUD_CARRIER + "\u05C7",
    # Points de shin/sin.
    "shin_dot": "\u05E9\u05C1",
    "sin_dot": "\u05E9\u05C2",
    # Ratafim (hateph) : voyelles ultracourtes.
    "hateph_segol": _NIKKUD_CARRIER + "\u05B1",
    "hateph_patach": _NIKKUD_CARRIER + "\u05B2",
    "hateph_qamats": _NIKKUD_CARRIER + "\u05B3",
}

# Points-voyelles répartis sur deux rangées : voyelles principales, puis
# sheva/dagesh/qamats qatan, points shin-sin et ratafim.
NIKKUD_ROWS = (
    ("qamats", "patach", "segol", "tsere", "hireq", "holem", "qubuts",
     "sheva"),
    ("dagesh", "qamats_qatan", "shin_dot", "sin_dot",
     "hateph_segol", "hateph_patach", "hateph_qamats"),
)


# Disposition du clavier hébreu standard (Israel), par rangée.
# Chaque rangée correspond à une rangée physique d'un vrai clavier.
_HEBREW_ROWS = (
    # Rangée 1 (chiffres omises) : ;  /  '  ק ר א ט ו ן ם פ
    (";", "/", "'", "\u05E7", "\u05E8", "\u05D0", "\u05D8", "\u05D5",
     "\u05DF", "\u05DD", "\u05E4"),
    # Rangée 2 : ש ד ג כ ע י ח ל ך ף
    ("\u05E9", "\u05D3", "\u05D2", "\u05DB", "\u05E2", "\u05D9", "\u05D7",
     "\u05DC", "\u05DA", "\u05E3"),
    # Rangée 3 : ז ס ב ה נ מ צ ת ץ
    ("\u05D6", "\u05E1", "\u05D1", "\u05D4", "\u05E0", "\u05DE",
     "\u05E6", "\u05EA", "\u05E5"),
)


class BinyanimNotebook(ttk.Frame):
    """Bloc d'onglets des binyanim.

    Contrairement à ttk.Notebook, chaque titre d'onglet est un tk.Label :
    son libellé peut être coloré individuellement (rouge pour un binyan
    qui n'a pas de sens pour la racine analysée, jaune pour un binyan
    attesté dans la Mishna mais absent de la Bible, vert pour un binyan
    attesté en hébreu moderne — Pealim — mais absent de la Bible), ce que l'API
    ttk.Notebook ne permet pas.

    Repris l'API utile de ttk.Notebook : add/insert/forget/select/tabs/
    index, plus ``tab(tab_id, text=..., fg=...)`` pour modifier un onglet.
    Le widget enfant doit être griddé dans ``self.body`` par l'appelant.
    """

    _FG_ACTIVE = "black"
    _FG_INACTIVE = "gray40"
    _FG_MISSING = "#b00020"
    _FG_MISHNAH = "#b8a000"
    _FG_MODERN = "#007000"

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._tab_id_seq = 0
        self._tabs = []
        # barre de titres : rangée de labels cliquables
        self.bar = tk.Frame(self)
        self.bar.grid(row=0, column=0, sticky="ew")
        # corps : seul l'onglet sélectionné est griddé
        self.body = tk.Frame(self)
        self.body.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        # L'onglet sélectionné doit s'étendre sur toute la largeur/hauteur
        # du corps (sinon la zone de texte garde sa largeur demandée).
        self.body.rowconfigure(0, weight=1)
        self.body.columnconfigure(0, weight=1)
        self._selected = None

    def _tab_id(self):
        self._tab_id_seq += 1
        return f"tab{self._tab_id_seq}"

    def _button_fg(self, tab):
        if tab["fg"] is not None:
            return tab["fg"]
        return self._FG_ACTIVE if tab["id"] == self._selected else self._FG_INACTIVE

    def _refresh_bar(self):
        base_font, bold_font = self._btn_font()
        for tab in self._tabs:
            btn = tab["button"]
            btn.configure(foreground=self._button_fg(tab))
            btn.configure(font=bold_font if tab["id"] == self._selected else base_font)

    def _select(self, tab_id):
        for tab in self._tabs:
            if tab["id"] == tab_id:
                tab["widget"].grid(row=0, column=0, sticky="nsew")
                self._selected = tab_id
            else:
                tab["widget"].grid_forget()
        self._refresh_bar()

    def _on_click(self, tab_id):
        # tkinter callback : ne jamais laisser remonter d'exception
        self._select(tab_id)

    def _btn_font(self):
        """Police des titres d'onglets : normale, et grasse pour l'onglet actif.

        Famille et taille configurables via gui.properties
        (font.tabs.family / font.tabs.size, cf. BINYAN_TAB_FONT).
        """
        if not hasattr(self, "_fonts"):
            bold = tkfont.Font(root=self, font=BINYAN_TAB_FONT)
            bold.configure(weight="bold")
            self._fonts = (BINYAN_TAB_FONT, bold)
        return self._fonts


    def add(self, widget, text=""):
        return self.insert(len(self._tabs), widget, text=text)

    def insert(self, index, widget, text=""):
        tab_id = self._tab_id()
        btn = tk.Label(self.bar, text=text, padx=8, pady=3, takefocus=False)
        tab = {"id": tab_id, "widget": widget, "button": btn, "text": text,
               "fg": None}
        self._tabs.insert(index, tab)
        btn.bind("<Button-1>", lambda e, t=tab_id: self._on_click(t))
        # reconstruire la barre dans l'ordre logique des onglets
        for tab_ in self._tabs:
            tab_["button"].grid_forget()
        for i, tab_ in enumerate(self._tabs):
            tab_["button"].grid(row=0, column=i, sticky="w")
        if self._selected is None:
            self._select(tab_id)
        return tab_id

    def forget(self, tab_id):
        for i, tab in enumerate(self._tabs):
            if tab["id"] == tab_id:
                del self._tabs[i]
                tab["button"].destroy()
                tab["widget"].grid_forget()
                break
        else:
            return
        for i, tab_ in enumerate(self._tabs):
            tab_["button"].grid(row=0, column=i, sticky="w")
        if self._selected == tab_id:
            self._selected = None
            if self._tabs:
                self._select(self._tabs[0]["id"])

    def select(self, target):
        if self.index(target) is None:
            return
        self._select(self._resolve(target))

    def tab(self, target, text=None, fg=None):
        tab = self._find(target)
        if tab is None:
            return {}
        if text is not None:
            tab["text"] = text
            tab["button"].configure(text=text)
        if fg is not None:
            tab["fg"] = fg
        self._refresh_bar()
        return {"text": tab["text"]}

    def tabs(self):
        return [tab["id"] for tab in self._tabs]

    def index(self, target):
        tab = self._find(target)
        return None if tab is None else self._tabs.index(tab)

    def _resolve(self, target):
        tab = self._find(target)
        return tab["id"] if tab else None

    def _find(self, target):
        for tab in self._tabs:
            if target == tab["id"] or target == tab["widget"]:
                return tab
        return None


class HebrewKeyboard(ttk.Frame):
    """Clavier hébreu virtuel qui insère des caractères UTF-8 dans le widget
    texte ciblé (Entry ou Text).

    La disposition des consonnes reproduit celle d'un vrai clavier hébreu
    (3 rangées), suivie de deux rangées de points-voyelles (nikkud) et
    dagesh, puis d'une rangée de contrôles (espace, sof pasuq, retour).
    """

    def __init__(self, master, target_getter):
        super().__init__(master)
        # target_getter() renvoie le widget Entry/Text actuellement ciblé.
        self._get_target = target_getter

        # Style de touche utilisant la police de sortie (configurable).
        # Padding vertical accru pour que les diacritiques hauts (ex. hateph
        # qamats U+05B3) portés par le cercle ◌ ne soient pas tronqués.
        self._style = ttk.Style(self)
        # Style des touches de consonnes : police plus petite (5 points de
        # moins), style par défaut.
        self._style.configure("HebKey.TButton", font=KEYBOARD_FONT_CONSONANTS,
                              padding=(2, 10))
        # Style des touches de voyelles : police de sortie, taille pleine.
        self._style.configure("HebKeyVowel.TButton", font=KEYBOARD_FONT_VOWELS,
                              padding=(2, 10))

        # Rangées de consonnes (disposition clavier hébreu standard).
        for row in _HEBREW_ROWS:
            row_frame = ttk.Frame(self)
            row_frame.pack(fill="x", pady=(0, 2))
            for ch in row:
                self._make_key(row_frame, ch, ch)

        # Rangées de points-voyelles (nikkud) + dagesh : deux lignes pour
        # garder des touches de taille pleine.
        for row in NIKKUD_ROWS:
            nik_frame = ttk.Frame(self)
            nik_frame.pack(fill="x", pady=(4, 2))
            for key in row:
                self._make_key(nik_frame, _NIKKUD[key], NIKKUD_LABELS[key],
                               style="HebKeyVowel.TButton")

        # Rangée de contrôles.
        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", pady=(2, 0))
        self._make_key(ctrl, " ", "Espace", width=14)
        self._make_key(ctrl, "\u05C3", _CARRIER + "\u05C3", width=10,
                       style="HebKeyVowel.TButton")
        self._make_key(ctrl, None, "\u232B Retour", width=12, action="backspace")

    def _make_key(self, parent, char, label, width=4, action=None,
                  style="HebKey.TButton"):
        btn = ttk.Button(parent, text=label, width=width, style=style,
                         command=lambda c=char, a=action: self._press(c, a))
        btn.pack(side="left", padx=1, pady=1)
        return btn

    def _press(self, char, action):
        target = self._get_target()
        if target is None:
            return
        try:
            if action == "backspace":
                if isinstance(target, BidiHebrewText):
                    target._on_backspace()
                elif isinstance(target, tk.Text):
                    target.delete("insert-1c", "insert")
                else:
                    pos = target.index(tk.INSERT)
                    if pos > 0:
                        target.delete(pos - 1)
            elif isinstance(target, BidiHebrewText):
                target.insert_logical(char)
            else:
                target.insert(tk.INSERT, char)
                if isinstance(target, tk.Text):
                    target.see(tk.INSERT)
            target.focus_set()
        except tk.TclError:
            pass


class BidiHebrewText(tk.Text):
    """Champ de saisie hébreu (modes Mot, Phrase, Binyanim) : stockage
    VISUEL, édition LOGIQUE.

    La sélection à la souris dans un tk.Text hébreu en ordre logique
    « danse » sous Windows (moteur bidi Uniscribe : plusieurs indices
    logiques sont rendus au même pixel, w.index("@x,y") oscille entre
    eux). La seule architecture stable — celle de ResultText, et la
    recommandation de la communauté Tk pour l'RTL (wiki Tcl/Tk
    « bidi rendering », awesometkinter.bidirender) — est de stocker le
    texte en ordre VISUEL : l'ordre du widget coïncide avec
    l'affichage, la sélection est naturelle et stable.

    Mais un champ de saisie doit rester ÉDITABLE : on maintient donc un
    miroir LOGIQUE du contenu et on intercepte les opérations d'édition.
    Chaque édition (frappe, collage, effacement, coupure) est traduite
    en opération sur le miroir logique, puis le contenu stocké est
    régénéré (to_visual) et le caret replacé à la frontière logique
    correspondante (visual_caret_offsets). Les flèches se déplacent de
    cluster logique en cluster logique, dans l'ordre de lecture.
    get_logical() restitue le texte en ordre de lecture pour
    l'analyse ; la copie (Ctrl+C) copie l'ordre logique. Le clavier
    virtuel insère via insert_logical(). Ctrl-A sélectionne tout le
    texte logique ; Ctrl-Z/Ctrl-Y annulent et rétablissent.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logical_lines = [""]
        self._caret_line = 0
        self._caret_boundary = 0
        self._anchor_boundary = None
        # Annulation (Ctrl-Z) / rétablissement (Ctrl-Y) : pile
        # d'instantanés du miroir LOGIQUE (lignes + caret). Chaque
        # caractère tapé (ou effacé) forme son propre groupe, comme
        # dans un champ de saisie standard : Ctrl-Z annule le dernier
        # caractère, pas le mot entier.
        self._undo_stack = []
        self._redo_stack = []
        self.bind("<Control-z>", self._on_undo)
        self.bind("<Control-Z>", self._on_redo)
        self.bind("<Control-y>", self._on_redo)
        self.bind("<Control-Y>", self._on_redo)
        self.bind("<<Undo>>", self._on_undo)
        self.bind("<<Redo>>", self._on_redo)
        self.bind("<Control-a>", self._on_select_all)
        self.bind("<Control-A>", self._on_select_all)
        self.bind("<<Paste>>", self._on_paste)
        self.bind("<<Copy>>", self._on_copy)
        self.bind("<<Cut>>", self._on_cut)
        self.bind("<Key>", self._on_key)
        self.bind("<BackSpace>", self._on_backspace)
        self.bind("<Delete>", self._on_delete)
        self.bind("<Left>", self._on_left)
        self.bind("<Right>", self._on_right)
        self.bind("<Home>", self._on_home)
        self.bind("<End>", self._on_end)
        # Sélection à la souris : clic et glissement convertis en
        # frontières logiques (le texte stocké est VISUEL : son ordre
        # est l'ordre affiché, la sélection est stable par nature).
        self._sel_anchor = None
        self.bind("<Button-1>", self._on_mouse_down)
        self.bind("<B1-Motion>", self._on_mouse_drag)
        self.bind("<Shift-Button-1>", self._on_mouse_shift)
        self.bind("<Double-Button-1>", self._on_mouse_double)
        self.bind("<Triple-Button-1>", self._on_mouse_triple)
        # La sélection native doit rester visible par-dessus.
        self.tag_raise("sel")

    # --- Miroir logique --------------------------------------------------

    def set_logical(self, text):
        """Remplace le contenu (texte logique ; les \\n ouvrent des
        lignes logiques distinctes) et réinitialise l'historique
        d'annulation (remplacement programmatique, pas une édition)."""
        self._logical_lines = text.split("\n") if text else [""]
        self._caret_line = 0
        self._caret_boundary = 0
        self._anchor_boundary = None
        self._undo_stack = []
        self._redo_stack = []
        self._refresh()

    def get_logical(self):
        """Texte en ordre de lecture (pour l'analyse)."""
        return "\n".join(self._logical_lines)

    def _line_clusters(self):
        """Clusters logiques de la ligne du caret."""
        return clusters(self._logical_lines[self._caret_line])

    def _refresh(self):
        """Régénère le contenu stocké depuis le miroir logique, place
        le caret et restitue la sélection logique."""
        self.delete("1.0", "end")
        for i, line in enumerate(self._logical_lines):
            if i:
                self.insert("end-1c", "\n")
            self.insert("end", to_visual(line))
        self._apply_selection()
        self._place_caret()

    def _place_caret(self):
        offsets = visual_caret_offsets(self._logical_lines[self._caret_line])
        col = offsets[min(self._caret_boundary, len(offsets) - 1)]
        self.mark_set(tk.INSERT, f"{self._caret_line + 1}.{col}")
        self.see(tk.INSERT)

    def _sel_range(self):
        """Bornes logiques de la sélection (anchor, active) triées, ou
        (None, None) si pas de sélection."""
        if self._anchor_boundary is None:
            return None, None
        a = (self._caret_line, self._anchor_boundary)
        b = (self._caret_line, self._caret_boundary)
        return min(a, b), max(a, b)

    def _apply_selection(self):
        self.tag_remove("sel", "1.0", "end")
        a, b = self._sel_range()
        if a is None or a == b:
            return
        ia, ib = self._boundary_indices(a, b)
        # Sur une ligne RTL, la frontière logique basse a une colonne
        # stockée HAUTE (ordre visuel inverse) : ordonner les indices
        # Tk pour que le surlignage couvre le segment.
        if self.compare(ia, ">", ib):
            ia, ib = ib, ia
        self.tag_add("sel", ia, ib)

    def _boundary_indices(self, a, b):
        """Frontières logiques (ligne, k) -> indices Tk stockés."""
        oa = visual_caret_offsets(self._logical_lines[a[0]])
        ob = visual_caret_offsets(self._logical_lines[b[0]])
        return (f"{a[0] + 1}.{oa[min(a[1], len(oa) - 1)]}",
                f"{b[0] + 1}.{ob[min(b[1], len(ob) - 1)]}")

    def _delete_sel(self):
        """Supprime la sélection logique si présente (renvoie True si
        quelque chose a été supprimé)."""
        a, b = self._sel_range()
        if a is None or a == b:
            return False
        self._delete_logical(a, b)
        return True

    def _delete_logical(self, a, b):
        """Supprime les clusters logiques entre les frontières a et b
        ((ligne, k) triées, a < b) et place le caret à a."""
        (la, ka), (lb, kb) = a, b
        if la != lb:
            head = clusters(self._logical_lines[la])[:ka]
            tail = clusters(self._logical_lines[lb])[kb:]
            self._logical_lines = (self._logical_lines[:la]
                                   + ["".join(head + tail)]
                                   + self._logical_lines[lb + 1:])
            self._caret_line = la
            self._caret_boundary = ka
        else:
            cl = clusters(self._logical_lines[la])
            self._logical_lines[la] = "".join(cl[:ka] + cl[kb:])
            self._caret_line = la
            self._caret_boundary = ka
        self._anchor_boundary = None

    def _push_undo(self, kind):
        """Mémorise l'état avant édition. Chaque nouvelle édition vide
        la pile de rétablissement."""
        self._undo_stack.append((list(self._logical_lines),
                                 self._caret_line, self._caret_boundary,
                                 kind))
        if len(self._undo_stack) > 200:
            del self._undo_stack[0]
        self._redo_stack = []

    def _restore(self, state):
        self._logical_lines = list(state[0])
        self._caret_line = state[1]
        self._caret_boundary = state[2]
        self._anchor_boundary = None
        self._refresh()

    def _on_undo(self, event=None):
        if not self._undo_stack:
            return "break"
        state = self._undo_stack.pop()
        self._redo_stack.append((list(self._logical_lines),
                                 self._caret_line, self._caret_boundary,
                                 "edit"))
        self._restore(state)
        return "break"

    def _on_redo(self, event=None):
        if not self._redo_stack:
            return "break"
        state = self._redo_stack.pop()
        self._undo_stack.append((list(self._logical_lines),
                                 self._caret_line, self._caret_boundary,
                                 "edit"))
        self._restore(state)
        return "break"

    def insert_logical(self, chars):
        """Insère des caractères logiques à la position du caret (les
        \\n sont ignorés : champ monoligne par ligne de travail)."""
        self._push_undo("type" if len(clusters(chars)) == 1 else "edit")
        self._delete_sel()
        line = self._logical_lines[self._caret_line]
        cl = clusters(line)
        k = min(self._caret_boundary, len(cl))
        new_line = "".join(cl[:k]) + chars + "".join(cl[k:])
        self._logical_lines[self._caret_line] = new_line
        self._caret_boundary = min(self._caret_boundary
                                   + len(clusters(chars)), len(clusters(new_line)))
        self._anchor_boundary = None
        self._refresh()

    # --- Interaction souris ------------------------------------------------

    def _mouse_boundary(self, event):
        """Index brut du clic -> frontière logique de la ligne cliquée."""
        raw = self.index(f"@{event.x},{event.y}")
        line_no = int(raw.split(".")[0]) - 1
        line_no = max(0, min(line_no, len(self._logical_lines) - 1))
        col = int(raw.split(".")[1])
        visual = to_visual(self._logical_lines[line_no])
        return (line_no, logical_boundary_at(visual, col))

    def _on_mouse_down(self, event):
        self._sel_anchor = self._mouse_boundary(event)
        self._caret_line, self._caret_boundary = self._sel_anchor
        self._anchor_boundary = None
        self._refresh()
        self.focus_set()
        return "break"

    def _on_mouse_drag(self, event):
        if self._sel_anchor is None:
            return "break"
        cur = self._mouse_boundary(event)
        self._caret_line, self._caret_boundary = cur
        a = self._sel_anchor
        self._anchor_boundary = a[1] if a[0] == cur[0] else None
        if a[0] != cur[0]:
            # glissement multi-lignes : simple garde-fou, sélection de
            # la ligne entière la plus proche
            self._anchor_boundary = None
        self._refresh()
        return "break"

    def _on_mouse_shift(self, event):
        cur = self._mouse_boundary(event)
        if self._anchor_boundary is None:
            self._anchor_boundary = self._caret_boundary
        self._caret_line, self._caret_boundary = cur
        self._refresh()
        return "break"

    def _on_mouse_double(self, event):
        cur = self._mouse_boundary(event)
        line = self._logical_lines[cur[0]]
        cl = clusters(line)
        k = min(cur[1], len(cl))
        # bornes du mot logique autour de la frontière k
        lo = k
        while lo > 0 and not cl[lo - 1].isspace():
            lo -= 1
        hi = k
        while hi < len(cl) and not cl[hi].isspace():
            hi += 1
        self._caret_line = cur[0]
        self._caret_boundary = hi
        self._anchor_boundary = lo
        self._refresh()
        return "break"

    def _on_mouse_triple(self, event):
        cur = self._mouse_boundary(event)
        self._caret_line = cur[0]
        self._caret_boundary = len(clusters(self._logical_lines[cur[0]]))
        self._anchor_boundary = 0
        self._refresh()
        return "break"

    # --- Événements d'édition --------------------------------------------

    def _on_key(self, event):
        if len(event.char) != 1 or event.keysym in ("Return", "KP_Enter",
                                                   "Tab", "Escape"):
            return None
        ch = event.char
        if ch in ("\n", "\r", "\t") or ord(ch) < 32:
            return "break"
        self.insert_logical(ch)
        return "break"

    def _on_backspace(self, event=None):
        self._push_undo("del")
        if self._delete_sel():
            pass
        elif self._caret_boundary == 0:
            if self._caret_line == 0:
                return "break"
            prev = self._logical_lines[self._caret_line - 1]
            cur = self._logical_lines[self._caret_line]
            self._caret_boundary = len(clusters(prev))
            self._logical_lines = (self._logical_lines[:self._caret_line - 1]
                                   + [prev + cur]
                                   + self._logical_lines[self._caret_line + 1:])
            self._caret_line -= 1
        else:
            cl = self._line_clusters()
            k = self._caret_boundary
            self._logical_lines[self._caret_line] = "".join(cl[:k - 1] + cl[k:])
            self._caret_boundary = k - 1
        self._anchor_boundary = None
        self._refresh()
        return "break"

    def _on_delete(self, event=None):
        self._push_undo("del")
        if self._delete_sel():
            pass
        else:
            cl = self._line_clusters()
            k = self._caret_boundary
            if k >= len(cl):
                if self._caret_line + 1 >= len(self._logical_lines):
                    self._refresh()
                    return "break"
                nxt = self._logical_lines[self._caret_line + 1]
                cur = self._logical_lines[self._caret_line]
                self._logical_lines = (self._logical_lines[:self._caret_line]
                                       + [cur + nxt]
                                       + self._logical_lines[self._caret_line + 2:])
            else:
                self._logical_lines[self._caret_line] = "".join(cl[:k] + cl[k + 1:])
        self._anchor_boundary = None
        self._refresh()
        return "break"

    def _on_paste(self, event=None):
        try:
            text = self.selection_get(selection="CLIPBOARD")
        except tk.TclError:
            return None
        if not text:
            return None
        if looks_visual(text):
            text = to_logical(text)
        text = text.replace("\n", " ").replace("\r", " ")
        self.insert_logical(text)
        return "break"

    def _on_select_all(self, event=None):
        """Ctrl-A : sélectionne tout le texte logique — anchor au
        début logique (frontière 0 de la première ligne), caret actif
        à la fin logique (dernière frontière de la dernière ligne),
        comme dans un éditeur standard."""
        self._anchor_boundary = 0
        self._caret_line = max(0, len(self._logical_lines) - 1)
        self._caret_boundary = len(clusters(
            self._logical_lines[self._caret_line]))
        self._sel_anchor = (0, 0)
        self._refresh()
        return "break"

    def _on_copy(self, event=None):
        try:
            text = self.get("sel.first", "sel.last")
        except tk.TclError:
            return None
        if not text:
            return None
        self.clipboard_clear()
        self.clipboard_append(to_logical(text))
        return "break"

    def _on_cut(self, event=None):
        a, b = self._sel_range()
        if a is None or a == b:
            return None
        self._push_undo("edit")
        self._on_copy()
        self._delete_logical(a, b)
        self._refresh()
        return "break"

    # --- Déplacement du caret ---------------------------------------------

    def _on_left(self, event=None):
        # Gauche visuel = cluster logique PRÉCÉDENT dans l'ordre de
        # lecture pour une ligne RTL ; pour une ligne LTR (latin),
        # gauche = précédent également. On se déplace de frontière
        # logique en frontière logique vers la gauche affichée.
        if self._caret_boundary > 0:
            self._caret_boundary -= 1
        elif self._caret_line > 0:
            self._caret_line -= 1
            self._caret_boundary = len(self._line_clusters())
        else:
            return "break"
        if self._shift_held(event):
            if self._anchor_boundary is None:
                self._anchor_boundary = self._caret_boundary + 1
        else:
            self._anchor_boundary = None
        self._refresh()
        return "break"

    def _on_right(self, event=None):
        if self._caret_boundary < len(self._line_clusters()):
            self._caret_boundary += 1
        elif self._caret_line + 1 < len(self._logical_lines):
            self._caret_line += 1
            self._caret_boundary = 0
        else:
            return "break"
        if self._shift_held(event):
            if self._anchor_boundary is None:
                self._anchor_boundary = self._caret_boundary - 1
        else:
            self._anchor_boundary = None
        self._refresh()
        return "break"

    def _shift_held(self, event):
        return bool(event and event.state & 0x0001)

    def _on_home(self, event=None):
        self._caret_boundary = 0
        if not self._shift_held(event):
            self._anchor_boundary = None
        self._refresh()
        return "break"

    def _on_end(self, event=None):
        self._caret_boundary = len(self._line_clusters())
        if not self._shift_held(event):
            self._anchor_boundary = None
        self._refresh()
        return "break"


class ResultText(tk.Text):
    """Zone de résultat en texte hébreu stable.

    Le texte affiché est stocké en ordre visuel (cf. bidi_display.to_visual),
    l'ordre logique du widget coïncide donc avec l'affichage : la sélection
    à la souris (gérée par StableSelection, qui arrime les bornes aux
    clusters de glyphes) est stable et prévisible. La copie (Ctrl+C)
    restitue l'ordre logique du texte d'origine.

    Le retour à la ligne automatique de Tk s'applique au texte stocké : sur
    une ligne en ordre visuel, la première ligne affichée contiendrait la
    FIN de la phrase. Les lignes hébraïques sont donc découpées en ordre
    logique (logical_wrap) à la largeur du widget avant conversion ; la
    découpe est refaite quand la fenêtre est redimensionnée.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind("<<Copy>>", self._on_copy)
        self._logical_text = ""
        self._wrap_width = 0
        self._wrap_job = None
        font = kwargs.get("font")
        self._tkfont = (tkfont.Font(root=self, font=font)
                        if font is not None else None)
        self._autowrap = kwargs.get("wrap") != "none"
        self.bind("<Configure>", self.on_resize)
        # Recherche Ctrl-F dans la zone (cf. _open_find_bar) : occurrences
        # surlignées, la courante dans une teinte plus soutenue.
        self.tag_configure("find", background="#ffe08a")
        self.tag_configure("find_cur", background="#ffb74d")
        # La sélection native doit rester visible sur le surlignage.
        self.tag_raise("sel")
        self._find_bar = None
        self._find_entry = None
        self._find_count = None
        self._find_var = tk.StringVar(self)
        self._find_matches = []
        self._find_pos = -1
        self._find_job = None
        self._find_last_query = None
        self._find_anchor = None
        self._find_focus_notifier = None
        # Insensible aux lettres finales (sofit) : cochée par défaut — ך/כ,
        # ם/מ, ן/נ, ף/פ, ץ/צ sont équivalentes ; décochée, seules les
        # formes exactes correspondent.
        self._find_sofit_var = tk.BooleanVar(self, value=True)
        self.bind("<Control-f>", self._on_find)
        self.bind("<Control-F>", self._on_find)
        self.bind("<F3>", self._on_f3)
        self.bind("<Shift-F3>", self._on_f3_prev)
        self.bind("<Up>", self._on_arrow_up)
        self.bind("<Down>", self._on_arrow_down)

    def set_text(self, text):
        """Mémorise le texte logique et affiche (découpe + ordre visuel)."""
        self._logical_text = text
        self._wrap_width = 0
        self._clear_find()
        self._redisplay()

    def _display_width(self):
        """Largeur intérieure disponible pour une ligne (pixels)."""
        try:
            return max(1, self.winfo_width() - 12)
        except tk.TclError:
            return 0

    def _redisplay(self):
        """Découpe les lignes hébraïques à la largeur courante, convertit
        en ordre visuel et remplace le contenu du widget."""
        self.configure(state="normal")
        self.delete("1.0", "end")
        width = self._display_width() if self._autowrap else 0
        if width <= 1:
            self.insert("1.0", to_visual(self._logical_text))
        else:
            self._wrap_width = width
            self.insert("1.0", to_visual(
                logical_wrap(self._logical_text, self._measure, width)))
        self.configure(state="disabled")
        # Le contenu affiché a changé : les occurrences surlignées et la
        # position mémorisée ne sont plus valides (les indices de ligne
        # ne correspondent plus) ; les barres de recherche restent ouvertes.
        self._find_anchor = None
        self._clear_find()
        if self._find_bar is not None:
            self._find_job = self.after_idle(self._refresh_find)

    def _measure(self, s):
        if self._tkfont is None:
            return len(s)
        return self._tkfont.measure(s)

    def on_resize(self, event=None):
        """Re-découpe (différé) si la largeur affichable a changé."""
        if not self._autowrap:
            return
        width = self._display_width()
        if width == self._wrap_width:
            return
        if self._wrap_job is not None:
            try:
                self.after_cancel(self._wrap_job)
            except tk.TclError:
                pass
        self._wrap_job = self.after(60, self._redisplay)
        self._wrap_width = width

    def set_font(self, font):
        """Change la police du rendu ; re-découpe car les largeurs changent."""
        self._tkfont = tkfont.Font(root=self, font=font)
        self.configure(font=font)
        if self._logical_text:
            self._redisplay()

    # --- Copie en ordre logique ------------------------------------------
    def _on_select_all(self, event=None):
        """Ctrl-A : sélectionne tout le texte logique — anchor au
        début logique (frontière 0 de la première ligne), caret actif
        à la fin logique (dernière frontière de la dernière ligne),
        comme dans un éditeur standard."""
        self._anchor_boundary = 0
        self._caret_line = max(0, len(self._logical_lines) - 1)
        self._caret_boundary = len(clusters(
            self._logical_lines[self._caret_line]))
        self._sel_anchor = (0, 0)
        self._refresh()
        return "break"

    def _on_copy(self, event=None):
        try:
            text = self.get("sel.first", "sel.last")
        except tk.TclError:
            return None
        if not text:
            return None
        self.clipboard_clear()
        self.clipboard_append(to_logical(text))
        return "break"

    # --- Recherche Ctrl-F -------------------------------------------------
    def _on_find(self, event=None):
        """Ouvre la barre de recherche, pré-remplie depuis la sélection."""
        self._open_find_bar()
        return "break"

    def _on_f3(self, event=None):
        """Occurrence suivante (barre ouverte ou non)."""
        if self._find_matches:
            self._find_next()
            return "break"
        self._open_find_bar()
        return "break"

    def _on_f3_prev(self, event=None):
        """Occurrence précédente (barre ouverte ou non)."""
        if self._find_matches:
            self._find_prev()
            return "break"
        self._open_find_bar()
        return "break"

    def _open_find_bar(self):
        if self._find_entry is not None:
            try:
                if self.focus_get() is self._find_entry:
                    # Focus déjà dans le champ : tout sélectionner (comme
                    # les navigateurs), sans écraser la saisie.
                    self._find_entry.select_range(0, "end")
                    return
            except KeyError:
                pass
        if self._find_bar is None:
            bar = ttk.Frame(self)
            entry = ttk.Entry(bar, textvariable=self._find_var, width=18,
                              font=HEBREW_FONT, justify="right")
            entry.pack(side="left", padx=(0, 4))
            sofit_box = ttk.Checkbutton(
                bar, text="Sofit insensible",
                variable=self._find_sofit_var,
                command=self._refresh_find)
            sofit_box.pack(side="left", padx=(0, 6))
            self._find_count = ttk.Label(bar, text="", width=12, anchor="w")
            self._find_count.pack(side="left")
            btn_next = ttk.Button(bar, text="\u25b6", width=2,
                                  command=self._find_next)
            btn_next.pack(side="left", padx=1)
            btn_prev = ttk.Button(bar, text="\u25c0", width=2,
                                  command=self._find_prev)
            btn_prev.pack(side="left", padx=(1, 4))
            btn_close = ttk.Button(bar, text="\u2715", width=2,
                                   command=self._close_find_bar)
            btn_close.pack(side="left")
            # En haut à gauche : pour l'hébreu (droite-à-gauche), le bord
            # gauche est la FIN de lecture — la barre couvre le moins
            # possible le début des lignes.
            bar.place(in_=self, relx=0.0, x=6, y=4, anchor="nw")
            self._find_bar = bar
            self._find_entry = entry
            entry.bind("<Return>", self._find_next)
            entry.bind("<KP_Enter>", self._find_next)
            entry.bind("<Shift-Return>", self._find_prev)
            entry.bind("<Up>", self._on_arrow_up)
            entry.bind("<Down>", self._on_arrow_down)
            entry.bind("<Escape>", self._close_find_bar)
            entry.bind("<KeyRelease>", self._on_find_typed)
            entry.bind("<FocusIn>", self._on_find_entry_focus)
        # Pré-remplissage depuis la sélection courante (ordre logique).
        try:
            sel = self.get("sel.first", "sel.last")
        except tk.TclError:
            sel = ""
        if sel:
            # Une sélection multi-lignes devient une requête sur une
            # seule ligne (les sauts de ligne ne sont pas cherchés).
            self._find_var.set(to_logical(sel).replace("\n", " "))
        self._find_bar.lift()
        self._refresh_find()
        self._find_entry.focus_set()
        self._find_entry.icursor("end")
        self._find_entry.select_range(0, "end")

    def _on_find_entry_focus(self, event):
        # Le clavier virtuel (qui tape dans le dernier widget ciblé) doit
        # pouvoir remplir le champ de recherche.
        if self._find_focus_notifier is not None:
            self._find_focus_notifier(event)

    def _close_find_bar(self, event=None):
        if self._find_job is not None:
            try:
                self.after_cancel(self._find_job)
            except tk.TclError:
                pass
            self._find_job = None
        self._clear_find()
        if self._find_bar is not None:
            try:
                self._find_bar.destroy()
            except tk.TclError:
                pass
        self._find_bar = None
        self._find_entry = None
        self._find_count = None
        self.focus_set()

    def _on_find_typed(self, event=None):
        # Seul un changement réel de la requête déclenche un rafraîchissement :
        # les KeyRelease de navigation (F3, Entrée, flèches) ou de touche
        # modificatrice (Maj, Ctrl) ne modifient pas le champ, alors que le
        # refresh réinitialiserait la position courante.
        if self._find_var.get() == self._find_last_query:
            return
        if self._find_job is not None:
            try:
                self.after_cancel(self._find_job)
            except tk.TclError:
                pass
        self._find_job = self.after(150, self._refresh_find)

    def _clear_find(self):
        self.tag_remove("find", "1.0", "end")
        self.tag_remove("find_cur", "1.0", "end")
        self._find_matches = []
        self._find_pos = -1
        if self._find_count is not None:
            try:
                self._find_count.configure(text="")
            except tk.TclError:
                pass

    def _refresh_find(self):
        """Recalcule les occurrences de la requête courante.

        Si la requête contient des lettres hébraïques, la recherche se fait
        sur les consonnes seules (sans nikkud ni teamim) dans l'ordre de
        lecture, via le module bidi_display ; sinon la recherche est
        littérale insensible à la casse (texte latin, chiffres).
        """
        self._find_job = None
        anchor = self._find_anchor
        self._clear_find()
        query = self._find_var.get()
        self._find_last_query = query
        if not query:
            return
        matches = self._compute_find_matches(query)
        self._find_matches = matches
        for line, a, b in matches:
            self.tag_add("find", f"{line}.{a}", f"{line}.{b}")
        if matches:
            start = 0
            if anchor is not None:
                for i, (line, a, b) in enumerate(matches):
                    if (line, a) >= anchor:
                        start = i
                        break
            self._find_pos = start
            line, a, b = matches[start]
            self.tag_add("find_cur", f"{line}.{a}", f"{line}.{b}")
            self.see(f"{line}.{a}")
        self._update_find_count()

    def _compute_find_matches(self, query):
        """Occurrences ``[(ligne, début, fin), …]`` en indices du texte
        stocké (ordre visuel + marques bidi), en ordre de lecture."""
        n_lines = int(self.index("end - 1c").split(".")[0])
        matches = []
        if has_hebrew_letters(query):
            skeleton = normalize_query(query)
            if not skeleton:
                return []
            sofit_insensitive = bool(self._find_sofit_var.get())
            for line_no in range(1, n_lines + 1):
                line = self.get(f"{line_no}.0", f"{line_no}.0 lineend")
                if not line:
                    continue
                for a, b in find_line_matches(line, skeleton,
                                              sofit_insensitive=sofit_insensitive):
                    matches.append((line_no, a, b))
        else:
            needle = query.casefold()
            for line_no in range(1, n_lines + 1):
                line = self.get(f"{line_no}.0", f"{line_no}.0 lineend")
                if not line:
                    continue
                hay = line.casefold()
                start = 0
                while True:
                    j = hay.find(needle, start)
                    if j < 0:
                        break
                    matches.append((line_no, j, j + len(needle)))
                    start = j + 1
        return matches

    def _find_next(self, event=None):
        if not self._find_matches:
            self._refresh_find()
            return "break"
        self._find_pos = (self._find_pos + 1) % len(self._find_matches)
        self._show_find_current()
        return "break"

    def _find_prev(self, event=None):
        if not self._find_matches:
            self._refresh_find()
            return "break"
        self._find_pos = (self._find_pos - 1) % len(self._find_matches)
        self._show_find_current()
        return "break"

    def _on_arrow_up(self, event=None):
        """Fait défiler le texte d'une ligne vers le haut (réponse directe)."""
        self._scroll_lines(-1)
        return "break"

    def _on_arrow_down(self, event=None):
        """Fait défiler le texte d'une ligne vers le bas (réponse directe)."""
        self._scroll_lines(1)
        return "break"

    def _scroll_lines(self, delta):
        """Fait défiler la vue de delta lignes, sans déplacer le curseur.

        Contrairement à la navigation par marque d'insertion (see), le
        défilement est immédiat à chaque KeyPress — pas de décalage entre
        l'appui et le mouvement, y compris en répétition automatique (clé
        maintenue). La marque d'insertion reste en cohérence : si elle sort
        de la fenêtre, elle est ramenée à la ligne visible la plus proche.
        """
        try:
            self.yview_scroll(delta, "units")
            self._clamp_insert_to_view()
        except tk.TclError:
            pass

    def _clamp_insert_to_view(self):
        """Ramène la marque d'insertion dans la fenêtre visible si besoin."""
        try:
            first = self.index("@0,0")
            last = self.index("@0,%d" % max(0, self.winfo_height() - 1))
            ins = self.index("insert")
            if self.compare(ins, "<", first):
                self.mark_set("insert", first)
            elif self.compare(ins, ">", last):
                self.mark_set("insert", last)
        except tk.TclError:
            pass

    def _show_find_current(self):
        self.tag_remove("find_cur", "1.0", "end")
        line, a, b = self._find_matches[self._find_pos]
        self._find_anchor = (line, a)
        self.tag_add("find_cur", f"{line}.{a}", f"{line}.{b}")
        # Le curseur clavier suit le match : la marque d'insertion est
        # déplacée juste après, pour que la navigation F3/Maj+F3 suivie
        # d'une flèche verticale reparte de la ligne du match.
        self.mark_set("insert", f"{line}.{b}")
        self.see(f"{line}.{a}")
        self._update_find_count()

    def _update_find_count(self):
        if self._find_count is None:
            return
        n = len(self._find_matches)
        if not n:
            self._find_count.configure(text="0 / 0")
        else:
            self._find_count.configure(
                text=f"{self._find_pos + 1} / {n}")


class ScaleTimeTooltip:
    """Infobulle du curseur de lecture : deux lignes — le temps à la
    position survolée (« où reprendre si je clique ») et le temps de
    lecture courant (mis à jour en continu, même souris immobile, pour
    suivre le thumb pendant la lecture). Création/destruction par
    événements Enter/Leave ; seul le texte est rafraîchi périodiquement
    et uniquement tant que la bulle est visible."""

    _REFRESH_MS = 200

    def __init__(self, scale, value_to_text):
        self._scale = scale
        self._value_to_text = value_to_text
        self._tip = None
        self._label = None
        self._after_id = None
        self._last_text = None
        scale.bind("<Enter>", self._show, add="+")
        scale.bind("<Leave>", self._hide, add="+")

    def _pointer_frac(self):
        try:
            frac = (self._scale.winfo_pointerx() - self._scale.winfo_rootx()
                    ) / max(1, self._scale.winfo_width())
        except tk.TclError:
            return 0.0
        return min(1.0, max(0.0, frac))

    def _current_text(self):
        return self._value_to_text(self._pointer_frac())

    def _show(self, event=None):
        if self._tip is None or not self._tip.winfo_exists():
            self._tip = tk.Toplevel(self._scale)
            self._tip.wm_overrideredirect(True)
            self._label = tk.Label(
                self._tip, text="", relief="solid", borderwidth=1,
                font=("Segoe UI", 9), justify="left")
            self._label.pack()
        self._refresh()
        self._schedule()

    def _schedule(self):
        if self._after_id is None:
            self._after_id = self._scale.after(self._REFRESH_MS,
                                               self._refresh_scheduled)

    def _refresh_scheduled(self):
        self._after_id = None
        if self._tip is None or not self._tip.winfo_exists():
            return
        self._refresh()
        self._schedule()

    def _refresh(self):
        if self._tip is None or not self._tip.winfo_exists():
            return
        text = self._current_text()
        if text != self._last_text:
            self._label.configure(text=text)
            self._last_text = text
        try:
            x = self._scale.winfo_pointerx() + 12
            y = self._scale.winfo_pointery() + 14
            self._tip.wm_geometry(f"+{x}+{y}")
        except tk.TclError:
            pass

    def _hide(self, event=None):
        if self._after_id is not None:
            try:
                self._scale.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
        if self._tip is not None and self._tip.winfo_exists():
            self._tip.destroy()
        self._tip = None
        self._label = None
        self._last_text = None


class AnalyseurGUI:
    """Fenêtre principale de l'analyseur grammatical."""

    def __init__(self, root):
        self.root = root
        self.api = None
        self.translations = {}  # {lang: index} traductions chargées
        self._work_queue = queue.Queue()
        self._target_widget = None  # widget actuellement ciblé par le clavier

        # Style « lien hypertexte » (bleu, souligné, fond plat) pour le
        # bouton d'impression des binyanim.
        link_font = tkfont.Font(root=root, font=HEBREW_FONT_MONO)
        link_font.configure(underline=True)
        self._link_style = ttk.Style(root)
        self._link_style.configure("Link.TButton", foreground="#0000EE",
                                   font=link_font, relief="flat",
                                   borderwidth=0, padding=(0, 2))
        self._link_style.map("Link.TButton",
                             foreground=[("active", "#0000EE"),
                                         ("pressed", "#551A8B")])

        root.title(
            "Analyseur grammatical de l'hébreu biblique — כָּבוֹד לַיהוָה"
            + (f" (v{__version__})" if __version__ else "")
        )
        root.minsize(1000, 760)
        root.geometry(_saved_geometry() or DEFAULT_GEOMETRY)

        self._build_widgets()
        self._start_loading()

        # Recherche Ctrl-F : routée vers la zone de résultat de l'onglet
        # actif (le widget focusé peut être une Entry de saisie ; les
        # ResultText gèrent aussi leur propre <Control-f>/<F3>).
        root.bind("<Control-f>", self._on_global_find)
        root.bind("<F3>", self._on_global_find_next)
        root.bind("<Shift-F3>", self._on_global_find_prev)

        # Polling des résultats des travaux en arrière-plan.
        root.after(120, self._poll_queue)

    def _active_result_widget(self):
        """Zone de résultat visible de l'onglet actif, ou None.

        Livre/Mot/Phrase : la zone unique de l'onglet. Binyanim : la zone
        du sous-onglet affiché (Verbe, binyan ou Sortie complète)."""
        idx = self.notebook.select()
        if not idx:
            return None
        tab = self.notebook.tab(idx, "text")
        if tab in ("Livre", "Mot", "Phrase"):
            return getattr(self.notebook.nametowidget(idx), "_output", None)
        if tab == "Binyanim":
            sel = self.binyanim_notebook._selected
            if sel is None:
                return None
            for t in self.binyanim_notebook._tabs:
                if t["id"] == sel:
                    for child in t["widget"].winfo_children():
                        if isinstance(child, ResultText):
                            return child
            return None
        return None

    def _on_global_find(self, event):
        w = self._active_result_widget()
        if w is not None:
            w._on_find(event)
            return "break"
        return None

    def _on_global_find_next(self, event):
        w = self._active_result_widget()
        if w is not None:
            return w._on_f3(event)
        return None

    def _on_global_find_prev(self, event):
        w = self._active_result_widget()
        if w is not None:
            return w._on_f3_prev(event)
        return None

    # --- Construction de l'interface -------------------------------------
    def _build_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_verse = ttk.Frame(self.notebook)
        self.tab_word = ttk.Frame(self.notebook)
        self.tab_phrase = ttk.Frame(self.notebook)
        self.tab_binyanim = ttk.Frame(self.notebook)
        self.tab_readme = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_verse, text="Livre")
        self.notebook.add(self.tab_word, text="Mot")
        self.notebook.add(self.tab_phrase, text="Phrase")
        self.notebook.add(self.tab_binyanim, text="Binyanim")
        self.notebook.add(self.tab_readme, text="README")

        self._build_verse_tab()
        self._build_word_tab()
        self._build_phrase_tab()
        self._build_binyanim_tab()
        self._build_readme_tab()

        # Raccourcis globaux de navigation : Ctrl+↑/↓ verset, Shift+↑/↓
        # chapitre, Alt+↑/↓ livre — équivalents aux boutons ▲/▼ de
        # l'onglet « Livre ».
        for seq, handler in (("<Control-Up>", self._on_nav_verse_key),
                             ("<Control-Down>", self._on_nav_verse_key),
                             ("<Shift-Up>", self._on_nav_chapter_key),
                             ("<Shift-Down>", self._on_nav_chapter_key),
                             ("<Alt-Up>", self._on_nav_book_key),
                             ("<Alt-Down>", self._on_nav_book_key)):
            step = -1 if seq.endswith("Up>") else 1
            self.root.bind_all(seq, lambda e, h=handler, s=step: h(s))

        # Raccourcis VS combobox : quand une combobox de référence a le
        # focus, le class binding natif de ttk.Combobox réagit AUSSI à
        # Alt+↓ (ouverture de sa liste déroulante) — et l'ordre Tk
        # (widget → class → toplevel → all) l'exécute AVANT le bind_all
        # ci-dessus. La popdown restait alors ouverte sur l'ancien livre
        # pendant que la navigation repeuplait chapitres/versets, et sa
        # fermeture émettait un <<ComboboxSelected>> en retard qui
        # cassait la cascade. Binder au niveau widget (avant le class
        # binding) court-circute l'ouverture : « break » l'emporte.
        for seq, handler in (("<Control-Up>", self._on_nav_verse_key),
                             ("<Control-Down>", self._on_nav_verse_key),
                             ("<Shift-Up>", self._on_nav_chapter_key),
                             ("<Shift-Down>", self._on_nav_chapter_key),
                             ("<Alt-Up>", self._on_nav_book_key),
                             ("<Alt-Down>", self._on_nav_book_key)):
            step = -1 if seq.endswith("Up>") else 1
            for combo in (self.corpus_combo, self.book_combo,
                          self.chapter_combo, self.verse_combo):
                combo.bind(seq, lambda e, h=handler, s=step: h(s))

        # Barre d'état (chargement de la base / analyse en cours).
        self.status = ttk.Label(self.root,
                                text=f"Chargement de la base BHSA… (v{__version__})",
                                relief="sunken", anchor="w")
        self.status.pack(fill="x", side="bottom")

    def _build_verse_tab(self):
        tab = self.tab_verse

        form = ttk.LabelFrame(tab, text="Référence du livre")
        form.pack(fill="x", padx=8, pady=8)

        # Corpus : Bible hébraïque (BHSA) ou Mishna (Sefaria).
        ttk.Label(form, text="Corpus :").grid(row=0, column=0, sticky="w", padx=4, pady=6)
        self.corpus_var = tk.StringVar(value=CORPUS_BIBLE)
        self.corpus_combo = ttk.Combobox(form, textvariable=self.corpus_var,
                                         state="readonly", width=14,
                                         values=[CORPUS_BIBLE, CORPUS_MISHNA])
        self.corpus_combo.grid(row=0, column=1, sticky="w", padx=4, pady=6)
        self.corpus_combo.bind("<<ComboboxSelected>>", self._on_corpus_change)

        # Livre (ordre canonique : Torah en premier), Chapitre, Verset.
        ttk.Label(form, text="Livre :").grid(row=0, column=2, sticky="w", padx=(16, 4), pady=6)
        self.book_var = tk.StringVar()
        self.book_combo = ttk.Combobox(form, textvariable=self.book_var,
                                       state="readonly", width=30)
        self.book_combo.grid(row=0, column=3, sticky="w", padx=4, pady=6)
        self.book_combo.bind("<<ComboboxSelected>>", self._on_book_change)

        # Navigation rapide entre livres : ▲/▼ sélectionne le livre
        # précédent/suivant (ordre canonique de la liste) et affiche
        # automatiquement son premier chapitre/premier verset.
        self.btn_book_prev = ttk.Button(form, text="▲", width=2,
                                        command=lambda: self._nav_book(-1))
        self.btn_book_prev.grid(row=0, column=4, sticky="w", padx=(0, 2), pady=6)
        self.btn_book_next = ttk.Button(form, text="▼", width=2,
                                        command=lambda: self._nav_book(1))
        self.btn_book_next.grid(row=0, column=5, sticky="w", padx=(0, 2), pady=6)

        ttk.Label(form, text="Chapitre :").grid(row=0, column=6, sticky="w", padx=(16, 4), pady=6)
        self.chapter_var = tk.StringVar()
        self.chapter_combo = ttk.Combobox(form, textvariable=self.chapter_var,
                                          state="readonly", width=8)
        self.chapter_combo.grid(row=0, column=7, sticky="w", padx=4, pady=6)
        self.chapter_combo.bind("<<ComboboxSelected>>", self._on_chapter_change)

        # Navigation rapide entre chapitres : ▲/▼ sélectionne le chapitre
        # précédent/suivant du livre courant et affiche automatiquement son
        # premier verset (via _on_chapter_change puis _run_verse).
        self.btn_chapter_prev = ttk.Button(form, text="▲", width=2,
                                           command=lambda: self._nav_chapter(-1))
        self.btn_chapter_prev.grid(row=0, column=8, sticky="w", padx=(0, 2), pady=6)
        self.btn_chapter_next = ttk.Button(form, text="▼", width=2,
                                           command=lambda: self._nav_chapter(1))
        self.btn_chapter_next.grid(row=0, column=9, sticky="w", padx=(0, 2), pady=6)

        ttk.Label(form, text="Verset :").grid(row=0, column=10, sticky="w", padx=(16, 4), pady=6)
        self.verse_var = tk.StringVar()
        self.verse_combo = ttk.Combobox(form, textvariable=self.verse_var,
                                        state="readonly", width=8)
        self.verse_combo.grid(row=0, column=11, sticky="w", padx=4, pady=6)

        # Navigation rapide entre versets (boutons ci-dessous et raccourcis Ctrl+↑ / Ctrl+↓). : ▲/▼ sélectionne le verset
        # précédent/suivant du chapitre courant et l'affiche aussitôt.
        self.btn_verse_prev = ttk.Button(form, text="▲", width=2,
                                         command=lambda: self._nav_verse(-1))
        self.btn_verse_prev.grid(row=0, column=12, sticky="w", padx=(0, 2), pady=6)
        self.btn_verse_next = ttk.Button(form, text="▼", width=2,
                                         command=lambda: self._nav_verse(1))
        self.btn_verse_next.grid(row=0, column=13, sticky="w", padx=(0, 2), pady=6)

        # Options de format (analyse BHSA uniquement ; sans effet en mode
        # Mishna, qui affiche texte hébreu + traduction).
        opts = ttk.Frame(tab)
        opts.pack(fill="x", padx=8)
        ttk.Label(opts, text="Format :").pack(side="left", padx=(0, 4))
        self.verse_format = tk.StringVar(value="text")
        self.verse_format_widgets = []
        for value, label in (("text", "Texte"), ("summary", "Synthèse"),
                             ("json", "JSON")):
            rb = ttk.Radiobutton(opts, text=label, variable=self.verse_format,
                                 value=value)
            rb.pack(side="left")
            self.verse_format_widgets.append(rb)
        self.verse_no_words = tk.BooleanVar(value=False)
        self.verse_no_words_widget = ttk.Checkbutton(
            opts, text="Masquer le détail mot à mot",
            variable=self.verse_no_words)
        self.verse_no_words_widget.pack(side="left", padx=(16, 0))

        # Analyse grammaticale de la mishna affichée (requiert la base BHSA,
        # chargée au démarrage ; les formats Texte/JSON s'appliquent).
        self.mishna_analyze = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Analyse grammaticale (mishna)",
                        variable=self.mishna_analyze).pack(
            side="left", padx=(16, 0))

        # Choix des traductions affichées (BHSA uniquement ; la Mishna a sa
        # propre traduction Schwab).
        trads = ttk.Frame(tab)
        trads.pack(fill="x", padx=8, pady=(4, 0))
        self.verse_trads_frame = trads
        ttk.Label(trads, text="Traductions :").pack(side="left", padx=(0, 4))
        self.verse_trans = {}
        for lang, label in TRANSLATIONS:
            var = tk.BooleanVar(
                value=_PROPS.get(f"translation.{lang}", "true").strip().lower()
                not in ("0", "false", "no", "off"))
            ttk.Checkbutton(trads, text=label, variable=var).pack(side="left", padx=4)
            self.verse_trans[lang] = var

        self.btn_verse = ttk.Button(tab, text="Afficher le verset / la mishna",
                                   command=self._run_verse)
        self.btn_verse.pack(anchor="w", padx=8, pady=8)
        self.btn_verse.state(["disabled"])

        # Lecture audio du verset : synthèse WAV (phonikud-tts, locale)
        # puis lecteur avec curseur de position déplaçable. Requiert le
        # paquet phonikud-tts (synthèse, toute plateforme) et Windows pour
        # la lecture MCI ; sinon le bouton reste désactivé.
        audio = ttk.Frame(tab)
        audio.pack(anchor="w", padx=8, pady=(0, 8))
        # Bouton unique : ▶ (re)lance la lecture, ⏸ met en pause pendant
        # la lecture, ▶ reprend — ▶ à l'état de repos comme en pause.
        self.btn_audio = ttk.Button(audio, text="▶",
                                    width=4,
                                    command=self._on_audio_button)
        self.btn_audio.pack(side="left")
        self.btn_audio.state(["disabled"])
        ttk.Label(audio, text="Lire le verset").pack(side="left", padx=(2, 6))
        self.audio_time = ttk.Label(audio, text="0:00 / 0:00")
        self.audio_time.pack(side="left", padx=(10, 0))
        ttk.Label(audio, text="Voix :").pack(side="left", padx=(12, 2))
        # gui.properties stocke la clé (ex. « michael ») ; la combobox
        # affiche les libellés — la traduction se fait dans les deux sens :
        # clé -> libellé ici (au démarrage), libellé -> clé à la synthèse
        # et à la sauvegarde (via _voice_labels).
        self._voice_labels = {v["label"]: k for k, v in VOICES.items()}
        _saved_voice_key = _PROPS.get("audio.voice", "shaul").strip()
        if _saved_voice_key not in VOICES:
            _saved_voice_key = "shaul"
        self.audio_voice = tk.StringVar(
            value=VOICES[_saved_voice_key]["label"])
        self.audio_voice_combo = ttk.Combobox(
            audio, textvariable=self.audio_voice, state="readonly", width=14,
            values=list(self._voice_labels))
        self.audio_voice_combo.pack(side="left")
        self.audio_voice_combo.state(["disabled"])
        self.audio_voice_combo.bind("<<ComboboxSelected>>",
                                    self._on_audio_voice_change)
        ttk.Label(audio, text="Vitesse :").pack(side="left", padx=(12, 2))
        _saved_speed = _PROPS.get("audio.speed", "1.0").strip()
        try:
            if not 0.5 <= float(_saved_speed) <= 2.0:
                raise ValueError
        except ValueError:
            _saved_speed = "1.0"
        self.audio_speed = tk.StringVar(value=_saved_speed)
        self.audio_speed_spin = ttk.Spinbox(
            audio, textvariable=self.audio_speed, width=4,
            from_=0.5, to=2.0, increment=0.1)
        self.audio_speed_spin.pack(side="left")
        self.audio_speed_spin.state(["disabled"])
        self.audio_speed_spin.bind("<Return>", self._on_audio_speed_change)
        self.audio_speed_spin.bind("<FocusOut>", self._on_audio_speed_change)
        self._audio_last_text = None
        self.audio_pos = tk.IntVar(value=0)
        self.audio_scale = ttk.Scale(audio, from_=0, to=1000,
                                     variable=self.audio_pos,
                                     command=self._on_audio_seek)
        # Largeur fixe (en pixels) : le curseur ne s'étire pas avec la
        # fenêtre ; ~10 cm restent confortables pour placer finement la
        # lecture, et la rangée reste compacte à côté du bouton et des
        # contrôles Vitesse/Voix.
        self.audio_scale.configure(length=280)
        self.audio_scale.pack(side="left", padx=(10, 0))
        self.audio_scale.state(["disabled"])
        # Infobulle dynamique : temps à la position du pointeur (pause,
        # glissement) — format identique au compteur temps écoulé/total.
        def _audio_tooltip_text(frac):
            def fmt(ms):
                return f"{int(ms) // 60000}:{int(ms) % 60000 // 1000:02d}"
            hover = fmt(frac * self._audio_duration_ms)
            total = fmt(self._audio_duration_ms)
            player = self._audio_player
            if player is not None and self._audio_duration_ms:
                # Temps de lecture courant : suit le thumb même souris
                # immobile (la bulle est rafraîchie toutes les 200 ms).
                return (f"Position : {hover} / {total}\n"
                        f"Lecture  : {fmt(player.position_ms())} / {total}")
            return f"Position : {hover} / {total}"

        self._audio_tooltip = ScaleTimeTooltip(self.audio_scale,
                                               _audio_tooltip_text)
        self._audio_player = None
        self._audio_tts_ready = False
        self._audio_wav = None
        self._audio_ref = None
        self._audio_duration_ms = 0
        self._audio_seeking = False
        self._audio_polling = False

        self._build_output(tab)

    def _build_word_tab(self):
        tab = self.tab_word
        form = ttk.LabelFrame(tab, text="Mot hébreu à analyser")
        form.pack(fill="x", padx=8, pady=8)

        self.word_entry = BidiHebrewText(form, font=HEBREW_FONT, height=1,
                                      wrap="none", padx=4, pady=4)
        self.word_entry.pack(fill="x", padx=4, pady=4)
        self.word_entry.bind("<FocusIn>", self._remember_target)

        hint = ttk.Label(form,
                         text="Saisissez le mot avec le nikkud mais sans les teamim. "
                              "Les préfixes (ב/כ/ל/מ/ו/ה/ש) restent attachés.",
                         wraplength=760, justify="left")
        hint.pack(anchor="w", padx=4, pady=(2, 6))

        self._build_keyboard(form)

        opts = ttk.Frame(tab)
        opts.pack(fill="x", padx=8)
        ttk.Label(opts, text="Format :").pack(side="left", padx=(0, 4))
        self.word_format = tk.StringVar(value="text")
        ttk.Radiobutton(opts, text="Texte", variable=self.word_format,
                        value="text").pack(side="left")
        ttk.Radiobutton(opts, text="JSON", variable=self.word_format,
                        value="json").pack(side="left")

        self.btn_word = ttk.Button(tab, text="Analyser le mot",
                                   command=self._run_word)
        self.btn_word.pack(anchor="w", padx=8, pady=8)
        self.btn_word.state(["disabled"])

        self._build_output(tab)

    def _build_phrase_tab(self):
        tab = self.tab_phrase
        form = ttk.LabelFrame(tab, text="Phrase hébreu à analyser")
        form.pack(fill="both", expand=False, padx=8, pady=8)

        self.phrase_text = BidiHebrewText(form, font=HEBREW_FONT, height=3,
                                      wrap="word", padx=4, pady=4)
        self.phrase_text.pack(fill="x", padx=4, pady=4)
        self.phrase_text.bind("<FocusIn>", self._remember_target)

        hint = ttk.Label(form,
                         text="Séparez les mots par des espaces. L'analyse est indicative "
                              "(pas de parsing syntaxique complet).",
                         wraplength=760, justify="left")
        hint.pack(anchor="w", padx=4, pady=(2, 6))

        self._build_keyboard(form)

        opts = ttk.Frame(tab)
        opts.pack(fill="x", padx=8)
        ttk.Label(opts, text="Format :").pack(side="left", padx=(0, 4))
        self.phrase_format = tk.StringVar(value="text")
        ttk.Radiobutton(opts, text="Texte", variable=self.phrase_format,
                        value="text").pack(side="left")
        ttk.Radiobutton(opts, text="JSON", variable=self.phrase_format,
                        value="json").pack(side="left")

        self.btn_phrase = ttk.Button(tab, text="Analyser la phrase",
                                     command=self._run_phrase)
        self.btn_phrase.pack(anchor="w", padx=8, pady=8)
        self.btn_phrase.state(["disabled"])

        self._build_output(tab)

    def _build_keyboard(self, parent):
        kb_frame = ttk.LabelFrame(parent, text="Clavier hébreu (UTF-8)")
        kb_frame.pack(fill="x", padx=4, pady=(2, 6))
        self.keyboard = HebrewKeyboard(kb_frame, self._get_target)
        self.keyboard.pack(fill="x", padx=4, pady=4)

    def _build_output(self, parent):
        frame = ttk.LabelFrame(parent, text="Résultat")
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.output_text = ResultText(frame, font=HEBREW_FONT_MONO,
                                      wrap="word", height=10, width=40)
        # Le clavier virtuel doit cibler le champ de la barre Ctrl-F.
        self.output_text._find_focus_notifier = self._remember_target
        self.output_text.grid(row=0, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(frame, orient="vertical",
                               command=self.output_text.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(frame, orient="horizontal",
                               command=self.output_text.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        self.output_text.configure(yscrollcommand=yscroll.set,
                                   xscrollcommand=xscroll.set)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.output_text.configure(state="disabled")
        StableSelection(self.output_text)
        # Associer la zone de résultat partagée (une par onglet).
        parent._output = self.output_text

    # --- Cible du clavier virtuel ----------------------------------------
    def _remember_target(self, event):
        self._target_widget = event.widget

    def _get_target(self):
        # Priorité au widget ayant le focus ; sinon l'entrée du clavier.
        w = self._target_widget
        if w is not None and w.winfo_exists():
            return w
        # Fallback : selon l'onglet actif.
        idx = self.notebook.select()
        if not idx:
            return None
        if self.notebook.tab(idx, "text") == "Mot":
            return self.word_entry
        if self.notebook.tab(idx, "text") == "Phrase":
            return self.phrase_text
        return None

    # --- Chargement de la base BHSA --------------------------------------
    def _start_loading(self):
        # Sablier sur toute la fenêtre principale tant que la base BHSA
        # est en cours de lecture : le mode verset (Bible) n'est pas
        # encore disponible. Tk mappe « watch » sur le sablier Windows.
        self.root.configure(cursor="watch")

        def worker():
            try:
                api = load_corpus()
                self._work_queue.put(("loaded", api))
            except DataNotFoundError as exc:
                self._work_queue.put(("error", str(exc)))
            except Exception as exc:  # noqa: BLE001
                self._work_queue.put(("error", repr(exc)))

            # Chargement des traductions (domaine public). Non bloquant :
            # leur absence ne prive que de la traduction, pas du reste de
            # l'analyse.
            for lang, _label in TRANSLATIONS:
                try:
                    self.translations[lang] = load_translation(language=lang)
                except (TranslationNotFoundError, Exception):  # noqa: BLE001
                    self.translations[lang] = None

        threading.Thread(target=worker, daemon=True).start()

    def _on_corpus_loaded(self, api):
        self.api = api
        self.root.configure(cursor="")
        self.status.configure(text="Base BHSA chargée. Prêt.")
        for btn in (self.btn_verse, self.btn_word, self.btn_phrase, self.btn_binyanim):
            btn.state(["!disabled"])
        try:
            import soundfile  # noqa: F401
            _audio_tts_ok = True
        except ImportError:
            _audio_tts_ok = False
        # Le bouton de lecture n'est activé que par « Afficher le verset » ;
        # les contrôles annexes sont actifs dès que la synthèse est
        # disponible.
        self._audio_tts_ready = _audio_tts_ok
        if _audio_tts_ok:
            self.audio_speed_spin.state(["!disabled"])
            self.audio_voice_combo.state(["!disabled"])
        else:
            self._set_audio_error(
                "Lecture audio : installez phonikud-tts (pip install "
                "phonikud-tts) pour la synthèse.")
        self._populate_books()

    def _on_corpus_error(self, msg):
        self.root.configure(cursor="")
        self.status.configure(text="Erreur de chargement de la base BHSA.")
        messagebox.showerror(
            "Base BHSA introuvable",
            f"Impossible de charger la base BHSA.\n\n{msg}\n\n"
            "Placez un clone de ETCBC/bhsa (branche data2021) à bhsa_repo/tf/c, "
            "ou définissez la variable BHSA_DATA.",
        )

    # --- Peuplement des listes déroulantes ------------------------------
    def _populate_books(self):
        """Remplit la liste des livres selon le corpus sélectionné.

        - Bible (BHSA) : ordre canonique de la Bible hébraïque (Torah en
          tête) = ordre naturel des nœuds « book » dans Text-Fabric ;
        - Mishna (Sefaria) : les six sedarim dans l'ordre canonique, les
          traités dans l'ordre canonique au sein de chaque seder (le
          catalogue statique évite tout appel réseau).
        """
        if self.corpus_var.get() == CORPUS_MISHNA:
            self._book_order = []
            display = []
            for seder, tracts in SEDARIM:
                display.append(seder)
                self._book_order.append((None, seder, None))
                for title, fr in tracts:
                    display.append("    " + fr)
                    self._book_order.append((title, fr, None))
            self.book_combo["values"] = display
            # Index par libellé affiché (indenté) ; l'indentation marque
            # visuellement l'appartenance au seder et est retirée à l'usage.
            self._book_index = {}
            for title, fr, _n in self._book_order:
                if title is not None:
                    self._book_index["    " + fr] = (title, None)
            if display:
                # Premier traité (Bérakhot), pas le seder lui-même.
                self.book_combo.set(display[1])
                self._on_book_change()
            return
        if self.api is None:
            # Base BHSA pas encore chargée (ou en échec) : la liste des
            # livres bibliques reste vide ; _on_corpus_loaded la remplira.
            self.book_combo["values"] = []
            return
        F = self.api.F
        # Ordre canonique de la Bible hébraïque (Torah en tête) = ordre
        # naturel des nœuds « book » dans Text-Fabric.
        self._book_order = []
        display = []
        for b in F.otype.s("book"):
            bhsa = F.book.v(b)
            fr = book_french(bhsa)
            self._book_order.append((bhsa, fr, b))
            display.append(fr)
        self.book_combo["values"] = display
        # Index internes pour retrouver les bornes (chapitres/versets).
        self._book_index = {fr: (bhsa, b) for bhsa, fr, b in self._book_order}
        if display:
            self.book_combo.current(0)
            self._on_book_change()

    # --- Navigation rapide (livre / verset) ------------------------------
    def _nav_book(self, step):
        """Sélectionne le livre précédent (step=-1) ou suivant (step=+1)
        dans la liste affichée, puis affiche automatiquement son premier
        chapitre / premier verset. Reste silencieux aux bornes de la liste."""
        values = list(self.book_combo["values"])
        if not values:
            return
        try:
            idx = values.index(self.book_var.get())
        except ValueError:
            return
        new_idx = idx + step
        if not 0 <= new_idx < len(values):
            return
        # En mode Mishna, ignorer les entrées « seder » (non sélectionnables
        # : ce sont les titres de section, pas des traités).
        if self.corpus_var.get() == CORPUS_MISHNA:
            while 0 <= new_idx < len(values) and not values[new_idx].startswith("    "):
                new_idx += step
            if not 0 <= new_idx < len(values):
                return
        self.book_combo.current(new_idx)
        self._on_book_change()
        self._run_verse()

    def _nav_chapter(self, step):
        """Sélectionne le chapitre précédent (step=-1) ou suivant (step=+1)
        du livre courant, repeuple la liste des versets (premier verset
        via _on_chapter_change) puis l'affiche automatiquement. Retourne
        False (et joue un son) aux bornes du livre."""
        values = list(self.chapter_combo["values"])
        if not values:
            self._nav_boundary_sound()
            return False
        try:
            idx = values.index(self.chapter_var.get())
        except ValueError:
            self._nav_boundary_sound()
            return False
        new_idx = idx + step
        if not 0 <= new_idx < len(values):
            self._nav_boundary_sound()
            return False
        self.chapter_combo.current(new_idx)
        self._on_chapter_change()
        self._run_verse()
        return True

    def _nav_verse(self, step):
        """Sélectionne le verset précédent (step=-1) ou suivant (step=+1)
        du chapitre courant, puis l'affiche automatiquement. Retourne
        False (et joue un son) aux bornes du chapitre."""
        values = list(self.verse_combo["values"])
        if not values:
            self._nav_boundary_sound()
            return False
        try:
            idx = values.index(self.verse_var.get())
        except ValueError:
            self._nav_boundary_sound()
            return False
        new_idx = idx + step
        if not 0 <= new_idx < len(values):
            self._nav_boundary_sound()
            return False
        self.verse_combo.current(new_idx)
        self._run_verse()
        return True

    def _nav_boundary_sound(self):
        """Son système (« cloche » Tk) signalant un début ou une fin de liste."""
        try:
            self.root.bell()
        except tk.TclError:
            pass

    def _on_nav_verse_key(self, step):
        """Raccourci clavier Ctrl+↑ / Ctrl+↓ : même comportement que les
        boutons ▲/▼ du verset (navigation + affichage, son aux bornes)."""
        self._nav_verse(step)
        return "break"

    def _on_nav_chapter_key(self, step):
        """Raccourci clavier Shift+↑ / Shift+↓ : même comportement que les
        boutons ▲/▼ du chapitre (navigation + affichage, son aux bornes)."""
        self._nav_chapter(step)
        return "break"

    def _on_nav_book_key(self, step):
        """Raccourci clavier Alt+↑ / Alt+↓ : même comportement que les
        boutons ▲/▼ du livre (navigation + affichage, son aux bornes)."""
        self._nav_book(step)
        return "break"

    def _on_corpus_change(self, event=None):
        """Bascule entre Bible et Mishna : repeuple la liste des livres.

        En mode Mishna, les options propres à la BHSA (masquage du détail
        mot à mot, traductions Segond/KJV) n'ont pas d'effet : elles sont
        grisées. Les formats Texte/Synthèse/JSON restent actifs : ils
        s'appliquent aussi à l'analyse grammaticale de la mishna (Synthèse
        est ramenée à Texte pour la Mishna).
        """
        mishna = self.corpus_var.get() == CORPUS_MISHNA
        state = "disabled" if mishna else "!disabled"
        self.verse_no_words_widget.state([state])
        for child in self.verse_trads_frame.winfo_children():
            if isinstance(child, ttk.Checkbutton):
                child.state([state])
        # Le bouton de lecture reste grisé en basculant de corpus : seule
        # « Afficher le verset » l'autorise (corpus Bible).
        self.btn_audio.state(["disabled"])
        self._populate_books()

    def _on_book_change(self, event=None):
        fr = self.book_var.get()
        entry = self._book_index.get(fr)
        if entry is None:
            return
        bhsa, book_node = entry
        if self.corpus_var.get() == CORPUS_MISHNA:
            # Catalogue statique : nombre de mishnayot par chapitre.
            shape = STRUCTURE.get(bhsa, [])
            chapters = list(range(1, len(shape) + 1))
            self.chapter_combo["values"] = [str(c) for c in chapters]
            if chapters:
                self.chapter_combo.current(0)
                self._on_chapter_change()
            return
        if self.api is None:
            return
        F, L = self.api.F, self.api.L
        chapters = sorted({F.chapter.v(c) for c in L.i(book_node, "chapter")})
        self._chapters_for_book = chapters
        self.chapter_combo["values"] = [str(c) for c in chapters]
        if chapters:
            self.chapter_combo.current(0)
            self._on_chapter_change()

    def _on_chapter_change(self, event=None):
        fr = self.book_var.get()
        entry = self._book_index.get(fr)
        if entry is None:
            return
        bhsa, book_node = entry
        try:
            chap = int(self.chapter_var.get())
        except ValueError:
            return
        if self.corpus_var.get() == CORPUS_MISHNA:
            shape = STRUCTURE.get(bhsa, [])
            n = shape[chap - 1] if 1 <= chap <= len(shape) else 0
            self.verse_combo["values"] = [str(v) for v in range(1, n + 1)]
            if n:
                self.verse_combo.current(0)
            return
        if self.api is None:
            return
        F, L = self.api.F, self.api.L
        chap_node = next((c for c in L.i(book_node, "chapter")
                         if F.chapter.v(c) == chap), None)
        if chap_node is None:
            self.verse_combo["values"] = []
            return
        verses = sorted({F.verse.v(v) for v in L.i(chap_node, "verse")})
        self.verse_combo["values"] = [str(v) for v in verses]
        if verses:
            self.verse_combo.current(0)

    def _build_readme_tab(self, parent=None):
        """Onglet README : rendu enrichi du fichier README.md.

        Le markdown est converti en HTML par le module ``markdown``
        (structure de référence), puis le HTML est restitué dans un
        tk.Text avec tags : titres, gras, italique, blocs de code,
        listes à puces. Ce rendu maison (pas de moteur HTML externe,
        notamment pas tkinterweb qui provoque un segmentation fault
        sous Windows) ne peut pas planter la fenêtre. Sans module
        markdown, repli sur le markdown brut.
        """
        tab = self.tab_readme
        # Lecture du README : à côté du script, puis ressources
        # embarquées (PyInstaller), puis dossier de l'exécutable.
        readme = None
        for base in (os.path.dirname(os.path.abspath(__file__)),
                     _resource_dir(), _app_dir()):
            for name in ("README.md", "readme.md"):
                p = os.path.join(base, name)
                if os.path.isfile(p):
                    readme = p
                    break
            if readme:
                break
        if readme is None:
            ttk.Label(tab, text="README.md introuvable.").pack(padx=8,
                                                              pady=8)
            return
        with open(readme, encoding="utf-8") as fh:
            md_text = fh.read()

        # Zone de texte défilable avec rendu enrichi.
        wrap = tk.Frame(tab)
        wrap.pack(fill="both", expand=True, padx=4, pady=4)
        text = tk.Text(wrap, wrap="word", padx=12, pady=8,
                       font=("Segoe UI", 10) if sys.platform == "win32"
                       else ("TkDefaultFont", 10),
                       bg="white", relief="flat")
        yscroll = ttk.Scrollbar(wrap, orient="vertical", command=text.yview)
        yscroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.configure(yscrollcommand=yscroll.set)

        # Tags du rendu. cget("font") renvoie une CHAÎNE : résoudre
        # la police via tkinter.font pour obtenir famille et taille
        # numériques.
        from tkinter import font as tkfont
        base = tkfont.Font(font=text.cget("font"))
        fam = base.actual("family")
        size = base.actual("size")
        mono = tkfont.Font(family="Consolas", size=10) \
            if sys.platform == "win32" else tkfont.nametofont("TkFixedFont")
        mono_small = mono.copy()
        mono_small.configure(size=mono.actual("size") - 1)
        # Hiérarchie h1..h6 : chaque niveau se distingue par la taille,
        # la couleur et l'espacement — h1 titre principal, h2 section
        # (souligné par un filet), h3 sous-section, h4-h6 niveaux fins.
        text.tag_configure("h1", font=(fam, size + 9, "bold"),
                           foreground="#1a1a2e", spacing3=12, spacing1=14)
        text.tag_configure("h2", font=(fam, size + 5, "bold"),
                           foreground="#16213e", spacing3=8, spacing1=16,
                           underline=True)
        text.tag_configure("h3", font=(fam, size + 2, "bold"),
                           foreground="#0f3460", spacing1=10, spacing3=4)
        text.tag_configure("h4", font=(fam, size, "bold italic"),
                           foreground="#0f3460", spacing1=8)
        text.tag_configure("h5", font=(fam, size - 1, "bold"),
                           foreground="#51557e", spacing1=6)
        text.tag_configure("h6", font=(fam, size - 1, "italic"),
                           foreground="#51557e", spacing1=6)
        text.tag_configure("bold", font=(fam, size, "bold"))
        text.tag_configure("italic", font=(fam, size, "italic"))
        text.tag_configure("code", font=mono, background="#f0f0f0")
        text.tag_configure("pre", font=mono_small, background="#f5f5f5",
                           lmargin1=12, lmargin2=12,
                           spacing1=4, spacing3=4)
        text.tag_configure("li", lmargin1=16, lmargin2=24)
        text.tag_configure("hr", justify="center", foreground="gray60")

        try:
            import markdown
            html = markdown.markdown(
                md_text, extensions=["tables", "fenced_code",
                                     "sane_lists"])
            self._render_html_to_text(text, html)
        except ImportError:
            text.insert("1.0", md_text)

        text.configure(state="disabled")

    def _render_html_to_text(self, text_widget, html):
        """Restitue un sous-ensemble HTML dans un tk.Text avec tags.

        Pris en charge : h1-h6, p, br, hr, ul/ol/li (imbrication
        approximée par l'indentation), strong/b, em/i, code, pre,
        blockquote. Le texte brut du HTML est inséré, les tags
        s'appliquent par plages.
        """
        import html as _html
        import re

        # Découpage du HTML en événements (ouvrant/fermant/texte).
        tag_re = re.compile(r"<(/?)(\w+)([^>]*)>")
        pos = 0
        events = []  # (type, nom, attrs) / ("text", contenu)
        for m in tag_re.finditer(html):
            if m.start() > pos:
                events.append(("text", html[pos:m.start()], ""))
            events.append(("close" if m.group(1) else "open",
                           m.group(2).lower(), m.group(3) or ""))
            pos = m.end()
        if pos < len(html):
            events.append(("text", html[pos:], ""))

        headings = {"h1", "h2", "h3", "h4", "h5", "h6"}
        # --- Traitement séquentiel des événements ---
        text_widget.delete("1.0", "end")
        markup = []  # pile de tags actifs ("bold", "italic", "code")
        list_stack = []
        counters = []
        def current_tags():
            return list(markup)

        for kind, a, b in events:
            if kind == "text":
                content = _html.unescape(a)
                if not content:
                    continue
                # Sauter les contenus vides (inter-tags).
                if not content.strip() and not content.startswith("\n"):
                    continue
                tags = current_tags() + (["li"] if list_stack else [])
                text_widget.insert("end", content, tags or ())
            elif kind == "open":
                if a in headings:
                    text_widget.insert("end", "\n")
                    markup.append("h" + a[1])
                    # Les titres ferment implicitement les paragraphes.
                elif a in ("strong", "b"):
                    markup.append("bold")
                elif a in ("em", "i"):
                    markup.append("italic")
                elif a == "code":
                    markup.append("code")
                elif a == "pre":
                    text_widget.insert("end", "\n")
                    markup.append("pre")
                elif a in ("ul", "ol"):
                    list_stack.append(a)
                    counters.append(0)
                    text_widget.insert("end", "\n")
                elif a == "li":
                    # Nouvelle ligne seulement si le dernier caractère
                    # inséré n'est pas déjà un retour à la ligne.
                    end = text_widget.index("end - 1c")
                    last = text_widget.get(f"{end}", "end")
                    sep = "" if last == "\n" else "\n"
                    if list_stack and list_stack[-1] == "ol":
                        counters[-1] += 1
                        text_widget.insert("end", sep + "  " * (len(list_stack) - 1)
                                          + f"{counters[-1]}. ", ("li",))
                    else:
                        text_widget.insert("end", sep + "  " * max(0, len(list_stack) - 1)
                                          + "\u2022 ", ("li",))
                elif a == "br":
                    text_widget.insert("end", "\n")
                elif a == "hr":
                    text_widget.insert("end", "\n\u2500" * 30 + "\n", ("hr",))
                elif a == "blockquote":
                    markup.append("li")
                    text_widget.insert("end", "\n")
            elif kind == "close":
                if a in headings:
                    if markup and markup[-1].startswith("h"):
                        markup.pop()
                    text_widget.insert("end", "\n\n", ())
                elif a in ("strong", "b", "em", "i", "code", "li",
                           "blockquote"):
                    if markup and markup[-1] in ("bold", "italic",
                                                 "code", "li"):
                        markup.pop()
                elif a == "pre":
                    if markup and markup[-1] == "pre":
                        markup.pop()
                    text_widget.insert("end", "\n\n", ())
                elif a in ("ul", "ol"):
                    if list_stack:
                        list_stack.pop()
                    if counters:
                        counters.pop()
                    text_widget.insert("end", "\n")
        # Nettoyage : lignes vides multiples -> une seule. La
        # suppression doit être CIBLÉE (search/delete sur la plage
        # excédentaire) : relire tout le texte avec get() puis le
        # réinsérer perdrait tous les tags de formatage.
        while True:
            idx = text_widget.search("\n\n\n", "1.0", "end")
            if not idx:
                break
            # Supprimer UN newline de la séquence (boucle jusqu'à
            # normalisation complète).
            text_widget.delete(f"{idx} lineend", f"{idx} lineend +1c")

    def _build_binyanim_tab(self):
        """Onglet « Binyanim » : conjugaison d'un verbe dans les 7 binyanim.

        Le résultat du CLI (texte marqué) est parsé puis présenté en
        sous-onglets, un par binyan, dont le libellé combine le nom
        français et le nom hébreu (ex. « qal (paal) / פָּעַל »).
        """
        tab = self.tab_binyanim
        form = ttk.LabelFrame(tab, text="Verbe à conjuguer (mot conjugué ou racine trilitaire)")
        form.pack(fill="x", padx=8, pady=8)

        self.binyanim_entry = BidiHebrewText(form, font=HEBREW_FONT, height=1,
                                         wrap="none", padx=4, pady=4)
        self.binyanim_entry.pack(fill="x", padx=4, pady=4)
        self.binyanim_entry.bind("<FocusIn>", self._remember_target)

        hint = ttk.Label(form,
                         text="Saisissez un mot conjugué (ex. שָׁמַר, avec nikkud) ou une racine "
                              "trilitaire nue (ex. שמר, קום, בנה). La conjugaison est générée "
                              "pour les 7 binyanim ; la catégorie du verbe (fort ou faible) "
                              "est détectée automatiquement.",
                         wraplength=760, justify="left")
        hint.pack(anchor="w", padx=4, pady=(2, 6))

        self._build_keyboard(form)

        opts = ttk.Frame(tab)
        opts.pack(fill="x", padx=8)
        ttk.Label(opts, text="Format :").pack(side="left", padx=(0, 4))
        self.binyanim_format = tk.StringVar(value="text")
        ttk.Radiobutton(opts, text="Texte", variable=self.binyanim_format,
                        value="text").pack(side="left")
        ttk.Radiobutton(opts, text="JSON", variable=self.binyanim_format,
                        value="json").pack(side="left")
        # Les libellés des deux cases reprennent la couleur que prend
        # l'onglet d'un binyan attesté dans ce corpus : jaune pour la
        # Mishna, vert pour l'hébreu moderne (cf. BinyanimNotebook).
        # La couleur passe par des styles dédiés : selon le thème ttk
        # (ex. « vista » sous Windows), l'option -foreground est
        # refusée sur les widgets ttk (TclError unknown option).
        opts_style = ttk.Style(self.root)
        opts_style.configure("BinyanimMishnah.TCheckbutton",
                              foreground=BinyanimNotebook._FG_MISHNAH)
        opts_style.configure("BinyanimModern.TCheckbutton",
                              foreground=BinyanimNotebook._FG_MODERN)
        self.binyanim_use_mishnah = tk.BooleanVar(
            value=_PROPS.get("binyanim.mishnah", "false").strip().lower()
            == "true")
        ttk.Checkbutton(opts, text="Binyanim mishnaïques (Sefaria)",
                        variable=self.binyanim_use_mishnah,
                        style="BinyanimMishnah.TCheckbutton").pack(
                            side="left", padx=(16, 0))
        self.binyanim_use_modern = tk.BooleanVar(
            value=_PROPS.get("binyanim.modern", "false").strip().lower()
            == "true")
        ttk.Checkbutton(opts, text="Binyanim modernes (Pealim)",
                        variable=self.binyanim_use_modern,
                        style="BinyanimModern.TCheckbutton").pack(
                            side="left", padx=(8, 0))
        # Variantes attestées par cellule : toutes les conjuguaisons
        # concurrentes (ex. qal yiqtol 1cs אֶקְטֹל / אֶקְטַל) ou la forme
        # dominante seule.
        self.binyanim_use_variants = tk.BooleanVar(
            value=_PROPS.get("binyanim.variants", "true").strip().lower()
            == "true")
        ttk.Checkbutton(opts, text="Toutes les formes attestées",
                        variable=self.binyanim_use_variants).pack(
                            side="left", padx=(8, 0))
        # Référence biblique attestée par cellule (quand elle existe) :
        # « forme [Livre ch:v] ».
        self.binyanim_use_references = tk.BooleanVar(
            value=_PROPS.get("binyanim.references", "false").strip().lower()
            == "true")
        ttk.Checkbutton(opts, text="Référence attestée",
                        variable=self.binyanim_use_references).pack(
                            side="left", padx=(8, 0))

        self.btn_binyanim = ttk.Button(tab, text="Conjuguer le verbe",
                                       command=self._run_binyanim)
        self.btn_binyanim.pack(anchor="w", padx=8, pady=8)
        self.btn_binyanim.state(["disabled"])

        # Zone de résultat : sous-onglets par binyan + sortie brute.
        frame = ttk.LabelFrame(tab, text="Résultat")
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.binyanim_notebook = BinyanimNotebook(frame)
        self.binyanim_notebook.grid(row=0, column=0, sticky="nsew")
        # Onglet « Verbe » : identification + catégorie faible.
        self.binyanim_verb_tab = ttk.Frame(self.binyanim_notebook.body)
        self.binyanim_notebook.add(self.binyanim_verb_tab, text="Verbe")
        self.binyanim_verb_text = self._make_binyanim_output(self.binyanim_verb_tab)
        # Onglet « Sortie complète » : texte marqué brut du CLI.
        self.binyanim_raw_tab = ttk.Frame(self.binyanim_notebook.body)
        self.binyanim_notebook.add(self.binyanim_raw_tab, text="Sortie complète")
        self.binyanim_raw_text = self._make_binyanim_output(self.binyanim_raw_tab)
        # Ids des onglets fixes, pour le nettoyage des sous-onglets de binyan.
        self.binyanim_fixed_ids = set(self.binyanim_notebook.tabs())
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        # Résultat binyanim courant (structure parse_binyanim_text) : garde
        # par le bouton « Imprimer ce binyan… » de chaque sous-onglet.
        self.binyanim_parsed = None

    def _make_binyanim_output(self, parent):
        """Zone de texte défilable (ascenseurs vertical + horizontal)."""
        text = ResultText(parent, font=HEBREW_FONT_MONO, wrap="none",
                          height=10, width=40)
        # Le clavier virtuel doit cibler le champ de la barre Ctrl-F.
        text._find_focus_notifier = self._remember_target
        text.grid(row=0, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(parent, orient="vertical", command=text.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(parent, orient="horizontal", command=text.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        text.configure(state="disabled")
        StableSelection(text)
        # Menu contextuel : ouvrir le mode verset sur la référence
        # contenue dans (ou autour de) la sélection. Les modifieurs font
        # partie du pattern Tk : Shift+clic droit génère <Shift-Button-3>,
        # un bind distinct est nécessaire.
        text.bind("<Button-3>", lambda e, t=text: self._binyan_context_menu(e, t))
        text.bind("<Shift-Button-3>", lambda e, t=text: self._binyan_context_menu(e, t))
        return text

    def _reference_pairs_in(self, chunk):
        """Couples (forme, référence) d'un extrait de texte.

        Chaque segment « forme  [Livre ch:v] » donne un couple ; les
        formes sont séparées par « / ». Retourne [] si l'extrait ne
        porte aucune référence.
        """
        import re
        pairs = []
        # Segments : texte jusqu'à la référence fermante.
        seg_re = re.compile(
            r"(?P<form>[^/\[]+)\s*\[(?P<book>[^\]]+?)\s"
            r"(?P<ch>\d+)[:.](?P<v>\d+)\]")
        for m in seg_re.finditer(chunk):
            form = m.group("form").strip()
            # Ne garder que le dernier mot hébreu du segment (la
            # forme attachée à sa référence, après le libellé de
            # personne).
            toks = [t for t in form.split() if t]
            he = ""
            for tok in reversed(toks):
                if any("\u05D0" <= c <= "\u05EA" for c in tok):
                    he = tok
                    break
            ref = f"{m.group('book')} {m.group('ch')}:{m.group('v')}"
            pairs.append((he, ref))
        return pairs

    def _line_reference_pairs(self, text_widget):
        """Couples (forme, référence) de la sélection, sinon de la
        ligne du clic (marques insert/current)."""
        import re
        chunks = []
        try:
            sel = text_widget.get("sel.first", "sel.last")
            if sel.strip():
                chunks.append(sel)
        except tk.TclError:
            pass
        for mark in ("insert", "current"):
            try:
                line = text_widget.get(f"{mark} linestart",
                                       f"{mark} lineend")
            except tk.TclError:
                continue
            if line.strip():
                chunks.append(line)
        for chunk in chunks:
            pairs = self._reference_pairs_in(chunk)
            if pairs:
                return pairs
        return []

    def _all_reference_pairs(self, text_widget):
        """Tous les couples (forme, référence) du texte affiché."""
        try:
            content = text_widget.get("1.0", "end")
        except tk.TclError:
            return []
        return self._reference_pairs_in(content)

    def _binyan_context_menu(self, event, text_widget):
        # AnalyseurGUI n'est pas un widget Tk : le menu doit avoir un
        # parent réel, le widget de sortie lui-même.
        menu = tk.Menu(text_widget, tearoff=0)
        # Priorité aux couples de la sélection ou de la ligne du clic
        # (TOUTES les références de la ligne, pas seulement la
        # première) ; repli : tous les couples du texte affiché.
        pairs = self._line_reference_pairs(text_widget)
        scope = "cette ligne"
        if not pairs:
            pairs = self._all_reference_pairs(text_widget)
            scope = "le texte"
        if pairs:
            menu.add_command(label=f"Ouvrir le verset ({scope})…",
                              state="disabled")
            for form, r in pairs:
                label = f"{form}  {r}" if form else r
                menu.add_command(
                    label=label,
                    command=lambda rr=r: self._open_verse_reference(rr))
        else:
            menu.add_command(label="Aucune référence dans la sélection",
                              state="disabled")
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            # Sous Windows, sans grab_release le menu peut rester
            # « capturé » et ignorer le clic suivant.
            menu.grab_release()

    def _open_verse_reference(self, reference):
        """Bascule sur l'onglet Livre et affiche la référence donnée."""
        # Bascule de corpus vers la Bible si nécessaire.
        if self.corpus_var.get() == CORPUS_MISHNA:
            self.corpus_var.set(CORPUS_BIBLE)
            self._on_corpus_change()
        self.notebook.select(self.tab_verse)
        # Sélectionner livre / chapitre / verset dans les combobox.
        import re as _re
        m = _re.match(r"(.+?)\s+(\d+)[:.](\d+)$", reference.strip())
        if not m:
            messagebox.showwarning("Référence", f"Référence illisible : {reference}")
            return
        book_fr, chapter, verse = m.group(1), m.group(2), m.group(3)
        values = list(self.book_combo["values"])
        target = None
        for v in values:
            if v.strip() == book_fr or v == book_fr:
                target = v
                break
        if target is None:
            messagebox.showwarning("Référence",
                                   f"Livre introuvable : {book_fr}")
            return
        self.book_combo.set(target)
        self._on_book_change()
        if str(chapter) not in list(self.chapter_combo["values"]):
            messagebox.showwarning("Référence",
                                   f"Chapitre introuvable : {chapter}")
            return
        self.chapter_combo.set(chapter)
        self._on_chapter_change()
        if str(verse) not in list(self.verse_combo["values"]):
            messagebox.showwarning("Référence",
                                   f"Verset introuvable : {verse}")
            return
        self.verse_combo.set(verse)
        self._run_verse()

    def _run_binyanim(self):
        if self.api is None:
            return
        form = self.binyanim_entry.get_logical().strip()
        if not form:
            messagebox.showwarning("Binyanim", "Saisissez un verbe hébreu ou une racine.")
            return
        fmt = self.binyanim_format.get()
        use_mishnah = bool(self.binyanim_use_mishnah.get())
        use_modern = bool(self.binyanim_use_modern.get())
        use_variants = bool(getattr(self, "binyanim_use_variants", None)
                            and self.binyanim_use_variants.get())
        use_references = bool(getattr(self, "binyanim_use_references", None)
                              and self.binyanim_use_references.get())
        F = self.api.F
        self._disable_buttons()
        # Sablier : la collecte des références attestées (surtout avec
        # les variantes) scanne la base BHSA et peut prendre du temps.
        # root.update_idletasks() force l'affichage du curseur avant
        # le lancement du thread.
        self.root.configure(cursor="watch")
        self.root.update_idletasks()
        self.status.configure(text=f"Conjugaison de « {form} »…")

        def worker():
            L = self.api.L
            analysis = analyze_binyanim(F, form, use_mishnah=use_mishnah,
                                        use_modern=use_modern,
                                        with_variants=use_variants,
                                        with_references=use_references,
                                        L=L)
            if not analysis.get("found"):
                verb = analysis.get("verb", {})
                reason = verb.get("reason") or analysis.get("reason")
                suggestions = verb.get("suggestions") \
                    or analysis.get("suggestions") or []
                self._work_queue.put(("binyanim_not_found",
                                      (form, reason, suggestions)))
                return
            if fmt == "json":
                result = format_binyanim_json(analysis)
                self._work_queue.put(("binyanim_raw", result))
            else:
                result = format_binyanim(analysis)
                self._work_queue.put(("binyanim_raw", result))
                parsed = parse_binyanim_text(result)
                self._work_queue.put(("binyanim_parsed", parsed))

        threading.Thread(target=worker, daemon=True).start()

    def _show_binyanim_not_found(self, payload):
        """Forme non identifiable : message, résultat précédent conservé."""
        form, reason, suggestions = payload
        msg = (f"Aucun verbe trouvé pour « {form} » dans la base BHSA.\n\n"
               "La fenêtre résultat n'a pas été modifiée.")
        if reason == "orphan_shin_dot":
            msg = (f"Saisie invalide : « {form} » contient un point "
                   "shin/sin sans la lettre ש.\n\n"
                   "Saisissez la lettre ש, puis son point (שׁ ou שׂ) — "
                   "ou la racine sans point.\n\n"
                   "La fenêtre résultat n'a pas été modifiée.")
        elif suggestions:
            hint = ", ".join(suggestions)
            if reason == "root_truncated":
                msg = (f"« {form} » est la forme courte d'un verbe faible "
                       f"(racine probable : {hint}).\n\n"
                       "Saisissez la racine complète pour la conjuguer.\n\n"
                       "La fenêtre résultat n'a pas été modifiée.")
            else:
                msg = (f"Aucun verbe trouvé pour « {form} » dans la base "
                       f"BHSA. Racines proches : {hint}.\n\n"
                       "La fenêtre résultat n'a pas été modifiée.")
        messagebox.showwarning("Binyanim", msg)
        self.status.configure(text="Prêt.")
        self.root.configure(cursor="")
        self._enable_buttons()

    def _show_binyanim_raw(self, text):
        """Affiche la sortie brute (texte marqué ou JSON)."""
        self._set_output(self.binyanim_raw_text, text)
        self.binyanim_notebook.select(self.binyanim_raw_tab)
        self.status.configure(text="Prêt.")
        self.root.configure(cursor="")
        self._enable_buttons()

    def _show_binyanim_parsed(self, parsed):
        """Construit un sous-onglet par binyan à partir du texte parsé.

        Le libellé de chaque sous-onglet combine le nom français et le nom
        hébreu du binyan : « qal (paal) · פָּעַל ».

        Quand la racine n'a pas de sens dans un binyan (binyan non attesté
        pour ce lemme dans la Bible hébraïque), le libellé de l'onglet est
        coloré en rouge et l'onglet affiche un avertissement. Si des formes
        de ce binyan sont attestées dans la Mishna (option « Binyanim
        mishnaïques »), le libellé passe en jaune et l'avertissement
        mentionne ces formes. Si le binyan est attesté en hébreu moderne
        (option « Binyanim modernes », dictionnaire Pealim) mais absent
        de la Bible, le libellé passe en vert et l'avertissement mentionne
        le lemme moderne ; un binyan biblique attesté en hébreu moderne
        garde sa couleur mais l'onglet affiche l'attestation moderne.
        """
        # Nettoyer les sous-onglets de binyanim précédents (garder Verbe
        # et Sortie complète, toujours en fin de notebook).
        keep = self.binyanim_fixed_ids
        for tab_id in list(self.binyanim_notebook.tabs()):
            if tab_id in keep:
                continue
            self.binyanim_notebook.forget(tab_id)

        verb = parsed.get("verb", {})
        weak = parsed.get("weak", {})
        header = []
        if verb.get("root"):
            header.append(f"Racine : {verb['root']}")
        if verb.get("lex"):
            header.append(f"lemme BHSA : {verb['lex']}")
        if verb.get("gloss_fr"):
            header.append(f"« {verb['gloss_fr']} »")
        lines = []
        if header:
            lines.append("  · ".join(header))
        if weak:
            code = weak.get("code")
            is_weak = code not in (None, "strong")
            if is_weak:
                lines.append("")
                lines.append(f"Verbe faible : {weak.get('label', '')}")
                if weak.get("desc"):
                    lines.append(f"  {weak['desc']}")
                # Règles de conjugaison caractéristiques de la catégorie,
                # affichées à la suite de l'identification du verbe
                # (assimilation du nun, élision du ה final, refus du sheva
                # des gutturales, etc.).
                if code in WEAK_CONJ_RULES:
                    lines.append("")
                    lines.append("Règles de conjugaison caractéristiques :")
                    lines.append("")
                    for title, rule in WEAK_CONJ_RULES[code]:
                        lines.append(f"• {title}")
                        lines.append(f"  {rule}")
                        lines.append("")
            else:
                lines.append("")
                lines.append("Verbe fort (shalem) : conjugaison régulière.")
        self._set_output(self.binyanim_verb_text, "\n".join(lines))

        raw_index = self.binyanim_notebook.index(self.binyanim_raw_tab)
        for b in parsed.get("binyanim", []):
            tab = ttk.Frame(self.binyanim_notebook.body)
            label = f"{b['name_fr']} · {b['name_he']}"
            if b.get("attested"):
                label += " ✓"
            # Insérer avant l'onglet « Sortie complète ».
            self.binyanim_notebook.insert(raw_index, tab, text=label)
            raw_index += 1
            header = ttk.Frame(tab)
            header.grid(row=0, column=0, sticky="ew")
            ttk.Button(header, text="Imprimer ce binyan…",
                       style="Link.TButton",
                       command=lambda b=b: self._print_binyan(b["code"])
                       ).pack(side="left", padx=8, pady=4)
            body = ttk.Frame(tab)
            body.grid(row=1, column=0, sticky="nsew")
            tab.rowconfigure(1, weight=1)
            tab.columnconfigure(0, weight=1)
            text = self._make_binyanim_output(body)
            content = b.get("text", "")
            tr_fr = b.get("translation_fr") or ""
            tr_en = b.get("translation_en") or ""
            trads = [f"fr : {tr_fr}" for _ in (0,) if tr_fr] + \
                    [f"en : {tr_en}" for _ in (0,) if tr_en]
            if trads:
                head = ("Traduction : " + "  |  ".join(trads) + "\n\n")
                content = head + content
            mishnah_forms = b.get("mishnah_forms") or []
            modern = b.get("modern_forms") or None
            if modern:
                modern_txt = ("◈ Attesté en hébreu moderne : "
                              + (modern.get("lemma") or ""))
                if modern.get("gloss"):
                    modern_txt += f" ({modern['gloss']})"
                if modern.get("url"):
                    modern_txt += f"\n  {modern['url']}"
                modern_note = modern_txt + "\n\n"
            else:
                modern_note = ""
            if b.get("exists") is False:
                if mishnah_forms:
                    self.binyanim_notebook.tab(
                        tab, fg=BinyanimNotebook._FG_MISHNAH)
                    warn = ("⚠ Pas de sens biblique dans ce binyan "
                            f"({b['name_fr']} / {b['name_he']}), mais "
                            "attesté dans la Mishna (binyan non "
                            "biblique) : " + ", ".join(mishnah_forms) +
                            ".\n"
                            "Le paradigme ci-dessous est théorique, "
                            "construit par analogie.\n\n")
                    content = warn + modern_note + content
                elif modern:
                    self.binyanim_notebook.tab(
                        tab, fg=BinyanimNotebook._FG_MODERN)
                    warn = ("⚠ Pas de sens biblique dans ce binyan "
                            f"({b['name_fr']} / {b['name_he']}), mais "
                            "attesté en hébreu moderne (binyan non "
                            "biblique).\n"
                            "Le paradigme ci-dessous est théorique, "
                            "construit par analogie.\n\n")
                    content = warn + modern_note + content
                else:
                    self.binyanim_notebook.tab(
                        tab, fg=BinyanimNotebook._FG_MISSING)
                    warn = ("⚠ Cette racine n'a pas de sens dans ce binyan "
                            f"({b['name_fr']} / {b['name_he']}) : "
                            "aucune occurrence de ce binyan pour cette racine "
                            "dans la Bible hébraïque.\n"
                            "Le paradigme ci-dessous est théorique, construit "
                            "par analogie.\n\n")
                    content = warn + content
            elif modern:
                content = modern_note + content
            self._set_output(text, content)

        if parsed.get("binyanim"):
            # Sélectionner le premier binyan.
            first = self.binyanim_notebook.tabs()[0]
            self.binyanim_notebook.select(first)
        self.binyanim_parsed = parsed
        self.status.configure(text="Prêt.")
        self.root.configure(cursor="")
        self._enable_buttons()

    def _print_binyan(self, binyan_code):
        """Aperçu avant impression du paradigme d'un binyan (onglet actif).

        Le document est construit depuis le résultat binyanim courant
        (self.binyanim_parsed, structure parse_binyanim_text) : l'aperçu
        reflète exactement le sous-onglet affiché, y compris les
        traductions et le statut d'attestation (BHSA/Mishna).
        """
        if not self.binyanim_parsed:
            messagebox.showwarning(
                "Binyanim",
                "Conjuguez d'abord un verbe (bouton « Conjuguer le verbe »).")
            return
        try:
            two_up, font_scale = _saved_print_settings()
            binyan_print.open_binyan_preview(
                self.root, self.binyanim_parsed, binyan_code,
                two_up=two_up, font_scale=font_scale,
                on_close=self._save_print_settings)
            self.status.configure(text="Aperçu d'impression ouvert.")
        except ValueError:
            messagebox.showwarning(
                "Binyanim",
                f"Binyan « {binyan_code} » introuvable dans le résultat courant.")
        except Exception as exc:
            messagebox.showerror(
                "Impression", f"Échec de la préparation de l'aperçu : {exc}")

    def _save_print_settings(self, two_up, font_scale):
        """Persiste les réglages d'aperçu (gui.properties) à la fermeture."""
        _save_properties(self.root, {
            "print.pages.per.sheet": "2" if two_up else "1",
            "print.font.scale": str(int(font_scale)),
        })

    # --- Lancement des analyses (en arrière-plan) -----------------------
    def _set_output(self, widget, text):
        widget.set_text(text)

    def _disable_buttons(self):
        for btn in (self.btn_verse, self.btn_word, self.btn_phrase, self.btn_binyanim):
            btn.state(["disabled"])

    def _enable_buttons(self):
        if self.api is not None:
            for btn in (self.btn_verse, self.btn_word, self.btn_phrase,
                        self.btn_binyanim):
                btn.state(["!disabled"])

    # --- Lecture audio du verset -----------------------------------------
    def _set_audio_error(self, msg):
        self.audio_time.configure(text=msg)
        self.audio_scale.state(["disabled"])

    def _current_verse_reference(self):
        """Référence actuellement sélectionnée (Bible ou Mishna), ou None
        si la sélection est incomplète. La comparaison avec le WAV en
        lecture se fait sur cette même chaîne (les traités Mishna sont
        indentés dans la liste : .strip() comme pour _start_audio_mishnah)."""
        fr = self.book_var.get()
        entry = self._book_index.get(fr)
        if entry is None:
            return None
        chap = self.chapter_var.get()
        verse = self.verse_var.get()
        if not chap or not verse:
            return None
        return f"{fr.strip()} {chap}:{verse}"

    def _on_audio_button(self):
        if self._audio_player is not None:
            # Référence courante ≠ celle du WAV en lecture (l'utilisateur a
            # affiché un autre verset) : on repart d'une synthèse du verset
            # courant, pas d'une reprise de l'ancien WAV.
            current_ref = self._current_verse_reference()
            if current_ref is not None and current_ref != self._audio_ref:
                self._stop_audio()
            else:
                # Bouton unique, machine à états : ⏸ pendant la lecture (clic
                # = pause), ▶ en pause ou en fin de lecture (clic = (re)
                # lecture depuis la position du curseur), ▶ au repos.
                player = self._audio_player
                if not player.is_playing() and not player.is_paused():
                    # Fin de lecture : relance à la position du curseur ; si
                    # le curseur est en fin de verset, on repart du début.
                    pos = player.position_ms()
                    if self._audio_duration_ms - pos < 50:
                        pos = 0
                        self.audio_pos.set(0)
                    try:
                        player.play(pos)
                        self.btn_audio.configure(text="⏸")
                    except VersePlayerError:
                        pass
                    self._poll_audio()
                    return
                self._toggle_audio_pause()
                return
        mishna = self.corpus_var.get() == CORPUS_MISHNA
        fr = self.book_var.get()
        entry = self._book_index.get(fr)
        if entry is None:
            messagebox.showwarning("Référence", "Sélectionnez un livre.")
            return
        bhsa, _b = entry
        chap = self.chapter_var.get()
        verse = self.verse_var.get()
        if not chap or not verse:
            messagebox.showwarning("Référence",
                                   "Sélectionnez chapitre et verset.")
            return
        if mishna:
            self._start_audio_mishnah(bhsa, fr.strip(), int(chap),
                                      int(verse))
            return
        if self.api is None:
            return
        try:
            speed = float(self.audio_speed.get())
            if not 0.5 <= speed <= 2.0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Vitesse",
                                   "Vitesse invalide : entrez une valeur "
                                   "entre 0.5 et 2.0.")
            return
        voice = self._voice_labels.get(self.audio_voice.get(), "shaul")
        reference = self._current_verse_reference()

        def fetch():
            from bhsa_grammar.reference import find_verse
            F, L, T = self.api.F, self.api.L, self.api.T
            node = find_verse(F, L, bhsa, int(chap), int(verse))
            if node is None:
                return None, reference
            return T.text(node), reference

        self._start_audio_synthesis(fetch, speed, voice, reference)

    def _start_audio_mishnah(self, tractate, fr, chapter, mishnah):
        """Lecture audio d'une mishna : texte hébreu « Torat Emet 357 » via
        l'API Sefaria (requiert le réseau, comme l'affichage), puis la même
        chaîne de synthèse phonikud-tts que pour le verset biblique."""
        try:
            speed = float(self.audio_speed.get())
            if not 0.5 <= speed <= 2.0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Vitesse",
                                   "Vitesse invalide : entrez une valeur "
                                   "entre 0.5 et 2.0.")
            return
        voice = self._voice_labels.get(self.audio_voice.get(), "shaul")
        reference = f"{fr} {chapter}:{mishnah}"

        def fetch():
            he = fetch_mishnah_mishnayot(tractate, chapter, "hebrew")
            if not he or not 1 <= mishnah <= len(he):
                return None, reference
            return he[mishnah - 1], reference

        self._start_audio_synthesis(fetch, speed, voice, reference)

    def _start_audio_synthesis(self, fetch, speed, voice, reference):
        """Sablier + thread de synthèse commun aux deux corpus.

        ``fetch`` est un callable exécuté dans le thread de travail qui
        renvoie ``(texte_hébreu_ou_None, reference)``.
        """
        self.btn_audio.state(["disabled"])
        self.audio_time.configure(text=f"Synthèse : {reference}…")
        # Sablier comme pour le chargement de la base : le premier usage
        # peut télécharger ~370 Mo de modèles phonikud-tts.
        self.root.configure(cursor="watch")

        def worker():
            hebrew, reference = fetch()
            if hebrew is None:
                self._work_queue.put(("audio_error",
                                      "Texte hébreu introuvable pour "
                                      f"{reference}."))
                return
            self._audio_last_text = hebrew
            path = os.path.join(tempfile.gettempdir(),
                                "analyse_hebreu_verse.wav")
            duration = synthesize_wav(hebrew, path, speed=speed, voice=voice)
            if duration is None or duration <= 0:
                detail = (("Détail : " + verse_audio.LAST_ERROR)
                          if verse_audio.LAST_ERROR else
                          "modèles phonikud-tts introuvables.")
                self._work_queue.put(("audio_error",
                                      "Synthèse vocale indisponible "
                                      f"({detail})"))
                return
            self._work_queue.put(("audio_ready", (path, duration, reference)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_audio_ready(self, path, duration_ms, reference=None,
                         resume_ms=None, start_paused=False):
        self._audio_ref = reference
        player = VersePlayer()
        try:
            length = player.open(path)
        except VersePlayerError as exc:
            player.close()
            self._set_audio_error(str(exc))
            self.btn_audio.state(["!disabled"])
            return
        self._audio_player = player
        self._audio_wav = path
        self._audio_duration_ms = max(1, duration_ms or length)
        self.btn_audio.configure(text="⏸")
        self.btn_audio.state(["!disabled"])
        self.root.configure(cursor="")
        self.audio_scale.state(["!disabled"])
        self.audio_scale.configure(to=self._audio_duration_ms)
        resume_ms = int(resume_ms) if resume_ms else 0
        self.audio_pos.set(min(resume_ms, self._audio_duration_ms))
        try:
            player.play(resume_ms)
        except VersePlayerError as exc:
            self._set_audio_error(str(exc))
            self._stop_audio()
            return
        if start_paused:
            player.pause()
            self.btn_audio.configure(text="▶")
        self._poll_audio()

    def _on_audio_error(self, msg):
        self._set_audio_error(msg)
        self.btn_audio.state(["!disabled"])
        self.root.configure(cursor="")

    def _resynthesize_current(self, reason):
        """Resynthétise le verset courant (vitesse ou voix changée en cours
        de lecture) et reprend la lecture à la position proportionnelle."""
        if self._audio_player is None or self._audio_last_text is None:
            return
        try:
            speed = float(self.audio_speed.get())
            if not 0.5 <= speed <= 2.0:
                return
        except ValueError:
            return
        voice = self._voice_labels.get(self.audio_voice.get(), "shaul")
        text = self._audio_last_text
        was_paused = self._audio_player.is_paused()
        pos = self._audio_player.position_ms()
        old_dur = self._audio_duration_ms or 1
        self._stop_audio()
        self.btn_audio.state(["disabled"])
        self.audio_time.configure(text=reason)
        self.root.configure(cursor="watch")

        def worker():
            path = os.path.join(tempfile.gettempdir(),
                                "analyse_hebreu_verse.wav")
            duration = synthesize_wav(text, path, speed=speed, voice=voice)
            if duration is None or duration <= 0:
                detail = (("Détail : " + verse_audio.LAST_ERROR)
                          if verse_audio.LAST_ERROR else
                          "modèles phonikud-tts introuvables.")
                self._work_queue.put(("audio_error",
                                      "Synthèse vocale indisponible "
                                      f"({detail})"))
                return
            ratio = duration / float(old_dur)
            self._work_queue.put(
                ("audio_ready", (path, duration, self._audio_ref,
                                 int(pos * ratio), was_paused)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_audio_speed_change(self, event=None):
        self._resynthesize_current("Resynthèse à la nouvelle vitesse…")

    def _on_audio_voice_change(self, event=None):
        self._resynthesize_current("Resynthèse avec la nouvelle voix…")

    def _toggle_audio_pause(self):
        if self._audio_player is None:
            return
        if self._audio_player.is_paused():
            self._audio_player.play()
            self.btn_audio.configure(text="⏸")
        else:
            self._audio_player.pause()
            self.btn_audio.configure(text="▶")

    def _on_audio_seek(self, value):
        if self._audio_player is None or self._audio_seeking:
            return
        self._audio_seeking = True
        try:
            self._audio_player.seek(float(value))
        except VersePlayerError:
            pass
        finally:
            self._audio_seeking = False

    def _poll_audio(self):
        if self._audio_player is None or self._audio_polling:
            return
        self._audio_polling = True

        def tick():
            self._audio_polling = False
            player = self._audio_player
            if player is None:
                return
            if not player.is_playing() and not player.is_paused():
                # Fin du verset : le lecteur reste ouvert et le curseur
                # actif — ▶ relance la lecture à la position du curseur.
                # La position MCI peut être retombée à 0 : on ne touche
                # pas au curseur, il marque l'endroit atteint.
                self.btn_audio.configure(text="▶")
                return
            if not self._audio_seeking:
                pos = player.position_ms()
                self.audio_pos.set(pos)
                self._update_audio_time(pos)
            self.root.after(200, tick)

        self.root.after(200, tick)

    def _update_audio_time(self, pos_ms):
        dur = self._audio_duration_ms

        def fmt(ms):
            return f"{int(ms) // 60000}:{int(ms) % 60000 // 1000:02d}"

        self.audio_time.configure(text=f"{fmt(pos_ms)} / {fmt(dur)}")

    def _stop_audio(self):
        player = self._audio_player
        self._audio_player = None
        self._audio_wav = None
        self._audio_ref = None
        self.root.configure(cursor="")
        if player is not None:
            player.stop()
            player.close()
        self.btn_audio.configure(text="▶")
        self.audio_scale.state(["disabled"])
        self.audio_pos.set(0)
        self._audio_duration_ms = 0
        self.audio_time.configure(text="0:00 / 0:00")


    def _build_translation_header(self, analysis, fr, chap, verse, trans_enabled=None):
        """Construit l'en-tête de traduction(s) pour le verset analysé.

        ``trans_enabled`` est un dict {lang: bool} lu dans le thread principal.
        """
        b_book = analysis["reference"][0]
        b_ch = analysis["reference"][1]
        b_vs = analysis["reference"][2]
        if trans_enabled is None:
            trans_enabled = {lang: var.get()
                            for lang, var in self.verse_trans.items()}
        blocks = []
        labels = {"fr": "Louis Segond 1910 (fr)", "en": "King James Version 1611 (en)",
                  "es": "Torres Amat 1823 (es)", "it": "Riveduta Luzzi 1927 (it)",
                  "rab": "Bible du Rabbinat 1899 (fr)"}
        for lang, _label in TRANSLATIONS:
            if not trans_enabled.get(lang):
                continue
            idx = self.translations.get(lang)
            title = labels.get(lang, lang)
            if idx is None:
                continue
            trans = get_translation(idx, b_book, b_ch, b_vs)
            if trans:
                blocks.append(f"Traduction ({title}) — {fr} {chap}:{verse}\n{trans}")
            else:
                blocks.append(
                    f"Traduction ({title}) — {fr} {chap}:{verse}\n"
                    "(verset absent de la traduction : numérotation différente "
                    "de la BHSA)"
                )
        if blocks:
            return "\n\n".join(blocks) + "\n\n"
        return ""

    def _run_verse(self):
        fr = self.book_var.get()
        entry = self._book_index.get(fr)
        if entry is None:
            messagebox.showwarning("Référence", "Sélectionnez un livre.")
            return
        bhsa, _b = entry
        chap = self.chapter_var.get()
        verse = self.verse_var.get()
        if not chap or not verse:
            messagebox.showwarning("Référence", "Sélectionnez chapitre et verset.")
            return
        # Afficher le verset valide la référence : le bouton de lecture
        # s'active (corpus Bible uniquement).
        if self._audio_tts_ready:
            self.btn_audio.state(["!disabled"])
        if self.corpus_var.get() == CORPUS_MISHNA:
            self._run_mishnah(bhsa, fr.strip(), int(chap), int(verse))
            return
        if self.api is None:
            return
        reference = f"{fr} {chap}:{verse}"
        fmt = self.verse_format.get()
        no_words = self.verse_no_words.get()
        # Lecture des choix de traduction dans le thread principal (Tkinter
        # interdit l'accès aux variables Tk depuis un autre thread).
        trans_enabled = {lang: var.get() for lang, var in self.verse_trans.items()}
        out = self.tab_verse._output
        self._disable_buttons()
        self.status.configure(text=f"Analyse : {reference}…")

        def worker():
            try:
                analysis = analyze_verse_by_reference(self.api, reference)
                if fmt == "json":
                    result = format_json(analysis)
                elif fmt == "summary":
                    summary = format_summary(analysis)
                    lines = ["=== Règles détectées (synthèse) ==="]
                    for level in ("clause", "phrase", "word"):
                        lines.append(f"\n[{level}]")
                        for r in summary[level]:
                            lines.append(f"  - {r}")
                    result = "\n".join(lines)
                else:
                    result = format_text(analysis, verbose_words=not no_words)
                header = self._build_translation_header(
                    analysis, fr, chap, verse, trans_enabled)
                self._work_queue.put(("verse_done", header + result))
            except ValueError as exc:
                self._work_queue.put(("verse_done", f"Erreur : {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _run_mishnah(self, tractate, fr, chapter, mishnah):
        """Affiche une mishna (texte hébreu + traduction + analyse).

        Le texte vient de l'API Sefaria : hébreu « Torat Emet 357 » (couvre
        les 63 traités) et français « Le Talmud de Jérusalem, traduit par
        Moise Schwab, 1878-1890 » (38 traités seulement — sinon seul
        l'hébreu est affiché). L'analyse grammaticale (case à cocher « Analyse
        grammaticale (mishna) ») passe le texte hébreu au moteur de phrase
        BHSA : indicative, car la BHSA ne couvre que le vocabulaire biblique.
        """
        out = self.tab_verse._output
        self._disable_buttons()
        reference = f"{fr} {chapter}:{mishnah}"
        self.status.configure(text=f"Chargement Mishna : {reference}…")

        analyze = self.mishna_analyze.get() and self.api is not None
        fmt = "json" if self.verse_format.get() == "json" else "text"

        def worker():
            blocks = []
            he = fetch_mishnah_mishnayot(tractate, chapter, "hebrew")
            if he and 1 <= mishnah <= len(he):
                hebrew_text = he[mishnah - 1]
                blocks.append(f"Hébreu (Torat Emet) — {reference}\n{hebrew_text}")
                if analyze:
                    analysis = analyze_mishnah_text(self.api.F, self.api.L,
                                                     hebrew_text)
                    blocks.append(mishnah_analysis_block(analysis, fmt))
            else:
                blocks.append(f"Hébreu (Torat Emet) — {reference}\n"
                              "(texte indisponible : API Sefaria injoignable "
                              "ou référence absente)")
            if tractate in SCHWAB_TRACTATES:
                fr_texts = fetch_mishnah_mishnayot(tractate, chapter, "french")
                if fr_texts and 1 <= mishnah <= len(fr_texts):
                    blocks.append(
                        f"Traduction (Moïse Schwab, Talmud de Jérusalem) — "
                        f"{reference}\n{fr_texts[mishnah - 1]}")
                else:
                    blocks.append(
                        f"Traduction (Moïse Schwab, Talmud de Jérusalem) — "
                        f"{reference}\n(mishna absente de la traduction)")
            else:
                blocks.append(
                    f"Traduction française — {reference}\n"
                    "(traité non couvert par la traduction de Schwab ; "
                    "seul le texte hébreu est disponible)"
                )
            self._work_queue.put(("verse_done", "\n\n".join(blocks)))

        threading.Thread(target=worker, daemon=True).start()

    def _run_word(self):
        if self.api is None:
            return
        form = self.word_entry.get_logical().strip()
        if not form:
            messagebox.showwarning("Mot", "Saisissez un mot hébreu.")
            return
        fmt = self.word_format.get()
        F, L = self.api.F, self.api.L
        out = self.tab_word._output
        self._disable_buttons()
        self.status.configure(text=f"Analyse du mot « {form} »…")

        def worker():
            analysis = analyze_word(F, L, form)
            if fmt == "json":
                result = format_word_json(analysis)
            else:
                result = format_word(analysis)
            self._work_queue.put(("word_done", result))

        threading.Thread(target=worker, daemon=True).start()

    def _run_phrase(self):
        if self.api is None:
            return
        phrase = self.phrase_text.get_logical().strip()
        if not phrase:
            messagebox.showwarning("Phrase", "Saisissez une phrase hébreu.")
            return
        fmt = self.phrase_format.get()
        F, L = self.api.F, self.api.L
        out = self.tab_phrase._output
        self._disable_buttons()
        self.status.configure(text="Analyse de la phrase…")

        def worker():
            analysis = analyze_phrase(F, L, phrase)
            if fmt == "json":
                result = format_phrase_json(analysis)
            else:
                result = format_phrase(analysis)
            self._work_queue.put(("phrase_done", result))

        threading.Thread(target=worker, daemon=True).start()

    # --- Polling ----------------------------------------------------------
    def _poll_queue(self):
        try:
            while True:
                kind, payload = self._work_queue.get_nowait()
                if kind == "loaded":
                    self._on_corpus_loaded(payload)
                elif kind == "error":
                    self._on_corpus_error(payload)
                elif kind == "verse_done":
                    self._set_output(self.tab_verse._output, payload)
                    self.status.configure(text="Prêt.")
                    self._enable_buttons()
                elif kind == "word_done":
                    self._set_output(self.tab_word._output, payload)
                    self.status.configure(text="Prêt.")
                    self._enable_buttons()
                elif kind == "phrase_done":
                    self._set_output(self.tab_phrase._output, payload)
                    self.status.configure(text="Prêt.")
                    self._enable_buttons()
                elif kind == "binyanim_raw":
                    self._show_binyanim_raw(payload)
                elif kind == "binyanim_parsed":
                    self._show_binyanim_parsed(payload)
                elif kind == "binyanim_not_found":
                    self._show_binyanim_not_found(payload)
                elif kind == "audio_ready":
                    self._on_audio_ready(*payload)
                elif kind == "audio_error":
                    self._on_audio_error(payload)
        except queue.Empty:
            pass
        self.root.after(120, self._poll_queue)


def _quit_from_signal(root, signum, frame):
    """Fermeture demandée par Ctrl-C (SIGINT) en ligne de commande.

    La géométrie de la fenêtre principale est sauvegardée avant l'arrêt.
    Le mainloop() de Tk bloque le thread principal dans la boucle
    d'événements Tcl : un SIGINT peut y être délivré au milieu d'un
    callback Tkinter, et l'exception KeyboardInterrupt est alors avalée
    par le rapport d'exception de Tkinter (la boucle continue) — la
    fermeture semble aléatoire. On replane donc l'arrêt via
    after_idle : destroy() s'exécutera dans le thread principal, depuis
    la boucle d'événements, et mainloop() rend la main proprement.
    """
    _save_all_preferences(root)
    try:
        root.after_idle(root.destroy)
    except tk.TclError:
        pass


def _report_callback_exception(self, exc, val, tb):
    """Gestionnaire d'exception de callback : une KeyboardInterrupt qui
    s'échappe d'un callback Tkinter doit fermer l'application, pas être
    simplement imprimée (comportement par défaut de Tkinter) — sinon le
    Ctrl-C ne ferme pas systématiquement l'application."""
    if isinstance(val, KeyboardInterrupt):
        raise SystemExit(130)
    # Comportement par défaut : trace complète sur stderr.
    import traceback
    print("Exception in Tkinter callback", file=sys.stderr)
    traceback.print_exception(exc, val, tb)


def _save_all_preferences(root):
    """Sauvegarde toutes les préférences persistées (géométrie de la
    fenêtre, traductions affichées) dans gui.properties.
    """
    updates = {}
    try:
        updates["window.geometry"] = root.geometry()
    except tk.TclError:
        pass
    gui = getattr(root, "_gui", None)
    if gui is not None:
        for lang, var in gui.verse_trans.items():
            updates[f"translation.{lang}"] = "true" if var.get() else "false"
        try:
            speed = float(gui.audio_speed.get())
            if 0.5 <= speed <= 2.0:
                updates["audio.speed"] = f"{speed:g}"
        except ValueError:
            pass
        voice = getattr(gui, "audio_voice", None)
        if voice is not None:
            key = gui._voice_labels.get(voice.get())
            if key is not None:
                updates["audio.voice"] = key
        mishnah = getattr(gui, "binyanim_use_mishnah", None)
        if mishnah is not None:
            updates["binyanim.mishnah"] = ("true" if mishnah.get()
                                           else "false")
        modern = getattr(gui, "binyanim_use_modern", None)
        if modern is not None:
            updates["binyanim.modern"] = ("true" if modern.get()
                                          else "false")
        variants = getattr(gui, "binyanim_use_variants", None)
        if variants is not None:
            updates["binyanim.variants"] = ("true" if variants.get()
                                            else "false")
        references = getattr(gui, "binyanim_use_references", None)
        if references is not None:
            updates["binyanim.references"] = ("true" if references.get()
                                              else "false")
    if updates:
        _save_properties(root, updates)


def _close_from_window(root):
    """Fermeture demandée par le gestionnaire de fenêtres (bouton ✕).
    Sauvegarde la géométrie et les préférences avant la destruction.
    """
    _save_all_preferences(root)
    gui = getattr(root, "_gui", None)
    if gui is not None:
        gui._stop_audio()
    root.destroy()


def _set_app_user_model_id():
    """Déclare un AppUserModelID explicite pour le processus.

    Sans AppUserModelID explicite, la barre des tâches Windows associe
    la fenêtre au programme hôte (``python.exe``) et affiche son icône
    au lieu de celle de la fenêtre. La déclaration d'un identifiant
    propre à l'application fait retomber la barre des tâches sur
    l'icône de la fenêtre elle-même. Sans effet hors Windows ; toute
    erreur est ignorée.
    """
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Surcouf01.analyse_hebreu"
        )
    except (AttributeError, OSError):
        pass

import os
import tempfile

if sys.platform == "win32":
    import win32con
    import win32gui
    import win32ui
from PIL import Image


def getIconFileFromExe(exe):
    large, small = win32gui.ExtractIconEx(exe, 0)
    try:
        if not large and not small:
            return ""
        hicon = large[0] if large else small[0]

        # GetIconInfo -> (fIcon, xHotspot, yHotspot, hbmMask, hbmColor)
        _, _, _, hbm_mask, hbm_color = win32gui.GetIconInfo(hicon)
        image = None
        try:
            if hbm_color:
                bmp = win32ui.CreateBitmapFromHandle(hbm_color)
                try:
                    try:
                        width, height = bmp.GetSize()
                    except Exception:
                        info = {k.lower(): v for k, v in bmp.GetInfo().items()}
                        width = info.get("width", 0)
                        height = info.get("height", 0)
                    # BITMAP de l'icône : hauteur = pixels, le masque est traité séparément
                    height = abs(height)
                    bits = bmp.GetBitmapBits(False)
                    if not isinstance(bits, bytes):
                        bits = bytes((b & 0xFF) for b in bits)
                    if width and height and len(bits) == width * height * 4:
                        image = Image.frombuffer(
                            "RGBA", (width, height), bits, "raw", "BGRA", 0, 1
                        ).transpose(Image.FLIP_TOP_BOTTOM)
                finally:
                    win32gui.DeleteObject(hbmp if False else hbm_color)
        
            if image is None:
                # Icône monochrome : dessiner dans un bitmap 32 bits
                width = height = 32
                hdc = win32gui.GetDC(0)
                memdc = hbmp = None
                old = None
                try:
                    memdc = win32gui.CreateCompatibleDC(hdc)
                    hbmp = win32gui.CreateCompatibleBitmap(hdc, width, height)
                    old = win32gui.SelectObject(memdc, hbmp)
                    win32gui.PatBlt(memdc, 0, 0, width, height, win32con.BLACKNESS)
                    win32gui.DrawIconEx(memdc, 0, 0, hicon, width, height, 0, None, 3)  # DI_NORMAL
                    bmp = win32ui.CreateBitmapFromHandle(hbmp)
                    bits = bmp.GetBitmapBits(False)
                    if not isinstance(bits, bytes):
                        bits = bytes((b & 0xFF) for b in bits)
                    image = Image.frombuffer(
                        "RGBA", (width, height), bits, "raw", "BGRA", 0, 1
                    ).transpose(Image.FLIP_TOP_BOTTOM)
                finally:
                    if old:
                        win32gui.SelectObject(memdc, old)
                    if hbmp:
                        win32gui.DeleteObject(hbmp)
                    if memdc:
                        win32gui.DeleteDC(memdc)
                    win32gui.ReleaseDC(0, hdc)
        finally:
            win32gui.DeleteObject(hbm_mask)

        if image is None:
            return ""

        fd, ico_path = tempfile.mkstemp(suffix=".ico")
        os.close(fd)
        image.save(ico_path, format="ICO")
        return ico_path
    finally:
        for h in large + small:
            win32gui.DestroyIcon(h)
            
def _apply_window_icon(root):
    """Applique l'icône du projet comme icône de la fenêtre principale.

    Sur Windows, ``iconphoto`` avec un PNG est sans effet sur la barre de
    titre et la barre des tâches avec la plupart des versions de Tk :
    on utilise ``iconbitmap`` avec ``icone.ico`` (multi-résolutions),
    avec une marge blanche sur les petites tailles pour rester lisible
    dans la barre des tâches. Sur les autres plateformes, ``iconphoto``
    avec ``icone.png`` si présent (repli silencieux sinon).

    En mode exécutable PyInstaller (gelé), l'icône est d'abord chargée
    **depuis l'exécutable lui-même** : le spec l'embarque comme ressource
    Windows (RT_GROUP_ICON), et Tk sait lire l'icône d'un .exe via
    ``iconbitmap(sys.executable)``. La fenêtre affiche donc toujours
    l'icône du build, même si le répertoire courant ou les fichiers
    externes sont inaccessibles — c'est aussi ce qui alimente la barre
    des tâches (avec l'AppUserModelID explicite, cf. plus haut).

    Le chemin des icônes externes est ensuite résolu relativement à ce
    script, aux ressources embarquées et à l'exécutable. En cas
    d'absence ou d'erreur (fichier illisible, Tk indisponible), on
    poursuit silencieusement avec l'icône par défaut.
    """
    if sys.platform == "win32":
        exe = sys.executable
        icon_temppath = getIconFileFromExe(exe)
        root.iconbitmap(icon_temppath)
    try:
        here = _resource_dir()
        if sys.platform == "win32":
             ico_path = os.path.join(here, "icone.ico")
             if os.path.isfile(ico_path):
                 root.iconbitmap(ico_path)
                 return
    except (tk.TclError, OSError):
         pass

def _enable_console(argv):
    """Option --console : attache une console au processus pour rendre
    visibles stdout/stderr (traces, erreurs).

    Utile pour l'exécutable GUI (build PyInstaller console=False) : le
    mode fenêtré n'attache aucune console, sys.stdout/stderr valent None
    et les erreurs sont invisibles. Avec --console, une console est
    allouée (AllocConsole sous Windows) et les flux sont rebranchés
    dessus ; ailleurs l'option est sans effet (les flux existent déjà).

    Renvoie True si les flux sont utilisables après l'appel."""
    if "--console" not in argv:
        return False
    if sys.stdout is not None and sys.stderr is not None:
        return True
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.AllocConsole()
        except OSError:
            pass
        try:
            # Réouverture des flux sur la console allouée ; en mode
            # fenêtré, les handles d'origine sont invalides, on passe
            # donc par CONOUT$ / CONIN$ plutôt que par les fds 0/1/2.
            conout = os.open("CONOUT$", os.O_WRONLY)
            os.dup2(conout, 1)
            os.dup2(conout, 2)
            if conout > 2:
                os.close(conout)
            conin = os.open("CONIN$", os.O_RDONLY)
            os.dup2(conin, 0)
            if conin > 2:
                os.close(conin)
        except OSError:
            pass
    # Rebrancher sys.stdout/stderr sur les fds fraîchement valides :
    # dans l'exécutable fenêtré ils valent None à cet endroit.
    try:
        if sys.stdout is None:
            sys.stdout = open(1, "w", encoding="utf-8",
                              errors="replace", closefd=False)
        if sys.stderr is None:
            sys.stderr = open(2, "w", encoding="utf-8",
                              errors="replace", closefd=False)
    except OSError:
        pass
    return sys.stdout is not None and sys.stderr is not None


def main():
    _enable_console(sys.argv[1:])
    _set_app_user_model_id()
    root = tk.Tk()
    _set_app_user_model_id()
    _apply_window_icon(root)
    tk.Tk.report_callback_exception = _report_callback_exception
    gui = AnalyseurGUI(root)
    root._gui = gui
    root.protocol("WM_DELETE_WINDOW", lambda: _close_from_window(root))
    signal.signal(signal.SIGINT, lambda s, f: _quit_from_signal(root, s, f))
    try:
        root.mainloop()
    except SystemExit as exc:
        if exc.code == 130:
            root.destroy()
            return 130
        raise
    return 0


if __name__ == "__main__":
    main()
