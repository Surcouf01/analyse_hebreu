#!/usr/bin/env python3
"""Extraction des binyanim attestés dans la Mishna, par racine.

Télécharge la Mishna hébraïque vocalisée (« Torat Emet 357 », domaine
public) depuis l'API Sefaria (une requête par traité, avec cache disque),
isole les tokens dont la forme **vocalisée** correspond à une forme générée
par le moteur de conjugaison du projet (``binyan_gen`` — tous les gabarits
BHSA : parfait, imparfait, impératif, infinitifs, participes, y compris les
paradigmes des verbes faibles), puis retient les binyanim **mishnaïques** :
attestés dans la Mishna mais absents de la Bible hébraïque pour cette
racine.

La comparaison est vocalisée (et non consonantique) : les squelettes sans
nikkud confondent les binyanim (nif/hof, qal/piel…). La normalisation
retire les teamim et le daghesh (begadkefat), unifie hataf→voyelle pleine
et holam malé/haser, et ramène les lettres finales à leur forme médiane ;
les préfixes d'incorporation (וװ, הַ, מֵ, בְּ, כְּ, לְ, שֶׁ, et leurs
combinaisons) sont testés par retrait depuis le token.

Sortie : ``bhsa_grammar/mishnah_binyanim.json`` au format
    { "<racine hébreu>": { "<code>": ["<forme 1>", ...], ... }, ... }
où ne figurent que les binyanim non bibliques pour la racine (les binyanim
bibliques n'apportent rien au mode binyanim, qui les connaît déjà via la
BHSA et son champ ``exists``).

Usage :
    python scripts/extract_mishnah_binyanim.py [--out FICHIER]
        [--limit TRAITÉS] [--offline] [--force]

Le script n'écrase jamais un fichier existant sans --force (les
curations manuelles doivent être préservées).
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from bhsa_grammar.mishnah_catalog import SEDARIM  # noqa: E402

HE_TITLE = "Torat Emet 357"
OUT_DEFAULT = os.path.join(HERE, "bhsa_grammar", "mishnah_binyanim.json")

# ---------------------------------------------------------------------------
# Normalisation hébreu
# ---------------------------------------------------------------------------

TEAMIM = re.compile(r"[\u0591-\u05AF\u05BD\u05BF\u05C0\u05C4-\u05C7]")
END_TO_BASE = {"\u05DA": "\u05DB", "\u05DD": "\u05DE", "\u05DF": "\u05E0",
               "\u05E3": "\u05E4", "\u05E5": "\u05E6"}
VOWEL_MAP = str.maketrans({
    "\u05B1": "\u05B6",  # hataf segol -> segol
    "\u05B2": "\u05B7",  # hataf patach -> patach
    "\u05B3": "\u05B8",  # hataf qamats -> qamats
    "\u05BA": "\u05B9",  # holam haser -> holam
})


def normalize_vocal(s):
    """Forme vocalisée normalisée pour la comparaison exacte.

    Teamim retirés, hataf ramenés à leur voyelle pleine, holam malé/haser
    unifiés, daghesh retiré (spirantisation begadkefat insensible aux
    préfixes), lettres finales ramenées à leur forme médiane.
    """
    s = TEAMIM.sub("", s or "").translate(VOWEL_MAP).replace("\u05BC", "")
    return "".join(END_TO_BASE.get(c, c) for c in s)


def strip_nikud(s):
    """Retire nikkud, teamim et ta'amim d'une chaîne hébraïque."""
    return re.sub(r"[\u0591-\u05BD\u05BF\u05C0\u05C1-\u05C7]", "", s or "")


def root_letters(lex_utf8):
    """Consonnes radicales d'un lemme BHSA (forme UTF-8 sans nikkud).

    Retire les préfixes lexicaux des binyanim (ה/י/מ/נ/ת initiaux).
    """
    s = strip_nikud(lex_utf8 or "")
    while s and s[0] in "\u05D4\u05D9\u05D5\u05E0\u05EA\u05DE":
        s = s[1:]
    return s


# Préfixes d'incorporation, déjà normalisés (sans daghesh), testés par
# retrait depuis le début du token. L'ordre n'importe pas : chaque candidat
# donne lieu à une recherche indépendante dans l'index.
PREFIXES = (
    "",
    "\u05D5\u05B0",            # waw
    "\u05D4\u05B7",            # article
    "\u05D4\u05B8",
    "\u05D4\u05B6",
    "\u05DE\u05B5",            # min
    "\u05DE\u05B4",
    "\u05D1\u05B0",            # bet
    "\u05D1\u05B7",            # bet + article
    "\u05DB\u05B0",            # kaf
    "\u05DB\u05B7",
    "\u05DC\u05B0",            # lamed
    "\u05DC\u05B7",
    "\u05E9\u05C1\u05B6",      # shin
    "\u05E9\u05C1\u05B0",
    "\u05D5\u05B0\u05D4\u05B7",  # waw + article
    "\u05D5\u05B0\u05D4\u05B8",
    "\u05D5\u05B0\u05D4\u05B6",
    "\u05D5\u05B0\u05DE\u05B5",  # waw + min
    "\u05D5\u05B0\u05DE\u05B4",
    "\u05D5\u05B0\u05D1\u05B0",  # waw + bet
    "\u05D5\u05B0\u05D1\u05B7",
    "\u05D5\u05B0\u05DB\u05B0",
    "\u05D5\u05B0\u05DB\u05B7",
    "\u05D5\u05B0\u05DC\u05B0",
    "\u05D5\u05B0\u05DC\u05B7",
    "\u05D5\u05B0\u05E9\u05C1\u05B6",
)

# ---------------------------------------------------------------------------
# Formes des paradigmes générés (moteur binyan_gen)
# ---------------------------------------------------------------------------

def root_forms(code, root, category):
    """Formes vocalisées normalisées de toutes les formes d'un binyan.

    Utilise le moteur de conjugaison du projet : les gabarits extraits de
    la BHSA (``binyan_templates.json``) couvrent les verbes forts comme
    faibles, les formes finies (parfait/imparfait/impératif, toutes
    personnes) et non finies (infinitifs, participes).
    """
    from bhsa_grammar.binyan_gen import (generate_binyan_paradigm,
                                         generate_binyan_non_finite)
    out = set()
    for forms in generate_binyan_paradigm(code, root, category).values():
        for f in forms.values():
            if f:
                out.add(normalize_vocal(f))
    for f in generate_binyan_non_finite(code, root, category).values():
        if f:
            out.add(normalize_vocal(f))
    return out


def load_bhsa_roots():
    """Renvoie {racine (3 cons. hébreu): {"lex", "binyanim", "category"}}.

    Les binyanim bibliques servent à écarter du JSON final les binyanim
    déjà connus de la BHSA ; la catégorie (fort/faible) détermine le
    paradigme à générer pour comparer les formes.
    """
    from bhsa_grammar import load_corpus
    from bhsa_grammar.binyan_gen import classify_root
    api = load_corpus()
    F = api.F
    roots = {}
    for w in F.otype.s("word"):
        if F.sp.v(w) != "verb":
            continue
        lex_utf8 = F.lex_utf8.v(w) or ""
        r = root_letters(lex_utf8)
        if len(r) != 3:
            continue
        vs = F.vs.v(w)
        code = "hit" if vs in ("htpa", "htpo", "htpe") else vs
        entry = roots.setdefault(r, {"lex": F.lex.v(w) or "",
                                     "binyanim": set(),
                                     "root": tuple(r)})
        entry["binyanim"].add(code)
    for r, entry in roots.items():
        entry["category"] = classify_root(*entry["root"])
    return roots

# ---------------------------------------------------------------------------
# Téléchargement de la Mishna (une requête par traité)
# ---------------------------------------------------------------------------

def fetch_tractate(ref, cache_dir, offline=False):
    """Télécharge un traité (texte hébreu vocalisé), avec cache disque."""
    import hashlib
    import tempfile
    import urllib.parse
    import urllib.request
    cache_dir = cache_dir or os.path.join(tempfile.gettempdir(),
                                          "analyse_hebreu_mishnah")
    key = hashlib.sha1(ref.encode("utf-8")).hexdigest()[:16]
    cache = os.path.join(cache_dir, f"mishnah_{key}.json")
    if os.path.isfile(cache):
        with open(cache, encoding="utf-8") as fh:
            return json.load(fh)
    if offline:
        return None
    version = urllib.parse.quote(f"hebrew|{HE_TITLE}")
    url = (f"https://www.sefaria.org/api/v3/texts/{urllib.parse.quote(ref)}"
           f"?version={version}&return_format=text_only")
    req = urllib.request.Request(url, headers={"User-Agent": "analyse-hebreu/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    versions = data.get("versions") or []
    if not versions:
        return None
    os.makedirs(cache_dir, exist_ok=True)
    with open(cache, "w", encoding="utf-8") as fh:
        json.dump(versions[0].get("text") or [], fh, ensure_ascii=False)
    return versions[0].get("text") or []


def iter_mishnayot(tree):
    """Applatit un traité en mishnayot (chaînes hébreu vocalisé)."""
    for chap in tree or []:
        if isinstance(chap, list):
            for m in chap:
                if isinstance(m, str):
                    yield m
        elif isinstance(chap, str):
            yield chap


TOKEN_RE = re.compile(r"[\u05D0-\u05EA][\u05B0-\u05C7\u0591-\u05AF]*"
                      r"[\u05D0-\u05EA\u05B0-\u05C7\u0591-\u05AF]*")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--limit", type=int, default=0,
                    help="Limite le nombre de traités (debug).")
    ap.add_argument("--cache-dir", default=None,
                    help="Dossier de cache des traités téléchargés.")
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

    print("Chargement des racines verbales de la BHSA…", flush=True)
    bhsa_roots = load_bhsa_roots()
    print(f"  {len(bhsa_roots)} racines trilitaires", flush=True)

    # Index : forme vocalisée normalisée -> {(racine, code)}. Une même
    # forme peut appartenir à plusieurs binyanim (ambiguïté légitime,
    # tranchée par le contexte) ; on conserve tous les candidats.
    print("Génération des formes de paradigmes…", flush=True)
    index = {}
    for r, entry in bhsa_roots.items():
        root = entry["root"]
        cat = entry["category"]
        for code in ("qal", "nif", "piel", "pual", "hit", "hif", "hof"):
            for form in root_forms(code, root, cat):
                index.setdefault(form, set()).add((r, code))
    print(f"  {len(index)} formes indexées", flush=True)

    found = {}  # racine -> {code: {formes}}
    tracts = [t for _s, ts in SEDARIM for t, _fr in ts]
    if args.limit:
        tracts = tracts[:args.limit]

    for i, title in enumerate(tracts, 1):
        print(f"[{i}/{len(tracts)}] {title}…", flush=True)
        try:
            tree = fetch_tractate(title, args.cache_dir, offline=args.offline)
        except Exception as exc:  # noqa: BLE001
            print(f"    échec : {exc}", file=sys.stderr)
            continue
        if not tree:
            print("    vide ou absent", file=sys.stderr)
            continue
        n_tokens = 0
        for mishna in iter_mishnayot(tree):
            for tok in TOKEN_RE.findall(mishna):
                n_tokens += 1
                v = normalize_vocal(tok)
                for pfx in PREFIXES:
                    if not v.startswith(pfx):
                        continue
                    stem = v[len(pfx):]
                    if len(strip_nikud(stem)) < 3:
                        continue
                    hits = index.get(stem)
                    if not hits:
                        continue
                    for root, code in hits:
                        entry = found.setdefault(root, {})
                        entry.setdefault(code, set()).add(tok)
        print(f"    {n_tokens} tokens scannés", flush=True)

    # Ne garder que les binyanim NON bibliques pour chaque racine.
    out = {}
    n_new = 0
    for root, codes in sorted(found.items()):
        biblical = bhsa_roots.get(root, {}).get("binyanim", set())
        fresh = {c: sorted(forms)[:8] for c, forms in sorted(codes.items())
                 if c not in biblical and c in ("nif", "piel", "pual",
                                                "hit", "hif", "hof")}
        if fresh:
            out[root] = fresh
            n_new += sum(len(v) for v in fresh.values())
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"\n{len(out)} racines enrichies, {n_new} formes nouvelles -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
