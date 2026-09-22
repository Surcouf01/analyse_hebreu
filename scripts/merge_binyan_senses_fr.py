#!/usr/bin/env python3
"""Fusionne une curation manuelle de sens FR dans binyan_senses_fr_en.json.

Ce script est le dernier maillon du workflow d'enrichissement (cf.
``enrich_binyan_senses_fr.py`` pour la production du rapport qui sert
de support à la traduction) :

  1. ``python scripts/enrich_binyan_senses_fr.py --limit 40 --report rapport.txt``
     → rapport : sens BDB anglais + versets français d'occurrence, par
     racine et par binyan ;
  2. traduction manuelle : on rédige les sens français à partir du
     rapport (aucun lexique hébreu→français n'existe sur Sefaria, la
     curation ne peut pas être devinée automatiquement) ;
  3. ``python scripts/merge_binyan_senses_fr.py curation.json``
     → fusion dans le lexique du paquet.

Format du fichier de curation (JSON, un objet par racine) ::

    {
      "נכה": {
        "qal":  ["frapper, blesser", "smite, strike"],
        "nif":  ["être frappé"],
        "pual": ["être abattu"]
      },
      ...
    }

Règles :
  - chaque cellule est une paire ``[fr, en]`` ; le second élément est
    optionnel (EN inchangé s'il est absent ou null) ;
  - un FR non vide dans le lexique n'est JAMAIS écrasé (le fichier de
    curation ne remplit que les cellules vides) ; ``--force`` annule
    cette protection ;
  - l'EN n'est remplacé que si une valeur EN explicite est fournie
    (correction ponctuelle d'un bruit d'extraction BDB) ;
  - une racine/binyan absent du lexique est créé.

Usage :
    python scripts/merge_binyan_senses_fr.py curation.json [--force] [--dry-run]
    python scripts/merge_binyan_senses_fr.py --check curation.json
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SENSES_PATH = os.path.join(HERE, "bhsa_grammar", "binyan_senses_fr_en.json")

BINYAN_ORDER = ("qal", "nif", "piel", "pual", "hit", "hif", "hof")

# Translitération consonantique hébreu → latin (style BDB), pour les
# messages du script (cf. enrich_binyan_senses_fr.transliterate).
TRANSLIT = {
    "א": "'", "ב": "b", "ג": "g", "ד": "d", "ה": "h", "ו": "w",
    "ז": "z", "ח": "ch", "ט": "t", "י": "y", "כ": "k", "ל": "l",
    "מ": "m", "נ": "n", "ס": "s", "ע": "`", "פ": "p", "צ": "ts",
    "ק": "q", "ר": "r", "ת": "t",
    "ך": "k", "ם": "m", "ן": "n", "ף": "p", "ץ": "ts",
    "שׁ": "sh", "שׂ": "s", "ש": "sh",
}


def transliterate(root):
    out = []
    s = root or ""
    i = 0
    while i < len(s):
        pair = s[i:i + 2]
        if pair in TRANSLIT:
            out.append(TRANSLIT[pair])
            i += 2
            continue
        out.append(TRANSLIT.get(s[i], s[i]))
        i += 1
    return "".join(out)


def load_senses(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_senses(data, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def merge(data, curated, force=False):
    """Fusionne ``curated`` dans ``data`` ; renvoie les statistiques.

    Un FR non vide dans le lexique n'est jamais écrasé (protection de
    la curation existante), sauf avec ``force=True`` ; l'EN n'est
    remplacé que si une valeur explicite est fournie.
    """
    added_fr = kept_fr = replaced_en = created_cells = 0
    for root, byvs in curated.items():
        if not isinstance(byvs, dict):
            print(f"⚠ {root} : format invalide (attendu un objet "
                  "par binyan), ignoré", file=sys.stderr)
            continue
        entry = data.setdefault(root, {})
        for vs, cells in byvs.items():
            if vs not in BINYAN_ORDER:
                print(f"⚠ {root} ({transliterate(root)}) : binyan "
                      f"inconnu « {vs} », ignoré", file=sys.stderr)
                continue
            if not isinstance(cells, (list, tuple)) or not cells:
                print(f"⚠ {root} ({transliterate(root)}) [{vs}] : "
                      "valeur invalide (attendu [fr] ou [fr, en])",
                      file=sys.stderr)
                continue
            fr = (cells[0] or "").strip()
            en = (cells[1] or "").strip() if len(cells) > 1 else ""
            cur = entry.get(vs)
            if cur is None:
                cur = ["", ""]
                created_cells += 1
            while len(cur) < 2:
                cur.append("")
            cur_fr = (cur[0] or "").strip()
            if fr and (not cur_fr or force):
                cur[0] = fr
                if not cur_fr:
                    added_fr += 1
            elif fr and cur_fr:
                kept_fr += 1
            if en and (cur[1] or "").strip() != en:
                cur[1] = en
                replaced_en += 1
            entry[vs] = cur
    return added_fr, kept_fr, replaced_en, created_cells


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Fusionne une curation FR (JSON) dans "
                    "binyan_senses_fr_en.json sans écraser les FR "
                    "existants (sauf --force).")
    ap.add_argument("curation", help="Fichier JSON de curation "
                                     "(cf. docstring du script).")
    ap.add_argument("--force", action="store_true",
                    help="Écrase aussi les FR déjà traduits.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Affiche le résultat sans écrire le lexique.")
    ap.add_argument("--check", action="store_true",
                    help="Vérifie seulement la validité du fichier de "
                         "curation (aucune écriture).")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.curation):
        print(f"Fichier introuvable : {args.curation}", file=sys.stderr)
        return 2
    try:
        curated = load_senses(args.curation)
    except ValueError as exc:
        print(f"JSON invalide : {exc}", file=sys.stderr)
        return 2
    if not isinstance(curated, dict):
        print("Le fichier de curation doit être un objet "
              "{racine: {binyan: [fr, en]}}", file=sys.stderr)
        return 2

    data = load_senses(SENSES_PATH)
    before = sum(1 for e in data.values() for s in e.values()
                 if s and s[0].strip())

    if args.check:
        added, kept, en_fix, created = merge(json.loads(json.dumps(data)),
                                             curated, force=True)
        print(f"Curation valide : {len(curated)} racines, "
              f"{sum(len(v) for v in curated.values())} cellules.")
        print(f"FR ajoutés : {added} ; FR existants écrasés (--check) : "
              f"{kept} ; EN corrigés : {en_fix} ; "
              f"nouvelles cellules : {created}")
        return 0

    added, kept, en_fix, created = merge(data, curated, force=args.force)

    if args.dry_run:
        print(f"[dry-run] FR ajoutés : {added} ; FR existants conservés : "
              f"{kept} ; EN corrigés : {en_fix} ; "
              f"nouvelles cellules : {created}")
        return 0

    save_senses(data, SENSES_PATH)
    after = sum(1 for e in data.values() for s in e.values()
                if s and s[0].strip())
    print(f"Lexique mis à jour : {SENSES_PATH}")
    print(f"  FR ajoutés : {added} ; FR existants conservés : {kept} ; "
          f"EN corrigés : {en_fix} ; nouvelles cellules : {created}")
    print(f"  Sens FR total : {before} → {after}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
