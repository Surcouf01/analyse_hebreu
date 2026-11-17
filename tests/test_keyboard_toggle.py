#!/usr/bin/env python3
"""Test de non-régression du repli du clavier virtuel.

- gui.config._saved_keyboard_visible : état persisté (gui.properties,
  clé keyboard.visible), clavier déplié par défaut ;
- gui_hebreu.AnalyseurGUI : _build_keyboard crée le bouton de repli
  (style KbToggle, commande _toggle_keyboard) et appelle
  _set_keyboard_expanded ; icône chevron _chevron_image au niveau module.

Vérifié par import réel de gui.config (sans tkinter) et par AST pour
gui_hebreu.py (qui importe tkinter, indisponible sans affichage).

Usage :
    python tests/test_keyboard_toggle.py
"""

import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
GUI_HEBREU = os.path.join(ROOT, "gui_hebreu.py")


def test_saved_keyboard_visible():
    from gui.config import _saved_keyboard_visible, _PROPS
    saved = dict(_PROPS)
    try:
        _PROPS.pop("keyboard.visible", None)
        assert _saved_keyboard_visible() is True  # déplié par défaut
        _PROPS["keyboard.visible"] = "false"
        assert _saved_keyboard_visible() is False
        _PROPS["keyboard.visible"] = "true"
        assert _saved_keyboard_visible() is True
    finally:
        _PROPS.clear()
        _PROPS.update(saved)


def test_chevron_helper_and_toggle_wiring():
    with open(GUI_HEBREU, encoding="utf-8") as fh:
        src = fh.read()
    tree = ast.parse(src)
    assert any(isinstance(n, ast.FunctionDef) and n.name == "_chevron_image"
               for n in tree.body)
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "AnalyseurGUI")
    methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
    assert "_toggle_keyboard" in methods
    assert "_set_keyboard_expanded" in methods
    build = ast.get_source_segment(src, methods["_build_keyboard"])
    assert "_set_keyboard_expanded" in build
    assert "KbToggle" in build
    assert "_toggle_keyboard" in build
    # persistance de l'état dans gui.properties
    assert "keyboard.visible" in src


def test_run_methods_collapse_keyboard():
    """Les boutons « Analyser » (Mot/Phrase/Binyanim) replient le clavier."""
    with open(GUI_HEBREU, encoding="utf-8") as fh:
        src = fh.read()
    tree = ast.parse(src)
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "AnalyseurGUI")
    methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
    assert "_collapse_keyboard" in methods
    for name, attr in (("_run_word", "word_kb"), ("_run_phrase", "phrase_kb"),
                       ("_run_binyanim", "binyanim_kb")):
        seg = ast.get_source_segment(src, methods[name])
        assert "_collapse_keyboard" in seg and attr in seg, name


def main():
    test_saved_keyboard_visible()
    test_chevron_helper_and_toggle_wiring()
    test_run_methods_collapse_keyboard()
    print("OK")


if __name__ == "__main__":
    main()
