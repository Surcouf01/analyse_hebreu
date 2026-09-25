#!/usr/bin/env python3
"""Extraction des gabarits de conjugaison par binyan et catégorie de verbe.

Parcourt la base BHSA (Text-Fabric) et, pour chaque catégorie de verbe
(fort, pe-guttural, lamed-he, creux, double, ...), extrait les gabarits
vocaliques dominants de chaque cellule du paradigme (binyan × temps ×
personne/genre/nombre). Le résultat est écrit en JSON
(``bhsa_grammar/binyan_templates.json``) et utilisé par
``bhsa_grammar/binyan_gen.py`` pour conjuguer un verbe dans les 7 binyanim.

Un gabarit est une chaîne où P1, P2, P3 marquent les radicales ; tout le
reste (préfixes, voyelles, daguesh, terminaisons) est littéral. Pour les
verbes lamed-he, P3 (ה) est laissé hors gabarit : les terminaisons
(ה/ת/י/נוּ/וֹת) sont littérales. Pour les verbes creux, P2 (ו/י) est
littéral. Pour les verbes doubles, P2 et P3 partagent la même radicale.

Usage :

    python scripts/extract_binyan_templates.py
"""

import collections
import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bhsa_grammar import load_corpus  # noqa: E402
from bhsa_grammar.binyan_gen import classify_root, _normalize  # noqa: E402

BINYANIM = ("qal", "nif", "piel", "pual", "hit", "hif", "hof")
TENSES = ("perf", "impf", "impv")
NON_FINITE = ("infa", "infc")
PARTICIPLES = ("ptca", "ptcp")

# Volitifs (modes du yiqtol) : la BHSA les code comme des impf/wayq ; ils
# sont identifiés ici par des critères morphologiques.
#   - cohortatif : impf 1re personne + finale \u05b8\u05d4 (« que je ... ») ;
#   - jussif : wayq 2e/3e personne — le wayyiqtol a exactement la
#     morphologie de la forme courte du yiqtol (le \u05d5\u05b7 est un mot
#     séparé dans la BHSA) ; reprise pour les personnes 2/3.
QAMATS = "\u05B8"
HE = "\u05D4"

# Cellules volitives (ps, gn, nu).
COHORT_CELLS = (
    ("p1", "c", "sg"), ("p1", "c", "pl"),
)
JUSSIVE_CELLS = (
    ("p3", "m", "sg"), ("p3", "f", "sg"), ("p2", "m", "sg"), ("p2", "f", "sg"),
    ("p3", "m", "pl"), ("p3", "f", "pl"), ("p2", "m", "pl"), ("p2", "f", "pl"),
)

# Cellules par temps (ps, gn, nu).
PERF_CELLS = (
    ("p3", "m", "sg"), ("p3", "f", "sg"), ("p2", "m", "sg"), ("p2", "f", "sg"),
    ("p1", "c", "sg"), ("p3", "m", "pl"), ("p3", "f", "pl"),
    ("p2", "m", "pl"), ("p2", "f", "pl"), ("p1", "c", "pl"),
)
IMPF_CELLS = PERF_CELLS
IMPV_CELLS = (
    ("p2", "m", "sg"), ("p2", "f", "sg"), ("p2", "m", "pl"), ("p2", "f", "pl"),
)

# Personnes inconnues dans la base (1re personne marquée "unknown" en gn).
CELLS_BY_TENSE = {
    "perf": PERF_CELLS,
    "impf": IMPF_CELLS,
    "impv": IMPV_CELLS,
    "juss": JUSSIVE_CELLS,
    "coh": COHORT_CELLS,
}

# Finale cohortative : qamats + he. Les paragogiques (\u05e0\u05b8\u05bc\u05d4) sont
# des imparfaits longs ordinaires, pas des cohortatifs.
_COH_END = QAMATS + HE
_PARAGOGIC_NUN = ("\u05E0",)


def _is_cohortative(form, nu):
    """Vrai si la forme est un cohortatif (imparfait + \u05b8\u05d4)."""
    if not form.endswith(_COH_END):
        return False
    if nu == "pl":
        return True
    # Au singulier, la finale \u05e0\u05b8\u05d4 (nun paragogique) est un imparfait long,
    # pas un cohortatif.
    base = form[:-len(_COH_END)]
    cons = [c for c in base if 0x05D0 <= ord(c) <= 0x05EA]
    return not (cons and cons[-1] in _PARAGOGIC_NUN)

# Correspondance BHSA : les 1res personnes ont gn=unknown (parfois "NA").
_GN_FALLBACK = {"c": ("unknown", "NA", None)}


def _cells_for(tense):
    return CELLS_BY_TENSE[tense]


