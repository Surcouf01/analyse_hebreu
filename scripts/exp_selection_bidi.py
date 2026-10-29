#!/usr/bin/env python3
"""Expérimentation isolée : le redessin d'une sélection taguée brouille-t-il
le texte hébreu selon le mode de stockage ?

Contexte (PR « sélection dansante ») : le GUI stocke l'ordre VISUEL avec un
LRM devant chaque cluster RTL (bidi_display.to_visual). Les bornes sel sont
correctes (bbox conformes), mais les PIXELS peints dans la zone sélectionnée
sont brouillés : consonnes amputées, nikkud orphelines, couleurs mélangées.
Hypothèse : quand Tk redessine la sous-séquence portant le tag sel, le moteur
bidi (Uniscribe) la ré-résout ISOLÉMENT ; les LRMs forts LTR au milieu des
lettre RTL forcent un réordonnancement des runs → glyphes garbled.

Ce script affiche la même ligne de Genèse 38:1 dans 4 widgets Text :

  A. visuel + LRM (le stockage actuel du GUI, to_visual)
  B. visuel SANS LRM (ordre inversé, marques retirées)
  C. logique pur (ordre du texte BHSA, Tk fait le bidi nativement)
  D. logique + RLM en tête de ligne (base RTL explicite)

Sur chaque ligne, le mot וַיֵּרֶד est sélectionné par tag_add après 300 ms
(sans interaction souris : pas de StableSelection, bornes calculées à partir
du stockage de chaque widget). Une capture d'écran de la fenêtre est sauvée,
et les bbox de la zone sélectionnée sont imprimées.

PROTOCOLE (sous Windows, depuis une console) :

    python scripts/exp selection_bidi.py

1. Laisser la fenêtre s'afficher et la sélection se poser (300 ms).
2. Capturer la sortie console (bbox + chemins des captures).
3. Regarder la capture PNG : pour chaque ligne A-D, le mot sélectionné
   (surligné bleu) est-il lisible et complet ? ses nikkud sont-ils visibles ?
   la sélection recouvre-t-elle exactement le mot ?

Attendu si l'hypothèse est vraie : A brouillé (comme dans le GUI), B peut-être
correct (pas de LRM pour casser le re-résolution), C et D corrects (le bidi
natif re-résout les sous-runs de façon cohérente).
"""

import os
import sys
import tempfile
import unicodedata

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    print("tkinter indisponible — ce script doit tourner sous Windows/Tk.")
    sys.exit(1)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bidi_display import to_visual  # noqa: E402

LRM = "\u200E"
RLM = "\u200F"

# Genèse 38:1 — texte BHSA réel (analyse déjà faite ; collé tel quel pour
# que le script soit autonome, sans charger la base).
VERSE = ("וַֽיְהִי֙ בְּעֵ֣ת הַהִ֔וא וַיֵּ֥רֶד יְהוּדָ֖ה מֵאֵ֣ת "
         "אֶחָ֑יו וַיֵּ֛ט עַד־אִ֥ישׁ עֲדֻלָּמִ֖י וּשְׁמֹ֥ו חִירָֽה׃")
WORD = "וַיֵּרֶד"  # sans teamim pour le find() ; teamim dans le verset


def no_marks(text):
    """Retire les marques bidi (LRM/RLM) d'un texte."""
    out = []
    for ch in text:
        if unicodedata.category(ch) == "Cf":
            continue
        out.append(ch)
    return "".join(out)


def reverse_clusters(text):
    """Inverse l'ordre des clusters (base+marques) — « visuel » sans LRM."""
    clusters = []
    for ch in text:
        if (clusters and (unicodedata.combining(ch) > 0
                          or unicodedata.category(ch) in ("Mn", "Me"))):
            clusters[-1] += ch
        else:
            clusters.append(ch)
    return "".join(reversed(clusters))


def select_word(widget, storage_kind):
    """Sélectionne le mot וַיֵּרֶד par tag_add, bornes calculées sur le
    stockage du widget. Retourne (first, last) ou None."""
    content = widget.get("1.0", "end - 1 c")
    if storage_kind in ("visual_lrm", "visual_plain"):
        # stockage visuel : le mot apparaît inversé (clusters RTL retournés)
        target = reverse_clusters(no_marks(WORD))
    else:
        target = WORD
    # recherche tolérante : trouver la position de la ד du mot dans le
    # stockage, puis étendre de l'espace précédent à l'espace suivant.
    d_positions = [i for i, ch in enumerate(content) if ch == "ד"]
    for d in d_positions:
        # bornes du mot autour de d (espaces)
        start = content.rfind(" ", 0, d)
        end = content.find(" ", d)
        if start < 0:
            start = -1
        if end < 0:
            end = len(content)
        seg = content[start + 1:end]
        # le mot fait 4 bases ; vérifier les bases attendues
        bases = [c for c in seg if "א" <= c <= "ת"]
        if storage_kind in ("visual_lrm", "visual_plain"):
            expect = ["ד", "ר", "י", "ו"]
        else:
            expect = ["ו", "י", "ר", "ד"]
        bases_clean = [c for c in bases
                       if unicodedata.category(c) != "Cf"]
        if bases_clean == expect:
            first = f"1.{start + 1}"
            last = f"1.{end}"
            widget.tag_add("sel", first, last)
            # Rendre la sélection VISIBLE : Tk ne peint le fond du tag sel
            # que lorsque le widget possède la sélection primaire (acquise
            # normalement par la souris). Sans focus ni ownership, tag_add
            # pose les bornes mais le surlignage n'est pas dessiné — les
            # premiers essais ont capturé des widgets sans aucune bande
            # bleue. focus + selection_own déclenchent le rendu SANS souris,
            # en gardant le test isolé de StableSelection.
            widget.focus_set()
            widget.selection_own()
            return first, last
    return None


