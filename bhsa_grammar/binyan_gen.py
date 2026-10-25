"""Conjugaison d'un verbe hébreu dans tous les binyanim (mode « binyanim »).

Étant donné un mot hébreu conjugué ou une racine trilitaire (ex. שמר), le
module :

  1. identifie le verbe (lemme BHSA) et sa racine trilitaire ;
  2. détermine s'il s'agit d'un verbe fort (shalem) ou faible, et la
     catégorie du verbe faible (pe-alef/guttural, ayin-guttural,
     lamed-he, lamed-alef, lamed-guttural, creux « ayin-vav/ayin-yod »,
     double « ayin-ayin », pe-nun assimilé, etc.) ;
  3. génère la conjugaison complète dans chacun des 7 binyanim hébreux
     (qal, nifal, piel, pual, hitpael, hifil, hofal) : parfait (qatal),
     imparfait (yiqtol), impératif, infinitifs et participes, pour toutes
     les personnes (1re/2e/3e, masculin/féminin, singulier/pluriel).

Les gabarits vocaliques sont ceux du verbe fort (shalem), extraits des
formes dominantes attestées dans la base BHSA. Pour les verbes faibles,
des ajustements réguliers sont appliqués : verbes ל״ה (élision de la 3e
radicale, terminaison ה/ת/י), gutturaux (voyelles de compensation
patah/ségol), creux (métaphonie), pe-nun (assimilation au daguesh fort).

Les formes produites sont **paradigmatiques** : pour les cellules non
attestées dans le texte biblique (ex. impératif hofal), la forme régulière
est construite par analogie.
"""

import os
import unicodedata

from .lex_fr import best_gloss, gloss_fr as _gloss_fr_pure
from ._paths import resource_dir

# Cache du lexique de sens par (lemme, binyan).
_SENSES_CACHE = None

# --- Binyanim (code BHSA, français, hébreu) -----------------------------------
# Ordre pédagogique classique : qal, nifal, piel, pual, hitpael, hifil, hofal.
BINYANIM = (
    ("qal", "qal (paal)", "פָּעַל"),
    ("nif", "nifal", "נִפְעַל"),
    ("piel", "piel", "פִּעֵל"),
    ("pual", "pual", "פֻּעַל"),
    ("hit", "hitpael", "הִתְפַּעֵל"),
    ("hif", "hifil", "הִפְעִיל"),
    ("hof", "hofal", "הָפְעַל"),
)

BINYAN_SENSE = {
    "qal": "actif simple",
    "nif": "moyen-passif / réfléchi-passif",
    "piel": "intensif actif",
    "pual": "intensif passif",
    "hit": "réfléchi / réciproque",
    "hif": "causatif actif",
    "hof": "causatif passif",
}

# Traduction du verbe dans chaque binyan, en français et en anglais, à partir
# du gloss du lemme (BHSA : gloss anglais ; lex_fr.json : gloss français).
# La BHSA ne fournit pas de gloss par binyan : la traduction est construite
# par périphrase d'après la valeur sémantique du binyan.
_BINYAN_TRANSLATION_FR = {
    "qal": "{v}",
    "nif": "être {pp}",
    "piel": "{v} (intensif)",
    "pual": "être {pp} (intensif)",
    "hit": "se {v}",
    "hif": "faire {v}",
    "hof": "être fait {v}",
}
_BINYAN_TRANSLATION_EN = {
    "qal": "{v}",
    "nif": "to be {pp}",
    "piel": "{v} (intensive)",
    "pual": "to be {pp} (intensive)",
    "hit": "to {v} oneself",
    "hif": "to cause to {v}",
    "hof": "to be made to {v}",
}

# Participe passé irrégulier des verbes anglais courants de la BHSA (les
# gloss de la base sont en anglais : keep, build, turn, ...).
_EN_IRREGULAR_PP = {
    "keep": "kept", "build": "built", "turn": "turned", "fall": "fallen",
    "sit": "sat", "send": "sent", "make": "made", "speak": "spoken",
    "write": "written", "eat": "eaten", "give": "given", "take": "taken",
    "know": "known", "come": "come", "go": "gone", "see": "seen",
    "say": "said", "do": "done", "find": "found", "hear": "heard",
    "bring": "brought", "buy": "bought", "teach": "taught",
    "think": "thought", "seek": "sought", "stand": "stood",
    "run": "ran", "rise": "risen", "be": "been", "have": "had",
    "love": "loved", "live": "lived", "die": "died", "rule": "ruled",
    "bear": "borne", "give": "given", "go out": "gone out",
}


def _en_participle(gloss):
    """Participe passé anglais du gloss BHSA (règles + irréguliers)."""
    if not gloss:
        return ""
    if gloss in _EN_IRREGULAR_PP:
        return _EN_IRREGULAR_PP[gloss]
    if gloss.endswith("e") and not gloss.endswith("ee"):
        return gloss + "d"
    if gloss.endswith(("ay", "ey", "oy")):
        return gloss + "ed"
    if gloss.endswith("y") and gloss[:-1].endswith(("b", "d", "g", "l",
                                                    "m", "n", "p", "r", "t")):
        return gloss[:-1] + "ied"
    return gloss + "ed"


def _fr_participe_passe(gloss):
    """Participe passé français du gloss (1er groupe -er, -ir/-re réguliers)."""
    if not gloss:
        return ""
    if gloss.endswith("er"):
        stem = gloss[:-2]
        if stem and stem[-1] in "éèê":
            stem = stem[:-1] + "é"
        return stem + "é"
    if gloss.endswith("ir"):
        return gloss[:-2] + "i"
    if gloss.endswith("re"):
        return gloss[:-2] + "u"
    return gloss


def _load_binyan_senses():
    """Charge le lexique de sens par (racine, binyan), s'il existe.

    binyan_senses_fr_en.json : {"ראה": {"binyan": ["fr", "en"], ...}} —
    les clés sont les racines hébraïques (consonnes nues, sans nikkud),
    plus lisibles à maintenir que les lemmes BHSA translittérés.
    Les sens par binyan proviennent du lexique BDB (Brown-Driver-Briggs,
    domaine public) via scripts/extract_binyan_senses.py (~1 000 racines,
    anglais), complétés manuellement en français pour certaines racines
    (ex. ראה : voir / apparaître / montrer). Toute racine/binyan
    absent retombe sur la périphrase générée.
    """
    import json
    import os
    global _SENSES_CACHE
    if _SENSES_CACHE is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "binyan_senses_fr_en.json")
        if not os.path.isfile(path):
            path = os.path.join(resource_dir(), "binyan_senses_fr_en.json")
        try:
            with open(path, encoding="utf-8") as fh:
                _SENSES_CACHE = json.load(fh)
        except (OSError, ValueError):
            _SENSES_CACHE = {}
    return _SENSES_CACHE


def binyan_translation(code, gloss_fr, gloss_en, root=None):
    """Traduction du verbe dans un binyan, en français et en anglais.

    Consulte d'abord le lexique de sens par (racine, binyan)\
    (binyan_senses_fr_en.json) : sens divergents réels documentés\
    (ex. ראה : qal « voir », nifal « apparaître », hifil « montrer »).
    À défaut, construit une périphrase à partir des gloss du lemme :
    « garder » → nifal « être gardé », hifil « faire garder »...
    Chaque langue n'est remplie que si le gloss source existe.
    Renvoie ("", "") si aucun gloss n'est disponible.
    """
    if root:
        root_entry = _load_binyan_senses().get(root, {})
        entry = root_entry.get(code)
        if entry and len(entry) >= 2 and (entry[0] or entry[1]):
            return entry[0] or "", entry[1] or ""
    v_fr = (gloss_fr or "").strip()
    v_en = (gloss_en or "").strip()
    pp_fr = _fr_participe_passe(v_fr) if v_fr else ""
    pp_en = _en_participle(v_en) if v_en else ""
    fr = _BINYAN_TRANSLATION_FR[code].format(v=v_fr, pp=pp_fr).strip() if v_fr else ""
    en = _BINYAN_TRANSLATION_EN[code].format(v=v_en, pp=pp_en).strip() if v_en else ""
    return fr, en

# --- Lettres et signes ---------------------------------------------------------
ALEF = "\u05D0"
HE = "\u05D4"
VAV = "\u05D5"
YOD = "\u05D9"
NUN = "\u05E0"
TAV = "\u05EA"
TET = "\u05D8"
MEM = "\u05DE"
END_MEM = "\u05DD"
END_NUN = "\u05DF"
GUTTURALS = (ALEF, HE, "\u05D7", "\u05E2")
WEAK_LETTERS = (ALEF, HE, VAV, YOD)
BEGADKEFAT = ("\u05D1", "\u05D2", "\u05D3", "\u05DB", "\u05E4", TAV)
FINALS = ("\u05DA", END_MEM, END_NUN, "\u05E3", "\u05E5")

PATAH = "\u05B7"
QAMATS = "\u05B8"
SEGOL = "\u05B6"
TSERE = "\u05B5"
HIREQ = "\u05B4"
HOLAM = "\u05B9"
QUBUTS = "\u05BB"
SHEVA = "\u05B0"
HATEF_PATAH = "\u05B2"
HATEF_SEGOL = "\u05B1"
HATAF_QAMATS = "\u05B3"
DAGESH = "\u05BC"
SHUREQ = VAV + DAGESH

# --- Personnes du paradigme (ps, gn, nu, libellé français) ---------------------
# gn="c" : commun (m/f) pour les 1res personnes.
# Ordre français : 1re, 2e, 3e personne ; singulier puis pluriel.
PERSONS = (
    ("p1", "c", "sg", "1re pers. sing. (je)"),
    ("p2", "m", "sg", "2e pers. masc. sing. (tu)"),
    ("p2", "f", "sg", "2e pers. fém. sing. (tu)"),
    ("p3", "m", "sg", "3e pers. masc. sing. (il)"),
    ("p3", "f", "sg", "3e pers. fém. sing. (elle)"),
    ("p1", "c", "pl", "1re pers. pl. (nous)"),
    ("p2", "m", "pl", "2e pers. masc. pl. (vous)"),
    ("p2", "f", "pl", "2e pers. fém. pl. (vous)"),
    ("p3", "m", "pl", "3e pers. masc. pl. (ils)"),
    ("p3", "f", "pl", "3e pers. fém. pl. (elles)"),
)

PERSONS_IMPV = (
    ("p2", "m", "sg", "2e pers. masc. sing. (tu)"),
    ("p2", "f", "sg", "2e pers. fém. sing. (tu)"),
    ("p2", "m", "pl", "2e pers. masc. pl. (vous)"),
    ("p2", "f", "pl", "2e pers. fém. pl. (vous)"),
)

# Terminaisons du parfait (suffixes pronominaux personnels) : la 2e/3e
# personne est marquée par un suffixe ; les gabarits ci-dessous l'incluent.
# Terminaisons de l'imparfait/impératif (préfixes + suffixes).
S_PERF = {
    ("p3", "m", "sg"): "",
    ("p3", "f", "sg"): QAMATS + HE,
    ("p2", "m", "sg"): SHEVA + TAV + QAMATS + DAGESH,
    ("p2", "f", "sg"): SHEVA + TAV + SHEVA + DAGESH,
    ("p1", "c", "sg"): SHEVA + TAV + HIREQ + YOD,
    # Parfait 3e pers. pl. : la BHSA ne connaît qu'une seule forme,
    # commune aux masculin et féminin, en -ּוּ (shureq ; les 2756
    # parfaites qal 3pl de la base sont toutes en -וּ, genre
    # « unknown »). La terminaison féminine -ָה (qatlāh) ne survit
    # qu'aux personnes du singulier ; au pluriel du parfait, l'hébreu
    # biblique emploie la forme commune (Gesenius §44g, §47k).
    # La 3fp distincte n'existe qu'à l'imparfait/jussif
    # (תִּכְתֹּבְנָה).
    ("p3", "m", "pl"): SHUREQ,
    ("p3", "f", "pl"): SHUREQ,
    ("p2", "m", "pl"): SHEVA + TAV + SEGOL + DAGESH + END_MEM,
    ("p2", "f", "pl"): TAV + SEGOL + DAGESH + END_NUN,
    ("p1", "c", "pl"): SHEVA + NUN + SHUREQ,
}

# Gabarits de l'imparfait : préfixe + racine ; le préfixe porte le daguesh
# quand la racine commence par une begadkefat (ex. שָׁמַר -> יִשְׁמֹר).
IMPF_PREF = {
    ("p3", "m", "sg"): (YOD + HIREQ, DAGESH),
    ("p3", "f", "sg"): (TAV + HIREQ, DAGESH),
    ("p2", "m", "sg"): (TAV + HIREQ, DAGESH),
    ("p2", "f", "sg"): (TAV + HIREQ, ""),
    ("p1", "c", "sg"): (ALEF + SEGOL, ""),
    ("p3", "m", "pl"): (YOD + HIREQ, DAGESH),
    ("p3", "f", "pl"): (TAV + HIREQ, DAGESH),
    ("p2", "m", "pl"): (TAV + HIREQ, DAGESH),
    ("p2", "f", "pl"): (TAV + HIREQ, DAGESH),
    ("p1", "c", "pl"): (NUN + HIREQ, ""),
}


# --- Gabarits du verbe fort (racine P1-P2-P3) ----------------------------------
# Ordre des codepoints : consonne, voyelle, daguesh (convention BHSA).

# QAL : parfait = qatal, imparfait = yiqtol, impératif, infinitifs, participes.
QAL_PERF_BASE = PATAH   # קָטַל : P1-qamats P2-patah P3
QAL_IMPF_V = HOLAM      # יִקְטֹל : P2-sheva P3-holam
QAL_IMPF_F_SG_END = HIREQ + YOD   # תִּקְטְלִי
QAL_IMPF_F_PL_END = SHEVA + NUN + QAMATS + HE   # תִּקְטֹלְנָה


def _qal_perf(p1, p2, p3):
    return {
        ("p3", "m", "sg"): p1 + QAMATS + p2 + PATAH + p3,
        ("p3", "f", "sg"): p1 + QAMATS + p2 + SHEVA + p3 + QAMATS + HE,
        ("p2", "m", "sg"): p1 + QAMATS + p2 + PATAH + p3 + S_PERF[("p2", "m", "sg")],
        ("p2", "f", "sg"): p1 + QAMATS + p2 + PATAH + p3 + S_PERF[("p2", "f", "sg")],
        ("p1", "c", "sg"): p1 + QAMATS + p2 + PATAH + p3 + S_PERF[("p1", "c", "sg")],
        ("p3", "m", "pl"): p1 + QAMATS + p2 + SHEVA + p3 + SHUREQ,
        # 3fp = forme commune en -ו׼ (cf. S_PERF).
        ("p3", "f", "pl"): p1 + QAMATS + p2 + SHEVA + p3 + SHUREQ,
        ("p2", "m", "pl"): p1 + SHEVA + p2 + PATAH + p3 + S_PERF[("p2", "m", "pl")],
        ("p2", "f", "pl"): p1 + SHEVA + p2 + PATAH + p3 + S_PERF[("p2", "f", "pl")],
        ("p1", "c", "pl"): p1 + QAMATS + p2 + PATAH + p3 + S_PERF[("p1", "c", "pl")],
    }


