#!/usr/bin/env python3
"""Enrichissement des sens par binyan via l'API Sefaria.

Sefaria ne fournit pas de lexique hébreu→français (les lexiques BDB,
Jastrow, Klein… y sont en anglais ou en hébreu). La seule ressource
française exploitable est la **Bible du Rabbinat 1899** (domaine public),
version Sefaria « Bible du Rabbinat 1899 [fr] ».

Ce script fait le pont entre la base BHSA (occurrences morphologiques)
et cette traduction française :

  1. pour chaque racine du lexique ``binyan_senses_fr_en.json`` dont les
     sens FR ne sont pas encore traduits, il collecte les occurrences
     verbales BHSA groupées par binyan (code ``vs``) ;
  2. pour chaque occurrence, il récupère le verset français de la Bible
     du Rabbinat 1899 via ``bhsa_grammar.sefaria_client`` (cache disque :
     un seul appel réseau par chapitre) ;
  3. il produit un rapport de curation textuel : racine, gloses EN du
     lexique, et pour chaque binyan les versets français d'occurrence.

Le rapport sert d'appui à la traduction manuelle des sens FR, qui est
ensuite fusionnée dans le JSON (jamais d'écrasement des FR existants).

Usage :
    python scripts/enrich_binyan_senses_fr.py [racines...] [--limit N]
        [--report CHEMIN] [--json-out CHEMIN]

Sans argument racine, traite les racines sans FR triées par fréquence
d'occurrence BHSA décroissante (les plus fréquentes d'abord).

Exemples :
    python scripts/enrich_binyan_senses_fr.py --limit 30
    python scripts/enrich_binyan_senses_fr.py נכה צוה גדל
"""

import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from bhsa_grammar.loader import load_corpus  # noqa: E402
from bhsa_grammar.sefaria_client import fetch_chapter_verses_fr  # noqa: E402

SENSES_PATH = os.path.join(HERE, "bhsa_grammar", "binyan_senses_fr_en.json")

# Nombre de versets d'exemple maximum par binyan dans le rapport.
MAX_VERSES_PER_BINYAN = 3

# Ordre pédagogique des binyanim (celui de binyan_gen.BINYANIM).
BINYAN_ORDER = ("qal", "nif", "piel", "pual", "hit", "hif", "hof")

# Libellé complet de chaque binyan pour l'indicateur de progression.
BINYAN_LABELS = {
    "qal": "qal (paal)", "nif": "nifal", "piel": "piel",
    "pual": "pual", "hit": "hitpael", "hif": "hifil",
    "hof": "hofal",
}

# Translitération consonantique hébreu → latin (style BDB, ASCII).
# Le shin pointé שׁ devient "sh", le sin שׂ devient "s" ; les lettres
# gutturales א/ע sont notées ' et ` pour rester distinguables.
TRANSLIT = {
    "א": "'", "ב": "b", "ג": "g", "ד": "d", "ה": "h", "ו": "w",
    "ז": "z", "ח": "ch", "ט": "t", "י": "y", "כ": "k", "ל": "l",
    "מ": "m", "נ": "n", "ס": "s", "ע": "`", "פ": "p", "צ": "ts",
    "ק": "q", "ר": "r", "ת": "t",
    "ך": "k", "ם": "m", "ן": "n", "ף": "p", "ץ": "ts",
    "שׁ": "sh", "שׂ": "s", "ש": "sh",
}


def transliterate(root):
    """Translittère une racine hébraïque en lettres latines (BDB-like).

    Le shin/sin est un pointé à deux graphèmes (ש + שׂ/שׁ) : on le
    consomme en priorité avant la lettre seule, pour distinguer
    שׁ « sh » (garder) de שׂ « s » (empoisonner).
    """
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

# Seuls les 7 binyanim hébreux sont dans le périmètre ; les stems
# araméens (peal, pael…) et formes rares sont écartés par le filtre
# d'appartenance à BINYAN_ORDER ci-dessous.


def _root_letters(s):
    """Extrait les lettres radicales d'un lemme pointé (cf. binyan_gen)."""
    out = []
    for ch in s or "":
        o = ord(ch)
        if 0x05D0 <= o <= 0x05EA:
            out.append(ch)
        elif ch in ("\u05C1", "\u05C2") and out and out[-1] == "\u05E9":
            out[-1] += ch
    return out


