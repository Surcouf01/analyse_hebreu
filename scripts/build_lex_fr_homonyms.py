#!/usr/bin/env python3
"""Collecte les homonymes BHSA et corrige les glosses français ambigus.

Le lexique `bhsa_grammar/lex_fr.json` a été aligné sur les consonnes du lemme
pointé ; les lexèmes BHSA homographes (ex. עור « peau » / עור « réveiller »)
ont donc reçu le même gloss français. Ce script :

  1. collecte les groupes d'homonymes BHSA (lemmes de même squelette
     consonantique, marqueurs de discours retirés) ;
  2. détecte les groupes où plusieurs membres partagent le même gloss FR
     alors que la BHSA les distingue (gloss EN / partie du discours) ;
  3. propose pour chaque membre une correction, par priorité :
       a. curation manuelle (`bhsa_grammar/lex_fr_homonyms_curation.json`,
          format {lex_id: "gloss FR"} — priorité maximale) ;
       b. sens français du verbe depuis `binyan_senses_fr_en.json`,
          validé par le gloss anglais BHSA ;
  4. pour les cas restants, écrit une traduction par défaut provenant de
     l'anglais, suffixée « (en) » pour signaler l'absence de traduction
     française vérifiée ;
  5. écrit `bhsa_grammar/lex_fr_homonyms.json` : {lex_id: {gloss_fr, sp, en}}
     — utilisé à l'exécution par `bhsa_grammar.lex_fr` en accord avec la
     partie du discours du mot analysé (choix selon le contexte).

Usage :
    BHSA_DATA=... python scripts/build_lex_fr_homonyms.py

Pour affiner les cas « (en) », éditer
`bhsa_grammar/lex_fr_homonyms_curation.json` puis relancer : les entrées
curées remplacent les traductions par défaut.
"""

import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bhsa_grammar import load_corpus  # noqa: E402

SKELETON_RE = re.compile(r"[/\[\]=\d]+$")

# Curation manuelle, prioritaire : lex_id BHSA -> gloss FR vérifié.
CURATION_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..",
    "bhsa_grammar", "lex_fr_homonyms_curation.json")

# Gloss anglais inutilisables comme traduction par défaut (placeholders
# BHSA entre chevrons ou gloss vide).
UNUSABLE_EN = re.compile(r"^<.*>$")


def skeleton(lex):
    return SKELETON_RE.sub("", lex or "")


def main():
    api = load_corpus()
    F, L = api.F, api.L

    lexfr = json.load(open("bhsa_grammar/lex_fr.json", encoding="utf-8"))
    senses = json.load(open("bhsa_grammar/binyan_senses_fr_en.json",
                            encoding="utf-8"))
    try:
        with open(CURATION_PATH, encoding="utf-8") as fh:
            manual = json.load(fh)
    except (OSError, ValueError):
        manual = {}

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

    # Dictionnaire FR -> EN construit sur les lemmes non ambigus : sert à
    # vérifier si le gloss FR partagé peut être une traduction correcte du
    # gloss EN du membre (auquel cas on le conserve tel quel).
    fr2en = defaultdict(set)
    for sk, members in groups.items():
        if len(members) != 1:
            continue
        m = members[0]
        fr = lexfr.get(m)
        if fr and lexemes[m]["en"] and not UNUSABLE_EN.match(lexemes[m]["en"]):
            fr2en[fr].add(lexemes[m]["en"].lower())

    def fr_matches_en(fr, en):
        """Le gloss FR est-il une traduction plausible du gloss EN ?"""
        if not en or UNUSABLE_EN.match(en):
            return True
        cands = fr2en.get(fr)
        if not cands:
            return False
        return en.lower() in cands

    # --- 4. détection + correction ----------------------------------------
    # Dans un groupe d'homonymes, plusieurs lexèmes distincts (verbe /
    # nom / adjectif) partagent le même gloss FR hérité de l'alignement
    # consonantique. Pour chaque membre, par priorité : curation manuelle,
    # sens verbal validé, sinon traduction par défaut « EN (en) ». La
    # sélection finale se fait à l'exécution selon la partie du discours
    # du mot analysé (choix contextuel).
    overrides = {}
    n_cured = n_senses = n_default = 0
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
            # Le gloss FR partagé « appartient » au membre le plus fréquent
            # du groupe (c'est lui que l'alignement consonantique a capté) :
            # il conserve le gloss ; les autres membres sont corrigés.
            owner = max(ms, key=lambda x: lexemes[x]["count"])
            for m in ms:
                if m == owner:
                    continue
                e = lexemes[m]
                new = manual.get(m)
                source = "curation" if new else None
                if new is None and e["sp"] == "verb":
                    cand = verb_fr.get(e["voc"])
                    if cand and e["en"] and e["en"].lower() in cand[1]:
                        new = cand[0]
                        source = "binyan_senses"
                if new and new != fr:
                    overrides[m] = {
                        "gloss_fr": new,
                        "sp": e["sp"],
                        "en": e["en"],
                    }
                    if source == "curation":
                        n_cured += 1
                    else:
                        n_senses += 1
                    continue
                # Non résolu : conserver le gloss FR s'il est déjà une
                # traduction plausible du gloss EN ; sinon traduction par
                # défaut depuis l'anglais, suffixée « (en) » tant qu'aucune
                # curation ne la remplace.
                en = (e["en"] or "").strip()
                if fr_matches_en(fr, en):
                    continue
                if en and en != fr:
                    overrides[m] = {
                        "gloss_fr": f"{en} (en)",
                        "sp": e["sp"],
                        "en": e["en"],
                    }
                    n_default += 1
                else:
                    report_unresolved.append(
                        (m, e["voc"], e["sp"], e["en"], fr))

    # --- 5. écriture -------------------------------------------------------
    out = "bhsa_grammar/lex_fr_homonyms.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(overrides, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")

    print(f"Groupes homonymes ambigus : {len(report_ambiguous)}")
    print(f"Corrections écrites dans {out} : {len(overrides)} "
          f"(curation : {n_cured}, sens verbaux : {n_senses}, "
          f"défaut « (en) » : {n_default})")
    print(f"Cas sans gloss utilisable (gloss FR conservé) : {len(report_unresolved)}")
    for m, voc, sp, en, fr in sorted(report_unresolved)[:20]:
        print(f"  NON RÉSOLU  {m} {voc} {sp} « {en} » -> « {fr} »")


if __name__ == "__main__":
    main()