def _qal_impf(p1, p2, p3):
    d = {}
    for key, (pref, _d) in IMPF_PREF.items():
        dash = DAGESH if p1 in BEGADKEFAT else ""
        if key[0] == "p3" and key[1] == "f" and key[2] == "pl":
            body = p1 + SHEVA + p2 + PATAH + DAGESH + p3 + QAL_IMPF_F_PL_END
        elif key[0] == "p2" and key[1] == "f" and key[2] == "sg":
            body = p1 + SHEVA + p2 + SHEVA + DAGESH + p3 + QAL_IMPF_F_SG_END
        elif key[0] == "p2" and key[1] == "f" and key[2] == ("p2", "f", "pl")[2]:
            body = p1 + SHEVA + p2 + PATAH + DAGESH + p3 + QAL_IMPF_F_PL_END
        elif key[0] == "p1" and key[2] == "pl":
            body = p1 + SHEVA + p2 + SHEVA + p3 + QAMATS + HE
        elif key[0] == "p1" and key[2] == "sg":
            body = p1 + SHEVA + p2 + HOLAM + p3
        elif nu_is_pl(key):
            body = p1 + SHEVA + p2 + SHEVA + DAGESH + p3 + SHUREQ
        else:
            body = p1 + SHEVA + p2 + HOLAM + (DAGESH if p3 in BEGADKEFAT else "") + p3
        d[key] = pref + dash + body if key[0] != "p1" or key[2] == "sg" else pref + body
    return d


def nu_is_pl(key):
    return key[2] == "pl" and not (key[0] == "p2" and key[1] == "f")


def _qal_impv(p1, p2, p3):
    dash = DAGESH if p1 in BEGADKEFAT else ""
    return {
        ("p2", "m", "sg"): p1 + dash + SHEVA + p2 + HOLAM + p3,
        ("p2", "f", "sg"): p1 + dash + HIREQ + p2 + SHEVA + DAGESH + p3 + HIREQ + YOD,
        ("p2", "m", "pl"): p1 + dash + HIREQ + p2 + SHEVA + p3 + SHUREQ,
        ("p2", "f", "pl"): p1 + dash + SHEVA + p2 + HOLAM + p3 + SHEVA + NUN + QAMATS + HE,
    }


# --- NIFAL ----------------------------------------------------------------------
def _nif_perf(p1, p2, p3):
    return {
        ("p3", "m", "sg"): NUN + HIREQ + p1 + SHEVA + p2 + PATAH + p3,
        ("p3", "f", "sg"): NUN + HIREQ + p1 + SHEVA + p2 + SHEVA + p3 + QAMATS + HE,
        ("p2", "m", "sg"): NUN + HIREQ + p1 + SHEVA + p2 + PATAH + DAGESH + p3 + S_PERF[("p2", "m", "sg")],
        ("p2", "f", "sg"): NUN + HIREQ + p1 + SHEVA + p2 + PATAH + DAGESH + p3 + S_PERF[("p2", "f", "sg")],
        ("p1", "c", "sg"): NUN + HIREQ + p1 + SHEVA + p2 + PATAH + DAGESH + p3 + S_PERF[("p1", "c", "sg")],
        ("p3", "m", "pl"): NUN + HIREQ + p1 + SHEVA + p2 + SHEVA + p3 + SHUREQ,
        # 3fp = forme commune en -ו׼ (cf. S_PERF).
        ("p3", "f", "pl"): NUN + HIREQ + p1 + SHEVA + p2 + SHEVA + p3 + SHUREQ,
        ("p2", "m", "pl"): NUN + HIREQ + p1 + SHEVA + p2 + PATAH + DAGESH + p3 + S_PERF[("p2", "m", "pl")],
        ("p2", "f", "pl"): NUN + HIREQ + p1 + SHEVA + p2 + PATAH + DAGESH + p3 + S_PERF[("p2", "f", "pl")],
        ("p1", "c", "pl"): NUN + HIREQ + p1 + SHEVA + p2 + PATAH + DAGESH + p3 + S_PERF[("p1", "c", "pl")],
    }


def _nif_impf(p1, p2, p3):
    out = {}
    for key, (pref, _) in IMPF_PREF.items():
        dash = DAGESH if p1 in BEGADKEFAT else ""
        if key[0] == "p1":
            body = p1 + QAMATS + DAGESH + p2 + TSERE + p3
            if key[2] == "pl":
                body = p1 + QAMATS + DAGESH + p2 + SHEVA + p3 + QAMATS + HE
        elif key[0] == "p2" and key[1] == "f" and key[2] == "sg":
            body = p1 + QAMATS + DAGESH + p2 + TSERE + p3 + HIREQ + YOD
        elif key[0] == "p2" and key[1] == "f" and key[2] == "pl":
            body = p1 + QAMATS + DAGESH + p2 + PATAH + p3 + SHEVA + NUN + QAMATS + HE
        elif key[0] == "p3" and key[1] == "f" and key[2] == "pl":
            body = p1 + QAMATS + DAGESH + p2 + PATAH + p3 + SHEVA + NUN + QAMATS + HE
        elif nu_is_pl(key):
            body = p1 + QAMATS + DAGESH + p2 + SHEVA + p3 + SHUREQ
        else:
            body = p1 + QAMATS + DAGESH + p2 + TSERE + p3
        out[key] = pref + dash + body
    return out


def _nif_impv(p1, p2, p3):
    return {
        ("p2", "m", "sg"): HE + HIREQ + p1 + QAMATS + DAGESH + p2 + TSERE + p3,
        ("p2", "f", "sg"): HE + HIREQ + p1 + QAMATS + DAGESH + p2 + TSERE + p3 + HIREQ + YOD,
        ("p2", "m", "pl"): HE + HIREQ + p1 + QAMATS + DAGESH + p2 + SHEVA + p3 + SHUREQ,
        ("p2", "f", "pl"): HE + HIREQ + p1 + QAMATS + DAGESH + p2 + PATAH + p3 + SHEVA + NUN + QAMATS + HE,
    }


NIF_INFC = HE + HIREQ + "P1" + QAMATS + DAGESH + "P2" + TSERE + "P3"
NIF_INFA = NUN + HIREQ + "P1" + SHEVA + "P2" + HOLAM + "P3"


def _nif_ptc(p1, p2, p3):
    return {
        ("ptca", "m", "sg"): NUN + HIREQ + p1 + SHEVA + p2 + QAMATS + DAGESH + p3,
        ("ptca", "m", "pl"): NUN + HIREQ + p1 + SHEVA + p2 + QAMATS + DAGESH + p3 + HIREQ + YOD + END_MEM,
        ("ptca", "f", "sg"): NUN + HIREQ + p1 + SHEVA + p2 + QAMATS + DAGESH + p3 + QAMATS + HE,
        ("ptca", "f", "pl"): NUN + HIREQ + DAGESH + p1 + SHEVA + p2 + QAMATS + DAGESH + p3 + HOLAM + VAV + TSERE + TAV,
    }


# --- PIEL ------------------------------------------------------------------------
def _piel_perf(p1, p2, p3):
    return {
        ("p3", "m", "sg"): p1 + HIREQ + DAGESH + p2 + SEGOL + DAGESH + p3,
        ("p3", "f", "sg"): p1 + HIREQ + DAGESH + p2 + SHEVA + DAGESH + p3 + QAMATS + HE,
        ("p2", "m", "sg"): p1 + HIREQ + DAGESH + p2 + SEGOL + DAGESH + p3 + S_PERF[("p2", "m", "sg")],
        ("p2", "f", "sg"): p1 + HIREQ + DAGESH + p2 + SEGOL + DAGESH + p3 + S_PERF[("p2", "f", "sg")],
        ("p1", "c", "sg"): p1 + HIREQ + DAGESH + p2 + SEGOL + DAGESH + p3 + S_PERF[("p1", "c", "sg")],
        ("p3", "m", "pl"): p1 + HIREQ + DAGESH + p2 + SHEVA + DAGESH + p3 + SHUREQ,
        # 3fp = forme commune en -וּ (cf. S_PERF) : le parfait 3fp
        # biblique n'a pas de terminaison propre.
        ("p3", "f", "pl"): p1 + HIREQ + DAGESH + p2 + SHEVA + DAGESH + p3 + SHUREQ,
        ("p2", "m", "pl"): p1 + HIREQ + DAGESH + p2 + SEGOL + DAGESH + p3 + S_PERF[("p2", "m", "pl")],
        ("p2", "f", "pl"): p1 + HIREQ + DAGESH + p2 + SEGOL + DAGESH + p3 + S_PERF[("p2", "f", "pl")],
        ("p1", "c", "pl"): p1 + HIREQ + DAGESH + p2 + SEGOL + DAGESH + p3 + S_PERF[("p1", "c", "pl")],
    }


def _piel_impf(p1, p2, p3):
    """Imparfait piel.

    Le sheva du préfixe personnel (תְּ, יְ, נְ) est simple : la 1re
    radicale ne porte PAS de dagesh — même begadkefat (תְּדַבֵּרִי,
    יְבָרֵךְ, אֲדַבֵּר ; la BHSA n'atteste aucun dagesh sur P1 dans
    les 492 formes de piel impf à P1 begadkefat, y compris après le
    hatef de la 1re personne). Le dagesh fort du piel est sur P2
    (redoublement), pas sur P1.
    """
    out = {}
    for key, (pref, _) in IMPF_PREF.items():
        if key[0] == "p1" and key[2] == "sg":
            out[key] = ALEF + HATAF_QAMATS + p1 + PATAH + p2 + TSERE + DAGESH + p3
        elif key[0] == "p1" and key[2] == "pl":
            out[key] = NUN + SHEVA + p1 + PATAH + p2 + TSERE + DAGESH + p3
        elif key[0] == "p2" and key[1] == "f" and key[2] == "sg":
            out[key] = TAV + SHEVA + p1 + PATAH + p2 + TSERE + DAGESH + p3 + HIREQ + YOD
        elif key[0] == "p2" and key[1] == "f" and key[2] == "pl":
            out[key] = TAV + SHEVA + p1 + PATAH + p2 + TSERE + DAGESH + p3 + SHEVA + NUN + QAMATS + HE
        elif key[0] == "p3" and key[1] == "f" and key[2] == "pl":
            out[key] = TAV + SHEVA + p1 + PATAH + p2 + TSERE + DAGESH + p3 + SHEVA + NUN + QAMATS + HE
        elif key[0] == "p2" and key[1] == "m" and key[2] == "sg":
            out[key] = TAV + SHEVA + p1 + PATAH + p2 + TSERE + DAGESH + p3
        elif key[0] == "p2" and key[1] == "m" and key[2] == "pl":
            out[key] = TAV + SHEVA + p1 + PATAH + p2 + SHEVA + DAGESH + p3 + SHUREQ
        elif key[0] == "p3" and key[1] == "m" and key[2] == "sg":
            out[key] = YOD + SHEVA + p1 + PATAH + p2 + TSERE + DAGESH + p3
        elif key[0] == "p3" and key[1] == "m" and key[2] == "pl":
            out[key] = YOD + SHEVA + p1 + PATAH + p2 + SHEVA + DAGESH + p3 + SHUREQ
        elif key[0] == "p3" and key[1] == "f" and key[2] == "sg":
            out[key] = TAV + SHEVA + p1 + PATAH + p2 + TSERE + DAGESH + p3
        else:
            out[key] = ""
    return out


def _piel_impv(p1, p2, p3):
    # Daguesh lene sur P1 (début de mot, après son patah) : légitime
    # pour une begadkefat (דַּבֵּר, גַּרֵשׁ) ; la BHSA atteste aussi la
    # graphie sans lene (דַבֵּר). Jamais sur une non-begadkefat.
    dash = DAGESH if p1 in BEGADKEFAT else ""
    return {
        ("p2", "m", "sg"): p1 + PATAH + dash + p2 + TSERE + DAGESH + p3,
        ("p2", "f", "sg"): p1 + PATAH + dash + p2 + SHEVA + DAGESH + p3 + HIREQ + YOD,
        ("p2", "m", "pl"): p1 + PATAH + dash + p2 + SHEVA + DAGESH + p3 + SHUREQ,
        ("p2", "f", "pl"): p1 + PATAH + dash + p2 + TSERE + DAGESH + p3 + SHEVA + NUN + QAMATS + HE,
    }


PIEL_INFC = "P1" + PATAH + "P2" + TSERE + DAGESH + "P3"
PIEL_INFA = PIEL_INFC


def _piel_ptc(p1, p2, p3):
    return {
        ("ptca", "m", "sg"): MEM + SHEVA + p1 + PATAH + p2 + TSERE + DAGESH + p3,
        ("ptca", "m", "pl"): MEM + SHEVA + p1 + PATAH + p2 + SHEVA + DAGESH + p3 + HIREQ + YOD + END_MEM,
        ("ptca", "f", "sg"): MEM + SHEVA + p1 + PATAH + p2 + SEGOL + DAGESH + p3 + SEGOL + TAV,
        ("ptca", "f", "pl"): MEM + SHEVA + p1 + PATAH + p2 + SHEVA + DAGESH + p3 + HOLAM + VAV + TSERE + TAV,
    }


# --- PUAL ------------------------------------------------------------------------
def _pual_perf(p1, p2, p3):
    return {
        ("p3", "m", "sg"): p1 + QUBUTS + p2 + PATAH + DAGESH + p3,
        ("p3", "f", "sg"): p1 + QUBUTS + p2 + SHEVA + DAGESH + p3 + QAMATS + HE,
        ("p2", "m", "sg"): p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + S_PERF[("p2", "m", "sg")],
        ("p2", "f", "sg"): p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + S_PERF[("p2", "f", "sg")],
        ("p1", "c", "sg"): p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + S_PERF[("p1", "c", "sg")],
        ("p3", "m", "pl"): p1 + QUBUTS + p2 + SHEVA + DAGESH + p3 + SHUREQ,
        # 3fp = forme commune en -וּ (cf. S_PERF).
        ("p3", "f", "pl"): p1 + QUBUTS + p2 + SHEVA + DAGESH + p3 + SHUREQ,
        ("p2", "m", "pl"): p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + S_PERF[("p2", "m", "pl")],
        ("p2", "f", "pl"): p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + S_PERF[("p2", "f", "pl")],
        ("p1", "c", "pl"): p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + S_PERF[("p1", "c", "pl")],
    }

