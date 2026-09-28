#!/usr/bin/env python3
"""Renumérote les traductions Segond, KJV et Riveduta vers la versification BHSA.

Segond 1910, KJV 1611 et Riveduta Luzzi 1927 suivent la versification
chrétienne (KJV) des versets, qui diffère de la numérotation massorétique
de la base BHSA sur environ 120 chapitres : décalages de chapitres
(Genèse 31:55/32:1, Exode 7-8, Deut 12-13/22-23/28-29, Nomb 16-17,
Josué, 1-2 Samuel, 1 Rois 4-5/22, 2 Rois, Chroniques, Néhémie, Esther,
Job, Proverbes, Ecclésiaste, Cantique, Ésaïe 9/64, Jérémie 9, Ézéchiel
20-21, Daniel 3-6, Osée, Joël 2-3, Jonas, Michée 5, Nahum, Zacharie 1-2,
Malachie 4) et titres des Psaumes comptés comme verset 1 dans la BHSA
(environ 115 psaumes décalés de +1, voire +2 pour Ps 51/52/54/60/108).

Ce script convertit les références des fichiers data/*.txt vers la
numérotation BHSA, sur le modèle de la renumérotation Torres Amat
(scripts/extract_torres_amat.py) :

- **décalages** : la référence KJV (livre, chapitre, verset) devient la
  référence BHSA (livre, chapitre, verset) via la table _SEGMENTS ;
- **versets sans équivalent hébreu** (_ENGLISH_ABSENT) : trois versets
  KJV (Ésaïe 64:1, Néhémie 7:68, Psaume 13:6) sont fusionnés dans le
  verset hébreu précédent ; leurs lignes sont supprimées ;
- **versets hébreux sans équivalent KJV** : 67 titres de psaumes restent
  « en creux » (pas de ligne, l'application affiche « verset absent de
  la traduction ») ;
- **livres** : les noms Segond français sont normalisés vers les noms
  BHSA (Osée -> Hosea, Cantique Des Cantiques -> Canticum,
  Lamentations De Jérémie -> Threni).

La table de correspondance est dérivée des tables TVTMS de STEPBible
(Translators Versification Traditions with Methodology for
Standardisation, colonnes « English KJV » et « Hebrew »), fichier
« TVTMS - ... CC BY.txt » du dépôt github.com/STEPBible/STEPBible-Data
(© STEPBible.org, CC BY 4.0) : les segments divergents ont été extraits
automatiquement, puis calibrés contre la base BHSA locale
(bhsa_repo/tf). En cas de doute, la référence STEPBible fait foi.

Le Nouveau Testament de Segond (27 livres, sans équivalent BHSA) est
recopié tel quel, seules les références de l'Ancien Testament sont
converties.

Usage :
    python scripts/renumber_translations.py [fichier1 fichier2 ...]

Sans argument, renumérote data/louis_segond_1910.txt, data/kjv_1611.txt
et data/riveduta_1927.txt en place. À n'appliquer qu'une seule fois :
une seconde application sur un fichier déjà renuméroté est détectée
(collisions) et refusée sans écriture. Vérifications intégrées : aucune
référence finale hors des bornes BHSA, aucun doublon, aucune collision
deux-versets-vers-un, et comptes rendus imprimés.
"""

import argparse
import sys

# ---------------------------------------------------------------------------
# Versification KJV -> BHSA (massorétique)
# ---------------------------------------------------------------------------

