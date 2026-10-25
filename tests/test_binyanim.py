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
    L = api.L
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

    # Binyanim modernes (Pealim, modern_binyanim.json) : שמר y est
    # attesté en qal, nifal, pi'el et hitpa'el, mais pas en pual/hifil/
    # hufal ; le champ modern_forms porte lemme/gloss/url, le texte
    # marqué l'attestation (◈) et le parse la restitue.
    r_mod = analyze_binyanim(F, "שמר", use_modern=True)
    modern_smr = {b["code"]: b.get("modern_forms") for b in r_mod["binyanim"]}
    for code in ("qal", "nif", "piel", "hit"):
        if not modern_smr.get(code):
            failures.append(f"שמר moderne: binyan {code} devrait être attesté "
                            f"en hébreu moderne : {modern_smr}")
    for code in ("pual", "hif", "hof"):
        if modern_smr.get(code):
            failures.append(f"שמר moderne: binyan {code} ne devrait pas être "
                            f"attesté en hébreu moderne : {modern_smr}")
    if modern_smr.get("qal") and "url" not in modern_smr["qal"]:
        failures.append("שמר moderne: modern_forms devrait porter l'url Pealim")
    parsed_mod = parse_binyanim_text(binyanim_to_text(r_mod))
    for b in parsed_mod["binyanim"]:
        want = bool(modern_smr[b["code"]])
        got = bool(b.get("modern_forms"))
        if got != want:
            failures.append(f"parse שמר moderne: {b['code']} "
                            f"modern={got} != {want}")
        if want and "hébreu moderne" not in b["text"]:
            failures.append(f"parse שמר moderne: attestation ◈ manquante "
                            f"pour {b['code']}")
        if not want and "hébreu moderne" in b["text"]:
            failures.append(f"parse שמר moderne: attestation ◈ indue pour "
                            f"{b['code']}")

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
    # Point shin après un meteg réordonné par NFC (יֹושֵֽׁב) : la
    # normalisation déplace le point shin après le meteg (U+05BD) ;
    # la garde orphelin ne doit pas le prendre pour un point isolé.
    r_ysb = analyze_binyanim(F, "\u05D9\u05B9\u05D5\u05E9\u05C1\u05B5\u05BD\u05D1")
    if not r_ysb["found"] or r_ysb["verb"].get("reason") == "orphan_shin_dot":
        failures.append(f"יֹושֵֽׁב: devrait être identifié (racine ישׁב), "
                        f"obtenu {r_ysb['found']}/"
                        f"{r_ysb['verb'].get('reason')!r}")
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
    # Variantes attestées d'une même cellule : plusieurs conjuguaisons
    # du même binyan coexistent dans la BHSA (ex. qal yiqtol 1cs :
    # אֶקְטֹל holam dominant, אֶקְטַל patah attesté ; שָׁמַע : אֶשְׁמַע/
    # אֶשְׁמָע). Le paradigme porte la dominante, « variants » les
    # conjuguaisons concurrentes réellement attestées, et le texte les
    # affiche sur la même ligne séparées par « / ».
    r_ktb = analyze_binyanim(F, "\u05DB\u05BC\u05B8\u05EA\u05B7\u05D1")
    ktb_qal = r_ktb["binyanim"][0]
    cell_1cs = ("p1", "c", "sg")
    vars_1cs = (ktb_qal["paradigm"].get("variants", {})
                .get("impf", {}).get(cell_1cs) or [])
    if "\u05D0\u05B6\u05DB\u05B0\u05EA\u05B7\u05BC\u05D1" not in vars_1cs:
        failures.append(f"\u05db\u05bc\u05ea\u05d1 qal impf 1cs : la variante "
                        f"patah \u05d0\u05b6\u05db\u05b0\u05ea\u05b7\u05bc\u05d1 devrait "
                        f"\u00eatre list\u00e9e : {vars_1cs!r}")
    if ktb_qal["paradigm"]["impf"].get(cell_1cs) == "\u05D0\u05B6\u05DB\u05B0\u05EA\u05B7\u05BC\u05D1":
        failures.append("\u05db\u05bc\u05ea\u05d1 qal impf 1cs : le holam "
                        "\u05d0\u05b6\u05db\u05b0\u05ea\u05b9\u05d1 doit rester la forme "
                        "dominante")
    r_sma = analyze_binyanim(F, "\u05E9\u05C1\u05DE\u05B7\u05E2" if False else "\u05E9\u05B8\u05C1\u05DE\u05B7\u05E2")
    sma_qal = r_sma["binyanim"][0]
    vars_sma = (sma_qal["paradigm"].get("variants", {})
                .get("impf", {}).get(cell_1cs) or [])
    if "\u05D0\u05B6\u05E9\u05C1\u05B0\u05DE\u05B7\u05E2" not in (sma_qal["paradigm"]["impf"].get(cell_1cs),
                         *vars_sma):
        failures.append(f"\u05e9\u05c1\u05de\u05e2 qal impf 1cs : \u05d0\u05b6\u05e9\u05c1\u05b0\u05de\u05b7\u05e2 "
                        f"manquant : {vars_sma!r}")
    if "\u05D0\u05B6\u05E9\u05C1\u05B0\u05DE\u05B8\u05E2" not in vars_sma:
        failures.append(f"\u05e9\u05c1\u05de\u05e2 qal impf 1cs : la variante qamats "
                        f"\u05d0\u05b6\u05e9\u05c1\u05b0\u05de\u05b8\u05e2 devrait \u00eatre "
                        f"list\u00e9e : {vars_sma!r}")
    # Le texte marqué affiche les variantes sur la ligne de la cellule.
    text_ktb = binyanim_to_text(r_ktb)
    line_1cs = [ln for ln in text_ktb.split("\n")
                if "1re pers. sing. (je)" in ln]
    if not any("\u05D0\u05B6\u05DB\u05B0\u05EA\u05B9\u05D1 / " in ln for ln in line_1cs):
        failures.append(f"texte : variante absente de la ligne 1cs "
                        f"de l'imparfait : {line_1cs!r}")

    # Dagesh parasite sur P1 après le patah (piel/hitpael imparfait) : un
    # signe combinant s'attache à la lettre PRÉCÉDENTE — p1 + PATAH +
    # DAGESH + p2 posait le dagesh sur P1 (תְּדַּבֵּרִי). La BHSA
    # n'atteste aucun dagesh sur P1 : תְּדַבֵּרִי (Ps 45:6, Jer 1:5),
    # יְגַדֵּל, הִתְקַדָּשׁוּ. Le dagesh fort du piel reste sur P2 (בֵּ).
    r_dbr = analyze_binyanim(F, "\u05D3\u05BC\u05B8\u05D1\u05B7\u05E8")
    piel_dbr = [b for b in r_dbr["binyanim"] if b["code"] == "piel"][0]
    form_2fs = piel_dbr["paradigm"]["impf"].get(("p2", "f", "sg"), "")
    # le ד ne doit PAS porter de dagesh : דַּ interdit
    import re as _re
    if _re.search("\u05D3\u05B7\u05BC", form_2fs):
        failures.append(f"piel impf 2fs : dagesh parasite sur P1 : "
                        f"{form_2fs!r} (attendu \u05ea\u05b0\u05d3\u05b7\u05d1\u05b5\u05bc\u05e8\u05b4\u05d9)")
    hit_dbr = [b for b in r_dbr["binyanim"] if b["code"] == "hit"][0]
    form_hit = hit_dbr["paradigm"]["impf"].get(("p2", "f", "sg"), "")
    if _re.search("\u05D3\u05B7\u05BC", form_hit):
        failures.append(f"hit impf 2fs : dagesh parasite sur P1 : "
                        f"{form_hit!r}")
    # L'impératif piel garde le lene légitime sur P1 begadkefat : דַּבֵּר.
    form_impv = piel_dbr["paradigm"]["impv"].get(("p2", "m", "sg"), "")
    if "\u05D3\u05B7\u05BC\u05D1\u05B5\u05BC\u05E8" not in form_impv:
        failures.append(f"piel impv 2ms : lene attendu sur le \u05d3 : "
                        f"{form_impv!r}")

    # Références attestées (option --references / checkbox GUI) : chaque
    # cellule attestée porte « [Livre ch:v] » ; les cellules non
    # attestées n'en portent pas.
    r_ref = analyze_binyanim(F, "\u05DB\u05BC\u05B8\u05EA\u05B7\u05D1",
                             with_references=True, L=L)
    qal_ref = r_ref["binyanim"][0]
    refs = qal_ref.get("references") or {}
    import re as _re2
    got_3ms = refs.get("perf", {}).get(("p3", "m", "sg"), "")
    if not _re2.match(r"^[^\]]+\s\d+:\d+$", got_3ms or ""):
        failures.append(f"r\u00e9f\u00e9rences : parfait 3ms devrait porter "
                        f"une r\u00e9f\u00e9rence, obtenu {got_3ms!r}")
    # Une cellule non attestée (imparfait 2fs de KTB) n'en porte pas.
    got_2fs = refs.get("impf", {}).get(("p2", "f", "sg"))
    if got_2fs:
        failures.append(f"r\u00e9f\u00e9rences : impf 2fs de \u05db\u05ea\u05d1 "
                        f"non attest\u00e9, r\u00e9f\u00e9rence indue {got_2fs!r}")
    # Sans L (appel programmatique sans Locality), pas de référence.
    r_noref = analyze_binyanim(F, "\u05DB\u05BC\u05B8\u05EA\u05B7\u05D1",
                               with_references=True)
    if r_noref["binyanim"][0].get("references"):
        failures.append("r\u00e9f\u00e9rences : sans L, aucune r\u00e9f\u00e9rence "
                        "ne devrait \u00eatre produite")
    # Le texte marqu\u00e9 affiche la r\u00e9f\u00e9rence entre crochets.
    text_ref = binyanim_to_text(r_ref)
    if "[Nombres 5:23]" not in text_ref and "[Exode 32:32]" not in text_ref:
        failures.append("r\u00e9f\u00e9rences : texte sans r\u00e9f\u00e9rence "
                        "entre crochets")

    # Parfait 3e pers. fém. pl. : la BHSA n'atteste AUCUNE forme de
    # parfait 3fp en hébreu — les 2756 parfaites qal 3pl de la base
    # sont toutes en -\u05d5\u05bc (shureq, genre « unknown », commun).
    # La terminaison -\u05b8\u05d4 (qatl\u0101h) ne survit qu'au singulier ; au
    # pluriel du parfait, l'hébreu biblique emploie la forme commune
    # (Gesenius §44g, §47k). Le paradigme doit donc générer la 3fp
    # IDENTIQUE à la 3mp (כָּתְבוּ), et non le théorique כָּתְבָה.
    cell_3fp = ("p3", "f", "pl")
    cell_3mp = ("p3", "m", "pl")
    r_3fp = analyze_binyanim(F, "\u05DB\u05BC\u05B8\u05EA\u05B7\u05D1")
    for b in r_3fp["binyanim"]:
        fp = b["paradigm"]["perf"].get(cell_3fp, "")
        mp = b["paradigm"]["perf"].get(cell_3mp, "")
        if not fp:
            continue
        # La forme 3fp est COMMUNE (même terminaison -\u05d5\u05bc que la
        # 3mp) ; les sources peuvent différer (gabarit BHSA vs builtin,
        # orthographe du dagesh) — on compare les terminaisons.
        if fp[-2:] != mp[-2:]:
            failures.append(f"parfait 3fp {b['code']} : {fp!r} devrait "
                            f"partager la terminaison de {mp!r} "
                            f"(cf. S_PERF)")
        if fp.endswith("\u05B8\u05D4"):
            failures.append(f"parfait 3fp {b['code']} : terminaison "
                            f"-\u05b8\u05d4 non biblique : {fp!r}")
    # L'imparfait 3fp garde sa terminaison propre (תִּכְתֹּבְנָה).
    impf_3fp = r_3fp["binyanim"][0]["paradigm"]["impf"].get(cell_3fp, "")
    if impf_3fp and not impf_3fp.endswith("\u05E0\u05B8\u05D4"):
        failures.append(f"imparfait 3fp qal : {impf_3fp!r} devrait "
                        "se terminer en -\u05e0\u05b8\u05d4")

    if failures:
        print(f"ÉCHECS ({len(failures)}) :")
        for f in failures:
            print("  -", f)
        return 1
    print("TOUS LES TESTS BINYANIM PASSENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
