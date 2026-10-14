#!/usr/bin/env python3
"""Sélection à la souris stable sur l'hébreu vocalisé (RTL) dans tk.Text.

Tk tranche la sélection par défaut (tk::TextClosestGap) avec la
demi-largeur du caractère sous le curseur ; sur un caractère sans largeur
propre (nikkud, teamim, marques bidi), la borne tombe à l'intérieur d'un
cluster de glyphes (base + ses points), là où plusieurs indices
s'affichent au même endroit — sur un rendu bidi (Windows), l'index oscille
d'un pixel à l'autre et la sélection « danse ». La classe
:class:`StableSelection` arrime chaque borne au bord du cluster, position
stable visuellement, et remplace la sélection par défaut de Tk pour un
widget ``tk.Text`` donné.
"""


import unicodedata
import tkinter as tk


RLM = "\u200F"
RLE = "\u202B"
PDF = "\u202C"


class StableSelection:
    """Sélection à la souris stable sur l'hébreu vocalisé.

    Remplace la sélection par défaut de Tk (tk::TextButton1 /
    tk::TextSelectTo) pour ce widget : chaque borne est arrimée aux bords
    de clusters de glyphes (base + nikkud + teamim). Sans cela, Tk
    tranche à la demi-largeur du caractère sous le curseur ; sur un
    nikkud ou un teamim (largeur nulle) la borne tombe au milieu d'un
    cluster, là où plusieurs indices s'affichent au même endroit — et
    sur un rendu bidi (Windows), chaque mouvement de souris fait
    osciller l'index entre ces positions : la sélection « danse ».

    Les handlers sont liés au widget (avant la classe Text dans les
    bindtags) et retournent "break" : Tk n'applique pas sa sélection par
    défaut. Double-clic et triple-clic sélectionnent mot et ligne
    (bornes de mots/lignes de Tk, arrimées aux clusters), le clic simple
    place le curseur, Maj+clic étend la sélection.
    """

    # Caractères sans largeur propre (combining) : nikoud, teamim, marques
    # bidi. La sélection par défaut de Tk (tk::TextClosestGap) tranche avec la
    # demi-largeur du caractère sous le curseur ; sur ces caractères de
    # largeur nulle, la borne tombe à l'intérieur d'un cluster (base + ses
    # points), là où plusieurs indices s'affichent au même endroit — sur un
    # rendu bidi (Windows), l'index oscille d'un pixel à l'autre et la
    # sélection « danse ». On ramène donc les bornes de sélection au bord du
    # cluster, position stable visuellement.
    _MARKS = frozenset(
        [chr(c) for c in range(0x0591, 0x05BD)]       # teamim + nikoud
        + [chr(0x05BD), chr(0x05BF), chr(0x05C0)]
        + [chr(c) for c in range(0x05C1, 0x05C8)]     # shin/sin, qamats qatan…
        + [chr(c) for c in range(0x200E, 0x200F)]      # LRM, RLM
        + [chr(c) for c in range(0x202A, 0x202F)]      # embeddings bidi (RLE, PDF…)
    )

    def __init__(self, text_widget):
        self.widget = text_widget
        self.anchor = None
        w = text_widget
        if getattr(w, "_stable_sel_bound", False):
            return
        w._stable_sel_bound = True
        w.bind("<Button-1>", self._press)
        w.bind("<B1-Motion>", self._drag)
        w.bind("<ButtonRelease-1>", self._release)
        w.bind("<Double-Button-1>", self._double_click)
        w.bind("<Triple-Button-1>", self._triple_click)
        w.bind("<Shift-Button-1>", self._shift_press)
        w.bind("<Shift-B1-Motion>", self._drag)

    # --- Marques et clusters ---------------------------------------------

    @classmethod
    def _is_mark(cls, ch):
        """Vrai pour un caractère sans largeur propre (marque combinante,
        teamim, nikkud, marque bidi)."""
        return len(ch) == 1 and (ch in cls._MARKS
                                or unicodedata.combining(ch) != 0)

    def _cluster_start(self, index):
        """Index du début du cluster de glyphes contenant ``index``.

        Un cluster = un caractère de base + ses marques combinantes (nikkud,
        teamim, marques bidi). Ramener une borne de sélection au début du
        cluster la rend positionnellement stable (les marques ont une
        largeur nulle : tous les indices du cluster occupent le même espace
        visuel).
        """
        w = self.widget
        idx = w.index(index)
        while self._is_mark(w.get(idx)):
            prev = w.index(idx + " - 1 c")
            if prev == idx:
                break
            idx = prev
        return idx

    def _cluster_end(self, index):
        """Index de fin (exclusive) du cluster contenant ``index``."""
        w = self.widget
        idx = self._cluster_start(index)
        last = w.index("end - 1 c")
        while w.compare(idx, "<=", last):
            nxt = w.index(idx + " + 1 c")
            if not self._is_mark(w.get(nxt)):
                return nxt
            idx = nxt
        return w.index("end")

    def _nearest_cluster_index(self, x, y):
        """Index de bord de cluster le plus proche du pixel (x, y).

        Tk trancherait avec la demi-largeur du caractère sous le pixel —
        quand ce caractère est un nikkud (largeur nulle), la borne tombe au
        milieu d'un cluster, position instable. On prend l'index brut puis on
        l'arrime au bord de cluster (début du cluster pointé, ou fin du
        précédent selon la moitié de la largeur du caractère de base).
        """
        w = self.widget
        raw = w.index(f"@{x},{y}")
        cstart = self._cluster_start(raw)
        # Cluster de marques sans base (ex. RLE en début de ligne) : le
        # rattacher au cluster suivant, visible lui.
        while self._is_mark(w.get(cstart)):
            nxt = self._cluster_end(cstart)
            if nxt == cstart:
                break
            cstart = nxt
        bb = w.bbox(cstart)
        if bb and x > bb[0] + bb[2] / 2:
            return self._cluster_end(cstart)
        return cstart

    # --- Application de la sélection --------------------------------------

    def _sel_apply(self, first, last):
        w = self.widget
        w.tag_remove("sel", "1.0", "end")
        if w.compare(first, "<", last):
            w.tag_add("sel", first, last)

    # --- Handlers de souris ------------------------------------------------

    def _press(self, event):
        self.anchor = self._nearest_cluster_index(event.x, event.y)
        w = self.widget
        w.mark_set("insert", self.anchor)
        w.tag_remove("sel", "1.0", "end")
        w.focus_set()
        return "break"

    def _drag(self, event):
        w = self.widget
        if self.anchor is None:
            return "break"
        cur = self._nearest_cluster_index(event.x, event.y)
        anchor = self.anchor
        if w.compare(cur, "<=", anchor):
            self._sel_apply(cur, anchor)
        else:
            self._sel_apply(anchor, cur)
        return "break"

    def _release(self, event):
        w = self.widget
        try:
            if w.index("sel.first") == w.index("sel.last"):
                w.tag_remove("sel", "1.0", "end")
        except tk.TclError:
            pass
        self.anchor = None
        return "break"

    def _double_click(self, event):
        # Mot : bornes définies par les espaces (les wordbreaks de Tk
        # traitent chaque nikkud comme un mot isolé), arrimées aux
        # clusters.
        w = self.widget
        pos = self._nearest_cluster_index(event.x, event.y)
        first = pos
        while True:
            prev = w.index(f"{first} - 1 c")
            if prev == first or w.get(prev) == " " or w.get(prev) == "\n":
                break
            first = prev
        last = pos
        while True:
            nxt = w.index(f"{last} + 1 c")
            if nxt == last or w.get(last) == " " or w.get(last) == "\n":
                break
            last = nxt
        first = self._cluster_start(first)
        last = self._cluster_end(last)
        self.anchor = first
        self._sel_apply(first, last)
        w.mark_set("insert", first)
        return "break"

    def _triple_click(self, event):
        w = self.widget
        pos = self._nearest_cluster_index(event.x, event.y)
        first = w.index(f"{pos} linestart")
        last = w.index(f"{pos} lineend")
        self.anchor = first
        self._sel_apply(first, self._cluster_end(last))
        w.mark_set("insert", first)
        return "break"

    def _shift_press(self, event):
        # Étendre la sélection jusqu'à la position cliquée.
        w = self.widget
        anchor = self.anchor
        if anchor is None:
            # Pas de drag en cours : ancre = position courante du curseur.
            anchor = w.index("insert")
            self.anchor = anchor
        cur = self._nearest_cluster_index(event.x, event.y)
        if w.compare(cur, "<=", anchor):
            self._sel_apply(cur, anchor)
        else:
            self._sel_apply(anchor, cur)
        return "break"
