"""Gloss français par lemme, alignés sur la base BHSA via le lexique
Strong hébreu-français de Bible Strong (STEP interlinear FR).

Les traductions proviennent de la base interlinéaire STEP en français
(assets.bible-strong.app, « bible-step-interlinear-fr.sqlite », CC BY 4.0),
alignées sur les lexèmes BHSA par les consonnes du lemme hébreu pointé.
Les ~25 préfixes/particules grammaticaux sont corrigés à la main ; les
lemmes non couverts retombent sur le gloss anglais de la BHSA.
"""

import json
import os

_CACHE = None


def _load():
    global _CACHE
    if _CACHE is None:
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "lex_fr.json")
        try:
            with open(path, encoding="utf-8") as f:
                _CACHE = json.load(f)
        except (OSError, ValueError):
            _CACHE = {}
    return _CACHE


def gloss_fr(lex_id):
    """Renvoie le gloss français d'un lemme BHSA (feature `lex`), ou ''."""
    if not lex_id:
        return ""
    return _load().get(lex_id, "")


def best_gloss(lex_id, en_gloss):
    """Renvoie le gloss français si disponible, sinon le gloss anglais."""
    fr = gloss_fr(lex_id)
    return fr if fr else (en_gloss or "")