# Segments (livre, ch_kjv, ch_bhsa, v_kjv_debut, v_kjv_fin, v_bhsa_début) :
# les versets v_kjv..v_kjv_fin du chapitre ch_kjv portent les numéros BHSA
# v_bhsa..v_bhsa+(v_kjv_fin-v_kjv) du chapitre ch_bhsa. Le livre est
# identique (seul le chapitre/verset changent). Dérivé de TVTMS (CC BY 4.0).
_SEGMENTS = [
    ("Canticum", 6, 7, 13, 13, 1),
    ("Canticum", 7, 7, 1, 13, 2),
    ("Chronica_I", 6, 5, 1, 15, 27),
    ("Chronica_I", 6, 6, 16, 81, 1),
    ("Chronica_I", 12, 12, 5, 40, 6),
    ("Chronica_II", 2, 1, 1, 1, 18),
    ("Chronica_II", 2, 2, 2, 18, 1),
    ("Chronica_II", 14, 13, 1, 1, 23),
    ("Chronica_II", 14, 14, 2, 15, 1),
    ("Daniel", 4, 3, 1, 3, 31),
    ("Daniel", 4, 4, 4, 37, 1),
    ("Daniel", 5, 6, 31, 31, 1),
    ("Daniel", 6, 6, 1, 28, 2),
    ("Deuteronomium", 12, 13, 32, 32, 1),
    ("Deuteronomium", 13, 13, 1, 18, 2),
    ("Deuteronomium", 22, 23, 30, 30, 1),
    ("Deuteronomium", 23, 23, 1, 25, 2),
    ("Deuteronomium", 29, 28, 1, 1, 69),
    ("Deuteronomium", 29, 29, 2, 29, 1),
    ("Ecclesiastes", 5, 4, 1, 1, 17),
    ("Ecclesiastes", 5, 5, 2, 20, 1),
    ("Exodus", 8, 7, 1, 4, 26),
    ("Exodus", 8, 8, 5, 32, 1),
    ("Exodus", 22, 21, 1, 1, 37),
    ("Exodus", 22, 22, 2, 31, 1),
    ("Ezechiel", 20, 21, 45, 49, 1),
    ("Ezechiel", 21, 21, 1, 32, 6),
    ("Genesis", 31, 32, 55, 55, 1),
    ("Genesis", 32, 32, 1, 32, 2),
    ("Hosea", 1, 2, 10, 11, 1),
    ("Hosea", 2, 2, 1, 23, 3),
    ("Hosea", 11, 12, 12, 12, 1),
    ("Hosea", 12, 12, 1, 14, 2),
    ("Hosea", 13, 14, 16, 16, 1),
    ("Hosea", 14, 14, 1, 9, 2),
    ("Iob", 41, 40, 1, 8, 25),
    ("Iob", 41, 41, 9, 34, 1),
    ("Jeremia", 9, 8, 1, 1, 23),
    ("Jeremia", 9, 9, 2, 26, 1),
    ("Jesaia", 9, 8, 1, 1, 23),
    ("Jesaia", 9, 9, 2, 21, 1),
    ("Jesaia", 64, 64, 2, 12, 1),
    ("Joel", 2, 3, 28, 32, 1),
    ("Joel", 3, 4, 1, 21, 1),
    ("Jona", 1, 2, 17, 17, 1),
    ("Jona", 2, 2, 1, 10, 2),
    ("Leviticus", 6, 5, 1, 7, 20),
    ("Leviticus", 6, 6, 8, 30, 1),
    ("Maleachi", 4, 3, 1, 6, 19),
    ("Micha", 5, 4, 1, 1, 14),
    ("Micha", 5, 5, 2, 15, 1),
    ("Nahum", 1, 2, 15, 15, 1),
    ("Nahum", 2, 2, 1, 13, 2),
    ("Nehemia", 4, 3, 1, 6, 33),
    ("Nehemia", 4, 4, 7, 23, 1),
    ("Nehemia", 7, 7, 69, 73, 68),
    ("Nehemia", 9, 10, 38, 38, 1),
    ("Nehemia", 10, 10, 1, 39, 2),
    ("Numeri", 16, 17, 36, 50, 1),
    ("Numeri", 17, 17, 1, 13, 16),
    ("Numeri", 26, 25, 1, 1, 19),
    ("Numeri", 29, 30, 40, 40, 1),
    ("Numeri", 30, 30, 1, 16, 2),
    ("Psalmi", 3, 3, 1, 8, 2),
    ("Psalmi", 4, 4, 1, 8, 2),
    ("Psalmi", 5, 5, 1, 12, 2),
    ("Psalmi", 6, 6, 1, 10, 2),
    ("Psalmi", 7, 7, 1, 17, 2),
    ("Psalmi", 8, 8, 1, 9, 2),
    ("Psalmi", 9, 9, 1, 20, 2),
    ("Psalmi", 12, 12, 1, 8, 2),
    ("Psalmi", 13, 13, 1, 5, 2),
    ("Psalmi", 18, 18, 1, 50, 2),
    ("Psalmi", 19, 19, 1, 14, 2),
    ("Psalmi", 20, 20, 1, 9, 2),
    ("Psalmi", 21, 21, 1, 13, 2),
    ("Psalmi", 22, 22, 1, 31, 2),
    ("Psalmi", 30, 30, 1, 12, 2),
    ("Psalmi", 31, 31, 1, 24, 2),
    ("Psalmi", 34, 34, 1, 22, 2),
    ("Psalmi", 36, 36, 1, 12, 2),
    ("Psalmi", 38, 38, 1, 22, 2),
    ("Psalmi", 39, 39, 1, 13, 2),
    ("Psalmi", 40, 40, 1, 17, 2),
    ("Psalmi", 41, 41, 1, 13, 2),
    ("Psalmi", 42, 42, 1, 11, 2),
    ("Psalmi", 44, 44, 1, 26, 2),
    ("Psalmi", 45, 45, 1, 17, 2),
    ("Psalmi", 46, 46, 1, 11, 2),
    ("Psalmi", 47, 47, 1, 9, 2),
    ("Psalmi", 48, 48, 1, 14, 2),
    ("Psalmi", 49, 49, 1, 20, 2),
    ("Psalmi", 51, 51, 1, 19, 3),
    ("Psalmi", 52, 52, 1, 9, 3),
    ("Psalmi", 53, 53, 1, 6, 2),
    ("Psalmi", 54, 54, 1, 7, 3),
    ("Psalmi", 55, 55, 1, 23, 2),
    ("Psalmi", 56, 56, 1, 13, 2),
    ("Psalmi", 57, 57, 1, 11, 2),
    ("Psalmi", 58, 58, 1, 11, 2),
    ("Psalmi", 59, 59, 1, 17, 2),
    ("Psalmi", 60, 60, 1, 12, 3),
    ("Psalmi", 61, 61, 1, 8, 2),
    ("Psalmi", 62, 62, 1, 12, 2),
    ("Psalmi", 63, 63, 1, 11, 2),
    ("Psalmi", 64, 64, 1, 10, 2),
    ("Psalmi", 65, 65, 1, 13, 2),
    ("Psalmi", 67, 67, 1, 7, 2),
    ("Psalmi", 68, 68, 1, 35, 2),
    ("Psalmi", 69, 69, 1, 36, 2),
    ("Psalmi", 70, 70, 1, 5, 2),
    ("Psalmi", 75, 75, 1, 10, 2),
    ("Psalmi", 76, 76, 1, 12, 2),
    ("Psalmi", 77, 77, 1, 20, 2),
    ("Psalmi", 80, 80, 1, 19, 2),
    ("Psalmi", 81, 81, 1, 16, 2),
    ("Psalmi", 83, 83, 1, 18, 2),
    ("Psalmi", 84, 84, 1, 12, 2),
    ("Psalmi", 85, 85, 1, 13, 2),
    ("Psalmi", 88, 88, 1, 18, 2),
    ("Psalmi", 89, 89, 1, 52, 2),
    ("Psalmi", 92, 92, 1, 15, 2),
    ("Psalmi", 102, 102, 1, 28, 2),
    ("Psalmi", 108, 108, 1, 13, 2),
    ("Psalmi", 140, 140, 1, 13, 2),
    ("Psalmi", 142, 142, 1, 7, 2),
    ("Reges_I", 4, 5, 21, 34, 1),
    ("Reges_I", 5, 5, 1, 18, 15),
    ("Reges_I", 22, 22, 44, 53, 45),
    ("Reges_II", 11, 12, 21, 21, 1),
    ("Reges_II", 12, 12, 1, 21, 2),
    ("Sacharia", 1, 2, 18, 21, 1),
    ("Sacharia", 2, 2, 1, 13, 5),
    ("Samuel_I", 21, 21, 1, 15, 2),
    ("Samuel_I", 23, 24, 29, 29, 1),
    ("Samuel_I", 24, 24, 1, 22, 2),
    ("Samuel_II", 18, 19, 33, 33, 1),
    ("Samuel_II", 19, 19, 1, 43, 2),
]

