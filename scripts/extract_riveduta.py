#!/usr/bin/env python3
"""Extrait la traduction italienne Riveduta (Luzzi 1927) d'un fichier OSIS.

La Bibbia Riveduta (Giovanni Luzzi, 1861-1927, public domain) est la
révision protestante italienne de la Diodati, publiée en 1924-1927. Sa
particularité, précisée dans les notes de l'éditeur (laparola.net), est de
distinguer explicitement le rendu du tétragramme YHWH (« l'Eterno ») de
celui d'Adonaï (« Signore ») — contrairement à la Diodati 1649, qui
traduit les deux par « il Signore ».

Source : seven1m/open-bibles, fichier ``ita-riveduta.osis.xml``
(Public Domain, OSIS). Ce script produit ``data/riveduta_1927.txt``
au format plat du projet :

    <nom BHSA>\t<chapitre>\t<verset>\t<texte italien>

La numérotation du fichier OSIS est déjà massorétique (BHS) ; aucun
remappage de versification n'est nécessaire, contrairement à la Torres
Amat (Vulgate). Le fichier source contient des reliquats d'encodage
CP1252 (apostrophes U+0092, points de suspension U+0085) : ils sont
normalisés en caractères Unicode corrects.

L'application n'analyse que l'Ancien Testament hébreu (base BHSA) ;
seuls les 39 livres protocanoniques de l'AT sont donc écrits.

Usage :
    python scripts/extract_riveduta.py <chemin ita-riveduta.osis.xml> [--out data/riveduta_1927.txt]
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET

OSIS_NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"

# OSIS -> nom BHSA (39 livres protocanoniques de l'AT).
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

# Reliquats CP1252 du fichier source -> Unicode.
_FIX_CHARS = {
    "\u0092": "'",
}


def _clean(text):
    for bad, good in _FIX_CHARS.items():
        text = text.replace(bad, good)
    return " ".join(text.split()).replace("\t", " ").strip()


def extract(src_path, out_path):
    root = ET.parse(src_path).getroot()
    count = 0
    lines = []
    for div in root.iter(OSIS_NS + "div"):
        if div.get("type") != "book":
            continue
        osis_book = div.get("osisID")
        bhsa_book = _BOOK_MAP.get(osis_book)
        if not bhsa_book:
            continue
        for chapter in div.iter(OSIS_NS + "chapter"):
            osis_id = chapter.get("osisID", "")
            try:
                chap = int(osis_id.split(".")[1])
            except (IndexError, ValueError):
                continue
            for verse in chapter.iter(OSIS_NS + "verse"):
                vid = verse.get("osisID", "")
                try:
                    num = int(vid.rsplit(".", 1)[1].split("-")[0].split(",")[0])
                except (IndexError, ValueError):
                    continue
                text = _clean("".join(verse.itertext()))
                if text:
                    lines.append(f"{bhsa_book}\t{chap}\t{num}\t{text}")
                    count += 1
    order = {name: i for i, name in enumerate(_BOOK_MAP.values())}
    lines.sort(key=lambda l: (
        order.get(l.split("\t")[0], 999),
        int(l.split("\t")[1]), int(l.split("\t")[2])))
    header = (
        "# Riveduta (Luzzi) 1927 — public domain (texte intégral de l'Ancien Testament).\n"
        "# La Bibbia versione Riveduta, révision de la Diodati par Giovanni Luzzi (1861-1927),\n"
        "# publiée 1924-1927 ; Riveduta traduit YHWH par « l'Eterno » et Adonaï par « Signore ».\n"
        "# Source : seven1m/open-bibles, fichier ita-riveduta.osis.xml (Public Domain, OSIS).\n"
        "# Format : nom_BHSA\tchapitre\tverset\ttexte_italien\n"
    )
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(header)
        fh.write("\n".join(lines))
        fh.write("\n")
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", help="chemin du fichier ita-riveduta.osis.xml")
    ap.add_argument("--out", default="data/riveduta_1927.txt")
    args = ap.parse_args()
    n = extract(args.src, args.out)
    print(f"{n} versets écrits dans {args.out}")


if __name__ == "__main__":
    sys.exit(main())
