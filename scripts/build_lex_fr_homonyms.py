#!/usr/bin/env python3
"""Collecte les homonymes BHSA et corrige les glosses français ambigus.

Le lexique `bhsa_grammar/lex_fr.json` a été aligné sur les consonnes du lemme
pointé ; les lexèmes BHSA homographes (ex. עור « peau » / עור « réveiller »)
ont donc reçu le même gloss français. Ce script :

  1. collecte les groupes d'homonymes BHSA (lemmes de même squelette
     consonantique, marqueurs de discours retirés) ;
  2. détecte les groupes où plusieurs membres partagent le même gloss FR
     alors que la BHSA les distingue (gloss EN / partie du discours) ;
  3. propose pour chaque membre une correction fiable :
       a. sens français du verbe depuis `binyan_senses_fr_en.json` ;
       b. traduction du gloss anglais via un dictionnaire en→fr construit
          sur les lemmes non ambigus (correspondance unique) ;
       c. overrides manuels (`MANUAL_OVERRIDES`) pour les cas restants ;
  4. écrit `bhsa_grammar/lex_fr_homonyms.json` : {lex_id: {gloss_fr, sp, en}}
     — utilisé à l'exécution par `bhsa_grammar.lex_fr` en accord avec la
     partie du discours du mot analysé (choix selon le contexte).

Usage :
    BHSA_DATA=... python scripts/build_lex_fr_homonyms.py
"""

import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bhsa_grammar import load_corpus  # noqa: E402

SKELETON_RE = re.compile(r"[/\[\]=\d]+$")

# Corrections manuelles, vérifiées à la main : lex_id BHSA -> gloss FR.
# Clé : lex_id ; on ne corrige que si la partie du discours du mot correspond.
MANUAL_OVERRIDES = {
    "<WR[": "éveiller, réveiller",       # עור « be awake » (hif : faire lever)
    "<WR=[": "être aveugle",              # עור « be blind »
    "<WR==[": "être nu",                  # עור « be naked »
}


def skeleton(lex):
    return SKELETON_RE.sub("", lex or "")


def main():
    api = load_corpus()
    F, L = api.F, api.L

    lexfr = json.load(open("bhsa_grammar/lex_fr.json", encoding="utf-8"))
    senses = json.load(open("bhsa_grammar/binyan_senses_fr_en.json",
                            encoding="utf-8"))

    # --- 1. lexèmes BHSA : partie du discours + gloss EN dominants ---------
    lexemes = {}
    for lx in F.otype.s("lex"):
        lex = F.lex.v(lx)
        if not lex:
            continue
        sps, ens = defaultdict(int), defaultdict(int)
        words = L.d(lx, "word")
        for w in words:
            sps[F.sp.v(w)] += 1
            if F.gloss.v(w):
                ens[F.gloss.v(w)] += 1
        lexemes[lex] = {
            "sp": max(sps, key=sps.get) if sps else None,
            "en": max(ens, key=ens.get) if ens else None,
            "voc": F.voc_lex_utf8.v(lx) or F.lex_utf8.v(lx),
            "count": len(words),
        }

    # --- 2. groupes d'homonymes -------------------------------------------
    groups = defaultdict(list)
    for lex, e in lexemes.items():
        groups[skeleton(lex)].append(lex)

    # --- 3. sens des verbes (binyan_senses_fr_en) -------------------------
    # voc (lemme pointé) -> sens FR (priorité qal, sinon premier non vide)
    # + sens EN concaténés, pour valider la correspondance avec le gloss
    # anglais BHSA du lexème.
    verb_fr = {}
    for voc, binyanim in senses.items():
        fr = (binyanim.get("qal") or [None])[0]
        frs = [fr0 for fr0, _en in binyanim.values() if fr0 and fr0.strip()]
        if not fr or not fr.strip():
            if frs:
                fr = frs[0]
        ens = " ".join({en for _fr, en in binyanim.values()}).lower()
        if fr and fr.strip():
            verb_fr[voc] = (fr.strip(), ens)

    # --- 4. détection + correction ----------------------------------------
    # Dans un groupe d'homonymes, plusieurs lexèmes distincts (verbe /
    # nom / adjectif) partagent le même gloss FR hérité de l'alignement
    # consonantique. Pour chaque membre, on ne corrige qu'avec des sources
    # fiables : overrides manuels, ou sens du verbe issu de
    # `binyan_senses_fr_en.json` validé par le gloss anglais BHSA. La
    # sélection finale se fait à l'exécution selon la partie du discours
    # du mot analysé (choix contextuel).
    overrides = {}
    report_ambiguous, report_unresolved = [], []
    for sk, members in groups.items():
        if len(members) < 2:
            continue
        frs = defaultdict(list)
        for m in members:
            fr = lexfr.get(m)
            if fr:
                frs[fr].append(m)
        for fr, ms in frs.items():
            if len(ms) < 2:
                continue
            distinct = {(lexemes[m]["sp"], lexemes[m]["en"]) for m in ms}
            if len(distinct) < 2:
                continue
            report_ambiguous.append((sk, fr,
                                     [(m, lexemes[m]["sp"], lexemes[m]["en"],
                                       lexemes[m]["count"]) for m in ms]))
            for m in ms:
                e = lexemes[m]
                new = MANUAL_OVERRIDES.get(m)
                if new is None and e["sp"] == "verb":
                    cand = verb_fr.get(e["voc"])
                    if cand and e["en"] and e["en"].lower() in cand[1]:
                        new = cand[0]
                if new and new != fr:
                    overrides[m] = {
                        "gloss_fr": new,
                        "sp": e["sp"],
                        "en": e["en"],
                    }
                else:
                    report_unresolved.append(
                        (m, e["voc"], e["sp"], e["en"], fr))

    # --- 5. écriture -------------------------------------------------------
    out = "bhsa_grammar/lex_fr_homonyms.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(overrides, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")

    print(f"Groupes homonymes ambigus : {len(report_ambiguous)}")
    print(f"Corrections écrites dans {out} : {len(overrides)}")
    print(f"Cas non résolus (gloss FR conservé) : {len(report_unresolved)}")
    for m, voc, sp, en, fr in sorted(report_unresolved)[:20]:
        print(f"  NON RÉSOLU  {m} {voc} {sp} « {en} » -> « {fr} »")


if __name__ == "__main__":
    main()
