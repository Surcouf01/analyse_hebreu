#!/usr/bin/env python3
"""Test de non-régression du clavier virtuel (gui/keyboard.py).

Vérifie, sans importer tkinter, que les structures de nikkud sont
cohérentes et que la voyelle shuruq dispose bien d'une touche dédiée :
shuruq = vav (U+05D5) + daguesh (U+05BC), qui n'a PAS de codepoint
combinant dédié en Unicode — la touche insère donc le glyphe complet וּ.

Usage :
    python tests/test_keyboard_nikkud.py
"""

import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

KEYBOARD_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "gui", "keyboard.py")

SHURUQ = "ו\u05BC"  # וּ : vav + daguesh


def _load_nikkud_structs():
    """Évalue _NIKKUD, NIKKUD_LABELS et NIKKUD_ROWS sans importer tkinter."""
    with open(KEYBOARD_PY, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    ns = {"_CARRIER": "◌", "_NIKKUD_CARRIER": "א"}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in ("_NIKKUD", "NIKKUD_LABELS",
                                            "NIKKUD_ROWS")):
            ns[node.targets[0].id] = eval(
                compile(ast.Expression(node.value), KEYBOARD_PY, "eval"), ns)
    return ns["_NIKKUD"], ns["NIKKUD_LABELS"], ns["NIKKUD_ROWS"]


def test_shuruq_key_exists():
    nikkud, labels, rows = _load_nikkud_structs()
    flat = [k for row in rows for k in row]
    assert "shuruq" in flat, "pas de touche shuruq dans NIKKUD_ROWS"
    assert nikkud["shuruq"] == SHURUQ
    assert labels["shuruq"] == SHURUQ


def test_rows_keys_consistent():
    nikkud, labels, rows = _load_nikkud_structs()
    for row in rows:
        for key in row:
            assert key in nikkud and nikkud[key], key
            assert key in labels and labels[key], key


def main():
    test_shuruq_key_exists()
    test_rows_keys_consistent()
    print("OK")


if __name__ == "__main__":
    main()
