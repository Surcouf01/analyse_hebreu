#!/usr/bin/env python3
"""Test de non-régression : Ctrl+PgUp/PgDn dans les zones de texte.

Les zones de texte (ResultText, BidiHebrewText) lient <Prior>/<Next> au
niveau widget avec « break ». En Tk, une binding sans modificateur
correspond aussi à l'événement avec Ctrl (sous-ensemble de modificateurs,
le plus spécifique gagne, niveau widget avant bind_all) : le handler
retournait donc « break » sur Ctrl+PgUp et le bind_all global
<Control-Prior>/<Control-Next> (changement d'onglet, gui_hebreu.py) ne
faisait jamais.

Correction : avec Ctrl maintenu (event.state & ControlMask 0x4), les
handlers _on_page_up/_on_page_down ne défilent pas et ne renvoient pas
« break » → l'événement se propage jusqu'au bind_all global.

Vérifié par extraction AST de gui/widgets.py (qui importe tkinter,
indisponible sans affichage).

Usage :
    python tests/test_ctrl_pgup_text.py
"""

import ast
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

WIDGETS_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "gui", "widgets.py")

CONTROL_MASK = 0x0004


def _load_handlers():
    with open(WIDGETS_PY, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    out = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.FunctionDef)
                and node.name in ("_on_page_up", "_on_page_down")):
            out[node.name] = compile(ast.Module(body=[node], type_ignores=[]),
                                     WIDGETS_PY, "exec")
    assert set(out) == {"_on_page_up", "_on_page_down"}
    ns = {}
    for name, code in out.items():
        exec(code, ns)
    return ns["_on_page_up"], ns["_on_page_down"]


class FakeText:
    def __init__(self):
        self.scrolls = []

    def _scroll_pages(self, delta):
        self.scrolls.append(delta)


def test_ctrl_pgup_propagates():
    up, down = _load_handlers()
    w = FakeText()
    ev = types.SimpleNamespace(state=CONTROL_MASK)
    assert up(w, ev) is None and down(w, ev) is None
    assert w.scrolls == []  # pas de défilement : propagation vers bind_all


def test_plain_pgup_still_scrolls():
    up, down = _load_handlers()
    w = FakeText()
    ev = types.SimpleNamespace(state=0)
    assert up(w, ev) == "break" and down(w, ev) == "break"
    assert w.scrolls == [-1, 1]
    # appel direct sans événement (event=None) : défilement inchangé
    assert up(w, None) == "break"
    assert w.scrolls == [-1, 1, -1]


def main():
    test_ctrl_pgup_propagates()
    test_plain_pgup_still_scrolls()
    print("OK")


if __name__ == "__main__":
    main()
