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


import re
import unicodedata
import tkinter as tk


RLM = "\u200F"
RLE = "\u202B"
PDF = "\u202C"
LRE = "\u202A"

# Marques de directionnalité (contrôle bidi) : retirées avant tout
# ré-embarquement pour éviter les embeddings imbriqués (LRE, RLE, PDF,
# LRM, RLM).
_BIDI_MARKS_RE = re.compile(
    "[\u200E\u200F\u202A-\u202E\u2066-\u2069]"
)


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

    # Marques TRAÇANTES : nikkud, teamim, daguesh — sans largeur propre,
    # elles suivent leur lettre de base et forment avec elle un cluster de
    # glyphes. La sélection par défaut de Tk (tk::TextClosestGap) tranche avec
    # la demi-largeur du caractère sous le curseur ; sur ces caractères de
    # largeur nulle, la borne tombe à l'intérieur d'un cluster (base + ses
    # points), là où plusieurs indices s'affichent au même endroit — sur un
    # rendu bidi (Windows), l'index oscille d'un pixel à l'autre et la
    # sélection « danse ». On ramène donc les bornes de sélection au bord du
    # cluster, position stable visuellement.
    _MARKS = frozenset(
        [chr(c) for c in range(0x0591, 0x05BD)]       # teamim + nikoud
        + [chr(0x05BD), chr(0x05BF), chr(0x05C0)]
        + [chr(c) for c in range(0x05C1, 0x05C8)]     # shin/sin, qamats qatan…
    )

    # Marques de TÊTE (LRM devant chaque cluster dans le stockage visuel de
    # bidi_display.to_visual, RLM/embeddings) : elles PRÉCÈDENT leur cluster
    # — les rattacher à la base précédente (comme les traçantes) décalait la
    # sélection d'un espace vers la gauche et la faisait chevaucher le mot
    # voisin (cf. _cluster_start/_cluster_end).
    _HEAD_MARKS = frozenset(
        [chr(c) for c in range(0x200E, 0x200F)]      # LRM, RLM
        + [chr(c) for c in range(0x202A, 0x202F)]      # embeddings bidi (LRE, RLE, PDF…)
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
        w.bind("<Control-d>", self._dump_selection_geometry)
        w.bind("<Control-D>", self._dump_selection_geometry)

    # --- Construction de chaînes mixtes RTL/LTR --------------------------

    @staticmethod
    def embed_ltr(ltr_text):
        """Enveloppe un segment LTR pour l'insérer dans une ligne à base RTL.

        Dans une ligne à base RTL (hébreu), un segment latin inséré à cru
        garde son ordre interne mais ses délimiteurs — parenthèses,
        crochets, guillemets — sont « miroités » par l'algorithme bidi
        (UAX #9) : « (abc) » s'affiche « )abc( » une fois replacé dans son
        contexte RTL. L'embedding explicite LRE...PDF force le segment
        (contenu ET délimiteurs) en direction LTR : il s'affiche tel
        quel, du premier au dernier caractère.

        :param ltr_text: segment à direction latine (latin, chiffres,
            ponctuation) ; les marques de directionnalité existantes sont
            d'abord retirées pour éviter les embeddings imbriqués.
        :return: le segment enveloppé LRE...PDF, prêt à être inséré dans
            une ligne à base RTL.
        """
        clean = _BIDI_MARKS_RE.sub("", ltr_text)
        return LRE + clean + PDF

    @staticmethod
    def embed_rtl(rtl_text):
        """Enveloppe un segment RTL pour l'insérer dans une ligne à base LTR.

        Pendant de :meth:`embed_ltr` : l'embedding RLE...PDF force le
        segment hébreu (contenu et délimiteurs) en direction RTL, afin
        que ses parenthèses ne soient pas miroitées par le contexte LTR.
        """
        clean = _BIDI_MARKS_RE.sub("", rtl_text)
        return RLE + clean + PDF

    # --- Marques et clusters ---------------------------------------------

    @classmethod
    def _is_mark(cls, ch):
        """Vrai pour une marque TRAÇANTE (nikkud, teamim, daguesh) : sans
        largeur propre, elle suit sa lettre de base. Les marques bidi de
        tête (LRM/RLM, embeddings) n'en sont pas : elles précèdent leur
        cluster (cf. :attr:`_HEAD_MARKS`)."""
        return len(ch) == 1 and (ch in cls._MARKS
                                or unicodedata.combining(ch) != 0)

    @classmethod
    def _is_head_mark(cls, ch):
        """Vrai pour une marque de TÊTE (LRM/RLM, embeddings bidi) : sans
        largeur propre, elle précède son cluster. Dans le stockage visuel
        du widget (bidi_display.to_visual), un LRM précède chaque cluster
        RTL ; les traits de caractère Cf non listés (isolats, ZWJ…) sont
        également de tête."""
        if len(ch) != 1:
            return False
        return (ch in cls._HEAD_MARKS
                or unicodedata.category(ch) == "Cf")

    def _cluster_start(self, index):
        """Index du début du cluster de glyphes contenant ``index``.

        Un cluster = un caractère de base + ses marques traçantes (nikkud,
        teamim), précédé ou non d'une marque de tête (LRM dans le stockage
        visuel, RLM/embeddings). Ramener une borne de sélection à la base
        du cluster la rend positionnellement stable (les marques ont une
        largeur nulle : tous les indices du cluster occupent le même espace
        visuel) ; rattacher la marque de tête à la base PRÉCÉDENTE — comme
        une traçante — décalait la sélection d'un espace vers la gauche
        (elle remontait jusqu'à l'espace inter-mots) : une marque de tête
        appartient au cluster SUIVANT.
        """
        w = self.widget
        idx = w.index(index)
        while self._is_mark(w.get(idx)):
            prev = w.index(idx + " - 1 c")
            if prev == idx:
                break
            idx = prev
        while self._is_head_mark(w.get(idx)):
            nxt = w.index(idx + " + 1 c")
            if nxt == idx:
                break
            idx = nxt
        return idx

    def _cluster_end(self, index):
        """Index de fin (exclusive) du cluster contenant ``index``.

        La fin s'étend sur les marques traçantes du cluster, mais pas sur
        une marque de tête : dans le stockage visuel elle ouvre le cluster
        SUIVANT — l'avaler, puis s'arrêter sur la base d'après, faisait
        chevaucher la sélection au mot voisin.
        """
        w = self.widget
        idx = self._cluster_start(index)
        last = w.index("end - 1 c")
        while w.compare(idx, "<=", last):
            nxt = w.index(idx + " + 1 c")
            if not (self._is_mark(w.get(nxt))
                    and not self._is_head_mark(w.get(nxt))):
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
        # clusters. L'espace adjacent au mot n'est PAS sélectionné : la
        # boucle droite s'arrête avant l'espace (et non sur lui), sinon
        # le surlignage déborde d'un espace du côté du mot — sur une
        # ligne hébraïque en ordre visuel, la sélection paraissait
        # décalée d'un espace par rapport au mot cliqué.
        w = self.widget
        pos = self._nearest_cluster_index(event.x, event.y)
        # Clic sur l'espace inter-mots : Tk renvoie l'index de l'espace. Les
        # boucles de mot ne s'arrêtent pas sur lui (gauche : le caractère
        # AVANT first ; droite : le caractère APRÈS last), donc la sélection
        # avalait le mot de gauche ET le mot de droite — sur une ligne
        # hébraïque en ordre visuel, le surlignage paraissait « décalé » d'un
        # mot. Comme les éditeurs standards, on rabat le clic sur le mot le
        # plus proche de l'espace (celui de droite dans l'ordre de stockage
        # visuel RTL, sauf s'il n'y en a pas).
        while w.get(pos) in (" ", "\n"):
            nxt = w.index(f"{pos} + 1 c")
            if nxt == pos:
                break
            pos = nxt
        first = pos
        while True:
            prev = w.index(f"{first} - 1 c")
            if prev == first or w.get(prev) == " " or w.get(prev) == "\n":
                break
            first = prev
        last = pos
        while True:
            nxt = w.index(f"{last} + 1 c")
            if nxt == last or w.get(nxt) == " " or w.get(nxt) == "\n":
                break
            if nxt.split(".")[0] != last.split(".")[0]:
                break
            last = nxt
        first = self._cluster_start(first)
        last = self._cluster_end(last)
        self.anchor = first
        self._sel_apply(first, last)
        # Caret à la FIN de la sélection, comme les éditeurs standards : à
        # ``first`` (bord gauche du mot dans l'ordre de stockage visuel), le
        # caret clignotait au milieu du verset, à gauche du mot ciblé.
        w.mark_set("insert", last)
        return "break"

    def _triple_click(self, event):
        w = self.widget
        pos = self._nearest_cluster_index(event.x, event.y)
        first = w.index(f"{pos} linestart")
        last = w.index(f"{pos} lineend")
        self.anchor = first
        self._sel_apply(first, self._cluster_end(last))
        w.mark_set("insert", self._cluster_end(last))
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

    # --- Diagnostic rendu/sélection (Ctrl+D) -------------------------------

    def _dump_selection_geometry(self, event):
        """Dump de diagnostic : pour chaque colonne de la ligne cliquée,
        compare la position ÉCRAN (bbox de Tk) à l'index de STOCKAGE.

        Contexte : le widget stocke l'ordre visuel (to_visual) ; la
        sélection est calculée sur ces indices de stockage. Si le moteur
        de rendu (bidi Windows) réordonne les glyphes différemment du
        stockage, le surlignage du tag sel ne recouvre pas les glyphes
        visés — le décalage « sélection dansante ». Ce dump imprime,
        pour CHAQUE colonne : l'index, le caractère (nom Unicode court),
        la bbox écran (x, y, largeur, hauteur), et si la colonne est dans
        la sélection courante. En comparant l'ordre des x écran à l'ordre
        des indices, on voit immédiatement si le rendu ré-inverse les
        runs RTL (x écran décroissants alors que les indices croissent)
        et de combien les bornes sel décalent le surlignage.

        Sortie sur stdout — lancer le GUI depuis une console pour lire.
        """
        w = self.widget
        try:
            pos = w.index(f"@{event.x},{event.y}")
        except Exception:
            pos = w.index("insert")
        line = pos.split(".")[0]
        try:
            sel_first = w.index("sel.first")
            sel_last = w.index("sel.last")
        except Exception:
            sel_first = sel_last = None
        end = w.index(f"{line}.0 lineend + 1 c")
        print(f"\n=== stable_selection diagnostic — ligne {line} ===")
        print(f"sel: {sel_first}..{sel_last}")
        print(f"{'idx':>8}  {'x':>5} {'y':>4} {'w':>3} {'h':>3}  in_sel  char")
        idx = f"{line}.0"
        rows = []
        while w.compare(idx, "<", end):
            ch = w.get(idx)
            col = int(idx.split(".")[1])
            in_sel = ""
            if sel_first is not None:
                in_sel = "SEL" if (w.compare(idx, ">=", sel_first)
                                    and w.compare(idx, "<", sel_last)) else "."
            try:
                bb = w.bbox(idx)
                bx, by, bw, bh = bb
            except Exception:
                bx = by = bw = bh = -1
            name = unicodedata.name(ch, "?")
            if len(name) > 28:
                name = name[:25] + "..."
            rows.append((col, bx, by, bw, bh, in_sel, ch, name))
            nxt = w.index(f"{idx} + 1 c")
            if nxt == idx:
                break
            idx = nxt
        for col, bx, by, bw, bh, in_sel, ch, name in rows:
            print(f"{col:>8}  {bx:>5} {by:>4} {bw:>3} {bh:>3}  {in_sel:<6} "
                  f"{ch!r} {name}")
        # Résumé : monotonie des x écran par rapport aux indices.
        vis = [(c, x) for c, x, _by, _bw, _bh, _s, _ch, _n in rows if x >= 0]
        if len(vis) >= 2:
            inc = sum(1 for (c1, x1), (c2, x2) in zip(vis, vis[1:]) if x2 > x1)
            dec = sum(1 for (c1, x1), (c2, x2) in zip(vis, vis[1:]) if x2 < x1)
            print(f"x écran croissants avec l'index : {inc} ; décroissants : {dec}")
            if dec > inc:
                print("=> le RENDU ré-inverse les indices (bidi natif) : "
                      "les bornes sel (indices de stockage) ne pointent pas "
                      "sur les glyphes affichés.")
            sel_x = [x for c, x, _by, _bw, _bh, s, _ch, _n in rows
                     if s == "SEL" and x >= 0]
            if sel_x:
                print(f"bande écran couverte par sel : x {min(sel_x)}..{max(sel_x)}")
        # Contexte : police réelle, configuration du tag sel, géométrie.
        try:
            font = w.cget("font")
            print(f"font configurée : {font!r}")
            actual = w.tk.call("font", "actual", str(font))
            print(f"font réelle (résolution) : {actual}")
        except Exception as exc:
            print(f"font : indisponible ({exc})")
        for opt in ("-background", "-foreground", "-borderwidth"):
            try:
                print(f"sel {opt} : {w.tag_cget('sel', opt)!r}")
            except Exception:
                pass
        print(f"widget : x={w.winfo_x()} y={w.winfo_y()} "
              f"w={w.winfo_width()} h={w.winfo_height()} "
              f"rootx={w.winfo_rootx()} rooty={w.winfo_rooty()}")
        # Capture d'écran du widget : les PIXELS réellement peints,
        # à comparer aux bbox ci-dessus (layout interne de Tk). Si le
        # surlignage peint ne correspond pas aux bbox, le décalage est
        # dans le dessin du texte sélectionné (segments redessinés sans
        # shaping : voyelles orphelines), pas dans les bornes.
        try:
            import os
            import tempfile
            from PIL import ImageGrab
            rx, ry = w.winfo_rootx(), w.winfo_rooty()
            rw, rh = w.winfo_width(), w.winfo_height()
            img = ImageGrab.grab((rx, ry, rx + rw, ry + rh))
            self._dump_n = getattr(self, "_dump_n", 0) + 1
            has_sel = sel_first is not None
            path = os.path.join(
                tempfile.gettempdir(),
                f"stable_sel_dump_{self._dump_n}"
                f"{'_sel' if has_sel else '_nosel'}.png")
            img.save(path)
            print(f"capture d'écran du widget : {path}")
        except Exception as exc:
            print(f"capture d'écran impossible : {exc}")
        print("=== fin diagnostic ===\n")
        return "break"
