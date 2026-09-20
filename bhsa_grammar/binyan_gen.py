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

import unicodedata

from .lex_fr import best_gloss, gloss_fr as _gloss_fr_pure

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


def binyan_translation(code, gloss_fr, gloss_en):
    """Traduction du verbe dans un binyan, en français et en anglais.

    Construite par périphrase à partir des gloss du lemme : « garder » →
    nifal « être gardé », hifil « faire garder », hitpael « se garder »...
    Chaque langue n'est remplie que si le gloss source existe (le gloss
    français pur vient de lex_fr.json, l'anglais de la BHSA).
    Renvoie ("", "") si aucun gloss n'est disponible.
    """
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
PERSONS = (
    ("p3", "m", "sg", "3e pers. masc. sing. (il)"),
    ("p3", "f", "sg", "3e pers. fém. sing. (elle)"),
    ("p2", "m", "sg", "2e pers. masc. sing. (tu)"),
    ("p2", "f", "sg", "2e pers. fém. sing. (tu)"),
    ("p1", "c", "sg", "1re pers. sing. (je)"),
    ("p3", "m", "pl", "3e pers. masc. pl. (ils)"),
    ("p3", "f", "pl", "3e pers. fém. pl. (elles)"),
    ("p2", "m", "pl", "2e pers. masc. pl. (vous)"),
    ("p2", "f", "pl", "2e pers. fém. pl. (vous)"),
    ("p1", "c", "pl", "1re pers. pl. (nous)"),
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
    ("p3", "m", "pl"): SHUREQ,
    ("p3", "f", "pl"): QAMATS + HE,
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
        ("p3", "f", "pl"): p1 + QAMATS + p2 + SHEVA + p3 + QAMATS + HE,
        ("p2", "m", "pl"): p1 + SHEVA + p2 + PATAH + p3 + S_PERF[("p2", "m", "pl")],
        ("p2", "f", "pl"): p1 + QAMATS + p2 + PATAH + p3 + S_PERF[("p2", "f", "pl")],
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
        ("p2", "m", "sg"): p1 + SHEVA + p2 + HOLAM + p3,
        ("p2", "f", "sg"): p1 + HIREQ + p2 + SHEVA + DAGESH + p3 + HIREQ + YOD,
        ("p2", "m", "pl"): p1 + HIREQ + p2 + SHEVA + p3 + SHUREQ,
        ("p2", "f", "pl"): p1 + SHEVA + p2 + HOLAM + p3 + SHEVA + NUN + QAMATS + HE,
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
        ("p3", "f", "pl"): NUN + HIREQ + p1 + SHEVA + p2 + SHEVA + p3 + QAMATS + HE,
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
        ("p3", "f", "pl"): p1 + HIREQ + DAGESH + p2 + SHEVA + DAGESH + p3 + QAMATS + HE,
        ("p2", "m", "pl"): p1 + HIREQ + DAGESH + p2 + SEGOL + DAGESH + p3 + S_PERF[("p2", "m", "pl")],
        ("p2", "f", "pl"): p1 + HIREQ + DAGESH + p2 + SEGOL + DAGESH + p3 + S_PERF[("p2", "f", "pl")],
        ("p1", "c", "pl"): p1 + HIREQ + DAGESH + p2 + SEGOL + DAGESH + p3 + S_PERF[("p1", "c", "pl")],
    }


def _piel_impf(p1, p2, p3):
    out = {}
    for key, (pref, _) in IMPF_PREF.items():
        if key[0] == "p1" and key[2] == "sg":
            out[key] = ALEF + HATAF_QAMATS + p1 + PATAH + DAGESH + p2 + TSERE + DAGESH + p3
        elif key[0] == "p1" and key[2] == "pl":
            out[key] = NUN + SHEVA + p1 + PATAH + DAGESH + p2 + TSERE + DAGESH + p3
        elif key[0] == "p2" and key[1] == "f" and key[2] == "sg":
            out[key] = TAV + SHEVA + DAGESH + p1 + PATAH + DAGESH + p2 + TSERE + DAGESH + p3 + HIREQ + YOD
        elif key[0] == "p2" and key[1] == "f" and key[2] == "pl":
            out[key] = TAV + SHEVA + DAGESH + p1 + PATAH + DAGESH + p2 + TSERE + DAGESH + p3 + SHEVA + NUN + QAMATS + HE
        elif key[0] == "p3" and key[1] == "f" and key[2] == "pl":
            out[key] = TAV + SHEVA + DAGESH + p1 + PATAH + DAGESH + p2 + TSERE + DAGESH + p3 + SHEVA + NUN + QAMATS + HE
        elif key[0] == "p2" and key[1] == "m" and key[2] == "sg":
            out[key] = TAV + SHEVA + DAGESH + p1 + PATAH + DAGESH + p2 + TSERE + DAGESH + p3
        elif key[0] == "p2" and key[1] == "m" and key[2] == "pl":
            out[key] = TAV + SHEVA + DAGESH + p1 + PATAH + DAGESH + p2 + SHEVA + DAGESH + p3 + SHUREQ
        elif key[0] == "p3" and key[1] == "m" and key[2] == "sg":
            out[key] = YOD + SHEVA + p1 + PATAH + DAGESH + p2 + TSERE + DAGESH + p3
        elif key[0] == "p3" and key[1] == "m" and key[2] == "pl":
            out[key] = YOD + SHEVA + p1 + PATAH + DAGESH + p2 + SHEVA + DAGESH + p3 + SHUREQ
        elif key[0] == "p3" and key[1] == "f" and key[2] == "sg":
            out[key] = TAV + SHEVA + DAGESH + p1 + PATAH + DAGESH + p2 + TSERE + DAGESH + p3
        else:
            out[key] = ""
    return out


