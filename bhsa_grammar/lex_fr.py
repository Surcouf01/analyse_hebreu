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

from ._paths import resource_dir

_CACHE = None
_HOMONYMS_CACHE = None


def _load():
    global _CACHE
    if _CACHE is None:
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "lex_fr.json")
        if not os.path.isfile(path):
            path = os.path.join(resource_dir(), "lex_fr.json")
        try:
            with open(path, encoding="utf-8") as f:
                _CACHE = json.load(f)
        except (OSError, ValueError):
            _CACHE = {}
    return _CACHE


def _load_homonyms():
    """Corrections d'homonymes : {lex_id: {gloss_fr, sp, en}}.

    Le lexique principal a été aligné sur les consonnes du lemme pointé :
    les lexèmes BHSA homographes (ex. עור « peau » / עור « réveiller »)
    y partagent le même gloss. Ce fichier, généré par
    ``scripts/build_lex_fr_homonyms.py``, redonne à chaque homonyme son
    sens propre, appliqué seulement si la partie du discours du mot
    analysé correspond (choix selon le contexte).
    """
    global _HOMONYMS_CACHE
    if _HOMONYMS_CACHE is None:
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "lex_fr_homonyms.json")
        if not os.path.isfile(path):
            path = os.path.join(resource_dir(), "lex_fr_homonyms.json")
        try:
            with open(path, encoding="utf-8") as f:
                _HOMONYMS_CACHE = json.load(f)
        except (OSError, ValueError):
            _HOMONYMS_CACHE = {}
    return _HOMONYMS_CACHE


def gloss_fr(lex_id, sp=None):
    """Gloss français d'un lemme BHSA (feature `lex`), ou ''.

    ``sp`` est la partie du discours du mot analysé (feature `sp`, ex.
    ``verb``, ``subs``) : quand elle est fournie et qu'une correction
    d'homonyme existe pour ce lemme avec la même partie du discours, la
    correction est préférée au gloss générique (ex. יָעִיר Deut 32:11,
    verbe עור « éveiller » et non le substantif « peau »).
    """
    if not lex_id:
        return ""
    if sp:
        hom = _load_homonyms().get(lex_id)
        if hom and hom.get("sp") == sp and hom.get("gloss_fr"):
            return hom["gloss_fr"]
    return _load().get(lex_id, "")


def best_gloss(lex_id, en_gloss, sp=None):
    """Renvoie le gloss français si disponible, sinon le gloss anglais."""
    fr = gloss_fr(lex_id, sp=sp)
    return fr if fr else (en_gloss or "")