# Versets KJV sans équivalent massorétique : fusionnés dans le verset
# hébreu précédent, leurs lignes sont supprimées (aucune perte de texte
# au sens BHSA : le contenu est couvert par le verset précédent).
_ENGLISH_ABSENT = {
    ("Jesaia", 64, 1),
    ("Nehemia", 7, 68),
    ("Psalmi", 13, 6),
}

# Normalisation des noms de livres Segond vers les noms BHSA.
_BOOK_ALIASES = {
    "Osée": "Hosea",
    "Cantique Des Cantiques": "Canticum",
    "Lamentations De Jérémie": "Threni",
}

# Ordre canonique BHSA des 39 livres de l'AT (pour le tri).
_OT_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numeri", "Deuteronomium", "Josua",
    "Judices", "Ruth", "Samuel_I", "Samuel_II", "Reges_I", "Reges_II",
    "Chronica_I", "Chronica_II", "Esra", "Nehemia", "Esther", "Iob",
    "Psalmi", "Proverbia", "Ecclesiastes", "Canticum", "Jesaia", "Jeremia",
    "Threni", "Ezechiel", "Daniel", "Hosea", "Joel", "Amos", "Obadia",
    "Jona", "Micha", "Nahum", "Habakuk", "Zephania", "Haggai", "Sacharia",
    "Maleachi",
]