def _pual_impf(p1, p2, p3):
    """Imparfait pual : pas de dagesh sur P1 (cf. _piel_impf ; la BHSA
    n'en atteste aucune sur les 37 formes à P1 begadkefat : תְּבֻשַּׁל,
    יְכֻפַּר...)."""
    out = {}
    for key, (pref, _) in IMPF_PREF.items():
        if key[0] == "p1" and key[2] == "sg":
            out[key] = ALEF + HATAF_QAMATS + p1 + QUBUTS + p2 + PATAH + DAGESH + p3
        elif key[0] == "p1" and key[2] == "pl":
            out[key] = NUN + SHEVA + p1 + QUBUTS + p2 + PATAH + DAGESH + p3
        elif key[0] == "p2" and key[1] == "f" and key[2] == "sg":
            out[key] = TAV + SHEVA + p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + HIREQ + YOD
        elif key[0] == "p2" and key[1] == "f" and key[2] == "pl":
            out[key] = TAV + SHEVA + p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + SHEVA + NUN + QAMATS + HE
        elif key[0] == "p3" and key[1] == "f" and key[2] == "pl":
            out[key] = TAV + SHEVA + p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + SHEVA + NUN + QAMATS + HE
        elif key[0] == "p2" and key[1] == "m" and key[2] == "sg":
            out[key] = TAV + SHEVA + p1 + QUBUTS + p2 + PATAH + DAGESH + p3
        elif key[0] == "p2" and key[1] == "m" and key[2] == "pl":
            out[key] = TAV + SHEVA + p1 + QUBUTS + p2 + SHEVA + DAGESH + p3 + SHUREQ
        elif key[0] == "p3" and key[1] == "m" and key[2] == "sg":
            out[key] = YOD + SHEVA + p1 + QUBUTS + p2 + PATAH + DAGESH + p3
        elif key[0] == "p3" and key[1] == "m" and key[2] == "pl":
            out[key] = YOD + SHEVA + p1 + QUBUTS + p2 + SHEVA + DAGESH + p3 + SHUREQ
        elif key[0] == "p3" and key[1] == "f" and key[2] == "sg":
            out[key] = TAV + SHEVA + p1 + QUBUTS + p2 + PATAH + DAGESH + p3
        else:
            out[key] = ""
    return out


def _pual_impv(p1, p2, p3):
    return {
        ("p2", "m", "sg"): p1 + QUBUTS + p2 + PATAH + DAGESH + p3,
        ("p2", "f", "sg"): p1 + QUBUTS + p2 + SHEVA + DAGESH + p3 + HIREQ + YOD,
        ("p2", "m", "pl"): p1 + QUBUTS + p2 + SHEVA + DAGESH + p3 + SHUREQ,
        ("p2", "f", "pl"): p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + SHEVA + NUN + QAMATS + HE,
    }


PUAL_INFC = "P1" + QUBUTS + "P2" + PATAH + DAGESH + "P3"


def _pual_ptc(p1, p2, p3):
    return {
        ("ptca", "m", "sg"): MEM + SHEVA + p1 + QUBUTS + p2 + PATAH + DAGESH + p3,
        ("ptca", "m", "pl"): MEM + SHEVA + p1 + QUBUTS + p2 + SHEVA + DAGESH + p3 + HIREQ + YOD + END_MEM,
        ("ptca", "f", "sg"): MEM + SHEVA + p1 + QUBUTS + p2 + SEGOL + DAGESH + p3 + SEGOL + TAV,
        ("ptca", "f", "pl"): MEM + SHEVA + p1 + QUBUTS + p2 + SHEVA + DAGESH + p3 + HOLAM + VAV + TSERE + TAV,
    }


# --- HITPAEL ---------------------------------------------------------------------
# Préformative הִתְ + racine ; la 2e radicale porte le daguesh fort.
# Métathèse du ת avec une 1re radicale sifflante (שׁ/שׂ/ס/ז/צ/נ...).
def _hit_meta(p1):
    """Vrai si le ת du hitpael se métathèse avec P1 sifflante/dentale."""
    return p1 in ("\u05E9", "\u05E9", "\u05E1", "\u05E6", "\u05D6", "\u05E0", "\u05EA", "\u05D8", "\u05E6")


def _hit_prefix(p1):
    """Préfixe hitpael et (pour la métathèse) segment ת initial du corps.

    Sans métathèse : הִתְ + corps ; avec métathèse (P1 sifflante
    ou dentale) : P1 + sheva, le ת (porteur du daguesh fort et du
    patah) ouvre le corps (הִשְׁתַּמֵּר).
    """
    if _hit_meta(p1):
        return p1 + SHEVA, TAV + DAGESH + PATAH
    return HE + HIREQ + TAV + SHEVA, ""


def _hit_perf(p1, p2, p3):
    pre, tav = _hit_prefix(p1)
    if tav:
        # Métathèse : P1 précède le ת, le corps est P2-P3
        # (הִשְׁתַּמֵּר, שָּׁמַרְתָּּ → הִשְׁתַּּמְרָה).
        stem3 = HE + HIREQ + pre + tav + p2 + TSERE + DAGESH + p3
        stem = HE + HIREQ + pre + tav + p2 + DAGESH + SHEVA + p3
    else:
        stem3 = pre + p1 + PATAH + p2 + HIREQ + DAGESH + p3
        stem = stem3 + SHEVA
    out = {}
    for key, end in S_PERF.items():
        if key == ("p3", "m", "sg"):
            out[key] = stem3
        else:
            out[key] = stem + end
    return out


def _hit_impf(p1, p2, p3):
    pre, tav = _hit_prefix(p1)
    meta = _hit_meta(p1)
    # M\u00e9tath\u00e8se : le \u05ea (daguesh fort + patah) ouvre le corps P2-P3,
    # P1 reste en t\u00eate apr\u00e8s le pr\u00e9fixe personnel
    # (\u05d0\u05b6\u05e9\u05b0\u05c1\u05ea\u05b7\u05bc\u05de\u05b5\u05bc\u05e8) ; sans m\u00e9tath\u00e8se le pr\u00e9fixe
    # personnel s'attache directement \u00e0 \u05d4\u05b4\u05ea\u05b0 (\u05d9\u05b4\u05ea\u05b0\u05e7\u05b7\u05bc\u05d8\u05b5\u05bc\u05dc).
    stem_sg = (tav + p2 + TSERE + DAGESH + p3
               if meta else TAV + SHEVA + p1 + PATAH + p2 + TSERE + DAGESH + p3)
    stem_pl = (tav + p2 + PATAH + DAGESH + p3 + SHEVA
               if meta else TAV + SHEVA + p1 + PATAH + p2 + SHEVA + DAGESH + p3)
    out = {}
    for key, (pref, _) in IMPF_PREF.items():
        if key[0] == "p1" and key[2] == "sg":
            out[key] = ALEF + SEGOL + pre + stem_sg if meta else ALEF + SEGOL + stem_sg
        elif key[0] == "p1" and key[2] == "pl":
            out[key] = NUN + HIREQ + pre + stem_pl if meta else NUN + HIREQ + stem_pl
        elif key[0] == "p2" and key[1] == "f" and key[2] == "sg":
            stem_fsg = (tav + p2 + PATAH + DAGESH + p3 + SHEVA + DAGESH
                        if meta
                        else TAV + SHEVA + p1 + PATAH + p2 + SHEVA + DAGESH + p3)
            out[key] = (TAV + HIREQ + pre + stem_fsg + HIREQ + YOD if meta
                        else TAV + HIREQ + stem_fsg + HIREQ + YOD)
        elif key[0] in ("p2", "p3") and key[2] == "pl" and key[1] == "f":
            stem_fpl = (tav + p2 + PATAH + DAGESH + p3 + PATAH
                        if meta
                        else TAV + SHEVA + p1 + PATAH + p2 + PATAH + p3)
            out[key] = (TAV + HIREQ + DAGESH + pre + stem_fpl + SHEVA + NUN + QAMATS + HE
                        if meta
                        else TAV + HIREQ + DAGESH + stem_fpl + SHEVA + NUN + QAMATS + HE)
        elif key[2] == "pl":
            out[key] = pref + pre + stem_pl if meta else pref + stem_pl
        else:
            out[key] = pref + pre + stem_sg if meta else pref + stem_sg
    return out


def _hit_impv(p1, p2, p3):
    pre, tav = _hit_prefix(p1)
    if tav:
        return {
            ("p2", "m", "sg"): HE + HIREQ + pre + tav + p2 + TSERE + DAGESH + p3,
            ("p2", "f", "sg"): HE + HIREQ + pre + tav + p2 + PATAH + DAGESH + p3 + SHEVA + DAGESH + HIREQ + YOD,
            ("p2", "m", "pl"): HE + HIREQ + pre + tav + p2 + PATAH + DAGESH + p3 + SHEVA + SHUREQ,
            ("p2", "f", "pl"): HE + HIREQ + pre + tav + p2 + PATAH + DAGESH + p3 + PATAH + SHEVA + NUN + QAMATS + HE,
        }
    dash = DAGESH if p1 in BEGADKEFAT else ""
    return {
        ("p2", "m", "sg"): pre + p1 + PATAH + dash + p2 + HIREQ + DAGESH + p3,
        ("p2", "f", "sg"): pre + p1 + PATAH + dash + p2 + SHEVA + DAGESH + p3 + HIREQ + YOD,
        ("p2", "m", "pl"): pre + p1 + PATAH + dash + p2 + SHEVA + DAGESH + p3 + SHUREQ,
        ("p2", "f", "pl"): pre + p1 + PATAH + dash + p2 + PATAH + p3 + SHEVA + NUN + QAMATS + HE,
    }


HIT_INFC = HE + HIREQ + TAV + SHEVA + "P1" + PATAH + DAGESH + "P2" + HIREQ + DAGESH + "P3"

# --- HIFIL -----------------------------------------------------------------------
def _hif_stem(p1, p2, p3, long_vowel=True):
    v = HIREQ + YOD if long_vowel else HIREQ
    return HE + HIREQ + p1 + SHEVA + p2 + v + p3


def _hif_perf(p1, p2, p3):
    base = HE + HIREQ + p1 + SHEVA + p2
    out = {}
    for key, end in S_PERF.items():
        if key == ("p3", "m", "sg"):
            out[key] = base + HIREQ + YOD + p3
        elif key == ("p3", "f", "sg"):
            out[key] = base + HIREQ + YOD + p3 + QAMATS + HE
        elif key[2] == "pl" and key[0] == "p3":
            # 3mp et 3fp : forme commune en -וּ (cf. S_PERF).
            out[key] = base + HIREQ + YOD + p3 + SHUREQ
        else:
            out[key] = HE + HIREQ + p1 + SHEVA + p2 + PATAH + p3 + end
    return out


def _hif_impf(p1, p2, p3):
    """Imparfait hifil.

    Le dagesh lene du préfixe porte sur le ת/נ/... du préfixe
    (תַּדַבֵּרִי-type), jamais sur P1 : la BHSA n'atteste
    aucun dagesh sur P1 dans les 369 formes de hifil impf à P1
    begadkefat (יַפְקֵד, תַּדֵשׁא, תַּבִיא…).
    """
    out = {}
    for key, (pref, dash) in IMPF_PREF.items():
        if key[0] == "p1" and key[2] == "sg":
            out[key] = ALEF + PATAH + p1 + SHEVA + p2 + HIREQ + YOD + p3
        elif key[0] == "p1" and key[2] == "pl":
            out[key] = NUN + PATAH + p1 + SHEVA + p2 + HIREQ + YOD + p3
        elif key[0] == "p2" and key[1] == "f" and key[2] == "sg":
            # Dagesh lene sur le ת du préfixe (תַּ), pas sur P1 :
            # la BHSA n'atteste pas de dagesh sur P1 (יַפְקֵד, תַּדֵשׁא).
            out[key] = TAV + PATAH + DAGESH + p1 + SHEVA + p2 + HIREQ + YOD + p3 + HIREQ + YOD
        elif key[0] in ("p2", "p3") and key[2] == "pl" and key[1] == "f":
            out[key] = TAV + PATAH + DAGESH + p1 + SHEVA + p2 + HIREQ + YOD + p3 + SHEVA + NUN + QAMATS + HE
        elif key[0] == "p3" and key[1] == "f" and key[2] == "sg":
            out[key] = TAV + PATAH + DAGESH + p1 + SHEVA + p2 + HIREQ + YOD + p3
        elif key[2] == "pl":
            out[key] = pref + dash + p1 + SHEVA + p2 + HIREQ + YOD + p3 + SHUREQ
        else:
            out[key] = pref + dash + p1 + SHEVA + p2 + HIREQ + YOD + p3
    return out


def _hif_impv(p1, p2, p3):
    return {
        ("p2", "m", "sg"): HE + PATAH + p1 + SHEVA + p2 + TSERE + p3,
        ("p2", "f", "sg"): HE + PATAH + p1 + SHEVA + p2 + HIREQ + YOD + p3 + HIREQ + YOD,
        ("p2", "m", "pl"): HE + PATAH + p1 + SHEVA + p2 + HIREQ + YOD + p3 + SHUREQ,
        ("p2", "f", "pl"): HE + PATAH + p1 + SHEVA + p2 + HIREQ + YOD + p3 + SHEVA + NUN + QAMATS + HE,
    }


HIF_INFC = HE + PATAH + "P1" + SHEVA + "P2" + HIREQ + YOD + "P3"
HIF_INFA = HE + PATAH + "P1" + SHEVA + "P2" + TSERE + "P3"


def _hif_ptc(p1, p2, p3):
    return {
        ("ptca", "m", "sg"): MEM + PATAH + p1 + SHEVA + p2 + HIREQ + YOD + p3,
        ("ptca", "m", "pl"): MEM + PATAH + p1 + SHEVA + p2 + HIREQ + YOD + p3 + HIREQ + YOD + END_MEM,
        ("ptca", "f", "sg"): MEM + PATAH + p1 + SHEVA + p2 + SEGOL + p3 + SEGOL + TAV,
        ("ptca", "f", "pl"): MEM + PATAH + p1 + SHEVA + p2 + HIREQ + YOD + p3 + HOLAM + VAV + TSERE + TAV,
    }


# --- HOFAL -----------------------------------------------------------------------
def _hof_perf(p1, p2, p3):
    base = HE + QAMATS + p1 + SHEVA + p2
    out = {}
    for key, end in S_PERF.items():
        if key == ("p3", "m", "sg"):
            out[key] = base + PATAH + p3
        else:
            out[key] = base + PATAH + p3 + end
    return out


