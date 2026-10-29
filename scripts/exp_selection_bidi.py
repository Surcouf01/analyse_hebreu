#!/usr/bin/env python3
"""Expérimentation isolée : le redessin d'une sélection taguée brouille-t-il
le texte hébreu selon le mode de stockage ?

Un seul widget par exécution — Tk ne peint le tag sel que du widget qui
possède la sélection primaire (selection_own), et un seul widget peut la
posséder à la fois : afficher les 4 modes dans une même fenêtre rendait
3 widgets sur 4 sans surlignage. Chaque mode se teste donc SEUL :

    python scripts/exp_selection_bidi.py A   # visuel + LRM (GUI actuel)
    python scripts/exp_selection_bidi.py B   # visuel sans LRM
    python scripts/exp_selection_bidi.py C   # logique pur
    python scripts/exp_selection_bidi.py D   # logique + RLM en tête

Le widget reçoit la ligne de Genèse 38:1, le mot וַיֵּרֶד est sélectionné
par tag_add (aucune interaction souris, aucun StableSelection : isole
purement le rendu Tk), le widget prend la sélection primaire, les bbox sont
imprimées et une capture d'écran est sauvée dans %TEMP%.

Lecture attendue : A brouillé mais B propre => ce sont les LRM qui cassent
le redessin ; A et B brouillés => le découpage par tag lui-même.
"""

import os
import sys
import tempfile
import unicodedata

try:
    import tkinter as tk
except ImportError:
    print("tkinter indisponible — ce script doit tourner sous Windows/Tk.")
    sys.exit(1)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bidi_display import to_visual  # noqa: E402

LRM = "\u200E"
RLM = "\u200F"

VERSE = ("\u05d5\u05b7\u05bd\u05d9\u05b0\u05d4\u05b4\u05d9\u0599 "
         "\u05d1\u05b0\u05bc\u05e2\u05b5\u05a3\u05ea "
         "\u05d4\u05b7\u05d4\u05b4\u0594\u05d5\u05d0 "
         "\u05d5\u05b7\u05d9\u05bc\u05b5\u05a5\u05e8\u05b6\u05d3 "
         "\u05d9\u05b0\u05d4\u05d5\u05bc\u05d3\u05b8\u0596\u05d4 "
         "\u05de\u05b5\u05d0\u05b5\u05a3\u05ea "
         "\u05d0\u05b6\u05d7\u05b8\u0591\u05d9\u05d5 "
         "\u05d5\u05b7\u05d9\u05bc\u05b5\u059b\u05d8 "
         "\u05e2\u05b7\u05d3\u05be\u05d0\u05b4\u05a5\u05d9\u05e9\u05c1 "
         "\u05e2\u05b2\u05d3\u05bb\u05dc\u05b8\u05bc\u05de\u05b4\u0596\u05d9 "
         "\u05d5\u05bc\u05e9\u05c1\u05b0\u05de\u05b9\u05a5\u05d5 "
         "\u05d7\u05b4\u05d9\u05e8\u05b8\u05bd\u05d4\u05c3")


def no_marks(text):
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cf")


def main():
    if len(sys.argv) < 2 or sys.argv[1].upper() not in "ABCD":
        print(__doc__)
        sys.exit(2)
    mode = sys.argv[1].upper()

    texts = {
        "A": ("A. visuel + LRM (GUI actuel)", to_visual(VERSE)),
        "B": ("B. visuel sans LRM", no_marks(to_visual(VERSE))),
        "C": ("C. logique pur", VERSE),
        "D": ("D. logique + RLM tête", RLM + VERSE),
    }
    title, text = texts[mode]

    root = tk.Tk()
    root.title(title)
    root.geometry("1100x120")
    font = ("Taamey Frank CLM", 24)
    try:
        root.tk.call("font", "actual", font)
    except Exception:
        font = ("DejaVu Sans", 24)
        print(f"police demandée indisponible, repli sur {font}")

    t = tk.Text(root, font=font, height=1, width=120, wrap="none")
    t.pack(fill="both", expand=True)
    t.insert("1.0", text)

    content = t.get("1.0", "end - 1 c")
    # repérer le mot וירד : bases attendues selon le mode
    if mode in ("A", "B"):
        expect = ["\u05d3", "\u05e8", "\u05d9", "\u05d5"]  # stockage visuel
    else:
        expect = ["\u05d5", "\u05d9", "\u05e8", "\u05d3"]
    found = None
    for i, ch in enumerate(content):
        if ch != "\u05d3":
            continue
        start = content.rfind(" ", 0, i)
        end = content.find(" ", i)
        if start < 0:
            start = -1
        if end < 0:
            end = len(content)
        seg = content[start + 1:end]
        bases = [c for c in seg
                 if "\u05d0" <= c <= "\u05ea"
                 and unicodedata.category(c) != "Cf"]
        if bases == expect:
            found = (f"1.{start + 1}", f"1.{end}")
            break
    if not found:
        print(f"MOT INTROUVABLE en mode {mode}")
        root.mainloop()
        return

    first, last = found

    def apply_sel(event=None):
        # Le clic dans la fenêtre a donné le focus RÉEL (fenêtre active) :
        # sans focus effectif, Tk ne peint pas le fond du tag sel — c'est
        # pourquoi les essais automatiques (focus_set sans fenêtre active)
        # ne montraient aucun surlignage alors que le GUI (clic utilisateur)
        # l'affiche. Le clic ne sert qu'à activer la fenêtre ; les bornes
        # restent posées programmatiquement.
        t.tag_add("sel", first, last)
        t.selection_own()
        print(f"=== {title} : sel {first}..{last} ===")
        f = int(first.split(".")[1])
        l = int(last.split(".")[1])
        for i in range(f, l):
            ch = t.get(f"1.{i}")
            try:
                bb = t.bbox(f"1.{i}")
                print(f"  idx {i}: {ch!r} bbox={bb}")
            except Exception:
                print(f"  idx {i}: {ch!r} bbox=?")
        root.after(500, capture)

    def capture():
        try:
            root.deiconify()
            root.lift()
            root.attributes("-topmost", True)
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
            path = os.path.join(tempfile.gettempdir(),
                                f"exp_selection_bidi_{mode}.png")
            img.save(path)
            print(f"\ncapture : {path}")
        except Exception as exc:
            print(f"capture impossible : {exc}")
        root.attributes("-topmost", False)
        root.after(1500, root.destroy)

    print("CLIQUEZ UNE FOIS dans la fenêtre Tk (n'importe où) : la "
          "sélection se posera et la capture sera prise automatiquement.")
    t.bind("<Button-1>", apply_sel)
    root.mainloop()


if __name__ == "__main__":
    main()