def _piel_impv(p1, p2, p3):
    return {
        ("p2", "m", "sg"): p1 + PATAH + DAGESH + p2 + TSERE + DAGESH + p3,
        ("p2", "f", "sg"): p1 + PATAH + DAGESH + p2 + SHEVA + DAGESH + p3 + HIREQ + YOD,
        ("p2", "m", "pl"): p1 + PATAH + DAGESH + p2 + SHEVA + DAGESH + p3 + SHUREQ,
        ("p2", "f", "pl"): p1 + PATAH + DAGESH + p2 + TSERE + DAGESH + p3 + SHEVA + NUN + QAMATS + HE,
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
        ("p3", "f", "pl"): p1 + QUBUTS + p2 + SHEVA + DAGESH + p3 + QAMATS + HE,
        ("p2", "m", "pl"): p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + S_PERF[("p2", "m", "pl")],
        ("p2", "f", "pl"): p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + S_PERF[("p2", "f", "pl")],
        ("p1", "c", "pl"): p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + S_PERF[("p1", "c", "pl")],
    }

def _pual_impf(p1, p2, p3):
    out = {}
    for key, (pref, _) in IMPF_PREF.items():
        if key[0] == "p1" and key[2] == "sg":
            out[key] = ALEF + HATAF_QAMATS + p1 + QUBUTS + p2 + PATAH + DAGESH + p3
        elif key[0] == "p1" and key[2] == "pl":
            out[key] = NUN + SHEVA + p1 + QUBUTS + p2 + PATAH + DAGESH + p3
        elif key[0] == "p2" and key[1] == "f" and key[2] == "sg":
            out[key] = TAV + SHEVA + DAGESH + p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + HIREQ + YOD
        elif key[0] == "p2" and key[1] == "f" and key[2] == "pl":
            out[key] = TAV + SHEVA + DAGESH + p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + SHEVA + NUN + QAMATS + HE
        elif key[0] == "p3" and key[1] == "f" and key[2] == "pl":
            out[key] = TAV + SHEVA + DAGESH + p1 + QUBUTS + p2 + PATAH + DAGESH + p3 + SHEVA + NUN + QAMATS + HE
        elif key[0] == "p2" and key[1] == "m" and key[2] == "sg":
            out[key] = TAV + SHEVA + DAGESH + p1 + QUBUTS + p2 + PATAH + DAGESH + p3
        elif key[0] == "p2" and key[1] == "m" and key[2] == "pl":
            out[key] = TAV + SHEVA + DAGESH + p1 + QUBUTS + p2 + SHEVA + DAGESH + p3 + SHUREQ
        elif key[0] == "p3" and key[1] == "m" and key[2] == "sg":
            out[key] = YOD + SHEVA + p1 + QUBUTS + p2 + PATAH + DAGESH + p3
        elif key[0] == "p3" and key[1] == "m" and key[2] == "pl":
            out[key] = YOD + SHEVA + p1 + QUBUTS + p2 + SHEVA + DAGESH + p3 + SHUREQ
        elif key[0] == "p3" and key[1] == "f" and key[2] == "sg":
            out[key] = TAV + SHEVA + DAGESH + p1 + QUBUTS + p2 + PATAH + DAGESH + p3
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
    if p1 in ("\u05E9", "\u05E1", "\u05E6", "\u05D6", "\u05E9"):
        return p1 + HIREQ + TAV + SHEVA   # ש ִ ת ְ  (métathèse : הִשְׁתְ...)
    if p1 in ("\u05E0", "\u05EA", "\u05D8", "\u05E6"):
        return p1 + HIREQ + TAV + SHEVA
    return HE + HIREQ + TAV + SHEVA


