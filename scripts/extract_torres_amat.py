#!/usr/bin/env python3
"""Extrait la traduction espagnole Torres Amat (1823) d'un module SWORD.

La Biblia Torres Amat (Félix Torres Amat, 1772-1847, dominio público) n'existe
pas en transcription numérique publiée : le projet OmarGonD/biblia-elim (GPL)
l'a reconstruite par OCR depuis l'édition de 1882 et la distribue comme module
SWORD zText. Ce script décode ce module via pysword et produit
``data/torres_amat_1823.txt`` au format plat du projet :

    <nom BHSA>\t<chapitre>\t<verset>\t<texte espagnol>

Torres Amat traduit la Vulgate : sa numérotation des versets suit la
versification Vulgate. Le script convertit vers la numérotation massorétique
de la base BHSA (BHS : p. ex. Deut 29:1 hébreu, Isaïe 8:23, Joël 4 chapitres,
Malachie 3 chapitres, Néhémie 7:72, Psaumes 9/10 et 113-116/145-147 fusionnés)
et n'écrit que les livres protocanoniques de l'AT.

La conversion a été calibrée verset par verset contre la base BHSA locale
(bhsa_repo/tf). Les défauts du module OCR sont gérés explicitement :
versets perdus (lacunes, laissés en creux), doublons de chapitre (1 Rois 4),
index des prophètes collé dans Osée 1, Jérémie 1 remplacé par une copie
numérotée de Jérémie 2:1-7, additions deutérocanoniques exclues.

Usage :

    python scripts/extract_torres_amat.py <chemin module SWORD> [--out data/torres_amat_1823.txt]

Le module SWORD attendu est l'arbre contenant ``mods.d/torresamat.conf`` et
``modules/texts/ztext/torresamat`` (6 fichiers .bzs/.bzv/.bzz).
"""

import argparse
import os
import re
import sys

try:
    from pysword.modules import SwordModules
except ImportError:  # pragma: no cover - pysword est optionnel à l'exécution
    SwordModules = None


# ---------------------------------------------------------------------------
# Versification Vulgate -> BHSA (massorétique)
# ---------------------------------------------------------------------------

# OSIS Vulgate du module -> nom BHSA (39 livres protocanoniques de l'AT).
_BOOK_MAP = {
    "Gen": "Genesis", "Exod": "Exodus", "Lev": "Leviticus",
    "Num": "Numeri", "Deut": "Deuteronomium", "Josh": "Josua",
    "Judg": "Judices", "Ruth": "Ruth", "1Sam": "Samuel_I",
    "2Sam": "Samuel_II", "1Kgs": "Reges_I", "2Kgs": "Reges_II",
    "1Chr": "Chronica_I", "2Chr": "Chronica_II", "Ezra": "Esra",
    "Neh": "Nehemia", "Esth": "Esther", "Job": "Iob", "Ps": "Psalmi",
    "Prov": "Proverbia", "Eccl": "Ecclesiastes", "Song": "Canticum",
    "Isa": "Jesaia", "Jer": "Jeremia", "Lam": "Threni",
    "Ezek": "Ezechiel", "Dan": "Daniel", "Hos": "Hosea", "Joel": "Joel",
    "Amos": "Amos", "Obad": "Obadia", "Jonah": "Jona", "Mic": "Micha",
    "Nah": "Nahum", "Hab": "Habakuk", "Zeph": "Zephania",
    "Hag": "Haggai", "Zech": "Sacharia", "Mal": "Maleachi",
}

# Livres apocryphes/deutérocanoniques du module : ignorés.
_SKIP_BOOKS = {"Tob", "Jdt", "Wis", "Sir", "1Macc", "2Macc", "Bar",
               "PrMan", "1Esd", "2Esd", "AddPs", "EpLao"}

