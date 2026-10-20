#!/usr/bin/env python3
"""Test de non-régression du détecteur de qamats qatan (qamats_qatan.py).

Règle : qamats en syllabe fermée non accentuée → qatan (/o/).
Exceptions : begadkefat (dagesh lene), gutturale+hateph, sheva naʿ
graphique (yod nu), monosyllabe fermé (כָּל), accent écrit (teamim)
ou par défaut (dernière voyelle), exceptions lexicales (חניה).

Le flux parole (apply_for_speech) convertit en holam — qui survit au
nettoyage des teamim de verse_audio (plage U+05C3..U+05C7, qui
contient le U+05C7).

Usage :
    python tests/test_qamats_qatan.py
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import qamats_qatan  # noqa: E402

# (mot voyellé, nb de qamats qatan attendu)
CASES = (
    # Qatan : syllabe fermée inaccentuée.
    ("כָּל", 1),                 # kol (monosyllabe fermé, accentué)
    ("כָּל־הָאָרֶץ", 1),         # kol-haʾarets
    ("חָכְמָה", 1),              # khokhmā
    ("קָדְשֵׁי", 1),              # qodshei
    ("יָדְךָ֖", 1),              # yodkha (teamim ailleurs)
    ("אָמְנָם", 1),              # omnam
    ("עָשׂוֹר", 0),              # ʿasor (pattern katol, gadol)
    ("חָשְׁכָה", 1),              # khoshkhā
    # Gadol : syllabe ouverte.
    ("שָׁמַר", 0),               # shamar
    ("בָּשָׂר", 0),               # basar
    ("תָּמִיד", 0),               # tamid
    ("שָׁלוֹם", 0),               # shalom
    # Gadol : begadkefat (dagesh lene, syllabe historiquement ouverte).
    ("בָּרַךְ", 0),               # barakh
    # Gadol : gutturale + hateph rouvre la syllabe.
    ("נָעֳמִי", 0),              # Naʿomi
    # Gadol : accent écrit sur la syllabe (teamim).
    ("שָׁמָֽר׃", 0),              # silluq sur le qamats
    # Gadol : sheva naʿ graphique (sheva + yod nu).
    ("חָנְיָה", 0),              # khanəyā (+ exception lexicale)
    # Pas de qamats.
    ("כֹּל", 0),                 # holam
    ("הַכֹּל", 0),
)


def test_detection():
    for word, expected in CASES:
        _new, count = qamats_qatan.qamats_qatan_text(word)
        assert count == expected, (word, count, expected)
    print("test_detection : ok")


def test_speech_flux():
    """apply_for_speech produit un holam qui survit à strip_teamim."""
    import verse_audio
    verse = "\u05d5\u05b7\u05d9\u05b0\u05d4\u05b4\u05d9\u05a9 \u05db\u05b8\u05bc\u05dc\u05be\u05d4\u05b8\u05d0\u05b8\u05a8\u05b6\u05e5\u05ae"  # Gen 11:1
    speech = qamats_qatan.apply_for_speech(verse)
    stripped = verse_audio.strip_teamim(speech)
    kol = "\u05db\u05b9\u05bc\u05dc"  # kaf+dagesh+HOLAM+lamed
    assert kol in stripped, f"holam attendu sur kol : {stripped!r}"
    # le qamats d'origine (U+05B8) a bien été remplacé sur ce mot
    assert "\u05db\u05b8\u05bc\u05dc" not in stripped, f"qamats résiduel : {stripped!r}"
    print("test_speech_flux : ok")


def test_replacement_positions():
    """Le remplacement préserve la longueur et les autres caractères."""
    word = "\u05d7\u05b8\u05db\u05b0\u05de\u05b8\u05d4"  # khokhmā
    new, count = qamats_qatan.qamats_qatan_text(word)
    assert count == 1
    assert len(new) == len(word)
    assert new.count(qamats_qatan.QAMATS) == 1      # le mā final reste gadol
    assert new.count(qamats_qatan.QAMATS_QATAN) == 1
    print("test_replacement_positions : ok")


if __name__ == "__main__":
    test_detection()
    test_speech_flux()
    test_replacement_positions()
    print("tests/test_qamats_qatan.py : tous les tests sont passés.")
