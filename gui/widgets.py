"""Widgets de texte du GUI.

Extrait de gui_hebreu.py (refactorisation en paquet gui/) :

  - BidiHebrewText : champ de saisie hébreu (stockage visuel,
    édition logique, undo/redo) ;
  - FindMixin + ResultText + ReadmeText : zones de texte avec barre
    de recherche Ctrl-F (cf. FindMixin) ;
  - ScaleTimeTooltip : infobulle du curseur de lecture audio.
"""

import re
import tkinter as tk
from tkinter import ttk, font as tkfont

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

from gui.config import HEBREW_FONT

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


class FindMixin:
    """Barre de recherche flottante commune aux zones de texte
    (Ctrl-F, F3, Maj+F3). Une zone définit ``_compute_find_matches``
    (les indices diffèrent selon que le texte est stocké en ordre
    visuel ou logique) ; tout le reste — ouverture, surlignage,
    navigation, compteur — est géré ici."""

    # --- Recherche Ctrl-F -------------------------------------------------
    def _init_find(self):
        """État de la recherche : à appeler en fin de __init__, après
        la configuration des tags find/find_cur ; « sofit insensible »
        est créée ici (cochée par défaut)."""
        self._find_bar = None
        self._find_entry = None
        self._find_count = None
        self._find_var = tk.StringVar(self)
        self._find_matches = []
        self._find_pos = -1
        self._find_job = None
        self._find_last_query = None
        self._find_anchor = None
        self._find_focus_notifier = getattr(self, "_find_focus_notifier",
                                           None)
        self._find_sofit_var = tk.BooleanVar(self, value=True)

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
            # Le champ est justifié à droite pour l'hébreu (saisie RTL) ;
            # une zone à dominante latine (README) peut le remettre à
            # gauche via l'attribut de classe _find_entry_justify.
            entry = ttk.Entry(bar, textvariable=self._find_var, width=18,
                              font=HEBREW_FONT,
                              justify=getattr(self, "_find_entry_justify",
                                              "right"))
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

    def _on_page_up(self, event=None):
        """Page précédente (PgUp) : défilement d'une page vers le haut."""
        self._scroll_pages(-1)
        return "break"

    def _on_page_down(self, event=None):
        """Page suivante (PgDn) : défilement d'une page vers le bas."""
        self._scroll_pages(1)
        return "break"

    def _scroll_pages(self, delta):
        """Fait défiler la vue de delta pages (hauteur visible moins
        une ligne, comme les visualiseurs usuels)."""
        try:
            page = max(1, self._visible_lines() - 1)
            self.yview_scroll(delta * page, "units")
            self._clamp_insert_to_view()
        except tk.TclError:
            pass

    def _visible_lines(self):
        """Nombre de lignes visibles dans la fenêtre du widget."""
        try:
            first = self.index("@0,0")
            last = self.index("@0,%d" % max(0, self.winfo_height() - 1))
            fa = int(first.split(".")[0])
            la = int(last.split(".")[0])
            return max(1, la - fa + 1)
        except tk.TclError:
            return 1

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


class ResultText(FindMixin, tk.Text):
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
        # Recherche Ctrl-F dans la zone (cf. FindMixin) : occurrences
        # surlignées, la courante dans une teinte plus soutenue.
        self.tag_configure("find", background="#ffe08a")
        self.tag_configure("find_cur", background="#ffb74d")
        # La sélection native doit rester visible sur le surlignage.
        self.tag_raise("sel")
        self.bind("<Control-f>", self._on_find)
        self.bind("<Control-F>", self._on_find)
        self.bind("<F3>", self._on_f3)
        self.bind("<Shift-F3>", self._on_f3_prev)
        self.bind("<Up>", self._on_arrow_up)
        self.bind("<Down>", self._on_arrow_down)
        self.bind("<Prior>", self._on_page_up)
        self.bind("<Next>", self._on_page_down)
        self._init_find()

    def _compute_find_matches(self, query):
        """Occurrences ``[(ligne, debut, fin), …]`` en indices du texte
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


class ReadmeText(FindMixin, tk.Text):
    """Zone de texte de l'onglet README, en ordre logique (pas de
    conversion bidi : le rendu maison du markdown reste tel quel).

    Bénéficie de la barre de recherche FindMixin (Ctrl-F, F3, etc.) ;
    les occurrences sont calculées sur le texte stocké : recherche
    littérale insensible à la casse pour le texte latin, squelette
    consonantique (sans nikkud ni teamim, « sofit insensible ») pour
    les requêtes hébraïques — les indices de cluster s'appliquent
    directement puisque l'ordre du widget est l'ordre de lecture.
    """

    # Champ de recherche aligné à gauche : dominante latine (doc).
    _find_entry_justify = "left"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag_configure("find", background="#ffe08a")
        self.tag_configure("find_cur", background="#ffb74d")
        # La sélection native doit rester visible sur le surlignage.
        self.tag_raise("sel")
        self._init_find()
        self.bind("<Control-f>", self._on_find)
        self.bind("<Control-F>", self._on_find)
        self.bind("<F3>", self._on_f3)
        self.bind("<Shift-F3>", self._on_f3_prev)
        # Défilement clavier comme dans les zones de résultat (mode
        # binyan) : flèches = une ligne, PgUp/PgDn = une page, sans
        # déplacer la marque d'insertion.
        self.bind("<Up>", self._on_arrow_up)
        self.bind("<Down>", self._on_arrow_down)
        self.bind("<Prior>", self._on_page_up)
        self.bind("<Next>", self._on_page_down)

    def _compute_find_matches(self, query):
        """Occurrences ``[(ligne, début, fin), …]`` en indices du texte
        stocké (ordre logique), directement surlignables."""
        n_lines = int(self.index("end - 1c").split(".")[0])
        matches = []
        if has_hebrew_letters(query):
            skeleton = normalize_query(query)
            if not skeleton:
                return []
            sofit_insensitive = bool(self._find_sofit_var.get())
            if sofit_insensitive:
                skeleton = fold_sofit(skeleton)
            for line_no in range(1, n_lines + 1):
                line = self.get(f"{line_no}.0", f"{line_no}.0 lineend")
                if not line:
                    continue
                # Une entrée par cluster portant des lettres hébraïques,
                # avec ses indices de colonne dans la ligne stockée.
                skel = []
                col = 0
                for cl in clusters(line):
                    letters = consonant_skeleton(cl)
                    if sofit_insensitive:
                        letters = fold_sofit(letters)
                    if letters:
                        skel.append((letters, col, col + len(cl)))
                    col += len(cl)
                if not skel:
                    continue
                hay = "".join(s[0] for s in skel)
                begin = 0
                while True:
                    j = hay.find(skeleton, begin)
                    if j < 0:
                        break
                    covered = skel[j:j + len(skeleton)]
                    matches.append((line_no,
                                     min(s for _l, s, _e in covered),
                                     max(e for _l, _s, e in covered)))
                    begin = j + 1
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
