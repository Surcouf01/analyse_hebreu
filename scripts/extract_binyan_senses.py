#!/usr/bin/env python3
"""Extraction des sens par binyan depuis le lexique BDB (Brown-Driver-Briggs).

Source : unabridged-BDB-Hebrew-lexicon (domaine public), version CSV
https://github.com/eliranwong/unabridged-BDB-Hebrew-lexicon
(unabridged-BDB-Hebrew-lexicon.csv.zip).

Le BDB structure chaque verbe par stem (Qal, Niph`al, Piel, Pu`al,
Hithpa`el, Hiph`il, Hoph`al) ; les sens y sont balisés <highlight>...</highlight>.
Le script produit ``bhsa_grammar/binyan_senses_fr_en.json`` :
    {"ראה": {"qal": ["voir", "see"], ...}, ...}
- clé : racine hébraïque (consonnes nues) ;
- valeur : sens anglais par binyan (le français reste à traduire/valider,
  le script reprend ceux du fichier existant s'il y en a).

Filtres de qualité :
  - ne garde que les entrées de la section BIBLICAL HEBREW ;
  - ignore les stems araméens (Peal/Pual araméens...) et les variantes
    rares (Hothpa`al -> hitpael) ;
  - pour chaque stem, garde les deux premiers sens (highlight) propres,
    en éliminant les fragments morphologiques (Perfect/Imperfect/
    Participle...), les références bibliques, les gloses contextuelles
    et les formes archaïques (and he, thou...).

Usage :
    python scripts/extract_binyan_senses.py /chemin/vers/unabridged-BDB-Hebrew-lexicon.csv
"""
import csv
import html
import json
import os
import re
import sys
import unicodedata

csv.field_size_limit(sys.maxsize)

# Stems BDB -> code binyan de binyan_gen.py
STEM_TO_BINYAN = {
    "Qal": "qal",
    "Niphal": "nif",
    "Piel": "piel",
    "Pual": "pual",
    "Hithpael": "hit",
    "Hiphil": "hif",
    "Hophal": "hof",
}

STEM_RE = re.compile(
    r"<b>\s*(Qal|Niph`al|Piel|Pu`al|Hithpa`el|Hiph`il|Hoph`al)"
    r"\s*(?:\d+)?\s*</b>")

# Mots purement morphologiques : les fragments qui commencent par eux
# ne sont pas des sens.
_MORPH_START = re.compile(
    r"^(Perfect|Imperfect|Imperative|Infinitive|Participle|Jussive|"
    r"cohortative|suffix|consecutive|absolute|construct|"
    r"3 ?m(asculine)?|2 ?m|1 ?(sing|pl)|feminine|masculine|plural|"
    r"passive|active|and he|and she|so|also|not|only)",
    re.I)
# Fragments à éliminer même au milieu d'un sens (bruit BDB).
_NOISE_TOKENS = ("and he", "and she", "hath made", "I kept", "thou")

HEB_RE = re.compile(r"<bdbheb>.*?</bdbheb>", re.S)
ARC_RE = re.compile(r"<bdbarc>.*?</bdbarc>", re.S)
TAG_RE = re.compile(r"<[^>]+>")
REF_RE = re.compile(r"\b(?:Gen|Exod|Lev|Num|Deut|Josh|Judg|Ruth|"
                    r"1Sam|2Sam|1Kgs|2Kgs|1Chr|2Chr|Ezra|Neh|Esth|Job|"
                    r"Ps|Prov|Eccl|Song|Isa|Jer|Lam|Ezek|Dan|Hos|Joel|"
                    r"Amos|Obad|Jonah|Mic|Nah|Hab|Zeph|Hag|Zech|Mal)"
                    r"\s*\d+:\d+\b")
LOOKUP_RE = re.compile(r"\([^)]*(?:Ges|Kö|van d\. H\.|Bae|Di|Dr|Bu|"
                       r"Du|Hi|Co|Wkl|Benz| GASm|Sm|Comm|Qr|Kt)[^)]*\)")


def _strip_diacritics(s):
    """Racine consonantique : retire nikkud, daguesh, accents, U+200E..."""
    out = []
    for ch in s:
        cat = unicodedata.category(ch)
        if 0x0591 <= ord(ch) <= 0x05C7:   # nikkud/teamim
            continue
        if ch in ("\u200e", "\u200f"):
            continue
        if cat.startswith("M"):
            continue
        out.append(ch)
    return "".join(out)