# Psaumes : chapitre Vulgate -> liste de segments
# (psaume hébreu, verset hébreu de départ, verset Vulgate de départ,
#  verset hébreu de fin ou None).
# Le verset hébreu = hb_start + vulg_vs - vulg_start ; les versets Vulgate
# antérieurs à vulg_start renvoient None (auto-exclus : titres seuls de
# Vulg 10:1 et 145:1).
# Vulg 1-8 = hébreu 1-8 (identité).
# Vulg 9 fusionne les hébreux 9+10 : v1-21 -> hébreu 9:1-21,
#   v22+ -> hébreu 10:1+.
# Vulg 10 = hébreu 11 (v2+ ; v1 est un titre seul).
# Vulg 11-112 = hébreux 12-113 (décalage +1, titre = verset 1 comme BHSA).
# Vulg 113 fusionne les hébreux 114+115 : v1-8 -> hébreu 114,
#   v9+ -> hébreu 115.
# Vulg 114 = hébreu 116:1-9 ; Vulg 115 = hébreu 116:10-19.
# Vulg 116 = hébreu 117 ; Vulg 117-144 = hébreux 118-145 (décalage +1).
# Vulg 145 = hébreu 146 (v2+ ; v1 est un titre égaré).
# Vulg 146 = hébreu 147:1-11 ; Vulg 147 = hébreu 147:12-20.
# Vulg 148-150 = hébreux 148-150 (identité).
_PSALMS_MAP = {}
for _h in range(1, 9):
    _PSALMS_MAP[_h] = [(_h, 1, 1, None)]
_PSALMS_MAP[9] = [(9, 1, 1, 21), (10, 1, 22, None)]
_PSALMS_MAP[10] = [(11, 1, 2, None)]
for _v in range(11, 113):
    _PSALMS_MAP[_v] = [(_v + 1, 1, 1, None)]
_PSALMS_MAP[113] = [(114, 1, 1, 8), (115, 1, 9, None)]
_PSALMS_MAP[114] = [(116, 1, 1, 9)]
_PSALMS_MAP[115] = [(116, 10, 1, None)]
_PSALMS_MAP[116] = [(117, 1, 1, None)]
for _v in range(117, 145):
    _PSALMS_MAP[_v] = [(_v + 1, 1, 1, None)]
_PSALMS_MAP[145] = [(146, 2, 2, None)]  # v1 : titre égaré, v2+ identité 146:2+
_PSALMS_MAP[146] = [(147, 1, 1, 11)]
_PSALMS_MAP[147] = [(147, 12, 1, None)]
for _v in range(148, 151):
    _PSALMS_MAP[_v] = [(_v, 1, 1, None)]


def _psalm_verses(vulg_ch, vulg_vs):
    """Convertit (chapitre, verset) Vulgate Psaumes en référence massorétique.

    Renvoie None pour les versets hors psaume massorétique (p. ex. titres
    seuls de Vulg 10:1 et 145:1).
    """
    for psalm, hb_start, vstart, hb_end in _PSALMS_MAP[vulg_ch]:
        if vulg_vs >= vstart:
            hb_vs = hb_start + vulg_vs - vstart
            if hb_end is None or hb_vs <= hb_end:
                return (psalm, hb_vs)
    return None


