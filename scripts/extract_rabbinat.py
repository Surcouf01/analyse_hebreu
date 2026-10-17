#!/usr/bin/env python3
"""Extrait la traduction française Bible du Rabbinat 1899 de l'API Sefaria.

La Bible du Rabbinat (« La Bible, traduite du texte original par les membres
du rabbinat français », direction Zadoc Kahn, Grand-Rabbin, A. Durlacher,
Paris, 1899-1906) est la version de référence du judaïsme francophone, dans
le domaine public. Sefaria la distribue sous le titre « Bible du Rabbinat
1899 [fr] » (source fr.wikisource.org) : c'est la version déjà utilisée par
``bhsa_grammar.sefaria_client`` pour l'enrichissement des sens par binyan.

Sa numérotation est déjà massorétique (BHS) : titres des psaumes comptés
comme verset 1, Joël et Malachie 4 chapitres, etc. Aucun remappage de
versification n'est nécessaire, contrairement à Segond/KJV/Riveduta
(chrétienne) et Torres Amat (Vulgate).

Ce script télécharge les 39 livres protocanoniques de l'AT (une requête HTTP
par livre) et produit ``data/rabbinat_1899.txt`` au format plat du projet :

    <nom BHSA>\t<chapitre>\t<verset>\t<texte français>

Les segments non-chaînés (notes de bas de page) sont ignorés, comme dans
``sefaria_client.fetch_chapter_verses_fr``.

Usage :
    python scripts/extract_rabbinat.py [--out data/rabbinat_1899.txt]
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir))

from bhsa_grammar.sefaria_client import (  # noqa: E402
    BHSA_TO_SEFARIA,
    DEFAULT_TIMEOUT,
    RABBINAT_TITLE,
    _API_BASE,
)

_HEADERS = {"User-Agent": "analyse_hebreu/1.0"}


def _fetch_book(bhsa_book, timeout):
    """Renvoie {chapitre: [versets]} pour un livre, ou None si absent."""
    sefaria_book = BHSA_TO_SEFARIA[bhsa_book]
    version = urllib.parse.quote(f"french|{RABBINAT_TITLE}")
    url = (f"{_API_BASE}{urllib.parse.quote(sefaria_book)}"
           f"?version={version}&return_format=text_only")
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    versions = data.get("versions") or []
    if not versions:
        return None
    text = versions[0].get("text")
    chapters = {}
    if isinstance(text, list) and text and isinstance(text[0], list):
        for ci, ch in enumerate(text, start=1):
            verses = [s for s in ch if isinstance(s, str) and s.strip()]
            if verses:
                chapters[ci] = verses
    elif isinstance(text, list) and text:
        verses = [s for s in text if isinstance(s, str) and s.strip()]
        if verses:
            chapters[1] = verses
    return chapters or None


def main():
    parser = argparse.ArgumentParser(
        description="Extrait la Bible du Rabbinat 1899 depuis Sefaria.")
    parser.add_argument("--out", default="data/rabbinat_1899.txt",
                        help="Fichier de sortie (défaut : data/rabbinat_1899.txt).")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help="Délai réseau par requête, en secondes.")
    args = parser.parse_args()

    lines = [
        "# Bible du Rabbinat 1899 — domaine public (texte intégral de l'Ancien Testament).",
        "# La Bible, traduite du texte original par les membres du rabbinat français",
        "# sous la direction de Zadoc Kahn, Grand-Rabbin, A. Durlacher, Paris, 1899-1906.",
        "# Source : Sefaria, version « Bible du Rabbinat 1899 [fr] » (fr.wikisource.org,",
        "# public domain). Numérotation massorétique (BHS), identique à la base BHSA.",
        "# Format : nom_BHSA\tchapitre\tverset\ttexte_français",
    ]
    n_versets = 0
    livres = 0
    echecs = []
    for bhsa_book in BHSA_TO_SEFARIA:
        for attempt in range(3):
            try:
                chapters = _fetch_book(bhsa_book, args.timeout)
                break
            except (OSError, ValueError, urllib.error.URLError) as exc:
                if attempt == 2:
                    chapters = None
                    echecs.append((bhsa_book, repr(exc)))
                else:
                    time.sleep(2 * (attempt + 1))
        if chapters is None:
            continue
        livres += 1
        for ci in sorted(chapters):
            for vi, text in enumerate(chapters[ci], start=1):
                text = " ".join(text.split()).replace("\t", " ")
                lines.append(f"{bhsa_book}\t{ci}\t{vi}\t{text}")
                n_versets += 1
        print(f"{bhsa_book}: ok")
        time.sleep(0.3)

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"\n{livres} livres, {n_versets} versets -> {args.out}")
    if echecs:
        print("Livres manquants :", ", ".join(b for b, _ in echecs), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