def _hof_impf(p1, p2, p3):
    stem = p1 + SHEVA + p2 + PATAH + p3
    stem_u = p1 + SHEVA + p2 + QAMATS + p3
    out = {}
    for key, (pref, dash) in IMPF_PREF.items():
        if key[0] == "p1" and key[2] == "sg":
            out[key] = ALEF + QUBUTS + p1 + SHEVA + p2 + PATAH + p3
        elif key[0] == "p1" and key[2] == "pl":
            out[key] = NUN + QUBUTS + p1 + SHEVA + p2 + PATAH + p3
        elif key[0] == "p2" and key[1] == "f" and key[2] == "sg":
            out[key] = TAV + QUBUTS + p1 + SHEVA + p2 + PATAH + p3 + HIREQ + YOD
        elif key[0] in ("p2", "p3") and key[2] == "pl" and key[1] == "f":
            out[key] = TAV + QUBUTS + p1 + SHEVA + p2 + PATAH + p3 + SHEVA + NUN + QAMATS + HE
        elif key[2] == "pl":
            out[key] = pref + QUBUTS + p1 + SHEVA + p2 + PATAH + p3 + SHUREQ
        else:
            out[key] = pref + QUBUTS + p1 + SHEVA + p2 + PATAH + p3
    return out


def _hof_impv(p1, p2, p3):
    return {
        ("p2", "m", "sg"): HE + QUBUTS + p1 + SHEVA + p2 + PATAH + p3,
        ("p2", "f", "sg"): HE + QUBUTS + p1 + SHEVA + p2 + PATAH + p3 + HIREQ + YOD,
        ("p2", "m", "pl"): HE + QUBUTS + p1 + SHEVA + p2 + PATAH + p3 + SHUREQ,
        ("p2", "f", "pl"): HE + QUBUTS + p1 + SHEVA + p2 + PATAH + p3 + SHEVA + NUN + QAMATS + HE,
    }


HOF_INFC = HE + QUBUTS + "P1" + SHEVA + "P2" + PATAH + "P3"


def _hof_ptc(p1, p2, p3):
    return {
        ("ptca", "m", "sg"): MEM + QUBUTS + p1 + SHEVA + p2 + PATAH + p3,
        ("ptca", "m", "pl"): MEM + QUBUTS + p1 + SHEVA + p2 + PATAH + p3 + HIREQ + YOD + END_MEM,
        ("ptca", "f", "sg"): MEM + QUBUTS + p1 + SHEVA + p2 + PATAH + p3 + QAMATS + HE,
        ("ptca", "f", "pl"): MEM + QUBUTS + p1 + SHEVA + p2 + PATAH + p3 + HOLAM + VAV + TSERE + TAV,
    }


# =============================================================================
# Normalisation et détection du verbe
# =============================================================================

def _strip_teamim(s):
    """Retire les signes de cantillation (teamim, U+0591..U+05AF)."""
    return "".join(c for c in s if not (0x0591 <= ord(c) <= 0x05AF))


def _normalize(s):
    """Normalise : NFC + retrait des teamim."""
    return unicodedata.normalize("NFC", _strip_teamim(s or ""))


def _root_letters(s):
    """Extrait les lettres radicales, en gardant le point shin/sin attaché
    au shin (שׁ « garder » vs שׂ « empoisonner »)."""
    out = []
    for ch in s or "":
        o = ord(ch)
        if 0x05D0 <= o <= 0x05EA:
            out.append(ch)
        elif ch in ("\u05C1", "\u05C2") and out and out[-1] == "\u05E9":
            out[-1] += ch
    return out


def _is_consonantal(s):
    """Vrai si la forme ne contient aucune voyelle (racine nue)."""
    return not any(0x05B0 <= ord(c) <= 0x05BB or ord(c) == 0x05C7
                   for c in s or "")


# --- Catégories de verbes faibles ----------------------------------------------
# (code, libellé français, description)
WEAK_CATEGORIES = (
    ("strong", "verbe fort (shalem)",
     "Racine trilitaire sans radicale faible : conjugaison régulière."),
    ("pe_alef", "verbe pe-alef (פ״א)",
     "1re radicale א : l'alef quiescent refuse le sheva (hatef-patah)."),
    ("pe_guttural", "verbe pe-guttural (פ״ה/פ״ח/פ״ע)",
     "1re radicale gutturale : refus du sheva, voyelle de compensation."),
    ("pe_nun", "verbe pe-nun (פ״נ)",
     "1re radicale נ : le nun s'assimile au daguesh fort des formes à préfixe."),
    ("pe_yod", "verbe pe-yod (פ״י)",
     "1re radicale י : le yod s'assimile en voyelle longue."),
    ("ayin_guttural", "verbe ayin-guttural (ע״ה/ע״ח/ע״ע/ע״א)",
     "2e radicale gutturale : refuse le daguesh fort, voyelle de compensation."),
    ("ayin_vav", "verbe creux (ע״ו/ע״י)",
     "2e radicale ו/י consonantique : la voyelle radicale s'allonge."),
    ("lamed_he", "verbe lamed-he (ל״ה)",
     "3e radicale ה : terminaisons vocaliques (ה/ת/י/נוּ), ה final élidé."),
    ("lamed_alef", "verbe lamed-alef (ל״א)",
     "3e radicale א : l'alef quiescent s'élide en syllabe ouverte."),
    ("lamed_guttural", "verbe lamed-guttural (ל״ח/ל״ע/ל״ה)",
     "3e radicale gutturale : patah furtif, voyelles de compensation."),
    ("double", "verbe double (ע״ע)",
     "2e et 3e radicales identiques : la 3e radicale se redouble."),
)

_WEAK_LABELS = {code: (label, desc) for code, label, desc in WEAK_CATEGORIES}

# Règles de conjugaison caractéristiques de chaque catégorie de verbe faible.
# Chaque entrée : liste de (titre, description) affichée par le GUI dans
# l'onglet « Règles du verbe faible » du mode binyanim.
WEAK_CONJ_RULES = {
    "pe_alef": [
        ("Alef quiescent", 
         "1re radicale א : l'alef ne se prononce qu'avec une voyelle ; "
         "après un préfixe (יִ, תִּ, נִ), le sheva attendu devient un "
         "hatef-patah (אֲ) ou une voyelle brève pleine."),
        ("Préfixes voyellés",
         "Imparfait : le préfixe porte une voyelle pleine au lieu du sheva "
         "(יָאמִין « il croira », pas *יְאמִין)."),
    ],
    "pe_guttural": [
        ("Refus du sheva",
         "1re radicale gutturale (ה/ח/ע) : la gutturale refuse le sheva, "
         "remplacé par une voyelle brève (hatef) — אֶחֱזֶק הַח֖וֹק plutôt "
         "que *יַחְזִיק."),
        ("Voyelles de compensation",
         "La voyelle du préfixe s'allonge parfois (a → e long) pour "
         "compenser l'impossibilité de doubler la gutturale."),
    ],
    "pe_nun": [
        ("Assimilation du nun",
         "1re radicale נ : dans les formes à préfixe (imparfait, "
         "impératif, participe), le נ s'assimile à la 2e radicale et "
         "apparaît comme daguesh fort : יִפֹּל « il tombera » (racine "
         "נפל), et non *יִנפֹּל."),
        ("Formes à suffixe",
         "Au parfait et dans les formes où le nun reste en position "
         "initiale de syllabe, il est conservé : נָפַל « il est tombé »."),
    ],
    "pe_yod": [
        ("Assimilation du yod",
         "1re radicale י : le yod s'assimile en voyelle longue, la forme "
         "commence par une consonne à daguesh (יֵשֵׁב « il habitera », "
         "racine ישׁב)."),
        ("Verbes mi",
         "Au qal imparfait, plusieurs verbes pe-yod présentent un "
         "préfixe en voyelle longue au lieu de la forme attendue."),
    ],
    "ayin_guttural": [
        ("Refus du daguesh fort",
         "2e radicale gutturale : la gutturale refuse le daguesh fort "
         "(caractéristique du piel/pual), la voyelle précédente "
         "s'allonge en compensation."),
        ("Voyelle de compensation",
         "Piel : le hatef du préfixe s'allonge (chariq → ségol/hireq "
         "long) pour compenser le redoublement impossible."),
    ],
    "ayin_vav": [
        ("Verbe creux",
         "2e radicale ו/י consonantique : la voyelle entre P2 et P3 "
         "s'allonge (qamats/holam) et la radicale médiane n'est jamais "
         "syllabée — קָם « il s'est levé », יָקֻם (hofal), etc."),
        ("Métaphonie de qamets",
         "Au qal imparfait, la voyelle radicale se réduit souvent à une "
         "voyelle de type (o/u) : יָקם → יָקֻם au hofal ; au qal, "
         "la voyelle « a » se conserve longue."),
    ],
    "lamed_he": [
        ("Terminaison vocalique",
         "3e radicale ה : le ה final n'est pas une vraie consonne mais "
         "une mater lectionis ; les formes se terminent par une voyelle "
         "longue ou une terminaison vocalique (ה/ת/י/נוּ)."),
        ("Élision du ה final",
         "Aux formes à suffixe (suffixe pronominal ou terminaison de "
         "personne), le ה s'élide et la voyelle se contracte : "
         "בָּנָה + תִּי → בָּנִיתִי (pas *בָּנָהְתִי)."),
        ("Jussif et cohortatif",
         "La forme courte (jussif) élide le ה avec sa voyelle : יִּבֶן ; "
         "le cohortatif 1re personne est identique à l'imparfait (אֶבְנֶה) "
         "— le ה paragogique s'agglutine à une forme déjà vocalique."),
        ("Impératif",
         "L'impératif construit sur l'imparfait sans préfixe : בְּנֵה « bâtis », "
         "avec tsere (voyelle-longue) car le ה élité laisse une syllabe "
         "ouverte."),
    ],
    "lamed_alef": [
        ("Alef quiescent",
         "3e radicale א : en syllabe ouverte finale, l'alef quiescent "
         "s'élide (מָצָא → מָצָה) ; en position initiale de syllabe, "
         "il est conservé."),
        ("Impératif",
         "La voyelle de l'impératif s'allonge pour compenser "
         "l'élision : מְצָא-מָצָה."),
    ],
    "lamed_guttural": [
        ("Patah furtif",
         "3e radicale gutturale : après une voyelle non-patah, un patah "
         "furtif s'insère avant la gutturale finale (שָׁמַע, גָּדַלְתָּ) ; "
         "la gutturale ne se redouble pas."),
        ("Voyelles de compensation",
         "Les voyelles de la racine s'adaptent à la gutturale : ségol "
         "fréquent en finale (שָׁמַע → impératif שְׁמַע) et refus "
         "du daguesh fort."),
    ],
    "double": [
        ("Redoublement",
         "2e et 3e radicales identiques : la 3e radicale se redouble "
         "avec daguesh fort dans les formes à préfixe — יְסֻבֵּב « il "
         "sera entouré » (racine סבב)."),
        ("Qal défectif",
         "Au qal parfait, la voyelle entre P2 et P3 s'allonge souvent "
         "(סָבַב comme un verbe fort, ou עִפֵּל־סָבֵב « doublement » "
         "au piel/pual)."),
    ],
}


def classify_root(p1, p2, p3):
    """Classe une racine trilitaire : renvoie le code de la catégorie."""
    if p2 == p3:
        return "double"
    if p3 == HE:
        return "lamed_he"
    if p3 == ALEF:
        return "lamed_alef"
    if p3 in GUTTURALS:
        return "lamed_guttural"
    if p2 in (VAV, YOD):
        return "ayin_vav"
    if p2 in GUTTURALS:
        return "ayin_guttural"
    if p1 == NUN:
        return "pe_nun"
    if p1 == ALEF:
        return "pe_alef"
    if p1 == YOD:
        return "pe_yod"
    if p1 in GUTTURALS:
        return "pe_guttural"
    return "strong"


def identify_verb(F, form):
    """Identifie le verbe correspondant à une forme conjuguée ou une racine.

    Renvoie un dict (cf. analyze_binyanim) avec la racine trilitaire et,
    si la forme est attestée, le lemme BHSA et sa traduction.
    """
    norm = _normalize(form)
    letters = _root_letters(norm)

    # Point shin/sin orphelin : la saisie a probablement inséré le point
    # sans la lettre ש (touche shin_dot du clavier virtuel seule). Sans
    # cette garde, le point serait ignoré et la recherche se ferait sur
    # les consonnes restantes, avec un verbe sans rapport (ex. ׁמר lu
    # comme מר → מרר). On refuse plutôt la forme. Le point suit le ש
    # immédiatement ou après les autres signes combinants (voyelles,
    # daguesh, meteg…) — la normalisation NFC peut les réordonner
    # (ex. ש + tsere + meteg + point shin, cf. יֹושֵֽׁב).
    for i, ch in enumerate(norm):
        if ch in ("\u05C1", "\u05C2"):
            j = i - 1
            while j >= 0 and not ("\u05D0" <= norm[j] <= "\u05EA"):
                j -= 1
            if j < 0 or norm[j] != "\u05E9":
                return {"found": False, "reason": "orphan_shin_dot",
                        "input": form}

    # 1) Racine trilitaire nue (ex. שמר, קטל, שׂמר) : lemme BHSA ou racine
    #    théorique si la racine n'existe pas dans la base.
    if len(letters) == 3 and _is_consonantal(norm):
        for w in F.otype.s("word"):
            if F.sp.v(w) != "verb":
                continue
            lex_utf8 = F.lex_utf8.v(w) or ""
            if _root_letters(lex_utf8) == letters:
                lex = F.lex.v(w)
                return {
                    "found": True,
                    "lex": lex,
                    "lex_utf8": lex_utf8,
                    "root": tuple(letters),
                    "gloss": F.gloss.v(w),
                    "gloss_fr": best_gloss(lex, F.gloss.v(w), sp="verb"),
                    "method": "root",
                }
        return {
            "found": True,
            "lex": None,
            "lex_utf8": None,
            "root": tuple(letters),
            "gloss": None,
            "gloss_fr": None,
            "method": "root",
        }

    # 2) Forme conjuguée : recherche BHSA (cf. word_analyzer.search_word).
    # Un match dont le squelette consonantique est un PRÉFIXE STRICT de la
    # racine trouvée est refusé : c'est la forme courte d'un verbe double
    # (ex. מר -> מרר, la 3e radicale absorbée dans le daguesh fort) ou
    # lamed-he (גל -> גלה). L'utilisateur qui saisit une racine inexistante
    # reçoit une erreur avec la racine complète suggérée, pas une
    # conjugaison surprise. Les formes légitimes restent identifiées :
    # verbe creux (קָם de קום : le squelette n'est pas un préfixe de la
    # racine), pe-nun assimilé (יפל de נפל : 3 lettres après le préfixe),
    # forme pleine d'un verbe double (מָרַר de מרר).
    from .word_analyzer import search_word, _strip_nikkud
    cons = _strip_nikkud(norm)
    truncated = []
    seen_lex = set()
    for method, w, pfx in search_word(F, form):
        if F.sp.v(w) != "verb":
            continue
        lex = F.lex.v(w)
        if lex in seen_lex:
            continue
        seen_lex.add(lex)
        lex_utf8 = F.lex_utf8.v(w) or ""
        rletters = _root_letters(lex_utf8)
        if len(rletters) != 3:
            continue
        skel = cons[len(pfx):] if pfx else cons
        skel_letters = _root_letters(skel)
        if (len(skel_letters) < len(rletters)
                and list(rletters[:len(skel_letters)])
                == list(skel_letters)):
            truncated.append("".join(rletters))
            continue
        return {
            "found": True,
            "lex": lex,
            "lex_utf8": lex_utf8,
            "root": tuple(rletters),
            "gloss": F.gloss.v(w),
            "gloss_fr": best_gloss(lex, F.gloss.v(w), sp="verb"),
            "binyan_attested": F.vs.v(w),
            "method": "form",
        }
    if truncated:
        return {"found": False, "reason": "root_truncated",
                "suggestions": sorted(set(truncated)), "input": form}
    # Racine nue trop courte (ex. מר) : aucune forme ne matche, mais des
    # racines verbales étendent la saisie — les suggérer.
    if 0 < len(letters) < 3:
        suggestions = set()
        for w in F.otype.s("word"):
            if F.sp.v(w) != "verb":
                continue
            rletters = _root_letters(F.lex_utf8.v(w) or "")
            if (len(rletters) == 3
                    and list(rletters[:len(letters)]) == list(letters)):
                suggestions.add("".join(rletters))
        if suggestions:
            # Racines doubles en premier (extension naturelle d'une
            # racine courte : מר -> מרר), puis les autres par ordre.
            ordered = sorted(suggestions, key=lambda r: (len(r), r))
            return {"found": False, "reason": "no_match",
                    "suggestions": ordered[:8],
                    "input": form}
    return {"found": False, "reason": "no_match", "input": form}