def _hit_perf(p1, p2, p3):
    pre = _hit_prefix(p1)
    if p1 in ("\u05E9", "\u05E1", "\u05E6", "\u05D6", "\u05E0", "\u05EA", "\u05D8", "\u05E6", "\u05E9"):
        # métathèse : racine = P1-P2-P3 mais le ת s'infixe après P1 : הִפְעֵל
        stem = p2 + PATAH + DAGESH + p3 + SHEVA
    else:
        stem = p1 + PATAH + DAGESH + p2 + HIREQ + DAGESH + p3 + SHEVA
    out = {}
    for key, end in S_PERF.items():
        if key == ("p3", "m", "sg"):
            out[key] = pre + p1 + PATAH + DAGESH + p2 + HIREQ + DAGESH + p3
        else:
            out[key] = pre + stem + end
    return out


def _hit_impf(p1, p2, p3):
    pre = _hit_prefix(p1)
    stem_sg = p1 + PATAH + DAGESH + p2 + HIREQ + DAGESH + p3
    stem_pl = p1 + PATAH + DAGESH + p2 + SHEVA + DAGESH + p3
    out = {}
    for key, (pref, _) in IMPF_PREF.items():
        if key[0] == "p1" and key[2] == "sg":
            out[key] = ALEF + HIREQ + pre + stem_sg
        elif key[0] == "p1" and key[2] == "pl":
            out[key] = NUN + HIREQ + pre + stem_pl
        elif key[0] == "p2" and key[1] == "f" and key[2] == "sg":
            out[key] = TAV + HIREQ + pre + p1 + PATAH + DAGESH + p2 + SHEVA + DAGESH + p3 + HIREQ + YOD
        elif key[0] in ("p2", "p3") and key[2] == "pl" and key[1] == "f":
            out[key] = TAV + HIREQ + DAGESH + pre + p1 + PATAH + DAGESH + p2 + PATAH + p3 + SHEVA + NUN + QAMATS + HE
        elif key[2] == "pl":
            out[key] = pref + pre + stem_pl + SHUREQ
        else:
            out[key] = pref + pre + stem_sg
    return out


def _hit_impv(p1, p2, p3):
    pre = _hit_prefix(p1)
    return {
        ("p2", "m", "sg"): pre + p1 + PATAH + DAGESH + p2 + HIREQ + DAGESH + p3,
        ("p2", "f", "sg"): pre + p1 + PATAH + DAGESH + p2 + SHEVA + DAGESH + p3 + HIREQ + YOD,
        ("p2", "m", "pl"): pre + p1 + PATAH + DAGESH + p2 + SHEVA + DAGESH + p3 + SHUREQ,
        ("p2", "f", "pl"): pre + p1 + PATAH + DAGESH + p2 + PATAH + p3 + SHEVA + NUN + QAMATS + HE,
    }


HIT_INFC = HE + HIREQ + TAV + SHEVA + "P1" + PATAH + DAGESH + "P2" + HIREQ + DAGESH + "P3"


def _hit_ptc(p1, p2, p3):
    pre = _hit_prefix(p1)
    return {
        ("ptca", "m", "sg"): MEM + HIREQ + pre + p1 + PATAH + DAGESH + p2 + HIREQ + DAGESH + p3,
        ("ptca", "m", "pl"): MEM + HIREQ + pre + p1 + PATAH + DAGESH + p2 + SHEVA + DAGESH + p3 + HIREQ + YOD + END_MEM,
        ("ptca", "f", "sg"): MEM + HIREQ + pre + p1 + PATAH + DAGESH + p2 + SEGOL + DAGESH + p3 + SEGOL + TAV,
        ("ptca", "f", "pl"): MEM + HIREQ + pre + p1 + PATAH + DAGESH + p2 + SHEVA + DAGESH + p3 + HOLAM + VAV + TSERE + TAV,
    }


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
        elif key[2] == "pl" and key[0] == "p3" and key[1] == "m":
            out[key] = base + HIREQ + YOD + p3 + SHUREQ
        elif key[2] == "pl" and key[0] == "p3" and key[1] == "f":
            out[key] = base + HIREQ + YOD + p3 + QAMATS + HE
        else:
            out[key] = HE + HIREQ + p1 + SHEVA + p2 + PATAH + p3 + end
    return out