# Décalages verset par verset (livre OSIS, chapitre Vulgate) -> règles.
# Chaque règle : (verse_min, verse_max ou None, chapitre BHSA, décalage
# verset BHSA) ; résultat = verse + décalage.
# Calibré verset par verset contre la base BHSA locale (bhsa_repo/tf).
_VERSE_SHIFTS = {
    # Genèse : la Vulgate place Gen 31:55 en tête du chapitre 32 hébreu
    # (Laban bénit ses fils).
    ("Gen", 31): [(55, 55, 32, -54)],
    ("Gen", 32): [(1, None, 32, 1)],
    # Exode : la Vulgate place Exod 7:26-29 en tête du chapitre 8 ;
    # Exod 22:1 manque dans le module (lacune OCR), 22:2+ décalé de -1.
    ("Exod", 8): [(1, 4, 7, 25), (5, None, 8, -4)],
    ("Exod", 22): [(2, None, 22, -1)],
    # Lévitique : la Vulgate place Lev 5:20-26 en tête du chapitre 6.
    ("Lev", 6): [(1, 7, 5, 19), (8, None, 6, -7)],
    # Nombres : la Vulgate place Num 12:16 en tête de chapitre 13 ;
    # Num 16:36-48 = TM 17:1-13 ; Num 17 Vulgate (28 v. en hébreu) est
    # décalé de +15 (17:1 -> 17:16).
    ("Num", 13): [(1, 1, 12, 15), (2, None, 13, -1)],
    ("Num", 16): [(36, 48, 17, -35)],
    ("Num", 17): [(1, None, 17, 15)],
    # Nombres : TA 20:30 = TM 20:29 (le verset 20:29 du module est
    # une lacune OCR, son texte est porté par 20:30).
    ("Num", 20): [(30, 30, 20, -1)],
    # Deutéronome : 12:32 -> 13:1 ; 22:30 = TM 23:1 (la Vulgate place
    # la femme du père à la fin du ch. 22) ; 23:1-23 = TM 23:2-24 et
    # 23:25 = TM 23:25 (défaut de numérotation OCR) ; 29:1 Vulgate =
    # 28:69 hébreu (mots de l'alliance), 29:2+ = 29:1+.
    ("Deut", 12): [(32, 32, 13, -31)],
    ("Deut", 13): [(1, None, 13, 1)],
    ("Deut", 22): [(30, 30, 23, -29)],
    ("Deut", 23): [(1, 23, 23, 1), (25, 25, 23, 0)],
    ("Deut", 29): [(1, 1, 28, 68), (2, None, 29, -1)],
    # Josué : 4:24 est la seconde moitié de TM 4:23 (exclue) ; 4:25
    # (texte de 5:1 collé, « CAPITULO » stripped) -> 4:24 ;
    # TA 21:37-43 = TM 21:38-44.
    ("Josh", 4): [(25, 25, 4, -1)],
    ("Josh", 21): [(37, None, 21, 1)],
    # 1 Samuel : TA 20:43 = « se levanta David... » = TM 21:1 ;
    # Vulg 21:1+ = TM 21:2+.
    ("1Sam", 20): [(43, 43, 21, -42)],
    ("1Sam", 21): [(1, None, 21, 1)],
    # 2 Samuel : la Vulgate place 2 Sam 18:33 en tête du chapitre 19.
    ("2Sam", 18): [(33, 33, 19, -32)],
    ("2Sam", 19): [(1, None, 19, 1)],
    # 1 Rois : TA 4:1-28 duplique le chapitre 3 (exclu) ; TA 4:29-34 =
    # TM 5:9-14 ; TA 5:1-18 = TM 5:15-32 (fusion Vulgate des ch. 4-5).
    ("1Kgs", 4): [(29, None, 5, -20)],
    ("1Kgs", 5): [(1, None, 5, 14)],
    # 2 Rois : la Vulgate place 2 Kgs 11:21 en tête du chapitre 12.
    ("2Kgs", 11): [(21, 21, 12, -20)],
    ("2Kgs", 12): [(1, None, 12, 1)],
    # 1 Chroniques : la Vulgate compte 6:1-15 comme 5:27-41 hébreu ;
    # 6:16+ = 6:1+ hébreu.
    ("1Chr", 6): [(1, 15, 5, 26), (16, None, 6, -15)],
    # 2 Chroniques : TA 2:1 manque (lacune OCR), 2:2+ décalé de -1 ;
    # la Vulgate place 2 Chr 13:23+14:1 en tête du chapitre 14.
    ("2Chr", 2): [(2, None, 2, -1)],
    ("2Chr", 14): [(1, 1, 13, 22), (2, None, 14, -1)],
    # Néhémie : TA 4:1-6 = TM 3:33-38 ; TM 7 compte 72 versets : TA 7:68
    # (verset des chevaux, addition) exclu, 7:69-73 -> 7:68-72 ;
    # TA 9:38 = TM 10:1 ; TA 10:1+ = TM 10:2+.
    ("Neh", 4): [(1, 6, 3, 32), (7, None, 4, -6)],
    ("Neh", 7): [(69, None, 7, -1)],
    ("Neh", 9): [(38, 38, 10, -37)],
    ("Neh", 10): [(1, None, 10, 1)],
    # Job : TA 16:7-23 = TM 16:6-22 (défaut de numérotation OCR) ;
    # TA 39:32-35 = TM 40:2-5 ; TA 40:1-19 = TM 40:6-24,
    # TA 40:20-28 = TM 41:1-9 ; TA 41:1+ = TM 41:2+.
    ("Job", 16): [(7, None, 16, -1)],
    ("Job", 39): [(32, 35, 40, -30)],
    ("Job", 40): [(1, 19, 40, 5), (20, 28, 41, -19)],
    ("Job", 41): [(1, None, 41, 1)],
    # Daniel : Vulg 3:91-100 = TM 3:24-33 (après exclusion de l'addition
    # 3:24-90) ; Vulg 5:31 = TM 6:1 ; Vulg 6:1+ = TM 6:2+.
    ("Dan", 3): [(91, None, 3, -67)],
    ("Dan", 5): [(31, 31, 6, -30)],
    ("Dan", 6): [(1, None, 6, 1)],
    # Isaïe : Vulg 9:1 = TM 8:23 (la BHSA compte 8:23), 9:2+ = 9:1+ ;
    # Vulg 64:1 est la seconde moitié de TM 63:19 (exclue), 64:2+ = 64:1+.
    ("Isa", 9): [(1, 1, 8, 22), (2, None, 9, -1)],
    # Isa 1 : TA 1:5 porte le texte de TM 1:8 (mal positionné par l'OCR) ;
    # TA 1:8 absent ; TA 1:9+ identité.
    ("Isa", 1): [(5, 5, 1, 3)],
    ("Isa", 45): [(26, 26, 45, -1)],
    ("Isa", 64): [(2, None, 64, -1)],
    # Jérémie : le module numérote une copie de TM 2:1-7 comme
    # chapitre 1 (le vrai Jer 1 est perdu par l'OCR) ; la Vulgate place
    # Jer 8:23 en tête du chapitre 9 ; TA 37:5+ = TM 37:6+ ; TA 49 = TM
    # 50:1-2 (le vrai Jer 49 est perdu par l'OCR).
    ("Jer", 1): [(1, None, 2, 0)],
    ("Jer", 9): [(1, 1, 8, 22), (2, None, 9, -1)],
    ("Jer", 37): [(5, None, 37, 1)],
    ("Jer", 49): [(1, 2, 50, 0)],
    # Ézéchiel : la Vulgate place Ezek 20:45-49 en tête du chapitre 21
    # (décalage de +5, pas +1).
    ("Ezek", 20): [(45, 49, 21, -44)],
    ("Ezek", 21): [(1, None, 21, 5)],
    # Osée : le module colle un index des prophètes en 1:1-2 et 1:10-11
    # (exclus) ; TA 2:1-23 = TM 2:3-25 (2:24 exclu : seconde moitié de
    # TM 2:25 avec « CAPITULO III » collé).
    ("Hos", 2): [(1, None, 2, 2)],
    ("Hos", 11): [(12, 12, 12, -11)],
    ("Hos", 12): [(1, None, 12, 1)],
    # Joël : la BHSA compte 4 chapitres ; Vulg 2:28+ = TM 3:1+,
    # Vulg 3:1+ = TM 4:1+ (le ch. 4 du module est vide).
    ("Joel", 2): [(28, None, 3, -27)],
    ("Joel", 3): [(1, None, 4, 0)],
    # Amos : TA 6:12-15 = TM 6:11-14 (défaut de numérotation OCR,
    # recalé sur mots-clés : « caballos », « casa grande »,
    # « levantaré contra vosotros »).
    ("Amos", 6): [(12, None, 6, -1)],
    # Aggée : la Vulgate place Hag 1:15b en tête du chapitre 2.
    ("Hag", 2): [(1, 1, 1, 14), (2, None, 2, -1)],
    # Malachie : la BHSA compte 3 chapitres ; Vulg 4:1+ = TM 3:19+.
    ("Mal", 4): [(1, None, 3, 18)],
    # Michée : Vulg 5:1 = TM 4:14 ; Vulg 5:2+ = TM 5:1+.
    ("Mic", 5): [(1, 1, 4, 13), (2, None, 5, -1)],
    # Nahum : la Vulgate place Nah 1:15 en tête du chapitre 2.
    ("Nah", 1): [(15, 15, 2, -14)],
    ("Nah", 2): [(1, None, 2, 1)],
    # Zacharie : la Vulgate place Zech 1:18-21 en tête du chapitre 2.
    ("Zech", 1): [(18, 21, 2, -17)],
    ("Zech", 2): [(1, None, 2, 4)],
    # Ecclésiaste : TA 7:1 contient en réalité le texte de TM 7:6
    # (« risas del insensato... »), mal positionné par l'OCR : rescrit
    # en 7:6 ; TA 7:2+ = TM 7:1+.
    ("Eccl", 7): [(1, 1, 7, 5), (2, None, 7, -1)],
    # Cantique : TA 1:4-16 = TM 1:5-17 (décalage +1, 1:1-3 perdus) ;
    # TA 2, 3, 4 et 5:1-16 identité ; TA 5:17 = TM 6:1 ;
    # TA 6:2-11 = TM 6:3-12, TA 6:12 = TM 7:1 ; TA 7:1 est une fusion
    # (fin de TM 7:1 + début de TM 7:2) laissée en TM 7:1 ;
    # TA 7:2+ = TM 7:3+.
    ("Song", 1): [(1, None, 1, 1)],
    ("Song", 5): [(17, 17, 6, -16)],
    ("Song", 6): [(2, 11, 6, 1), (12, 12, 7, -11)],
    ("Song", 7): [(2, None, 7, 1)],
}