def _clean_sense(fragment):
    """Nettoie un fragment HTML de sens BDB en texte anglais lisible."""
    t = HEB_RE.sub(" ", fragment)
    t = ARC_RE.sub(" ", t)
    t = TAG_RE.sub(" ", t)
    t = html.unescape(t)
    t = t.replace("\\&emsp;", " ").replace("\u200e", " ")
    t = REF_RE.sub(" ", t)
    t = LOOKUP_RE.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip(" .;,:")
    return t.strip()


def _root_of_entry(content):
    """Racine (consonnes nues) de l'entrée BDB : le premier mot hébreu."""
    m = re.search(r"<bdbheb>([^<]+)</bdbheb>", content)
    if not m:
        return None
    return _strip_diacritics(html.unescape(m.group(1)).strip())


def extract_senses(content):
    """Sens par binyan d'une entrée BDB (dict code -> sens anglais)."""
    out = {}
    marks = list(STEM_RE.finditer(content))
    for i, m in enumerate(marks):
        stem = m.group(1).replace("`", "").replace("al", "al")
        # normalisation Niph`al -> Niphal, etc.
        stem_key = stem.replace("`", "")
        stem_key = {"Niphal": "Niphal", "Pual": "Pual", "Hithpael": "Hithpael",
                    "Hiphil": "Hiphil", "Hophal": "Hophal",
                    "Qal": "Qal", "Piel": "Piel"}.get(stem_key, stem_key)
        code = STEM_TO_BINYAN.get(stem_key)
        if not code:
            continue
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(content)
        frag = content[start:end]
        # Sens = segments <highlight> du fragment ; on s'arrête dès qu'un
        # fragment ressort de la morphologie ou devient trop long.
        senses = []
        for hm in re.finditer(r"<highlight>(.*?)</highlight>", frag, re.S):
            txt = _clean_sense(hm.group(1))
            if not txt or len(txt) < 2 or len(txt) > 40:
                continue
            if _MORPH_START.match(txt):
                continue
            if any(n in txt for n in _NOISE_TOKENS):
                continue
            # écarter les gloses contextuelles (« fashioned the rib into
            # a woman », « the hill ») et les substantifs dérivés
            if " the " in txt or txt.endswith("er"):
                continue
            # normaliser le « to » initial (to be built = be built)
            if txt.startswith("to "):
                txt = txt[3:]
            if txt not in senses:
                senses.append(txt)
            # deux sens propres suffisent ; au-delà, le BDB détaille des
            # emplois contextuels de plus en plus spécifiques
            if len(senses) >= 2:
                break
        if senses:
            # fusionner les sens en une chaîne anglaise compacte
            en = "; ".join(senses)
            # ne pas écraser un sens déjà retenu (premier stem = principal)
            if code not in out:
                out[code] = en
    return out


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) != 1:
        print("Usage : python scripts/extract_binyan_senses.py "
              "<unabridged-BDB-Hebrew-lexicon.csv>")
        return 1
    path = argv[0]
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))

    # lexique FR/EN existant (pour conserver les sens français validés)
    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, "..", "bhsa_grammar",
                            "binyan_senses_fr_en.json")
    try:
        with open(out_path, encoding="utf-8") as fh:
            existing = json.load(fh)
    except (OSError, ValueError):
        existing = {}

    lexicon = {}
    stats = {"entries": 0, "verbs": 0, "with_senses": 0}
    for r in rows:
        stats["entries"] += 1
        content = r.get("content") or ""
        if "BIBLICAL HEBREW" not in content:
            continue
        if "<b>verb</b>" not in content and "<b>verb " not in content:
            continue
        stats["verbs"] += 1
        root = _root_of_entry(content)
        if not root or len(root) < 2:
            continue
        senses = extract_senses(content)
        if not senses:
            continue
        stats["with_senses"] += 1
        if root in lexicon:
            # entrée homonyme : fusionner les binyanim manquants
            for code, en in senses.items():
                lexicon[root].setdefault(code, en)
        else:
            lexicon[root] = senses

    # conserver les sens français déjà traduits manuellement
    final = {}
    for root, by in existing.items():
        final[root] = by
    for root, by in lexicon.items():
        if root not in final:
            final[root] = {}
        for code, en in by.items():
            if code not in final[root]:
                final[root][code] = ["", en]
            else:
                # le sens anglais du BDB affine l'existant
                entry = final[root][code]
                if len(entry) >= 2 and not entry[1]:
                    entry[1] = en

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(final, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"Entrées BDB : {stats['entries']}, verbes : {stats['verbs']}, "
          f"avec sens par binyan : {stats['with_senses']}")
    print(f"Lexique écrit : {out_path} ({len(final)} racines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