def _root_letters(s):
    out = []
    for ch in s or "":
        o = ord(ch)
        if 0x05D0 <= o <= 0x05EA:
            out.append(ch)
        elif ch in ("\u05C1", "\u05C2") and out and out[-1] == "\u05E9":
            out[-1] += ch
    return out


def _to_template(form, root, assimilate=False):
    """Remplace les radicales par P1/P2/P3 ; renvoie None si échec.

    Pour les verbes lamed-he, la 3e radicale (ה) n'est pas remplacée
    (elle se confond avec la terminaison ה des formes suffixées) : le
    gabarit ne contient que P1 et P2. Pour les verbes creux, la 2e
    radicale (ו/י) est littérale. Pour les verbes doubles, P2 désigne
    la radicale redoublée.

    ``assimilate=True`` : la 1re radicale est élidée (verbes pe-nun /
    pe-yod dont la radicale s'assimile au daguesh fort de la suivante) ;
    le gabarit ne contient alors que P2/P3.
    """
    letters = list(root)
    cat = classify_root(*letters) if len(letters) == 3 else None
    if cat == "lamed_he":
        letters = letters[:2]
    if cat == "ayin_vav":
        letters = [letters[0], letters[2]]
    if cat == "double":
        letters = [letters[0], letters[1]]
    if assimilate:
        letters = letters[1:]
    offset = 2 if assimilate else 1
    # Métathèse hitpael : avec une 1re radicale sifflante (שׁ/שׂ/ס/צ),
    # le ת s'infixe après P1 (הִשְׁתַּמֵּר) ; dans la forme, P1 apparaît
    # AVANT le ת. On autorise donc P1 à matcher n'importe où dans la
    # forme, tant que l'ordre P1..P2(..P3) est respecté.
    metathesis = False
    if (cat not in ("lamed_he", "ayin_vav", "double") and not assimilate
            and len(letters) == 3 and letters[0] in ("\u05E9", "\u05E9\u05C1",
                                                    "\u05E9\u05C2", "\u05E1",
                                                    "\u05E6")
            and letters[0] not in form[:1]):
        metathesis = True
    idx = 0
    out = []
    i = 0
    while i < len(form):
        ch = form[i]
        matched = False
        if idx < len(letters):
            cand = ch
            pending = ""
            if ch == "\u05E9" and i + 1 < len(form) and form[i + 1] in ("\u05C1", "\u05C2"):
                cand = ch + form[i + 1]
                i += 1
            elif (ch == "\u05E9" and len(letters[idx]) == 2
                    and letters[idx][0] == "\u05E9"):
                # Point shin/sin : le point peut suivre un signe vocalique
                # (\u05e9\u05b0\u05c1) ; on l'associe au \u05e9 en
                # conservant les signes interm\u00e9diaires dans le gabarit.
                j = i + 1
                while j < len(form) and 0x05B0 <= ord(form[j]) <= 0x05C2:
                    if form[j] in ("\u05C1", "\u05C2"):
                        if form[j] == letters[idx][1]:
                            cand = ch + form[j]
                            pending = form[i + 1:j]
                            i = j
                        break
                    j += 1
            if cand == letters[idx]:
                out.append(f"P{idx + offset}")
                if pending:
                    out.append(pending)
                idx += 1
                matched = True
        if not matched:
            out.append(ch)
        i += 1
    if idx != len(letters):
        return None
    tpl = "".join(out)
    # Verbes doubles : la radicale redoublée apparaît une 2e fois comme
    # littéral ; on la remplace aussi par P2 pour que la substitution
    # produise le redoublement (גִּלְלַ... -> P1ִP2ְP2...).
    if cat == "double" and len(letters) == 2:
        dbl = letters[1]
        tpl = tpl.replace(dbl, "P2")
    return tpl