def _convert(book_osis, chapter, verse):
    """Convertit une référence Vulgate en référence BHSA, ou None si le
    verset n'appartient pas au canon massorétique."""
    shifts = _VERSE_SHIFTS.get((book_osis, chapter))
    if shifts:
        for vs_min, vs_max, bhsa_ch, delta in shifts:
            if verse >= vs_min and (vs_max is None or verse <= vs_max):
                return (_BOOK_MAP[book_osis], bhsa_ch, verse + delta)
    if book_osis == "Ps":
        mapped = _psalm_verses(chapter, verse)
        if mapped is None:
            return None
        return ("Psalmi",) + mapped
    return (_BOOK_MAP[book_osis], chapter, verse)


# Chapitres/versets Vulgate à exclure : additions deutérocanoniques et
# défauts OCR du module (doublons, index collé, secondes moitiés de
# versets massorétiques).
_EXCLUDE = set()
for _v in range(24, 91):                    # Dan 3 : prière d'Azarias
    _EXCLUDE.add(("Dan", 3, _v))
for _c in range(13, 17):                    # Dan 13-14 : Bel, Suzanne
    _EXCLUDE.add(("Dan", _c, None))
for _v in range(4, 14):                     # Esth 10:4-13 : addition
    _EXCLUDE.add(("Esth", 10, _v))