# =============================================================================
# Gabarits extraits de la base BHSA
# =============================================================================
# binyan_templates.json est généré par scripts/extract_binyan_templates.py :
# pour chaque (catégorie, binyan, temps, personne), le gabarit vocalique
# dominant attesté dans la Bible. Repli : gabarit « strong », puis
# générateur intégré du verbe fort.

_TEMPLATE_CACHE = None


def _templates():
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE is None:
        import json
        import os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "binyan_templates.json")
        if not os.path.isfile(path):
            path = os.path.join(resource_dir(), "binyan_templates.json")
        try:
            with open(path, encoding="utf-8") as fh:
                _TEMPLATE_CACHE = json.load(fh)
        except OSError:
            _TEMPLATE_CACHE = {}
    return _TEMPLATE_CACHE


def _cell_key(cat, vs, vt, ps, gn, nu):
    return f"{cat}|{vs}|{vt}|{ps}|{gn}|{nu}"


def _exact_template(cat, vs, vt, cell):
    """Gabarit de la catégorie exacte (sans repli « strong »)."""
    t = _templates()
    ps, gn, nu = cell
    return t.get(f"{cat}|{vs}|{vt}|{ps}|{gn}|{nu}")


def _lookup_template(cat, vs, vt, cell):
    """Gabarit dominant d'une cellule (chaîne), voir _lookup_template_entry."""
    entry = _lookup_template_entry(cat, vs, vt, cell)
    return entry["template"] if entry else None


def _lookup_template_entry(cat, vs, vt, cell):
    """Cherche l'entrée de gabarit d'une cellule : catégorie, puis « strong ».

    Renvoie le dict complet du JSON (template, count, lexemes, variants)
    ou None. La forme dominante est dans "template" ; "variants" liste
    les gabarits concurrents attestés (au plus 3, par nombre de lemmes
    puis d'occurrences).

    Les cellules finies ont une clé à 6 champs (cat|vs|vt|ps|gn|nu) ;
    les non finies une clé à 5 champs (cat|vs|vt|gn|nu, ps=unknown).
    """
    t = _templates()
    ps, gn, nu = cell
    if vs in ("infa", "infc", "ptca", "ptcp") or ps == "unknown":
        keys = (f"{cat}|{vs}|{vt}|{gn}|{nu}",
                f"{cat}|{vs}|{vt}|{ps}|{gn}|{nu}")
    else:
        keys = (f"{cat}|{vs}|{vt}|{ps}|{gn}|{nu}",)
    entry = None
    for key in keys:
        entry = t.get(key)
        if entry:
            break
    # Un gabarit issu d'un seul lemme est idiosyncratique : préférer le
    # gabarit général du verbe fort s'il existe.
    if (entry is not None and cat != "strong"
            and entry.get("lexemes", 2) < 2):
        for key in keys:
            strong = t.get(key.replace(cat, "strong", 1))
            if strong:
                entry = strong
                break
    if entry is None and cat != "strong":
        for key in keys:
            entry = t.get(key.replace(cat, "strong", 1))
            if entry:
                break
    return entry


def _variant_canon(s):
    """Canonique d'une forme pour la comparaison des variantes.

    Neutralise les différences orthographiques mineures du texte
    massorétique (mêmes tolérances que tests/test_binyanim.py) :
    daguesh, meteg, point shin/sin, hatef vs sheva, maters du holam,
    hireq-yod et tsere-yod, segol vs patah. Deux formes qui ne
    diffèrent que par ces signes sont une même conjuguaison.
    """
    import re
    s = _normalize(s)
    s = re.sub(r"[\u05BC\u05BD\u05C1\u05C2]", "", s)
    s = re.sub(r"[\u05B1\u05B2\u05B3]", SHEVA, s)
    s = s.replace(HOLAM + VAV, HOLAM)
    s = s.replace(HIREQ + YOD, HIREQ)
    s = s.replace(TSERE + YOD, TSERE)
    s = s.replace(SEGOL, PATAH)
    return s


def _cell_variants(vs, root, category, tense, cell, entry, form):
    """Variantes attestées d'une cellule, rendues avec la racine.

    Les gabarits concurrents du dominant (champ « variants » du JSON,
    classés par nombre de lemmes puis d'occurrences) sont rendus comme
    la forme principale : mêmes radicales effectives, mêmes règles
    (daguesh lene parasite, métathèse hitpael). Les variantes sont
    dédupliquées et débarrassées de la forme dominante déjà affichée ;
    une variante qui se réduit, après rendu, à la forme principale
    (différence d'orthographe du gabarit uniquement) est écartée.

    Seules les cellules conjuguées par gabarit extrait ont des
    variantes : les volitifs dérivés (jussif, cohortatif) et le repli
    du générateur intégré n'en produisent pas.
    """
    if not entry:
        return []
    import re
    out = []
    seen = {_variant_canon(form)}
    for tpl in entry.get("variants") or ():
        if tpl == entry.get("template"):
            continue
        try:
            v = _initial_dagesh(_render(tpl, root, category, vs))
        except Exception:  # noqa: BLE001
            continue
        if not v:
            continue
        key = _variant_canon(v)
        if key not in seen:
            seen.add(key)
            out.append(v)
    return out


def _root_map(category, root):
    """Mapping gabarit -> radicales effectives.

    Les gabarits extraits nomment P1/P2/P3 les radicales **effectives** de
    la catégorie : pour un creux, P2 désigne la 3e radicale (la 2e étant ו/י
    vocalique) ; pour un double, P2 (redoublée) désigne la 2e=3e radicale ;
    pour un lamed-he, P3 est absente (ה élidée dans les terminaisons).
    """
    p1, p2, p3 = root
    if category == "ayin_vav":
        return {"P1": p1, "P2": p3}
    if category == "double":
        return {"P1": p1, "P2": p2}
    return {"P1": p1, "P2": p2, "P3": p3}


_SIBILANTS = ("\u05E9", "\u05E9\u05C1", "\u05E9\u05C2", "\u05E1", "\u05E6", "\u05D6")


def _apply_hit_metathesis(form, p1):
    """Métathèse du hitpael : P1 sifflante s'échange avec le ת infixé.

    הִתְפַּעֵל → הִסְתַּפֵּל (ס), הִשְׁתַּמֵּר (שׁ), etc. Le ת et P1 échangent
    leurs positions ; le daguesh fort passe de P2 à la consonne suivie.
    """
    tav = "\u05EA"
    if p1 not in _SIBILANTS:
        return form
    # Localiser le segment « תְ + P1 » et l'inverser en « P1ְ + ת ».
    i = form.find(tav)
    if i < 0:
        return form
    # Le ת du hitpael est suivi (après ses signes) de P1.
    j = i + 1
    while j < len(form) and (0x05B0 <= ord(form[j]) <= 0x05BC
                              or ord(form[j]) in (0x05C1, 0x05C2)):
        j += 1
    if j < len(form) and form.startswith(p1, j):
        seg_tav = form[i:j]
        return form[:i] + p1 + seg_tav[len(tav):] + tav + form[j + len(p1):]
    return form


def _render(template, root, category, vs=None):
    """Substitue les radicales effectives dans un gabarit.

    Les gabarits de la catégorie utilisent P1/P2(/P3) selon la racine
    effective (creux : P2 = 3e radicale ; double : P2 redoublée ;
    lamed-he : P3 absente). Un gabarit « strong » utilisé en repli pour
    une catégorie à racine réduite peut contenir P3 : il est d'abord
    converti (P3 → P2 pour creux/doubles ; P3 élidé pour lamed-he).
    """
    p1, p2, p3 = root
    if category == "ayin_vav":
        mapping = {"P1": p1, "P2": p3, "P3": p3}
    elif category == "double":
        mapping = {"P1": p1, "P2": p2, "P3": p2}
    elif category == "lamed_he":
        # Le ה final s'élide : les segments « P3 + voyelle » disparaissent
        # du gabarit strong avant substitution (ex. שְׁמֹרְנָה <- P1-P2-P3-V).
        template = _elide_p3(template)
        mapping = {"P1": p1, "P2": p2}
    else:
        mapping = {"P1": p1, "P2": p2, "P3": p3}
    # Daguesh lene parasite : un gabarit dominant issu de racines
    # begadkefat (ex. אֶקְבְּרָה) porte un daguesh lene après le
    # sheva d'une radicale ; il n'est légitime que si la radicale
    # effective est une begadkefat. En piel/pual, le daguesh après
    # la voyelle de P2 marque le redoublement (forte) et concerne
    # toute consonne : on ne le retire pas.
    if vs not in ("piel", "pual"):
        for ph, letter in mapping.items():
            if letter not in BEGADKEFAT:
                template = template.replace(ph + SHEVA + DAGESH,
                                            ph + SHEVA)
                # Daguesh lene après toute voyelle de la radicale
                # (patah du piel : תְּP1ַּP2ֵּP3 issu de תְּבַקֵּשׁ) :
                # illégitime pour une radicale non begadkefat
                # (תְּדַבֵּר, pas תְּדַּבֵּר).
                for vow in (PATAH, SEGOL, QAMATS, TSERE, HIREQ,
                            HOLAM, QUBUTS, HATAF_QAMATS, HATEF_PATAH,
                            HATEF_SEGOL):
                    template = template.replace(ph + vow + DAGESH,
                                                ph + vow)
    out = template
    for ph, letter in mapping.items():
        out = out.replace(ph, letter)
    # Hitpael : métathèse du ת avec une 1re radicale sifflante
    # (שׁ/שׂ/ס/צ) lorsque le gabarit est en ordre non métathésé.
    if vs == "hit":
        out = _apply_hit_metathesis(out, p1)
    return _fix_finals(out)


# Lettres finales -> formes médianes (le rendu place les radicales au
# milieu du mot ; la forme finale n'est légitime qu'en dernière position).
_MEDIAL = {"\u05DA": "\u05DB", "\u05DD": "\u05DE", "\u05DF": "\u05E0",
           "\u05E3": "\u05E4", "\u05E5": "\u05E6"}


def _fix_finals(form):
    """Convertit les lettres finales en formes médianes, sauf la dernière."""
    if len(form) <= 1:
        return form
    head = "".join(_MEDIAL.get(c, c) for c in form[:-1])
    return head + form[-1]


def _initial_dagesh(form):
    """Daguesh lene sur une begadkefat en début de mot (ex. כְּתֹב,
    כָּתַב) : les gabarits dominants, extraits de racines non
    begadkefat, ne le portent pas ; il est systématique en position
    initiale. Idempotent.

    Le daguesh est inséré APRÈS les signes vocaliques qui suivent la
    consonne initiale (ordre canonique : lettre, voyelle, daguesh —
    דַּבֵּר), pas entre la consonne et sa voyelle (דַּבֵּר), les deux
    s'affichant identiquement mais seule la première étant canonique.
    """
    if not form or form[0] not in BEGADKEFAT:
        return form
    i = 1
    while i < len(form) and unicodedata.combining(form[i]):
        if form[i] == DAGESH:
            return form
        i += 1
    return form[:i] + DAGESH + form[i:]


def _elide_p3(template):
    """Élide la 3e radicale d'un gabarit strong (verbes lamed-he).

    Supprime « P3 » ainsi que la voyelle qui suit immédiatement (la
    syllabe finale ouverte se contracte) : שְׁמֹרְנָה est construit sur
    שׁ-מ-ר-ְ-נ-ָ-ה où le ה final a été élidé avec sa voyelle.
    """
    out = []
    i = 0
    while i < len(template):
        if template.startswith("P3", i):
            i += 2
            # élider la voyelle/daguesh qui suit la radicale élidée
            while i < len(template) and (0x05B0 <= ord(template[i]) <= 0x05BB
                                          or template[i] == DAGESH):
                i += 1
            continue
        out.append(template[i])
        i += 1
    return "".join(out)


# --- HITPOLEL (hitpael des verbes creux) -----------------------------------------
# Les verbes creux (ע״ו/ע״י) suivent au hitpael le thème hitpolel avec
# redoublement de la 3e radicale (הִתְעֹורֵר, יִתְעֹורָר, מִתְעֹורֵר) ; la
# 2e radicale (ו/י) est vocalique (holam). Formes attestées : הִתְעֹורַרְתִּי
# (Deut 32:11), הִתְעֹורְרִי, יִתְעֹורָר, הִתְבֹּונָן, יִתְבֹּונָנוּ,
# תִּתְבֹּנְנוּ, תִּתְמֹוגַגְנָה, נִּתְעֹודָד, מִתְקֹומְמִים, מִתְבֹּוסֶסֶת.

_FINALS = {v: k for k, v in _MEDIAL.items()}


def _hitpolel_stem(p1):
    """Préfixe הִתְ + P1(qamats) ; sheva fermant : daguesh lene sur une
    P1 begadkefat (הִתְבֹּונָן)."""
    dash = DAGESH if p1 in BEGADKEFAT else ""
    return HE + HIREQ + TAV + SHEVA + p1 + dash + HOLAM + VAV


def _hitpolel_forms(p1, p3, base):
    """Applique le rendu final : P3 redoublée médiane, finale en ן/ם."""
    p3m = _MEDIAL.get(p3, p3)
    out = {}
    for key, form in base(p3m).items():
        out[key] = form[:-1] + _FINALS.get(form[-1], form[-1])
    return out


