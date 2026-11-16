#!/usr/bin/env python3
"""Test de non-régression des glosses français (bhsa_grammar/lex_fr.py).

Cas signalé : le mode « Mot » avec כְּנֶגְדּוֹ (lexème BHSA NGD/, נֶגֶד,
« counterpart ») affichait la traduction FR « dire » — gloss de l'homographe
NGD[ (נָגַד, « dire »). L'alignement consonantique de lex_fr.json avait
attribué « dire » aux deux lexèmes ; NGD/ a été corrigé en
« vis-à-vis, en face de, contrepartie » (cf. Segond, Genèse 21:16).

Usage :
    python tests/test_lex_fr.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bhsa_grammar import lex_fr  # noqa: E402

# NGD/ = נֶגֶד (H5048, nom « vis-à-vis / counterpart ») ; NGD[ = נָגַד
# (H5046, verbe « dire »).
NEGED_FR = "vis-à-vis, en face de, contrepartie"


def test_neged_noun_gloss_fr():
    assert lex_fr.gloss_fr("NGD/", sp="subs") == NEGED_FR


def test_neged_best_gloss_prefers_fr_over_en():
    # best_gloss(lex, gloss_en, sp) : le FR l'emporte sur le gloss EN.
    assert lex_fr.best_gloss("NGD/", "counterpart", sp="subs") == NEGED_FR


def test_neged_never_dire():
    # Sans partie du discours fournie non plus.
    assert lex_fr.gloss_fr("NGD/") != "dire"
    assert lex_fr.gloss_fr("NGD/", sp="subs") != "dire"


def test_nagad_verb_keeps_dire():
    # L'homographe verbal נָגַד conserve « dire ».
    assert lex_fr.gloss_fr("NGD[", sp="verb") == "dire"


def main():
    test_neged_noun_gloss_fr()
    test_neged_best_gloss_prefers_fr_over_en()
    test_neged_never_dire()
    test_nagad_verb_keeps_dire()
    print("OK")


if __name__ == "__main__":
    main()