for _c in range(11, 17):                    # Esth 11-16 : additions grecques
    _EXCLUDE.add(("Esth", _c, None))
_EXCLUDE.add(("Judg", 5, 32))               # 2e moitié de TM 5:31 (doublon)
_EXCLUDE.add(("Josh", 4, 24))               # 2e moitié de TM 4:23
_EXCLUDE.add(("Neh", 7, 68))                # verset des chevaux (addition)
for _v in range(1, 29):                     # 1Kgs 4: doublon OCR du ch. 3
    _EXCLUDE.add(("1Kgs", 4, _v))
# Osée 1 : index des prophètes collé par l'OCR (versets contaminés),
# pas d'écriture.
for _v in (1, 2, 6, 7, 9, 10, 11):
    _EXCLUDE.add(("Hos", 1, _v))
_EXCLUDE.add(("Hos", 2, 24))                # 2e moitié de TM 2:25 + « CAPITULO »
_EXCLUDE.add(("Isa", 64, 1))                # 2e moitié de TM 63:19
_EXCLUDE.add(("Ps", 2, 13))                 # 2e moitié de TM 2:12
_EXCLUDE.add(("Ps", 4, 10))                 # 2e moitié de TM 4:9
# Additions grecques / note du traductreur collées après le texte
# canonique : tronquer au marqueur.
_TRIM = {
    ("Esth", 10, 1): "Acuérdome",   # addition grecque (rêve de Mardoqueo)
    ("Esth", 10, 3): "HE TRADUCIDO",  # note du traducteur
}
# Isaïe 1 : le module OCR colle un commentaire sur le mot « Prophète »
# à la place des versets 1-4 et 6-7 (le vrai texte est perdu) ;
# TA 1:5 = TM 1:8, TA 1:8 absent, TA 1:9+ identité.
for _v in (1, 2, 3, 4, 6, 7):
    _EXCLUDE.add(("Isa", 1, _v))


# ---------------------------------------------------------------------------
# Nettoyage léger des résidus OCR
# ---------------------------------------------------------------------------