def _hitpolel_perf(p1, p3):
    pre = _hitpolel_stem(p1)
    def base(p3):
        return {
            ("p3", "m", "sg"): pre + p3 + QAMATS + p3,
            ("p3", "f", "sg"): pre + p3 + SHEVA + p3 + QAMATS + HE,
            ("p2", "m", "sg"): pre + p3 + PATAH + p3 + SHEVA + TAV + QAMATS + DAGESH,
            ("p2", "f", "sg"): pre + p3 + PATAH + p3 + SHEVA + TAV + SHEVA + DAGESH,
            ("p1", "c", "sg"): pre + p3 + PATAH + p3 + SHEVA + TAV + HIREQ + YOD,
            ("p3", "m", "pl"): pre + p3 + QAMATS + p3 + SHUREQ,
            # 3fp = forme commune en -ו׼ (cf. S_PERF).
            ("p3", "f", "pl"): pre + p3 + SHEVA + p3 + SHUREQ,
            ("p2", "m", "pl"): pre + p3 + PATAH + p3 + SHEVA + TAV + SEGOL + DAGESH + END_MEM,
            ("p2", "f", "pl"): pre + p3 + PATAH + p3 + SHEVA + TAV + SEGOL + DAGESH + END_NUN,
            ("p1", "c", "pl"): pre + p3 + PATAH + p3 + SHEVA + NUN + SHUREQ,
        }
    return _hitpolel_forms(p1, p3, base)


def _hitpolel_impf(p1, p3):
    dash = DAGESH if p1 in BEGADKEFAT else ""
    stem = TAV + SHEVA + p1 + dash + HOLAM + VAV
    def base(p3):
        out = {}
        for key, (pref, _d) in IMPF_PREF.items():
            if key == ("p1", "c", "sg"):
                out[key] = ALEF + SEGOL + stem + p3 + QAMATS + p3
            elif key == ("p1", "c", "pl"):
                out[key] = NUN + HIREQ + stem + p3 + QAMATS + p3
            elif key == ("p2", "f", "sg"):
                out[key] = pref + stem + p3 + SHEVA + p3 + HIREQ + YOD
            elif key[2] == "pl" and key[1] in ("m", "unknown") and key[0] == "p3":
                out[key] = pref + stem + p3 + QAMATS + p3 + SHUREQ
            elif key[2] == "pl" and key[1] in ("m", "unknown") and key[0] == "p2":
                out[key] = pref + DAGESH + stem + p3 + SHEVA + p3 + SHUREQ
            elif key[2] == "pl" and key[0] in ("p2", "p3") and key[1] in ("f", "unknown"):
                out[key] = pref + stem + p3 + PATAH + p3 + SHEVA + NUN + QAMATS + HE
            else:
                out[key] = pref + stem + p3 + QAMATS + p3
        return out
    return _hitpolel_forms(p1, p3, base)


def _hitpolel_impv(p1, p3):
    pre = _hitpolel_stem(p1)
    def base(p3):
        return {
            ("p2", "m", "sg"): pre + p3 + TSERE + p3,
            ("p2", "f", "sg"): pre + p3 + SHEVA + p3 + HIREQ + YOD,
            ("p2", "m", "pl"): pre + p3 + SHEVA + p3 + SHUREQ,
            ("p2", "f", "pl"): pre + p3 + PATAH + p3 + SHEVA + NUN + QAMATS + HE,
        }
    return _hitpolel_forms(p1, p3, base)


def _hitpolel_non_finite(p1, p3):
    pre = _hitpolel_stem(p1)
    stem = MEM + HIREQ + TAV + SHEVA + _hitpolel_stem(p1)[len(HE + HIREQ):]
    def base(p3):
        infc = pre + p3 + TSERE + p3
        return {
            ("infa", "unknown", "unknown"): infc,
            ("infc", "unknown", "unknown"): infc,
            ("ptca", "m", "sg"): stem + p3 + TSERE + p3,
            ("ptca", "m", "pl"): stem + p3 + SHEVA + p3 + HIREQ + YOD + END_MEM,
            ("ptca", "f", "sg"): stem + p3 + SEGOL + p3 + SEGOL + TAV,
            ("ptca", "f", "pl"): stem + p3 + SHEVA + p3 + QAMATS + TAV,
        }
    return _hitpolel_forms(p1, p3, base)

# --- HIFIL DES VERBES CREUX (ע״ו/ע״י) -------------------------------------------
# Schéma attesté (BHSA) : הֵעִיר, הֵבִיאָה (perf) ; יָעִיר, תָּעִירִי, נָעִיר,
# נָבִיא (impf : qamats + P1 + ḥireq-yod + P3) ; הָעֵר, הָבֵא (impv) ;
# הָאֵר (infa), הָאִיר/הָעִיר (infc) ; מֵעִיר, מֵבִיא (ptca). Perf suffixé :
# הֲעִירֹתִי, הֲבִיאֹתִי (ḥatef-qamats + P1 + ḥireq + P3 + holam + ות...).


def _hif_hollow_perf(p1, p3):
    pre = HE + TSERE + p1 + HIREQ + YOD
    # Hatef de préfixe : gutturale selon sa classe (ע → patah, א/ה/ח →
    # qamats), sinon segol (הֱשִׁיבֹתִי, הֱקִימֹותִי).
    if p1 == "\u05E2":
        hatef = HATEF_PATAH
    elif p1 in GUTTURALS:
        hatef = HATAF_QAMATS
    else:
        hatef = HATEF_SEGOL
    pre_h = HE + hatef + p1 + HIREQ + YOD
    return {
        ("p3", "m", "sg"): pre + p3,
        ("p3", "f", "sg"): pre + p3 + QAMATS + HE,
        ("p2", "m", "sg"): pre_h + p3 + HOLAM + TAV + QAMATS + DAGESH,
        ("p2", "f", "sg"): pre_h + p3 + HOLAM + TAV + SHEVA + DAGESH,
        ("p1", "c", "sg"): pre_h + p3 + HOLAM + TAV + HIREQ + YOD,
        ("p3", "m", "pl"): pre + p3 + SHUREQ,
        # 3fp = forme commune en -ו׼ (cf. S_PERF).
        ("p3", "f", "pl"): pre + p3 + SHUREQ,
        ("p2", "m", "pl"): pre_h + p3 + HOLAM + TAV + SEGOL + DAGESH + END_MEM,
        ("p2", "f", "pl"): pre_h + p3 + HOLAM + TAV + SEGOL + DAGESH + END_NUN,
        ("p1", "c", "pl"): pre_h + p3 + HOLAM + NUN + SHUREQ,
    }


def _hif_hollow_impf(p1, p3):
    # Préfixe voyelle qamats (יָעִיר, תָּשִׁיב) ; pas de daguesh lene sur
    # P1 puisque la voyelle préfixe la précède (הֵבִיא, יָשִׁיב).
    stem = p1 + HIREQ + YOD
    out = {}
    for key, (pref, _d) in IMPF_PREF.items():
        pref_q = pref[0] + QAMATS
        dash = DAGESH if pref[0] == TAV else ""
        if key == ("p2", "f", "sg"):
            out[key] = pref_q + dash + stem + p3 + HIREQ + YOD
        elif key[2] == "pl" and key[1] == "m":
            out[key] = pref_q + dash + stem + p3 + SHUREQ
        elif key[2] == "pl" and key[1] == "f":
            out[key] = (pref_q + dash + stem + p3 + SHEVA + NUN
                        + QAMATS + HE)
        else:
            out[key] = pref_q + dash + stem + p3
    return out


def _hif_hollow_impv(p1, p3):
    pre = HE + QAMATS + p1
    pre_i = HE + QAMATS + p1 + HIREQ + YOD
    return {
        ("p2", "m", "sg"): pre + TSERE + p3,
        ("p2", "f", "sg"): pre_i + p3 + HIREQ + YOD,
        ("p2", "m", "pl"): pre_i + p3 + SHUREQ,
        ("p2", "f", "pl"): pre_i + p3 + SHEVA + NUN + QAMATS + HE,
    }


def _hif_hollow_non_finite(p1, p3):
    ptc = MEM + TSERE + p1 + HIREQ + YOD
    return {
        ("infa", "unknown", "unknown"): HE + QAMATS + p1 + TSERE + p3,
        ("infc", "unknown", "unknown"): HE + QAMATS + p1 + HIREQ + YOD + p3,
        ("ptca", "m", "sg"): ptc + p3,
        ("ptca", "m", "pl"): MEM + SHEVA + p1 + HIREQ + YOD + p3 + HIREQ + YOD + END_MEM,
        ("ptca", "f", "sg"): MEM + SHEVA + p1 + HIREQ + YOD + p3 + PATAH + TAV,
        ("ptca", "f", "pl"): MEM + SHEVA + p1 + HIREQ + YOD + p3 + HOLAM + VAV + TSERE + TAV,
    }


def _builtin_paradigm(vs, root, category=None):
    """Paradigme du verbe fort par les générateurs intégrés (repli)."""
    p1, p2, p3 = root
    if category == "ayin_vav" and vs == "hif":
        return {"perf": _hif_hollow_perf(p1, p3),
                "impf": _hif_hollow_impf(p1, p3),
                "impv": _hif_hollow_impv(p1, p3)}
    if category == "ayin_vav" and vs == "hit":
        return {"perf": _hitpolel_perf(p1, p3),
                "impf": _hitpolel_impf(p1, p3),
                "impv": _hitpolel_impv(p1, p3)}
    builders = {
        "qal": (_qal_perf, _qal_impf, _qal_impv),
        "nif": (_nif_perf, _nif_impf, _nif_impv),
        "piel": (_piel_perf, _piel_impf, _piel_impv),
        "pual": (_pual_perf, _pual_impf, _pual_impv),
        "hit": (_hit_perf, _hit_impf, _hit_impv),
        "hif": (_hif_perf, _hif_impf, _hif_impv),
        "hof": (_hof_perf, _hof_impf, _hof_impv),
    }
    perf_f, impf_f, impv_f = builders[vs]
    return {"perf": perf_f(p1, p2, p3), "impf": impf_f(p1, p2, p3),
            "impv": impv_f(p1, p2, p3)}


# =============================================================================
# Génération des conjugaisons (toutes personnes, tous binyanim)
# =============================================================================
# Ordre des personnes : cf. PERSONS (ordre français, 1re/2e/3e, sg puis pl).

PERSONS_IMPV = (
    ("p2", "m", "sg", "2e pers. masc. sing. (tu)"),
    ("p2", "f", "sg", "2e pers. fém. sing. (tu)"),
    ("p2", "m", "pl", "2e pers. masc. pl. (vous)"),
    ("p2", "f", "pl", "2e pers. fém. pl. (vous)"),
)

TENSE_LABELS = {
    "perf": "Parfait (qatal)",
    "impf": "Imparfait (yiqtol)",
    "impv": "Impératif",
    "juss": "Jussif (forme courte)",
    "coh": "Cohortatif (volutif)",
}

# Personnes du jussif : 2e/3e (la 1re personne courte est un yiqtol
# ordinaire, couvert par l'imparfait).
PERSONS_JUSS = (
    ("p2", "m", "sg", "2e pers. masc. sing. (que tu)"),
    ("p2", "f", "sg", "2e pers. fém. sing. (que tu)"),
    ("p3", "m", "sg", "3e pers. masc. sing. (qu'il)"),
    ("p3", "f", "sg", "3e pers. fém. sing. (qu'elle)"),
    ("p2", "m", "pl", "2e pers. masc. pl. (que vous)"),
    ("p2", "f", "pl", "2e pers. fém. pl. (que vous)"),
    ("p3", "m", "pl", "3e pers. masc. pl. (qu'ils)"),
    ("p3", "f", "pl", "3e pers. fém. pl. (qu'elles)"),
)
PERSONS_COH = (
    ("p1", "c", "sg", "1re pers. sing. (que je)"),
    ("p1", "c", "pl", "1re pers. pl. (que nous)"),
)

TENSE_PERSONS = {"perf": PERSONS, "impf": PERSONS, "impv": PERSONS_IMPV,
                 "juss": PERSONS_JUSS, "coh": PERSONS_COH}


_COH_END = "\u05B8\u05D4"


def _cohortative_fallback(vs, root, category, cell):
    """Cohortatif : gabarit extrait des formes attestées, sinon dérivation
    (imparfait 1re personne + finale \u05b8\u05d4).

    Le gabarit cohortatif est extrait des impf 1re personne en \u05b8\u05d4 ;
    à défaut (binyan rare), la forme courte est prise au gabarit jussif
    (même voyelle radicale) ou à l'imparfait de la même personne.
    """
    ps, gn, nu = cell
    # Verbes lamed-he : le ה final de la racine s'élide avec la
    # finale paragogique ; le cohortatif est identique à l'imparfait
    # 1re personne (אֶבְנֶה Gen 30:3, אֶמְצָא Gen 41:11). Le repli
    # « strong » de _lookup_template est ici évité : son gabarit coh
    # (אֶP1ְP2ְP3ָה) dupliquerait la radicale finale.
    if category == "lamed_he":
        tpl = _exact_template(category, vs, "impf", cell)
        if tpl:
            return _render(tpl["template"], root, category, vs)
        return ""
    # 0. gabarit cohortatif attesté (catégorie exacte, puis strong).
    tpl = _lookup_template(category, vs, "coh", cell)
    if tpl:
        return _render(tpl, root, category, vs)
    # 1. gabarit jussif de la même personne : forme courte commune.
    tpl = _exact_template(category, vs, "juss", cell)
    if not tpl and nu == "sg":
        # La 2e pers. masc. sing. du jussif a le même schéma que la 1re
        # personne (préfixe à part, même voyelle finale courte).
        alt = _exact_template(category, vs, "juss", ("p2", "m", "sg"))
        tpl = alt
    if not tpl:
        tpl = _exact_template(category, vs, "impf", cell)
        if tpl:
            tpl = tpl["template"]
    if not tpl:
        return ""
    if nu == "pl":
        # L'imparfait 1cp se termine en \u05b0\u05e0\u05bc\u05d5\u05bc ; la finale
        # cohortative \u05b8\u05d4 la remplace ; sur les autres schémas
        # (hif : \u05e0\u05b7\u05e7\u05b0\u05d8\u05b4\u05bc\u05d9\u05dc) elle s'ajoute
        # (\u05e0\u05b7\u05d2\u05b0\u05bc\u05d1\u05b4\u05bc\u05d9\u05e8\u05b8\u05d4 Ps 35:25).
        out = _render(tpl, root, category, vs)
        if out.endswith("\u05B0\u05E0\u05BC\u05D5\u05BC"):
            return out[:-3] + _COH_END
        if out.endswith("\u05D5\u05BC"):
            return out[:-1] + _COH_END
        return out + _COH_END
    out = _render(tpl, root, category, vs)
    if out.endswith(_COH_END):
        return out
    return out + _COH_END


