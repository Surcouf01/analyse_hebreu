#!/usr/bin/env python3
"""Extraction des binyanim attestés en hébreu moderne, par racine.

Télécharge le dictionnaire d'hébreu moderne Pealim
(https://www.pealim.com — conjugaisons vocalisées, domaine public,
liste paginée « /dict/?pos=verb » : une requête par page, avec cache
disque), puis relève pour chaque verbe sa racine et son binyan
(libellés pa'al, nif'al, pi'el, pu'al, huf'al, hif'il, hitpa'el).

Contrairement à la Mishna (cf. extract_mishnah_binyanim.py), la
distinction Bible/hébreu moderne ne passe pas par la comparaison de
formes vocalisées : Pealim donne directement la racine et le binyan de
chaque verbe moderne. Le fichier de sortie garde donc TOUS les
binyanim modernes de chaque racine, bibliques compris (le mode
binyanim croise ensuite avec le champ ``exists`` de la BHSA pour
colorer les binyanim modernes non bibliques).

Sortie : ``bhsa_grammar/modern_binyanim.json`` au format
    { "<racine h\u00e9breu>": { "<code>": {"lemma": "לְשַׁמֵּר",
                                     "gloss": "to guard"},
                          ... }, ... }
où les codes sont ceux du projet (qal, nif, piel, pual, hit, hif, hof)
et ne figurent que les racines trilitaires.

Usage :
    python scripts/extract_modern_binyanim.py [--out FICHIER]
        [--pages N] [--offline] [--force]

Le script n'écrase jamais un fichier existant sans --force (les
curations manuelles doivent être préservées).
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_URL = "https://www.pealim.com/dict/?pos=verb"
USER_AGENT = "analyse-hebreu/1.0"

# Libellés Pealim -> codes du projet.
BINYAN_MAP = {
    "pa'al": "qal",
    "nif'al": "nif",
    "pi'el": "piel",
    "pu'al": "pual",
    "huf'al": "hof",
    "hif'il": "hif",
    "hitpa'el": "hit",
}

NIKKUD_RE = re.compile(r"[\u0591-\u05C7]")

# Une rangée du dictionnaire : lemme (avec nikkud), lien, racine,
# partie du discours (« Verb \u2013 <i>pa'al</i> »), sens anglais.
ROW_RE = re.compile(
    r'<a href="(/dict/[0-9]+[^"]*)">\s*<span class="menukad">([^<]+)</span>'
    r'.*?<td><a href="/dict/\?[^"]*">([^<]+)</a></td>'
    r'<td>Verb \u2013 <i>([a-z\'\u2019]+)</i></td>'
    r'<td class="dict-meaning">([^<]*)</td>',
    re.S,
)


def root_consonants(root_cell):
    """Consonnes radicales (nikkud et points de shin retirés)."""
    return NIKKUD_RE.sub("", root_cell or "").replace(" ", "").replace("-", "")


def fetch_page(page, cache_dir, offline=False):
    """Télécharge une page du dictionnaire Pealim, avec cache disque."""
    import hashlib
    import tempfile
    cache_dir = cache_dir or os.path.join(tempfile.gettempdir(),
                                          "analyse_hebreu_pealim")
    key = hashlib.sha1(f"pos=verb|page={page}".encode("utf-8")).hexdigest()[:16]
    cache = os.path.join(cache_dir, f"pealim_verbs_{key}.html")
    if os.path.isfile(cache):
        with open(cache, encoding="utf-8") as fh:
            return fh.read()
    if offline:
        return None
    url = BASE_URL + urllib.parse.quote(f"&page={page}", safe="&=")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8")
    os.makedirs(cache_dir, exist_ok=True)
    with open(cache, "w", encoding="utf-8") as fh:
        fh.write(html)
    return html


def iter_verb_rows(html):
    """Rangées de verbes d'une page : (lien, lemme, racine, binyan, sens)."""
    for m in ROW_RE.finditer(html or ""):
        yield m.groups()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "bhsa_grammar", "modern_binyanim.json"))
    ap.add_argument("--pages", type=int, default=0,
                    help="Limite le nombre de pages (debug ; 0 = toutes).")
    ap.add_argument("--cache-dir", default=None,
                    help="Dossier de cache des pages téléchargées.")
    ap.add_argument("--offline", action="store_true",
                    help="Utilise uniquement le cache disque local.")
    ap.add_argument("--force", action="store_true",
                    help="Écrase le fichier de sortie existant.")
    args = ap.parse_args()

    if os.path.exists(args.out) and not args.force:
        print(f"Le fichier {args.out} existe déjà. Utilisez --force pour "
              "le régénérer (les curations manuelles seraient perdues).",
              file=sys.stderr)
        return 1

    out = {}
    n_verbs = 0
    n_skipped = 0
    page = 1
    while True:
        if args.pages and page > args.pages:
            break
        print(f"[page {page}] {BASE_URL}&page={page} …", flush=True)
        try:
            html = fetch_page(page, args.cache_dir, offline=args.offline)
        except Exception as exc:  # noqa: BLE001
            print(f"    échec : {exc}", file=sys.stderr)
            break
        rows = list(iter_verb_rows(html))
        if not rows:
            print("    plus de verbes (fin du dictionnaire)", flush=True)
            break
        for link, lemma, root_cell, binyan_label, gloss in rows:
            code = BINYAN_MAP.get(binyan_label)
            root = root_consonants(root_cell)
            if not code or len(root) != 3:
                n_skipped += 1
                continue
            entry = out.setdefault(root, {})
            if code not in entry:
                entry[code] = {
                    "lemma": lemma.strip(),
                    "gloss": (gloss or "").strip(),
                    "url": "https://www.pealim.com" + link,
                }
                n_verbs += 1
        page += 1
        time.sleep(0.4)

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"\n{len(out)} racines, {n_verbs} verbes "
          f"({n_skipped} entrées non trilitaires ignorées) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