def _hif_impf(p1, p2, p3):
    out = {}
    for key, (pref, dash) in IMPF_PREF.items():
        if key[0] == "p1" and key[2] == "sg":
            out[key] = ALEF + PATAH + DAGESH + p1 + SHEVA + p2 + HIREQ + YOD + p3
        elif key[0] == "p1" and key[2] == "pl":
            out[key] = NUN + PATAH + DAGESH + p1 + SHEVA + p2 + HIREQ + YOD + p3
        elif key[0] == "p2" and key[1] == "f" and key[2] == "sg":
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
                    "gloss_fr": best_gloss(lex, F.gloss.v(w)),
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
    from .word_analyzer import search_word
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
        return {
            "found": True,
            "lex": lex,
            "lex_utf8": lex_utf8,
            "root": tuple(rletters),
            "gloss": F.gloss.v(w),
            "gloss_fr": best_gloss(lex, F.gloss.v(w)),
            "binyan_attested": F.vs.v(w),
            "method": "form",
        }
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
        try:
            with open(path, encoding="utf-8") as fh:
                _TEMPLATE_CACHE = json.load(fh)
        except OSError:
            _TEMPLATE_CACHE = {}
    return _TEMPLATE_CACHE


def _cell_key(cat, vs, vt, ps, gn, nu):
    return f"{cat}|{vs}|{vt}|{ps}|{gn}|{nu}"


def _lookup_template(cat, vs, vt, cell):
    """Cherche le gabarit d'une cellule : catégorie, puis « strong ».

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
    return entry["template"] if entry else None


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


def _builtin_paradigm(vs, root):
    """Paradigme du verbe fort par les générateurs intégrés (repli)."""
    p1, p2, p3 = root
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

PERSONS = (
    ("p3", "m", "sg", "3e pers. masc. sing. (il)"),
    ("p3", "f", "sg", "3e pers. fém. sing. (elle)"),
    ("p2", "m", "sg", "2e pers. masc. sing. (tu)"),
    ("p2", "f", "sg", "2e pers. fém. sing. (tu)"),
    ("p1", "c", "sg", "1re pers. sing. (je)"),
    ("p3", "m", "pl", "3e pers. masc. pl. (ils)"),
    ("p3", "f", "pl", "3e pers. fém. pl. (elles)"),
    ("p2", "m", "pl", "2e pers. masc. pl. (vous)"),
    ("p2", "f", "pl", "2e pers. fém. pl. (vous)"),
    ("p1", "c", "pl", "1re pers. pl. (nous)"),
)

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
}

TENSE_PERSONS = {"perf": PERSONS, "impf": PERSONS, "impv": PERSONS_IMPV}


def generate_binyan_paradigm(vs, root, category):
    """Paradigme complet d'un binyan : {tense: {(ps,gn,nu): forme}}.

    Chaque cellule utilise le gabarit BHSA de la catégorie du verbe ;
    à défaut, le gabarit du verbe fort ; à défaut, le générateur intégré.
    """
    out = {}
    builtin = None
    for tense, persons in TENSE_PERSONS.items():
        forms = {}
        for ps, gn, nu, _label in persons:
            tpl = _lookup_template(category, vs, tense, (ps, gn, nu))
            if tpl:
                forms[(ps, gn, nu)] = _render(tpl, root, category, vs)
            else:
                if builtin is None:
                    builtin = _builtin_paradigm(vs, root)
                forms[(ps, gn, nu)] = builtin[tense].get((ps, gn, nu), "")
        out[tense] = forms
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


def generate_binyan_non_finite(vs, root, category):
    """Infinitifs et participes d'un binyan : {(vt, gn, nu): forme}."""
    out = {}
    for vt, (gn, nu), _label in NON_FINITE_CELLS:
        # Les infinitifs n'ont ni genre ni nombre ; les participes ont
        # ps=unknown dans la base. La clé JSON est cat|vs|vt|unknown|gn|nu.
        tpl = _lookup_template(category, vs, vt, ("unknown", gn, nu))
        if tpl:
            out[(vt, gn, nu)] = _render(tpl, root, category, vs)
    return out


# =============================================================================
# API principale
# =============================================================================