def _jussive_fallback(vs, root, category, cell):
    """Jussif par dérivation : la forme courte est identique au yiqtol
    pour les verbes forts ; les verbes faibles l'obtiennent du gabarit
    jussif de la catégorie, ou à défaut de l'imparfait de la même
    catégorie (forme longue, meilleur que rien). Le repli « strong »
    de _lookup_template est évité : appliqué à une racine réduite
    (creuse, lamed-he…), il dupliquerait une radicale.
    """
    tpl = _exact_template(category, vs, "juss", cell)
    if tpl:
        return _render(tpl["template"], root, category, vs)
    tpl = _exact_template(category, vs, "impf", cell)
    if tpl:
        return _render(tpl["template"], root, category, vs)
    return ""


def generate_binyan_paradigm(vs, root, category, with_variants=True):
    """Paradigme complet d'un binyan : {tense: {(ps,gn,nu): forme}}.

    Chaque cellule utilise le gabarit BHSA de la catégorie du verbe ;
    à défaut, le gabarit du verbe fort ; à défaut, le générateur intégré.
    Les volitifs (jussif, cohortatif) utilisent les gabarits extraits des
    formes attestées (wayyiqtol pour le jussif, impf+\u05b8\u05d4 pour le
    cohortatif) ; sans gabarit attesté, ils sont dérivés de l'imparfait.

    ``with_variants`` : quand il est vrai, la clé "variants" recense,
    par temps puis cellule, les conjuguaisons concurrentes
    réellement attestées dans la BHSA (ex. qal yiqtol 1cs אֶקְטֹל /
    אֶקְטַל), en plus de la forme dominante.
    """
    out = {}
    builtin = None
    if category == "ayin_vav" and vs == "hif":
        # Hifil des verbes creux : la 2e radicale vocalique (ו/י) s'assimile
        # au ḥireq-yod du thème (יָעִיר, הֵעִיר, הָבֵא) ; les gabarits P1/P2
        # extraits la traitent comme consonne ou perdent la finale.
        builtin = _builtin_paradigm(vs, root, category)
        for tense, persons in TENSE_PERSONS.items():
            forms = {}
            for ps, gn, nu, _label in persons:
                cell = (ps, gn, nu)
                if tense in ("juss", "coh"):
                    # Volitifs : forme longue de l'imparfait (יָעִיר jussif,
                    # אָעִירָה cohortatif, Deut 32:11 / Ps 44:24).
                    base = builtin["impf"].get(cell, "")
                    if not base:
                        continue
                    if tense == "juss":
                        forms[cell] = base
                    else:
                        forms[cell] = (base + QAMATS + HE
                                       if not base.endswith(QAMATS + HE)
                                       else base)
                else:
                    forms[cell] = builtin[tense].get(cell, "")
            out[tense] = forms
        return out
    if category == "ayin_vav" and vs == "hit":
        # Hitpolel : les verbes creux redoublent la 3e radicale au hitpael
        # (הִתְעֹורֵר) ; les gabarits extraits (P1/P2/P3) ne peuvent pas
        # représenter ce redoublement.
        builtin = _builtin_paradigm(vs, root, category)
        for tense, persons in TENSE_PERSONS.items():
            forms = {}
            for ps, gn, nu, _label in persons:
                cell = (ps, gn, nu)
                if tense in ("juss", "coh"):
                    # Volitifs : dérivation sur la forme courte du
                    # hitpolel (תִּתְעֹורַרְנָה jussif, אֶתְעֹורֲרָה cohortatif).
                    base = builtin["impf"].get(cell, "")
                    if not base:
                        continue
                    if tense == "juss":
                        forms[cell] = base
                    else:
                        forms[cell] = (base + QAMATS + HE
                                       if not base.endswith(QAMATS + HE)
                                       else base)
                else:
                    forms[cell] = builtin[tense].get(cell, "")
            out[tense] = forms
        return out
    for tense, persons in TENSE_PERSONS.items():
        forms = {}
        variants = {}
        for ps, gn, nu, _label in persons:
            cell = (ps, gn, nu)
            if tense == "juss":
                form = _jussive_fallback(vs, root, category, cell)
                if not form:
                    # Dernier repli : le générateur intégré produit la
                    # forme longue (imparfait), la mieux approchante pour
                    # le jussif (ex. 3e fém. pl. \u05ea\u05b4\u05bc\u05e9\u05b0\u05c1\u05de\u05b7\u05bc\u05e8\u05b0\u05e0\u05b8\u05d4).
                    if builtin is None:
                        builtin = _builtin_paradigm(vs, root, category)
                    form = builtin["impf"].get(cell, "")
                forms[cell] = form
                continue
            if tense == "coh":
                form = _cohortative_fallback(vs, root, category, cell)
                if not form:
                    if builtin is None:
                        builtin = _builtin_paradigm(vs, root, category)
                    form = builtin["impf"].get(cell, "")
                forms[cell] = form
                continue
            tpl_entry = _lookup_template_entry(category, vs, tense, cell)
            tpl = tpl_entry["template"] if tpl_entry else None
            if tpl:
                forms[cell] = _render(tpl, root, category, vs)
                vars_ = (_cell_variants(vs, root, category, tense, cell,
                                       tpl_entry, forms[cell])
                        if with_variants else [])
                if vars_:
                    variants[cell] = vars_
            else:
                if builtin is None:
                    builtin = _builtin_paradigm(vs, root, category)
                forms[cell] = builtin[tense].get(cell, "")
            forms[cell] = _initial_dagesh(forms[cell])
        out[tense] = forms
        if variants:
            out.setdefault("variants", {})[tense] = variants
    return out


# Cellules non finies : (clé BHSA, cellule (gn, nu), libellé français).
NON_FINITE_CELLS = (
    ("infa", ("unknown", "unknown"), "Infinitif absolu"),
    ("infc", ("unknown", "unknown"), "Infinitif construit"),
    ("ptca", ("m", "sg"), "Participe actif masc. sing."),
    ("ptca", ("m", "pl"), "Participe actif masc. pl."),
    ("ptca", ("f", "sg"), "Participe actif fém. sing."),
    ("ptca", ("f", "pl"), "Participe actif fém. pl."),
    ("ptcp", ("m", "sg"), "Participe passif masc. sing."),
    ("ptcp", ("m", "pl"), "Participe passif masc. pl."),
    ("ptcp", ("f", "sg"), "Participe passif fém. sing."),
    ("ptcp", ("f", "pl"), "Participe passif fém. pl."),
)


def generate_binyan_non_finite(vs, root, category, with_variants=True):
    """Infinitifs et participes d'un binyan : {(vt, gn, nu): forme}.

    ``with_variants`` : conjuguaisons concurrentes attestées, sous la
    clé "variants" (cf. generate_binyan_paradigm).
    """
    out = {}
    if category == "ayin_vav" and vs == "hif":
        return _hif_hollow_non_finite(root[0], root[2])
    if category == "ayin_vav" and vs == "hit":
        return _hitpolel_non_finite(root[0], root[2])
    for vt, (gn, nu), _label in NON_FINITE_CELLS:
        # Les infinitifs n'ont ni genre ni nombre ; les participes ont
        # ps=unknown dans la base. La clé JSON est cat|vs|vt|unknown|gn|nu.
        entry = _lookup_template_entry(category, vs, vt, ("unknown", gn, nu))
        tpl = entry["template"] if entry else None
        if tpl:
            out[(vt, gn, nu)] = _initial_dagesh(_render(tpl, root, category, vs))
            vars_ = (_cell_variants(vs, root, category, vt,
                                   ("unknown", gn, nu), entry,
                                   out[(vt, gn, nu)])
                    if with_variants else [])
            if vars_:
                out.setdefault("variants", {})[(vt, gn, nu)] = vars_
    return out


# =============================================================================
# API principale
# =============================================================================

def _word_reference(F, L, w):
    """Référence lisible (livre FR chapitre:verset) d'un mot BHSA.

    Les features chapter/verse portent sur les nœuds chapter/verse,
    pas sur les mots : remonter via L.u().
    """
    from .reference import book_french
    book_nodes = L.u(w, "book")
    verse_nodes = L.u(w, "verse")
    if not book_nodes or not verse_nodes:
        return None
    book = book_french(F.book.v(book_nodes[0]))
    chapter = F.chapter.v(verse_nodes[0])
    verse = F.verse.v(verse_nodes[0])
    if chapter in (None, "unknown", "NA") or verse in (None, "unknown", "NA"):
        return None
    return f"{book} {chapter}:{verse}"


def binyan_references(F, L, lex, vs, vt, cell, limit=1):
    """Références attestées d'une cellule d'un lemme dans un binyan.

    Renvoie une liste (au plus ``limit``) de références « Livre ch:v »
    où la cellule (ps, gn, nu) du lemme ``lex`` est attestée dans le
    binyan/temps (vs, vt). Vide si non attesté. Sans suffixe
    pronominal ; hébreu uniquement.
    """
    if not lex or L is None:
        return []
    ps, gn, nu = cell
    out = []
    seen = set()
    for w in F.otype.s("word"):
        if F.lex.v(w) != lex or F.sp.v(w) != "verb":
            continue
        if F.vs.v(w) != vs or F.vt.v(w) != vt:
            continue
        if F.prs.v(w) not in (None, "n/a", "NA", "unknown", "absent"):
            continue
        if F.language.v(w) != "Hebrew":
            continue
        w_ps, w_gn, w_nu = F.ps.v(w), F.gn.v(w), F.nu.v(w)
        # Genre : la BHSA marque « unknown » les 1res personnes et
        # souvent les 3es pluriel — accepter la cellule commune.
        gn_ok = (w_gn == gn) or (
            w_gn in ("unknown", "NA", None)
            and (gn == "c" or nu == "pl"))
        if (w_ps, w_nu) != (ps, nu) or not gn_ok:
            continue
        ref = _word_reference(F, L, w)
        if ref and ref not in seen:
            seen.add(ref)
            out.append(ref)
            if len(out) >= limit:
                break
    return out


def analyze_binyanim(F, form, use_mishnah=False, use_modern=False,
                     with_variants=True, with_references=False, L=None):
    """Analyse « binyanim » complète d'un mot hébreu conjugué ou d'une
    racine trilitaire.

    Si ``use_mishnah`` est vrai, les binyanim attestés dans la Mishna
    (fichier ``mishnah_binyanim.json``, extrait du corpus Sefaria) mais
    absents de la Bible hébraïque sont signalés dans chaque entrée via
    le champ ``mishnah_forms`` (liste de formes attestées ; vide sinon).

    Si ``use_modern`` est vrai, les binyanim attestés en hébreu moderne
    (fichier ``modern_binyanim.json``, extrait du dictionnaire Pealim)
    sont signalés dans chaque entrée via le champ ``modern_forms``
    (dict ``{"lemma", "gloss", "url"}`` ; None sinon).

    Si ``with_variants`` est faux, seules les formes dominantes sont
    générées (les conjuguaisons concurrentes attestées par cellule ne
    sont pas produites).

    Si ``with_references`` est vrai, chaque entrée de binyan porte un
    champ ``references`` : {tense: {cellule: "Livre ch:v"}} — la
    première référence biblique où la cellule du lemme est attestée
    (forme dominante uniquement ; vide si non attesté).


    Renvoie :
        {
            "input": str,
            "found": bool,
            "verb": {           # identification + catégorie faible
                "root": (p1, p2, p3),
                "lex": "CMR[" | None,
                "gloss": "keep" | None,
                "gloss_fr": "garder" | None,
                "category": "strong" | "lamed_he" | ...,
                "category_label": "verbe lamed-he (ל״ה)",
                "category_desc": "...",
                "is_weak": bool,
                "binyan_attested": "qal" | None,
                "binyanim_of_lex": ["hif", "hof", "qal", ...] | None,
            },
            "binyanim": [       # 7 binyanim, ordre pédagogique
                {
                    "code": "qal",
                    "name_fr": "qal (paal)",
                    "name_he": "פָּעַל",
                    "sense": "actif simple",
                    "attested": bool,
                    "exists": bool | None,
                    "mishnah_forms": ["forme", ...],
                    "modern_forms": {"lemma": ..., "gloss": ..., "url": ...} | None,
                    "paradigm": {"perf": {...}, "impf": {...}, "impv": {...}},
                    "non_finite": {(vt, gn, nu): forme},
                },
                ...
            ],
        }
    """
    verb = identify_verb(F, form)
    out = {"input": form, "found": bool(verb.get("found")), "verb": verb,
           "binyanim": []}
    if not verb.get("found"):
        return out

    root = verb.get("root") or ()
    if len(root) != 3:
        verb["reason"] = "root_not_triliteral"
        out["found"] = False
        return out

    p1, p2, p3 = root
    category = classify_root(p1, p2, p3)
    label, desc = _WEAK_LABELS[category]
    verb["category"] = category
    verb["category_label"] = label
    verb["category_desc"] = desc
    verb["is_weak"] = category != "strong"
    verb["root_display"] = "".join(root)

    # Binyanim attestés pour la racine dans la BHSA (toutes occurrences
    # de tous les lemmes de la racine, indépendamment de la forme
    # saisie) : sert à repérer les binyanim qui « n'ont pas de sens »
    # pour cette racine. La BHSA scinde parfois une racine en plusieurs
    # lemmes (ex. מהר : `MHR=[` qal « acquérir », `MHR[` nif/piel
    # « hâter ») ; se limiter au lemme de la forme saisie colorerait en
    # rouge des binyanim pourtant attestés pour la racine. Les variantes
    # hitpael des verbes faibles (htpa/hitpolel « htpo », hitpelel
    # « htpe ») comptent comme hitpael.
    binyanim_of_lex = None
    if verb.get("root_display"):
        root_letters = [ch.replace("\u05C1", "").replace("\u05C2", "")
                        for ch in _root_letters(verb["root_display"])]
        if root_letters:
            binyanim_of_lex = set()
            for w in F.otype.s("word"):
                if F.sp.v(w) != "verb":
                    continue
                lex_utf8 = F.lex_utf8.v(w) or ""
                lex_letters = [ch.replace("\u05C1", "").replace("\u05C2", "")
                               for ch in _root_letters(lex_utf8)]
                if lex_letters != root_letters:
                    continue
                vs = F.vs.v(w)
                binyanim_of_lex.add("hit" if vs in ("htpa", "htpo", "htpe") else vs)
    verb["binyanim_of_lex"] = sorted(binyanim_of_lex or ())

    attested = verb.get("binyan_attested")
    gloss_fr = _gloss_fr_pure(verb.get("lex"), sp="verb")
    gloss_en = verb.get("gloss") or ""
    mishnah_data = load_mishnah_binyanim() if use_mishnah else {}
    mishnah_root = mishnah_data.get(verb.get("root_display") or "", {})
    modern_data = load_modern_binyanim() if use_modern else {}
    modern_root = modern_data.get(verb.get("root_display") or "", {})
    for code, name_fr, name_he in BINYANIM:
        tr_fr, tr_en = binyan_translation(code, gloss_fr, gloss_en,
                                         root=verb.get("root_display"))
        entry = {
            "code": code,
            "name_fr": name_fr,
            "name_he": name_he,
            "sense": BINYAN_SENSE[code],
            "translation_fr": tr_fr,
            "translation_en": tr_en,
            "attested": (attested == code),
            "exists": (code in binyanim_of_lex) if binyanim_of_lex is not None else None,
            "mishnah_forms": list(mishnah_root.get(code, [])),
            "modern_forms": modern_root.get(code),
            "paradigm": generate_binyan_paradigm(code, root, category,
                                                 with_variants=with_variants),
            "non_finite": generate_binyan_non_finite(code, root, category,
                                                    with_variants=with_variants),
        }
        if with_references and verb.get("lex"):
            refs = {}
            for tense, persons in TENSE_PERSONS.items():
                cells = {}
                for ps, gn, nu, _label in persons:
                    # La BHSA code le jussif comme wayq ; le
                    # cohortatif est un imparfait allongé.
                    vt_map = {"perf": "perf", "impf": "impf",
                              "impv": "impv", "juss": "wayq",
                              "coh": "impf"}
                    vt = vt_map.get(tense, tense)
                    r = binyan_references(F, L, verb["lex"], code,
                                          vt, (ps, gn, nu), limit=1)
                    if r:
                        cells[(ps, gn, nu)] = r[0]
                if cells:
                    refs[tense] = cells
            entry["references"] = refs
        out["binyanim"].append(entry)
    return out


