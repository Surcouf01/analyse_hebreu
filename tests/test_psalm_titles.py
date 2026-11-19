#!/usr/bin/env python3
"""Test de non-régression : titres des psaumes placés au verset 1 (BHSA).

Cas signalé : en mode verset, « Psaume 48:2 » affichait une traduction
Louis Segond commençant par « Cantique. Psaume des fils de Koré. » — le
titre, c'est-à-dire le texte du verset 1 massorétique, resté fusionné au
premier verset du texte après la renumérotation. Depuis
`scripts/split_psalm_titles.py`, le titre est au verset 1 (et au verset 2
pour les psaumes à double titre 51/52/54/60) : le verset 2 ne contient plus
que le texte du verset.

Usage :
    python tests/test_psalm_titles.py
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bhsa_grammar.translation import load_translation, get_translation  # noqa: E402

# Psaumes titrés (superscription = verset 1 BHSA) : ceux dont le verset 1
# était « en creux » avant scripts/split_psalm_titles.py.
TITLED_PSALMS = [
    3, 4, 5, 6, 7, 8, 9, 12, 13, 18, 19, 20, 21, 22, 30, 31, 34, 36, 38, 39,
    40, 41, 42, 44, 45, 46, 47, 48, 49, 51, 52, 53, 54, 55, 56, 57, 58, 59,
    60, 61, 62, 63, 64, 65, 67, 68, 69, 70, 75, 76, 77, 80, 81, 83, 84, 85,
    88, 89, 92, 102, 108, 140, 142,
]

# Début typique d'un titre de psaume, par langue (ne doit plus apparaître en
# tête du premier verset du texte).
_TITLE_STARTERS = {
    "fr": r"^(Au chef des chantres|Psaume\.|Cantique\.|Complainte|De David\.|"
           r"Prière d'un|Cantique d'Éthan)",
    "en": r"^(To the chief Musician|A Psalm|A Song|Shiggaion|Maschil)",
    "it": r"^(Al Capo|Per il Capo|Salmo\.|Canto\.|Shiggaion|Di Davide|"
           r"Cantico di|Preghiera dell')",
}


def test_psaume_48_cas_signale():
    """Psaume 48:2 : plus de titre de 48:1 en préfixe (LSG, KJV, Riveduta)."""
    fr = load_translation(language="fr")
    assert get_translation(fr, "Psalmi", 48, 1) == "Cantique. Psaume des fils de Koré."
    v2 = get_translation(fr, "Psalmi", 48, 2)
    assert v2.startswith("L'Éternel est grand")
    assert "Koré" not in v2
    en = load_translation(language="en")
    assert get_translation(en, "Psalmi", 48, 1) == "A Song and Psalm for the sons of Korah."
    assert get_translation(en, "Psalmi", 48, 2).startswith("Great is the LORD")
    it = load_translation(language="it")
    assert get_translation(it, "Psalmi", 48, 1) == "Canto. Salmo de' figliuoli di Core."
    assert get_translation(it, "Psalmi", 48, 2).startswith("Grande è l'Eterno")


def test_tous_les_psaumes_ont_un_verset_1():
    for lang in ("fr", "en", "it"):
        idx = load_translation(language=lang)
        for ch, verses in idx["Psalmi"].items():
            assert 1 in verses, f"{lang} Ps {ch} : verset 1 absent"


def test_doubles_titres_51_52_54_60():
    fr = load_translation(language="fr")
    assert get_translation(fr, "Psalmi", 51, 1) == "Au chef des chantres. Psaume de David."
    assert get_translation(fr, "Psalmi", 51, 2).startswith("Lorsque Nathan")
    assert get_translation(fr, "Psalmi", 51, 3).startswith("O Dieu! aie pitié")
    en = load_translation(language="en")
    assert get_translation(en, "Psalmi", 60, 1).startswith("To the chief Musician upon Shushan-eduth")
    assert get_translation(en, "Psalmi", 60, 2).startswith("when he strove with Aram-naharaim")
    assert get_translation(en, "Psalmi", 60, 3).startswith("O God, thou hast cast us off")


def test_aucun_premier_verset_du_texte_ne_commence_par_un_titre():
    for lang in ("fr", "en", "it"):
        idx = load_translation(language=lang)
        pattern = re.compile(_TITLE_STARTERS[lang])
        for ch in TITLED_PSALMS:
            v0 = 3 if ch in (51, 52, 54, 60) else 2
            text = idx["Psalmi"][ch][v0]
            assert not pattern.match(text), f"{lang} Ps {ch}:{v0} commence par un titre : {text[:60]}"