def dump_bbox(widget, first, last, label):
    print(f"\n--- {label} : sel {first}..{last} ---")
    f = int(first.split(".")[1])
    l = int(last.split(".")[1])
    for i in range(f, l):
        ch = widget.get(f"1.{i}")
        try:
            bb = widget.bbox(f"1.{i}")
            print(f"  idx {i}: {ch!r} bbox={bb}")
        except Exception:
            print(f"  idx {i}: {ch!r} bbox=?")


def main():
    root = tk.Tk()
    root.title("exp sélection bidi — 4 stockages")
    root.geometry("1100x560")

    font = ("Taamey Frank CLM", 24)
    try:
        root.tk.call("font", "actual", font)
    except Exception:
        font = ("DejaVu Sans", 24)
        print(f"police demandée indisponible, repli sur {font}")

    cases = [
        ("A. visuel + LRM (GUI actuel)", to_visual(VERSE), "visual_lrm"),
        ("B. visuel sans LRM", no_marks(to_visual(VERSE)), "visual_plain"),
        ("C. logique pur", VERSE, "logical"),
        ("D. logique + RLM tête", RLM + VERSE, "logical"),
    ]

    widgets = []
    for title, text, kind in cases:
        frame = ttk.LabelFrame(root, text=title)
        frame.pack(fill="x", padx=8, pady=6)
        t = tk.Text(frame, font=font, height=1, width=120, wrap="none")
        t.pack(fill="x")
        t.insert("1.0", text)
        widgets.append((t, kind, title))

    def apply_sel():
        print("=== bbox après sélection ===")
        for t, kind, title in widgets:
            res = select_word(t, kind)
            if res:
                dump_bbox(t, res[0], res[1], title)
            else:
                print(f"\n--- {title} : MOT INTROUVABLE dans ce stockage ---")
        root.update_idletasks()
        root.after(300, capture)

    def capture():
        # Forcer la fenêtre au premier plan AVANT la capture : les essais
        # précédents ont capturé la fenêtre de console derrière. Le topmost
        # doit être posé puis laissée au gestionnaire de fenêtres le temps
        # d'un cycle complet (update + délai), sinon le grab repart avant
        # que la pile Z ait changé.
        try:
            root.deiconify()
            root.lift()
            root.attributes("-topmost", True)
            root.update_idletasks()
            root.update()
            root.after(600, _grab)
        except Exception:
            _grab()

    def _grab():
        # Second cycle : re-vérifier le premier plan juste avant le grab.
        try:
            root.deiconify()
            root.lift()
            root.update()
        except Exception:
            pass
        try:
            from PIL import ImageGrab
            root.update()
            x = root.winfo_rootx()
            y = root.winfo_rooty()
            w = root.winfo_width()
            h = root.winfo_height()
            img = ImageGrab.grab((x, y, x + w, y + h))
            # Garde-fou : si la zone capturée est (presque) toute noire ou
            # vide, c'est que la fenêtre n'était pas au premier plan — le
            # dire au lieu de sauver une capture inutilisable.
            from PIL import ImageStat
            stat = ImageStat.Stat(img.convert("L"))
            if stat.mean[0] < 8:
                print("\nATTENTION : la capture semble noire — la fenêtre "
                      "n'était probablement pas au premier plan. "
                      "Réessayer en cliquant sur la fenêtre Tk pendant les "
                      "2 premières secondes.")
            path = os.path.join(tempfile.gettempdir(),
                                "exp_selection_bidi.png")
            img.save(path)
            print(f"\ncapture d'écran (fenêtre complète) : {path}")
            # Une capture PAR widget : découpe selon la géométrie réelle de
            # chaque Text, pour une lecture sans ambiguïté.
            for i, (t, kind, title) in enumerate(widgets):
                wx = t.winfo_rootx() - x
                wy = t.winfo_rooty() - y
                ww = t.winfo_width()
                wh = t.winfo_height()
                crop = img.crop((max(0, wx - 2), max(0, wy - 2),
                                 min(img.width, wx + ww + 2),
                                 min(img.height, wy + wh + 2)))
                p = os.path.join(tempfile.gettempdir(),
                                 f"exp_selection_bidi_{chr(65 + i)}.png")
                crop.save(p)
                print(f"capture {title} : {p}")
            root.attributes("-topmost", False)
        except Exception as exc:
            print(f"capture impossible : {exc}")
        print("\nProtocole : regarder les captures A-D — pour chaque ligne, "
              "le mot sélectionné est-il lisible, complet, avec ses "
              "nikkud ? La sélection couvre-t-elle exactement le mot ?")

    print("Dans 3 secondes, la sélection se pose et la capture est prise "
          "automatiquement — NE PAS cliquer ailleurs, laisser la fenêtre "
          "au premier plan.")
    root.after(3000, apply_sel)
    root.mainloop()


if __name__ == "__main__":
    main()