def load_senses():
    with open(SENSES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def root_occurrences(F, T):
    """{(racine): {code binyan: [(livre, chap, vers, glose EN)]}}.

    Les features ``chapter``/``verse`` ne sont définies que sur les
    nœuds de section (book/chapter/verse) ; la référence du verset
    s'obtient via ``T.sectionFromNode`` depuis chaque mot verbal.
    """
    occ = collections.defaultdict(lambda: collections.defaultdict(list))
    for w in F.otype.s("word"):
        if F.sp.v(w) != "verb" or F.language.v(w) != "Hebrew":
            continue
        letters = _root_letters(F.lex_utf8.v(w))
        if len(letters) != 3:
            continue
        vs = F.vs.v(w)
        if vs not in BINYAN_ORDER:
            continue
        book, chapter, verse = T.sectionFromNode(w)
        root = "".join(letters)
        occ[root][vs].append((book, chapter, verse,
                              F.gloss.v(w) or ""))
    return occ


def has_fr(entry):
    """Vrai si au moins un sens de la racine a un FR non vide."""
    return any(s and s[0].strip() for s in entry.values())


def build_report(senses, occurrences, roots, progress=None):
    """Construit le rapport de curation pour les racines demandées.

    ``progress`` : callback (index, total, racine, translitération, binyan,
    nb de versets affichés) appelé pour chaque binyan traité ; utilisé pour
    l'indicateur de progression (racine + translitération + binyan).
    """
    lines = []
    chapter_cache = {}

    def verse_text(book, chapter, verse):
        key = (book, chapter)
        if key not in chapter_cache:
            chapter_cache[key] = fetch_chapter_verses_fr(book, chapter)
        verses = chapter_cache[key] or []
        if 1 <= verse <= len(verses):
            return verses[verse - 1]
        return None

    total = len(roots)
    for idx, root in enumerate(roots, start=1):
        entry = senses.get(root)
        if entry is None:
            lines.append(f"### {root} : racine absente du lexique\n")
            continue
        lines.append(f"## {root}")
        if has_fr(entry):
            lines.append("(déjà traduite — contexte uniquement)\n")
        for vs in BINYAN_ORDER:
            en = entry.get(vs) or [None, None]
            en_sense = en[1] if len(en) > 1 else None
            if not en_sense:
                continue
            lines.append(f"  [{vs}] EN : {en_sense}")
            verses = occurrences.get(root, {}).get(vs) or []
            shown = 0
            for book, chapter, verse, gloss in verses:
                if shown >= MAX_VERSES_PER_BINYAN:
                    break
                text = verse_text(book, chapter, verse)
                if text:
                    ref = f"{book} {chapter}:{verse}"
                    lines.append(f"      {ref} — {text}")
                    shown += 1
            if progress:
                progress(idx, total, root, transliterate(root),
                         BINYAN_LABELS[vs], shown)
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Rapport de curation FR : occurrences BHSA des racines "
                    "du lexique de sens, mises en regard des versets "
                    "français (Bible du Rabbinat 1899, Sefaria).")
    ap.add_argument("roots", nargs="*",
                    help="Racines à traiter (hébreu). Par défaut : toutes "
                         "celles sans FR, par fréquence décroissante.")
    ap.add_argument("--limit", type=int, default=30,
                    help="Nombre de racines sans FR à traiter (défaut 30).")
    ap.add_argument("--report", default=None,
                    help="Fichier de sortie du rapport (défaut : stdout).")
    ap.add_argument("--json-out", default=None,
                    help="Écrit aussi les versets collectés en JSON "
                         "(debug / inspection).")
    args = ap.parse_args(argv)

    api = load_corpus()
    F, T = api.F, api.T

    print("Collecte des occurrences BHSA…", file=sys.stderr)
    occurrences = root_occurrences(F, T)

    senses = load_senses()
    if args.roots:
        roots = args.roots
    else:
        freq = collections.Counter()
        for root, byvs in occurrences.items():
            freq[root] = sum(len(v) for v in byvs.values())
        candidates = [r for r in senses
                       if not has_fr(senses[r]) and r in occurrences]
        candidates.sort(key=lambda r: -freq[r])
        roots = candidates[: args.limit]

    print(f"Racines à traiter : {len(roots)}", file=sys.stderr)

    def progress(idx, total, root, translit, binyan, shown):
        print(f"[{idx}/{total}] {root} ({translit}) — {binyan} : "
              f"{shown} verset(s)", file=sys.stderr, flush=True)

    report = build_report(senses, occurrences, roots, progress=progress)

    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"Rapport écrit : {args.report}", file=sys.stderr)
    else:
        print(report)

    if args.json_out:
        payload = {}
        for root in roots:
            byvs = occurrences.get(root, {})
            payload[root] = {
                vs: [
                    {"ref": f"{b} {c}:{v}", "verse_fr": None, "gloss": g}
                    for b, c, v, g in byvs.get(vs, [])
                ]
                for vs in BINYAN_ORDER if byvs.get(vs)
            }
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
        print(f"JSON écrit : {args.json_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