def analyze_binyanim(F, form):
    """Analyse « binyanim » complète d'un mot hébreu conjugué ou d'une
    racine trilitaire.

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

    # Binyanim attestés pour le lemme dans la BHSA (toutes occurrences du
    # lemme, indépendamment de la forme saisie) : sert à repérer les binyanim
    # qui « n'ont pas de sens » pour cette racine. Les variantes hitpael des
    # verbes faibles (htpa/hitpolel « htpo », hitpelel « htpe ») comptent
    # comme hitpael.
    binyanim_of_lex = None
    if verb.get("lex"):
        binyanim_of_lex = set()
        for w in F.otype.s("word"):
            if F.sp.v(w) != "verb":
                continue
            if F.lex.v(w) == verb["lex"]:
                vs = F.vs.v(w)
                binyanim_of_lex.add("hit" if vs in ("htpa", "htpo", "htpe") else vs)
        verb["binyanim_of_lex"] = sorted(binyanim_of_lex)

    attested = verb.get("binyan_attested")
    gloss_fr = _gloss_fr_pure(verb.get("lex"))
    gloss_en = verb.get("gloss") or ""
    for code, name_fr, name_he in BINYANIM:
        tr_fr, tr_en = binyan_translation(code, gloss_fr, gloss_en)
        entry = {
            "code": code,
            "name_fr": name_fr,
            "name_he": name_he,
            "sense": BINYAN_SENSE[code],
            "translation_fr": tr_fr,
            "translation_en": tr_en,
            "attested": (attested == code),
            "exists": (code in binyanim_of_lex) if binyanim_of_lex is not None else None,
            "paradigm": generate_binyan_paradigm(code, root, category),
            "non_finite": generate_binyan_non_finite(code, root, category),
        }
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


def binyanim_to_text(analysis):
    """Formate le résultat d'analyze_binyanim en texte lisible.

    Les en-têtes de binyan portent un marqueur parsable :
        ###BINYAN|<code>|<nom fr>|<nom hébreu>|<attesté 0/1>|<existant 0/1/vide>|<trad fr>|<trad en>###
    (le champ « existant » dit si le binyan est attesté pour cette racine
    dans la BHSA : vide = information indisponible, racine non attestée ;
    les traductions du verbe dans ce binyan suivent, fr puis en).
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
        lines.append(MARK_BINYAN + f"|{b['code']}|{b['name_fr']}|{b['name_he']}|{att}|{exists_flag}|{b.get('translation_fr', '')}|{b.get('translation_en', '')}###")
        attest = " (binyan attesté dans la BHSA pour cette forme)" if b["attested"] else ""
        lines.append(f"-- {b['name_fr']} / {b['name_he']} — {b['sense']}{attest} --")
        tr_fr = b.get("translation_fr") or ""
        tr_en = b.get("translation_en") or ""
        trads = [f"fr : {tr_fr}" for _ in (0,) if tr_fr] + \
                [f"en : {tr_en}" for _ in (0,) if tr_en]
        if trads:
            lines.append(f"  Traduction : {'  |  '.join(trads)}")
        if exists is False:
            lines.append("⚠ Cette racine n'a pas de sens dans ce binyan : "
                         "aucune occurrence de ce binyan pour cette racine "
                         "dans la Bible hébraïque (paradigme théorique, "
                         "construit par analogie).")
        for tense in ("perf", "impf", "impv"):
            lines.append(f"  {TENSE_LABELS[tense]} :")
            for ps, gn, nu, label in TENSE_PERSONS[tense]:
                form = b["paradigm"][tense].get((ps, gn, nu), "")
                if form:
                    lines.append(f"    {label:34} {form}")
        nf = b["non_finite"]
        if nf:
            lines.append("  Formes non finies :")
            for vt, (gn, nu), label in NON_FINITE_CELLS:
                form = nf.get((vt, gn, nu), "")
                if form:
                    lines.append(f"    {label:34} {form}")
        lines.append("")
    return "\n".join(lines)


def parse_binyanim_text(text):
    """Parse le texte marqué produit par binyanim_to_text.

    Renvoie :
        {
            "verb": {"root":..., "lex":..., "gloss_fr":...},
            "weak": {"code":..., "label":..., "desc":...},
            "binyanim": [{"code","name_fr","name_he","attested","exists",
                        "translation_fr","translation_en","text"}, ...],
        }
    ("exists" vaut True, False ou None si l'information est indisponible.)
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
                current = {"code": parts[0], "name_fr": parts[1],
                           "name_he": parts[2], "attested": parts[3] == "1",
                           "exists": (exists_part == "1") if exists_part else None,
                           "translation_fr": parts[5] if len(parts) > 5 else "",
                           "translation_en": parts[6] if len(parts) > 6 else "",
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
                "paradigm": {
                    tense: {_key(cell): form
                           for cell, form in forms.items() if form}
                    for tense, forms in b["paradigm"].items()
                },
                "non_finite": {_key(cell): form
                               for cell, form in b["non_finite"].items() if form},
            }
            for b in analysis["binyanim"]
        ],
    }
    if "verb" in analysis and "root" in analysis["verb"]:
        out["verb"]["root"] = list(analysis["verb"]["root"])
    return json.dumps(out, indent=indent, ensure_ascii=ensure_ascii)
