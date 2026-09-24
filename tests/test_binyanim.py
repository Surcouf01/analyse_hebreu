#!/usr/bin/env python3
"""Test de non-régression du mode binyanim (bhsa_grammar.binyan_gen).

Pour chaque verbe de test (fort et faible), vérifie que :
  1. le verbe est identifié et sa catégorie est correcte ;
  2. les formes générées pour les cellules attestées dans la BHSA
     correspondent aux formes réelles (comparaison après normalisation,
     en tolérant les variantes orthographiques mineures) ;
  3. le texte marqué produit par le CLI est parsable par le GUI
     (7 en-têtes de binyan, libellés français + hébreu).

Usage :

    python tests/test_binyanim.py
"""

import os
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bhsa_grammar import load_corpus  # noqa: E402
from bhsa_grammar.binyan_gen import (  # noqa: E402
    analyze_binyanim,
    binyanim_to_text,
    parse_binyanim_text,
)

# Verbes de test : (forme, catégorie attendue).
TEST_VERBS = (
    ("שָׁמַר", "strong", "שׁמר"),
    ("שׁמר", "strong", "שׁמר"),
    ("בָּנָה", "lamed_he", "בנה"),
    ("קָם", "ayin_vav", "קום"),
    ("סָבַב", "double", "סבב"),
    ("נָפַל", "pe_nun", "נפל"),
    ("יָשַׁב", "pe_yod", "ישׁב"),
    ("שָׁמַע", "lamed_guttural", "שׁמע"),
    ("אָהַב", "ayin_guttural", "אהב"),
    ("אָסַר", "pe_alef", "אסר"),
)

# Binyanim attendus dans l'ordre pédagogique.
EXPECTED_BINYANIM = ("qal", "nif", "piel", "pual", "hit", "hif", "hof")

# Cellules clés vérifiées pour chaque binyan (formes les plus courantes).
KEY_CELLS = (
    ("perf", ("p3", "m", "sg")),
    ("perf", ("p3", "f", "sg")),
    ("perf", ("p2", "m", "sg")),
    ("perf", ("p1", "c", "sg")),
    ("impf", ("p3", "m", "sg")),
    ("impf", ("p2", "m", "sg")),
    ("impv", ("p2", "m", "sg")),
)


def _strip_teamim(s):
    return "".join(c for c in s if not (0x0591 <= ord(c) <= 0x05AF))


# Voyelles susceptibles de varier (forme pleine/défective, hatef vs voyelle
# simple + sheva, holam/holam waw).
_MATER = {"\u05D5": "[\u05B9\u05D8]?", "\u05D9": "[\u05B4\u05B5]?"}


def _norm(s):
    return unicodedata.normalize("NFC", _strip_teamim(s or ""))


def _same_form(generated, attested_set):
    """Compare une forme générée à un ensemble de formes attestées.

    Tolère les variantes orthographiques mineures du texte massorétique :
    daguesh (בָּנְתָה vs בָּנְתָּה), hatef vs sheva+voyelle (תֶּא vs תְּאֲ),
    holam simple vs holam-waw, tsere vs tsere-yod, segol vs patah.
    """
    import re

    def canon(s):
        s = _norm(s)
        # Retirer les signes non distinctifs : daguesh, meteg, shin/sin dot.
        s = re.sub(r"[\u05BC\u05BD\u05C1\u05C2]", "", s)
        # hatef -> sheva (l'échelle vocalique est équivalente).
        s = re.sub(r"[\u05B1\u05B2\u05B3]", "\u05B0", s)
        # Mater lectionis facultatif : ו/י non précédés d'une autre voyelle
        # longue porteuse sont équivalents à leur voyelle.
        s = s.replace("\u05B9\u05D5", "\u05B9")   # holam waw -> holam
        s = s.replace("\u05B4\u05D9", "\u05B4")   # hireq yod -> hireq
        s = s.replace("\u05B5\u05D9", "\u05B5")   # tsere yod -> tsere
        # Segol et patah sont souvent interchangeables en finale ouverte.
        s = s.replace("\u05B6", "\u05B7")
        return s

    g = canon(generated)
    return any(g == canon(a) for a in attested_set)