def main():
    api = load_corpus()
    F = api.F

    # Index des lemmes verbaux hébreux : lex -> (root letters, catégorie).
    lex_info = {}
    for w in F.otype.s("word"):
        if F.sp.v(w) != "verb":
            continue
        lex = F.lex.v(w)
        if lex in lex_info:
            continue
        lu = F.lex_utf8.v(w) or ""
        letters = _root_letters(lu)
        if len(letters) != 3:
            continue
        lex_info[lex] = (letters, classify_root(*letters))

    # Comptage des gabarits par (catégorie, binyan, temps, cellule).
    # Chaque gabarit retient le nombre d'occurrences ET le nombre de
    # lemmes distincts qui le produisent : un gabarit issu d'un seul lemme
    # très fréquent mais irrégulier (ex. נתן) ne doit pas écraser le
    # schéma régulier de sa catégorie.
    templates = collections.defaultdict(lambda: collections.defaultdict(lambda: {"n": 0, "lexes": set()}))

    def record(cat, vs, vt, key, form, root, lex):
        def bump(tpl):
            entry = templates[(cat, vs, vt, key)][tpl]
            entry["n"] += 1
            entry["lexes"].add(lex)
        tpl = _to_template(form, root)
        if tpl and "P1" in tpl:
            bump(tpl)
            return
        # Assimilation pe-nun / pe-yod : la 1re radicale disparaît au
        # profit d'un daguesh fort sur la 2e (יִפֹּל, יֵשֵׁב) ; le gabarit
        # ne contient que P2/P3 (le daguesh fort reste littéral).
        tpl2 = _to_template(form, root, assimilate=True)
        if tpl2 and "P2" in tpl2:
            bump(tpl2)

    for w in F.otype.s("word"):
        sp = F.sp.v(w)
        if sp != "verb":
            continue
        lex = F.lex.v(w)
        info = lex_info.get(lex)
        if info is None:
            continue
        root, cat = info
        vs = F.vs.v(w)
        if vs not in BINYANIM:
            continue
        vt = F.vt.v(w)
        if vt not in TENSES + NON_FINITE + PARTICIPLES + ("wayq",):
            continue
        prs = F.prs.v(w)
        if prs not in (None, "n/a", "NA", "unknown", "absent"):
            continue
        form = _normalize(F.g_word_utf8.v(w))
        if not form:
            continue
        ps, gn, nu = F.ps.v(w), F.gn.v(w), F.nu.v(w)
        if vt in NON_FINITE + PARTICIPLES:
            # Cellule (vt, gn, nu) : ps est unknown pour les non finis.
            key = (gn or "unknown", nu or "unknown")
            record(cat, vs, vt, key, form, root, lex)
            continue
        if vt == "wayq":
            # Jussif : le wayyiqtol a la morphologie de la forme courte du
            # yiqtol (le \u05d5\u05b7 conversif est un mot séparé). On enregistre la
            # forme courte pour les personnes 2/3 du paradigme volitif.
            if ps in ("p2", "p3"):
                record(cat, vs, "juss", (ps, gn, nu), form, root, lex)
            continue
        if vt == "impf" and ps == "p1" and _is_cohortative(form, nu):
            # Cohortatif : impf 1re personne + finale \u05b8\u05d4.
            record(cat, vs, "coh", (ps, "c", nu), form, root, lex)
            continue
        if vt == "impv":
            if ps != "p2":
                continue
        cells = _cells_for(vt)
        # Normalisation du genre : les 1res personnes sont marquées "unknown"
        # dans la BHSA, et les 3es personnes pluriel souvent aussi (genre
        # commun). On accepte donc ces variantes pour la cellule correspondante.
        for cell in cells:
            cps, cgn, cnu = cell
            if cgn == "c":
                gn_candidates = ("c", "unknown", "NA")
            elif cnu == "pl" and cps == "p3":
                gn_candidates = (cgn, "unknown", "NA")
            else:
                gn_candidates = (cgn,)
            if ps == cps and gn in gn_candidates and nu == cnu:
                record(cat, vs, vt, cell, form, root, lex)
                break

    # Sélection du gabarit dominant : d'abord par nombre de lemmes
    # distincts (généralisabilité), puis par nombre d'occurrences. Un
    # gabarit issu d'un seul lemme est trop idiosyncratique pour
    # représenter la catégorie : on le garde seulement si aucun gabarit
    # concurrent n'existe (le générateur repliera sinon sur « strong »).
    out = {}
    for (cat, vs, vt, key), counter in templates.items():
        ranked = sorted(counter.items(),
                        key=lambda kv: (-len(kv[1]["lexes"]), -kv[1]["n"]))
        tpl, entry = ranked[0]
        if len(entry["lexes"]) < 2:
            # Gabarit idiosyncratique (un seul lemme) : ne pas l'écrire —
            # le générateur repliera sur le gabarit « strong » ou le
            # générateur intégré, plus sûrs qu'une forme isolée.
            if cat == "strong" and len(ranked) == 1:
                pass  # unique source, on garde (verbe fort de référence)
            else:
                continue
        out_key = "|".join([cat, vs, vt, *map(str, key)])
        out[out_key] = {
            "template": tpl,
            "count": entry["n"],
            "lexemes": len(entry["lexes"]),
            "variants": [t for t, _ in ranked[:3]],
        }

    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        "bhsa_grammar", "binyan_templates.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"{len(out)} gabarits écrits dans {os.path.normpath(dest)}")

    # Statistiques par catégorie.
    by_cat = collections.Counter(k.split("|")[0] for k in out)
    for cat, n in sorted(by_cat.items()):
        print(f"  {cat:16} {n}")


if __name__ == "__main__":
    main()