# =============================================================================
# Formatage (texte marqué pour le GUI, JSON)
# =============================================================================
# Les en-têtes de binyan du format texte sont marqués « ###BINYAN|...### »
# pour être identifiables/parsables par le GUI (cf. gui_hebreu.py, onglet
# Binyanim) comme par tout autre programme.

MARK_VERB = "###VERB"
MARK_WEAK = "###WEAK"
MARK_BINYAN = "###BINYAN"

_MISHNAH_JSON_DEFAULT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "mishnah_binyanim.json")
if not os.path.isfile(_MISHNAH_JSON_DEFAULT):
    _MISHNAH_JSON_DEFAULT = os.path.join(resource_dir(), "mishnah_binyanim.json")
MISHNAH_JSON = _MISHNAH_JSON_DEFAULT
_MISHNAH_CACHE = {"path": None, "data": {}}


_MODERN_JSON_DEFAULT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "modern_binyanim.json")
if not os.path.isfile(_MODERN_JSON_DEFAULT):
    _MODERN_JSON_DEFAULT = os.path.join(resource_dir(), "modern_binyanim.json")
MODERN_JSON = _MODERN_JSON_DEFAULT
_MODERN_CACHE = {"path": None, "data": {}}


def load_modern_binyanim():
    """Charge modern_binyanim.json (binyanim modernes par racine).

    Format : {"<racine>": {"<code>": {"lemma", "gloss", "url"}}}, extrait
    du dictionnaire d'hébreu moderne Pealim (cf. scripts/
    extract_modern_binyanim.py). Tolérant si le fichier est absent.
    Mis en cache tant que le fichier ne change pas de chemin.
    """
    if not os.path.isfile(MODERN_JSON):
        return {}
    if _MODERN_CACHE["path"] != MODERN_JSON:
        import json
        try:
            with open(MODERN_JSON, encoding="utf-8") as fh:
                _MODERN_CACHE["data"] = json.load(fh)
            _MODERN_CACHE["path"] = MODERN_JSON
        except (OSError, ValueError):
            _MODERN_CACHE["data"] = {}
            _MODERN_CACHE["path"] = None
    return _MODERN_CACHE["data"]


def load_mishnah_binyanim():
    """Charge mishnah_binyanim.json (binyanim mishnaïques par racine).

    Format : {"<racine>": {"<code>": ["<forme>", ...]}}. Tolérant si le
    fichier est absent (aucune donnée mishnaïque). Mis en cache tant que
    le fichier ne change pas de chemin.
    """
    if not os.path.isfile(MISHNAH_JSON):
        return {}
    if _MISHNAH_CACHE["path"] != MISHNAH_JSON:
        import json
        try:
            with open(MISHNAH_JSON, encoding="utf-8") as fh:
                _MISHNAH_CACHE["data"] = json.load(fh)
            _MISHNAH_CACHE["path"] = MISHNAH_JSON
        except (OSError, ValueError):
            _MISHNAH_CACHE["data"] = {}
            _MISHNAH_CACHE["path"] = None
    return _MISHNAH_CACHE["data"]


def binyanim_to_text(analysis):
    """Formate le résultat d'analyze_binyanim en texte lisible.

    Les en-têtes de binyan portent un marqueur parsable :
        ###BINYAN|<code>|<nom fr>|<nom hébreu>|<attesté 0/1>|<existant 0/1/vide>|<trad fr>|<trad en>|<formes mishna ; ;>|<lemme moderne~sens moderne~url Pealim>###
    (le champ « existant » dit si le binyan est attesté pour cette racine
    dans la BHSA : vide = information indisponible, racine non attestée ;
    les traductions du verbe dans ce binyan suivent, fr puis en ; puis
    les formes attestées dans la Mishna pour ce binyan non biblique,
    jointes par « ; », vide si aucune ; puis l'attestation en hébreu
    moderne — lemme Pealim, sens anglais et page, joints par « ~ »,
    vide si le binyan n'y est pas attesté).
    ainsi que l'en-tête de verbe et la catégorie de verbe faible :
        ###VERB|<racine>|<lemme>|<traduction fr>###
        ###WEAK|<code>|<libellé>|<description>###
    """
    lines = []
    lines.append(f"=== Binyanim : {analysis['input']} ===")
    if not analysis["found"]:
        lines.append("Aucun verbe trouvé pour cette forme dans la base BHSA.")
        lines.append("")
        lines.append("Astuces :")
        lines.append("  - Saisir un mot conjugué (ex. שָׁמַר) avec le nikkud ;")
        lines.append("  - ou une racine trilitaire nue (ex. שמר, קום, בנה).")
        return "\n".join(lines)

    v = analysis["verb"]
    root_disp = v.get("root_display", "")
    lex = v.get("lex") or ""
    gloss_fr = v.get("gloss_fr") or v.get("gloss") or ""
    lines.append(MARK_VERB + f"|{root_disp}|{lex}|{gloss_fr}###")
    lines.append(f"Racine : {root_disp}"
                  + (f"  (lemme BHSA : {lex})" if lex else "")
                  + (f"  « {gloss_fr} »" if gloss_fr else ""))
    lines.append(MARK_WEAK + f"|{v['category']}|{v['category_label']}|{v['category_desc']}###")
    if v["is_weak"]:
        lines.append(f"Verbe faible : {v['category_label']} — {v['category_desc']}")
    else:
        lines.append("Verbe fort (shalem) : conjugaison régulière.")
    lines.append("")

    for b in analysis["binyanim"]:
        att = "1" if b["attested"] else "0"
        exists = b.get("exists")
        exists_flag = "" if exists is None else ("1" if exists else "0")
        mishnah_forms = b.get("mishnah_forms") or []
        mishnah_part = ";".join(mishnah_forms)
        modern = b.get("modern_forms") or {}
        modern_part = "" if not modern else "~".join((
            (modern.get("lemma") or "").replace("~", " "),
            (modern.get("gloss") or "").replace("~", " "),
            (modern.get("url") or "").replace("~", " ")))
        lines.append(MARK_BINYAN + f"|{b['code']}|{b['name_fr']}|{b['name_he']}|{att}|{exists_flag}|{b.get('translation_fr', '')}|{b.get('translation_en', '')}|{mishnah_part}|{modern_part}###")
        attest = " (binyan attesté dans la BHSA pour cette forme)" if b["attested"] else ""
        lines.append(f"-- {b['name_fr']} / {b['name_he']} — {b['sense']}{attest} --")
        tr_fr = b.get("translation_fr") or ""
        tr_en = b.get("translation_en") or ""
        trads = [f"fr : {tr_fr}" for _ in (0,) if tr_fr] + \
                [f"en : {tr_en}" for _ in (0,) if tr_en]
        if trads:
            lines.append(f"  Traduction : {'  |  '.join(trads)}")
        if exists is False:
            if mishnah_forms:
                lines.append("✸ Attesté dans la Mishna (binyan non "
                             "biblique) : " + ", ".join(mishnah_forms))
            else:
                lines.append("⚠ Cette racine n'a pas de sens dans ce binyan : "
                             "aucune occurrence de ce binyan pour cette racine "
                             "dans la Bible hébraïque (paradigme théorique, "
                             "construit par analogie).")
        modern = b.get("modern_forms") or {}
        if modern:
            modern_txt = ("\u25c8 Attest\u00e9 en h\u00e9breu moderne : "
                          + (modern.get("lemma") or ""))
            if modern.get("gloss"):
                modern_txt += f" ({modern['gloss']})"
            lines.append(modern_txt)
        cell_refs = b.get("references") or {}
        for tense in ("perf", "impf", "impv", "juss", "coh"):
            lines.append(f"  {TENSE_LABELS[tense]} :")
            cell_variants = b["paradigm"].get("variants", {}).get(tense, {})
            tense_refs = cell_refs.get(tense, {}) if cell_refs else {}
            for ps, gn, nu, label in TENSE_PERSONS[tense]:
                form = b["paradigm"][tense].get((ps, gn, nu), "")
                if form:
                    vars_ = cell_variants.get((ps, gn, nu)) or []
                    shown = " / ".join([form] + vars_)
                    ref = tense_refs.get((ps, gn, nu))
                    if ref:
                        shown = f"{shown}  [{ref}]"
                    lines.append(f"    {label:34} {shown}")
        nf = b["non_finite"]
        if nf:
            lines.append("  Formes non finies :")
            nf_variants = nf.get("variants", {})
            for vt, (gn, nu), label in NON_FINITE_CELLS:
                form = nf.get((vt, gn, nu), "")
                if form:
                    vars_ = nf_variants.get((vt, gn, nu)) or []
                    shown = " / ".join([form] + vars_)
                    lines.append(f"    {label:34} {shown}")
        lines.append("")
    return "\n".join(lines)


def parse_binyanim_text(text):
    """Parse le texte marqué produit par binyanim_to_text.

    Renvoie :
        {
            "verb": {"root":..., "lex":..., "gloss_fr":...},
            "weak": {"code":..., "label":..., "desc":...},
            "binyanim": [{"code","name_fr","name_he","attested","exists",
                        "translation_fr","translation_en","mishnah_forms",
                        "modern_forms","text"}, ...],
        }
    ("exists" vaut True, False ou None si l'information est indisponible ;
    "mishnah_forms" liste les formes attestées dans la Mishna pour ce
    binyan, vide si aucune ; "modern_forms" vaut {"lemma", "gloss",
    "url"} si le binyan est attesté en hébreu moderne (Pealim), None
    sinon.)
    """
    import re
    verb = {}
    weak = {}
    binyanim = []
    current = None
    for line in text.split("\n"):
        if line.startswith(MARK_VERB + "|"):
            parts = line[len(MARK_VERB) + 1:].rstrip("#").split("|")
            if len(parts) >= 3:
                verb = {"root": parts[0], "lex": parts[1] or None,
                        "gloss_fr": parts[2] or None}
            continue
        if line.startswith(MARK_WEAK + "|"):
            parts = line[len(MARK_WEAK) + 1:].rstrip("#").split("|")
            if len(parts) >= 3:
                weak = {"code": parts[0], "label": parts[1], "desc": parts[2]}
            continue
        if line.startswith(MARK_BINYAN + "|"):
            parts = line[len(MARK_BINYAN) + 1:].rstrip("#").split("|")
            if len(parts) >= 4:
                exists_part = parts[4] if len(parts) >= 5 else None
                mishnah_part = parts[7] if len(parts) > 7 else ""
                modern_part = parts[8] if len(parts) > 8 else ""
                modern_fields = modern_part.split("~") if modern_part else []
                modern_forms = None
                if len(modern_fields) == 3 and any(modern_fields):
                    modern_forms = {"lemma": modern_fields[0],
                                    "gloss": modern_fields[1],
                                    "url": modern_fields[2]}
                current = {"code": parts[0], "name_fr": parts[1],
                           "name_he": parts[2], "attested": parts[3] == "1",
                           "exists": (exists_part == "1") if exists_part else None,
                           "translation_fr": parts[5] if len(parts) > 5 else "",
                           "translation_en": parts[6] if len(parts) > 6 else "",
                           "mishnah_forms": [f for f in mishnah_part.split(";") if f],
                           "modern_forms": modern_forms,
                           "text": []}
                binyanim.append(current)
            continue
        if current is not None:
            current["text"].append(line)
    for b in binyanim:
        b["text"] = "\n".join(b["text"]).strip("\n")
    return {"verb": verb, "weak": weak, "binyanim": binyanim}


def binyanim_to_json(analysis, indent=2, ensure_ascii=False):
    """Formate le résultat d'analyze_binyanim en JSON exploitable."""
    import json

    def _key(k):
        return "|".join(str(x) for x in k)

    out = {
        "input": analysis["input"],
        "found": analysis["found"],
        "verb": {k: v for k, v in analysis["verb"].items()
                 if k not in ("root",)},
        "binyanim": [
            {
                "code": b["code"],
                "name_fr": b["name_fr"],
                "name_he": b["name_he"],
                "sense": b["sense"],
                "translation_fr": b.get("translation_fr"),
                "translation_en": b.get("translation_en"),
                "attested": b["attested"],
                "exists": b.get("exists"),
                "mishnah_forms": b.get("mishnah_forms") or [],
                "modern_forms": b.get("modern_forms"),
                "paradigm": {
                    tense: {_key(cell): form
                           for cell, form in forms.items() if form}
                    for tense, forms in b["paradigm"].items()
                    if tense != "variants"
                },
                "paradigm_variants": {
                    f"{tense}|{_key(cell)}": forms
                    for tense, cells in b["paradigm"]
                    .get("variants", {}).items()
                    for cell, forms in cells.items() if forms
                },
                "non_finite": {_key(cell): form
                               for cell, form in b["non_finite"].items()
                               if form and cell != "variants"},
                "non_finite_variants": {
                    _key(cell): forms
                    for cell, forms in b["non_finite"]
                    .get("variants", {}).items() if forms},
                "references": {
                    f"{tense}|{_key(cell)}": ref
                    for tense, cells in (b.get("references") or {}).items()
                    for cell, ref in cells.items()
                },
            }
            for b in analysis["binyanim"]
        ],
    }
    if "verb" in analysis and "root" in analysis["verb"]:
        out["verb"]["root"] = list(analysis["verb"]["root"])
    return json.dumps(out, indent=indent, ensure_ascii=ensure_ascii)