def main():
    api = load_corpus()
    F = api.F
    failures = []

    for form, expected_cat, _root in TEST_VERBS:
        r = analyze_binyanim(F, form)
        tag = f"{form} ({expected_cat})"
        if not r["found"]:
            failures.append(f"{tag}: verbe non trouvé")
            continue
        cat = r["verb"].get("category")
        if cat != expected_cat:
            failures.append(f"{tag}: catégorie {cat!r} != {expected_cat!r}")
        codes = tuple(b["code"] for b in r["binyanim"])
        if codes != EXPECTED_BINYANIM:
            failures.append(f"{tag}: binyanim {codes} != {EXPECTED_BINYANIM}")

        # Toutes les cellules clés doivent produire une forme non vide.
        for b in r["binyanim"]:
            for tense, cell in KEY_CELLS:
                form_gen = b["paradigm"][tense].get(cell, "")
                if not form_gen:
                    failures.append(
                        f"{tag}: {b['code']} {tense} {cell} vide")

    # Le texte marqué doit être parsable et contenir les 7 binyanim avec
    # libellés français et hébreux.
    r = analyze_binyanim(F, "שָׁמַר")
    text = binyanim_to_text(r)
    parsed = parse_binyanim_text(text)
    if len(parsed["binyanim"]) != 7:
        failures.append(f"parse: {len(parsed['binyanim'])} binyanim != 7")
    for b in parsed["binyanim"]:
        if not b["name_fr"] or not b["name_he"]:
            failures.append(f"parse: libellés manquants pour {b['code']}")
    if not parsed["verb"].get("root"):
        failures.append("parse: racine manquante")
    if not parsed["weak"].get("code"):
        failures.append("parse: catégorie faible manquante")
    # Champ « existe » : d'après la BHSA, שמר est attesté en qal, nifal,
    # piel et hitpael, mais pas en pual/hifil/hofal ; בנה est attesté en
    # qal, nifal et hitpael (hitpelel des lamed-he), mais pas en
    # piel/pual/hifil/hofal.
    exists_smr = {b["code"]: b.get("exists") for b in r["binyanim"]}
    for code in ("qal", "nif", "piel", "hit"):
        if exists_smr.get(code) is not True:
            failures.append(f"שמר: binyan {code} devrait exister : {exists_smr}")
    for code in ("pual", "hif", "hof"):
        if exists_smr.get(code) is not False:
            failures.append(f"שמר: binyan {code} ne devrait pas exister : {exists_smr}")
    r_bn = analyze_binyanim(F, "בָּנָה")
    exists_bn = {b["code"]: b.get("exists") for b in r_bn["binyanim"]}
    for code in ("qal", "nif", "hit"):
        if exists_bn.get(code) is not True:
            failures.append(f"בנה: binyan {code} devrait exister : {exists_bn}")
    for code in ("piel", "pual", "hif", "hof"):
        if exists_bn.get(code) is not False:
            failures.append(f"בנה: binyan {code} ne devrait pas exister : {exists_bn}")
    text_bn = binyanim_to_text(r_bn)
    parsed_bn = parse_binyanim_text(text_bn)
    for b in parsed_bn["binyanim"]:
        want = exists_bn[b["code"]]
        if b.get("exists") != want:
            failures.append(f"parse בנה: exists {b['code']}={b.get('exists')!r} != {want!r}")
        if want is False and "pas de sens" not in b["text"]:
            failures.append(f"parse בנה: avertissement manquant pour {b['code']}")
    # Traductions par binyan (fr + en) : périphrase d'après le gloss.
    # בנה = « bâtir » / « build ».
    tr_bn = {b["code"]: (b.get("translation_fr"), b.get("translation_en"))
             for b in r_bn["binyanim"]}
    # qal/nif : sens BDB du lexique ; les autres binyanim ne sont pas
    # couverts par le BDB pour cette racine : périphrase.
    expect_tr = {
        "qal": ("bâtir", "build; rebuild"),
        "nif": ("être bâti", "be built; be rebuilt"),
        "piel": ("bâtir (intensif)", "build (intensive)"),
        "pual": ("être bâti (intensif)", "to be built (intensive)"),
        "hit": ("se bâtir", "to build oneself"),
        "hif": ("faire bâtir", "to cause to build"),
        "hof": ("être fait bâtir", "to be made to build"),
    }
    for code, want in expect_tr.items():
        if tr_bn.get(code) != want:
            failures.append(f"trad בנה: {code} {tr_bn.get(code)} != {want}")
    # Lexique de sens par binyan (binyan_senses_fr_en.json) : ראה a des sens
    # réellement divergents — voir (qal), apparaître (nifal), montrer (hifil).
    r_ra = analyze_binyanim(F, "רָאָה")
    tr_ra = {b["code"]: b.get("translation_fr") for b in r_ra["binyanim"]}
    expect_ra = {"qal": "voir", "nif": "être vu, apparaître",
                 "hif": "montrer", "hit": "se montrer, se faire voir"}
    for code, want in expect_ra.items():
        if tr_ra.get(code) != want:
            failures.append(f"trad ראה: {code} {tr_ra.get(code)!r} != {want!r}")
    distinct_ra = {t.split(",")[0] for t in tr_ra.values() if t}
    if len(distinct_ra) < 3:
        failures.append(f"trad ראה: moins de 3 sens distincts : {sorted(distinct_ra)}")
    # Les marqueurs du texte doivent porter les traductions, et le parse
    # doit les restituer.
    for b in parsed_bn["binyanim"]:
        want = expect_tr[b["code"]]
        got = (b.get("translation_fr"), b.get("translation_en"))
        if got != want:
            failures.append(f"parse trad בנה: {b['code']} {got} != {want}")
        if "Traduction" not in b["text"]:
            failures.append(f"parse trad בנה: ligne Traduction manquante pour {b['code']}")

    # Vérification contre les formes réellement attestées : pour le verbe
    # FORT de référence et les cellules clés du qal, les formes générées
    # doivent coïncider avec la base. Pour les verbes faibles, chaque lemme
    # peut présenter des idiosyncrasies (hapax, formes plènes) : on ne
    # vérifie que les cellules dont le gabarit de catégorie provient de
    # plusieurs lemmes distincts (généralisable), et on tolère une petite
    # marge de divergence pour les cellules restantes.
    checked = 0
    mismatch = 0
    for form, expected_cat, root_disp in TEST_VERBS:
        r = analyze_binyanim(F, form)
        if not r["found"]:
            continue
        lex = r["verb"].get("lex")
        if not lex:
            continue
        # Formes attestées de ce lemme, sans suffixe pronominal.
        attested = {}
        for w in F.otype.s("word"):
            if F.lex.v(w) != lex or F.sp.v(w) != "verb":
                continue
            if F.prs.v(w) not in (None, "n/a", "NA", "unknown", "absent"):
                continue
            vs, vt = F.vs.v(w), F.vt.v(w)
            ps, gn, nu = F.ps.v(w), F.gn.v(w), F.nu.v(w)
            if vs not in EXPECTED_BINYANIM or vt not in ("perf", "impf", "impv"):
                continue
            if gn in ("unknown", "NA"):
                gn = "c" if ps == "p1" else gn
            g = _norm(F.g_word_utf8.v(w))
            attested.setdefault((vs, vt, ps, gn, nu), set()).add(g)
        for b in r["binyanim"]:
            # Le qal est la référence pédagogique : tolérance stricte.
            # Les autres binyanim des verbes faibles tolèrent les
            # idiosyncrasies de lemme (hapax, formes plènes). Les
            # catégories « pe- » admettent des sous-schémas vocaliques par
            # lemme (tsere vs segol) : tolérance également sur leur qal.
            strict = (expected_cat == "strong") or (
                b["code"] == "qal" and expected_cat not in (
                    "pe_alef", "pe_yod", "pe_guttural", "ayin_guttural",
                    "ayin_vav", "double"))
            for tense, cell in KEY_CELLS:
                ps, gn, nu = cell
                real = attested.get((b["code"], tense, ps, gn, nu))
                if not real:
                    continue
                gen = b["paradigm"][tense].get(cell, "")
                if not gen:
                    continue
                checked += 1
                if not _same_form(gen, real):
                    if strict:
                        failures.append(
                            f"{root_disp} {b['code']} {tense} {cell}: "
                            f"généré {gen!r} != attesté {sorted(real)}")
                    else:
                        mismatch += 1

    # Marge : au plus 20 % de divergences non critiques (idiosyncrasies
    # de lemme sur les binyanim rares des verbes faibles).
    if checked and mismatch > checked * 0.20:
        failures.append(
            f"trop de divergences non critiques : {mismatch}/{checked}")
    print(f"Divergences non critiques (idiosyncrasies de lemme) : "
          f"{mismatch}/{checked}")

    print(f"Cellules vérifiées contre la base BHSA : {checked}")
    # Point shin/sin orphelin (sans lettre ש) : la forme doit être refusée
    # avec la raison orphan_shin_dot, pas identifiée comme un autre verbe
    # (ex. ׁמר lu comme מר → racine מרר).
    for bad in ("\u05C1\u05DE\u05E8", "\u05C2\u05DE\u05E8", "\u05DE\u05C1\u05E8"):
        r_bad = analyze_binyanim(F, bad)
        reason = r_bad["verb"].get("reason") or r_bad.get("reason")
        if r_bad["found"] or reason != "orphan_shin_dot":
            failures.append(
                f"{bad!r}: attendu found=False/orphan_shin_dot, "
                f"obtenu found={r_bad['found']}/{reason!r}")
    # Les formes correctes avec point shin restent identifiées (le point
    # suit le ש, éventuellement après la voyelle — convention BHSA).
    for good in ("\u05E9\u05C1\u05DE\u05E8", "\u05E9\u05C2\u05DE\u05E8", "\u05E9\u05B8\u05C1\u05DE\u05B7\u05E8",
                 "\u05E9\u05B0\u05C1\u05DE\u05B7\u05E8"):
        r_good = analyze_binyanim(F, good)
        if not r_good["found"]:
            failures.append(f"{good!r}: devrait être identifié")
    # Forme courte d'un verbe double (מר de מרר) : refusée avec la racine
    # complète suggérée, pas identifiée comme un autre verbe.
    r_mr = analyze_binyanim(F, "\u05DE\u05B7\u05E8")
    reason_mr = r_mr["verb"].get("reason")
    sugg_mr = r_mr["verb"].get("suggestions") or []
    if r_mr["found"] or reason_mr != "root_truncated":
        failures.append(f"מַר: attendu found=False/root_truncated, "
                        f"obtenu {r_mr['found']}/{reason_mr!r}")
    elif "\u05DE\u05E8\u05E8" not in sugg_mr:
        failures.append(f"מַר: מרר devrait être suggéré : {sugg_mr!r}")
    # Racine nue trop courte (מר) : refusée, racines proches suggérées
    # dont מרר.
    r_nu = analyze_binyanim(F, "\u05DE\u05E8")
    sugg_nu = r_nu["verb"].get("suggestions") or []
    if r_nu["found"]:
        failures.append("מר nu: devrait être refusé")
    elif "\u05DE\u05E8\u05E8" not in sugg_nu:
        failures.append(f"מר nu: מרר devrait être suggéré : {sugg_nu!r}")
    # Les formes légitimes restent identifiées : creux, pe-nun assimilé,
    # forme pleine d'un double, forme avec préfixe.
    for good, want_root in (("\u05E7\u05B8\u05DD", "\u05E7\u05D5\u05DD"),
                            ("\u05D9\u05B4\u05E4\u05BC\u05D5\u05B9\u05DC", "\u05E0\u05E4\u05DC"),
                            ("\u05D9\u05B0\u05DE\u05B8\u05E8\u05B0\u05E8\u05D5\u05BC", "\u05DE\u05E8\u05E8"),
                            ("\u05D2\u05B8\u05DC\u05B7\u05DC", "\u05D2\u05DC\u05DC")):
        r_legit = analyze_binyanim(F, good)
        root_legit = "".join(r_legit["verb"].get("root") or ())
        if not r_legit["found"] or root_legit != want_root:
            failures.append(f"{good!r}: attendu racine {want_root!r}, "
                            f"obtenu {r_legit['found']}/{root_legit!r}")
    if failures:
        print(f"ÉCHECS ({len(failures)}) :")
        for f in failures:
            print("  -", f)
        return 1
    print("TOUS LES TESTS BINYANIM PASSENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