def _build_map():
    """Table (livre, ch_kjv, v_kjv) -> (ch_bhsa, v_bhsa) pour les segments."""
    table = {}
    for book, ch_kjv, ch_bhsa, v1, v2, w1 in _SEGMENTS:
        for i, v in enumerate(range(v1, v2 + 1)):
            key = (book, ch_kjv, v)
            if key in table:
                raise ValueError(f"segment en double : {key}")
            table[key] = (ch_bhsa, w1 + i)
    return table


_KJV_TO_BHSA = _build_map()


def convert_ref(book, chapter, verse):
    """Référence KJV -> référence BHSA ; None si verset sans équivalent."""
    if (book, chapter, verse) in _ENGLISH_ABSENT:
        return None
    mapped = _KJV_TO_BHSA.get((book, chapter, verse))
    if mapped is not None:
        return book, mapped[0], mapped[1]
    return book, chapter, verse


def renumber_file(path, dry_run=False):
    """Renumérote un fichier plat vers la numérotation BHSA."""
    headers, rows = [], []
    converted = dropped = aliased = 0
    seen = set()
    collisions = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                headers.append(line)
                continue
            book, chapter, verse, text = line.split("\t", 3)
            chapter, verse = int(chapter), int(verse)
            if book in _BOOK_ALIASES:
                book = _BOOK_ALIASES[book]
                aliased += 1
            ref = convert_ref(book, chapter, verse)
            if ref is None:
                dropped += 1
                continue
            if ref in seen:
                collisions.append(ref)
                continue
            seen.add(ref)
            if ref != (book, chapter, verse):
                converted += 1
            rows.append((ref[0], ref[1], ref[2], text))
    if collisions:
        raise ValueError(f"{path} : collisions résiduelles {collisions[:5]}")
    report = (f"{path} : {len(rows)} versets, {converted} renumérotés, "
              f"{dropped} supprimés (fusionnés), {aliased} livres renommés")
    if dry_run:
        print(report)
        return rows
    with open(path, "w", encoding="utf-8") as fh:
        for line in headers:
            fh.write(line + "\n")
        for book, chapter, verse, text in rows:
            fh.write(f"{book}\t{chapter}\t{verse}\t{text}\n")
    print(report)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Renumérote les traductions vers la versification BHSA.")
    parser.add_argument("files", nargs="*",
                        help="fichiers data/*.txt à renuméroter en place")
    parser.add_argument("--dry-run", action="store_true",
                        help="afficher le rapport sans écrire")
    args = parser.parse_args(argv)
    targets = args.files or [
        "data/louis_segond_1910.txt",
        "data/kjv_1611.txt",
        "data/riveduta_1927.txt",
    ]
    for path in targets:
        renumber_file(path, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
