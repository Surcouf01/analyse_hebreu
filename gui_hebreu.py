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
import webbrowser
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
    consonant_skeleton,
    fold_sofit,
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


# Refactorisation en paquet gui/ : widgets, clavier, configuration,
# onglet README et lecteur audio sont extraits en modules ; ce fichier
# reste le point d'entrée (spec PyInstaller, scripts/check_imports.py).
from gui.config import (
    TRANSLATIONS,
    DEFAULT_GEOMETRY,
    PRINT_PER_SHEET_DEFAULT,
    PRINT_FONT_SCALE_DEFAULT,
    _PROPS,
    _saved_print_settings,
    _saved_geometry,
    _save_properties,
    HEBREW_FONT,
    HEBREW_FONT_MONO,
    KEYBOARD_FONT,
    KEYBOARD_FONT_VOWELS,
    KEYBOARD_FONT_CONSONANTS,
    BINYAN_TAB_FONT,
    CORPUS_BIBLE,
    CORPUS_MISHNA,
    _resource_dir,
    _app_dir,
    _github_slug,
    _font,
)
from gui.keyboard import (
    NIKKUD_LABELS,
    NIKKUD_ROWS,
    BinyanimNotebook,
    HebrewKeyboard,
)
from gui.widgets import (
    BidiHebrewText,
    FindMixin,
    ResultText,
    ReadmeText,
    ScaleTimeTooltip,
)
from gui.readme import ReadmeTabMixin
from gui.audio import AudioMixin
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
class AnalyseurGUI(ReadmeTabMixin, AudioMixin):
    """Fenêtre principale de l'analyseur grammatical."""

    def __init__(self, root):
        self.root = root
        self.api = None
        self.translations = {}  # {lang: index} traductions chargées
        self._work_queue = queue.Queue()
        self._target_widget = None  # widget actuellement ciblé par le clavier
        self._readme_text = None  # zone README (recherche Ctrl-F)
        # Historique de navigation des liens du README (cf. onglet).
        self._readme_nav_history = []
        self._readme_nav_pos = -1
        self._readme_nav_back = None
        self._readme_nav_fwd = None

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
        du sous-onglet affiché (Verbe, binyan ou Sortie complète).
        README : la zone de rendu du README (recherche Ctrl-F).
        """
        idx = self.notebook.select()
        if not idx:
            return None
        tab = self.notebook.tab(idx, "text")
        if tab in ("Livre", "Mot", "Phrase"):
            return getattr(self.notebook.nametowidget(idx), "_output", None)
        if tab == "README":
            w = getattr(self, "_readme_text", None)
            if w is not None:
                return w
            for child in self.notebook.nametowidget(idx).winfo_children():
                for sub in child.winfo_children():
                    if isinstance(sub, ReadmeText):
                        return sub
            return None
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
