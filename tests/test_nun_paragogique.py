#!/usr/bin/env python3
"""Test de non-régression du nun paragogique (bhsa_grammar.rules.word_rules).

La BHSA encode le ן final des formes comme יִלְמְדוּן dans la feature vbe
(verbal ending) : WN (yiqtol/wayyiqtol pl.), TN (parfait 2e f. pl.),
JN (yiqtol 2e f. sg.). word_rules doit émettre une règle « Nun paragogique »
pour ces formes — et seulement pour elles (jamais pour l'araméen biblique,
où -וּן est la terminaison régulière de l'imparfait pluriel).

Usage :
    python tests/test_nun_paragogique.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bhsa_grammar import load_corpus  # noqa: E402
from bhsa_grammar.rules import word_rules  # noqa: E402

PARAGOGIC_MARKER = "Nun paragogique"


def _has_paragogic(rules):
    return any(PARAGOGIC_MARKER in r for r in rules)


def main():
    api = load_corpus()
    F, L = api.F, api.L
    failures = []

    # Formes hébraïques à nun paragogique : la règle doit être émise.
    # (node, g_cons attendu, vbe attendu, référence)
    expected = [
        (95396, "JLMDWN", "WN", "Deut 4:10 יִלְמְדוּן (qal)"),
        (95412, "JLMDWN", "WN", "Deut 4:10 וְיַלְּמְדוּן (piel)"),
        (1231, "TMTWN", "WN", "Gen 3:3 תְּמֻתוּן"),
        (16470, "JD<TN", "TN", "Gen 31:6 יְדַעְתֶּן (parfait 2e f. pl.)"),
        (141814, "TCTKRJN", "JN", "1 Sam 1:14 תִּשְׁתַּכָּרִין"),
        (281330, "<FJTN", "TN", "Exod 1:16 עֲשִׂיתֶן (parfait 2e f. pl.)"),
    ]
    for w, cons, vbe, label in expected:
        if F.g_cons.v(w) != cons or F.vbe.v(w) != vbe:
            failures.append(f"base BHSA inattendue pour {label}: "
                            f"{F.g_cons.v(w)}/{F.vbe.v(w)}")
            continue
        rules = word_rules(F, L, w)
        if not _has_paragogic(rules):
            failures.append(f"{label}: règle « Nun paragogique » absente de "
                            f"{rules!r}")

    # Contre-exemples hébreux : pas de règle (terminaisons régulières,
    # infinitifs, impératifs, formes sans terminaison en N).
    non_expected = [
        (95383, "inf construit אֱמֹר"),
        (95386, "impératif hif הַקְהֵל"),
        (95392, "yiqtol cohéortif אַשְׁמִיעֵם"),
        (95402, "substantif יָמִים"),
    ]
    for w, label in non_expected:
        rules = word_rules(F, L, w)
        if _has_paragogic(rules):
            failures.append(f"{label}: règle parasite émise {rules!r}")

    # Araméen biblique : -וּן est la terminaison régulière de l'imparfait
    # pluriel ; la règle ne doit PAS être émise.
    aramaic_hits = [
        w for w in F.otype.s("word")
        if F.language.v(w) == "Aramaic" and F.sp.v(w) == "verb"
        and (F.vbe.v(w) or "").endswith("N")
    ]
    if not aramaic_hits:
        failures.append("aucune forme araméenne de contrôle trouvée")
    for w in aramaic_hits[:5]:
        rules = word_rules(F, L, w)
        if _has_paragogic(rules):
            failures.append(f"araméen {F.g_word_utf8.v(w)} (node {w}): "
                            f"règle parasite émise {rules!r}")

    if failures:
        print(f"ÉCHECS ({len(failures)}) :")
        for f in failures:
            print("  -", f)
        return 1
    print("TOUS LES TESTS NUN PARAGOGIQUE PASSENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