def _clean(text):
    """Nettoyage minimal du texte OCR : espaces, tirets d'OCR, caractères
    parasites isolés. Reste volontairement conservateur."""
    if not text:
        return ""
    text = text.replace("­", "")            # soft hyphen
    text = re.sub(r"\s+", " ", text)
    text = text.replace(" ,", ",").replace(" .", ".")
    text = re.sub(r"\s+([,;:!?])", r"\1", text)
    text = text.strip(" ;,.")
    # « ¿ ¿ » dupliqué par l'OCR : « ¿¿ » -> « ¿ »
    text = text.replace("¿¿", "¿")
    # Résidus OCR de fin de chapitre collés au dernier verset :
    # « CAPITULO ... » (Josh 4:25 = 5:1 collé, Esth 4:17, Neh 7:73,
    # Hos 2:24) et « HASTA AQUÍ ... » (Neh 7:69) : tronquer jusqu'à la fin.
    text = re.sub(r"\s*CAP[I1L]T[UUL][I1L][O0].*$", " ", text,
                  flags=re.IGNORECASE)
    text = re.sub(r"\s*HASTA\s+AQU[I1LíÍ].*$", " ", text,
                  flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract(module_path):
    """Renvoie {book_bhsa: {chapter: {verse: texte}}} pour l'AT massorétique."""
    if SwordModules is None:
        sys.exit("pysword est requis : pip install pysword")
    sm = SwordModules(module_path)
    sm.parse_modules()
    bible = sm.get_bible_from_module("TorresAmat")
    structure = bible.get_structure().get_books()["ot"]
    index = {}
    for book in structure:
        osis = book.osis_name
        if osis in _SKIP_BOOKS or osis not in _BOOK_MAP:
            continue
        for chapter in range(1, book.num_chapters + 1):
            nverses = book.chapter_lengths[chapter - 1]
            for verse in range(1, nverses + 1):
                if (osis, chapter, None) in _EXCLUDE \
                        or (osis, chapter, verse) in _EXCLUDE:
                    continue
                try:
                    raw = bible.get(books=[book.name],
                                    chapters=[chapter],
                                    verses=[verse])
                except Exception:  # noqa: BLE001 - verset absent de l'index
                    continue
                text = _clean(raw)
                marker = _TRIM.get((osis, chapter, verse))
                if marker:
                    pos = text.find(marker)
                    if pos > 0:
                        text = _clean(re.sub(r"[\s\d;,.:]+$", "",
                                             text[:pos]))
                if not text:
                    continue
                mapped = _convert(osis, chapter, verse)
                if mapped is None:
                    continue
                bhsa_book, bhsa_ch, bhsa_v = mapped
                index.setdefault(bhsa_book, {}) \
                     .setdefault(bhsa_ch, {})[bhsa_v] = text
    return index


def write_flat(index, path):
    """Écrit l'index au format plat BHSA (une ligne par verset)."""
    header = (
        "# Torres Amat 1823 — dominio público (texto íntegro del Antiguo "
        "Testamento). Traducción de la Vulgata latina al español por\n"
        "# don Félix Torres Amat (1772-1847), publicada entre 1823 y 1825.\n"
        "# Source : module SWORD TorresAmat du projet OmarGonD/biblia-elim "
        "(reconstruction OCR de l'édition de 1882 conservée à Internet "
        "Archive,\n# GPL-2.0-or-later ; le texte de Torres Amat lui-même "
        "est dominio público). Le module couvre 94 % des versets ; le\n"
        "# texte contient des erratas résiduelles d'OCR et n'est pas "
        "révisé (versets perdus laissés en creux).\n"
        "# Versification convertie Vulgate -> massorétique (BHSA, "
        "numérotation BHS : Deut 29:1, Isa 8:23, Joël 4 ch., Malachie\n"
        "# 3 ch., etc.) : Psaumes Vulgate renumérotés (fusions 9/10,\n"
        "# 113/114/115, 146/147 ; titres de psaumes conservés comme verset 1,\n"
        "# convention BHSA), additions deutérocanoniques exclues (Daniel\n"
        "# 3:24-90, 13-14 ; Esther Vulgate 10:4-13, 11-16), défauts OCR du\n"
        "# module exclus (doublon 1 Rois 4, index des prophètes collé en\n"
        "# Osée 1, Jérémie 1 perdu — copie numérotée de 2:1-7 mappée en\n"
        "# Jérémie 2, secondes moitiés de versets). Calibré verset par\n"
        "# verset contre la base BHSA ; voir scripts/extract_torres_amat.py.\n"
        "# Format : nom_BHSA\tchapitre\tverset\ttexte_espagnol\n"
    )
    lines = [header]
    for book in sorted(index):
        for chapter in sorted(index[book]):
            for verse in sorted(index[book][chapter]):
                text = index[book][chapter][verse].replace("\t", " ")
                lines.append(f"{book}\t{chapter}\t{verse}\t{text}\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    return len(lines) - 1


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("module", help="chemin de l'arbre du module SWORD "
                    "(contenant mods.d/torresamat.conf)")
    p.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "torres_amat_1823.txt"))
    args = p.parse_args(argv)
    if not os.path.isfile(os.path.join(args.module, "mods.d",
                                       "torresamat.conf")):
        p.error(f"module SWORD introuvable dans {args.module}")
    index = extract(args.module)
    n = write_flat(index, args.out)
    print(f"{n} versets écrits dans {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
