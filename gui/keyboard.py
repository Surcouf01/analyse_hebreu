"""Clavier hébreu virtuel et bloc d'onglets Binyanim.

Extrait de gui_hebreu.py (refactorisation en paquet gui/) : la
disposition du clavier (rangées de consonnes, points-voyelles),
le widget HebrewKeyboard, et le notebook à onglets BinyanimNotebook.
"""

import tkinter as tk
from tkinter import ttk, font as tkfont

from gui.widgets import BidiHebrewText
from gui.config import (
    KEYBOARD_FONT,
    KEYBOARD_FONT_CONSONANTS,
    KEYBOARD_FONT_VOWELS,
    BINYAN_TAB_FONT,
)

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
