"""Traductions françaises des codes morphologiques de la base BHSA (ETCBC).

Ces codes correspondent aux valeurs des features de Text-Fabric : sp, ls, vt, vs,
gn, nu, ps, st, pdp, function, typ, det, rela. Les libellés s'appuient sur la
documentation officielle BHSA/feature-docs et la terminologie grammaticale de
l'hébreu biblique.
"""

# --- Parties du discours (sp) et pdp (phrase dependent part of speech) ---
POS = {
    "art": "article",
    "conj": "conjonction",
    "subs": "substantif",
    "verb": "verbe",
    "prep": "préposition",
    "pron": "pronom",
    "nmpr": "nom propre",
    "advb": "adverbe",
    "nega": "négation",
    "inrg": "interrogatif",
    "intj": "interjection",
    "modal": "particule modale",
    "ques": "particule interrogative",
    "prps": "pronom personnel indépendant",
    "prde": "pronom démonstratif",
    "prin": "pronom interrogatif",
    "prca": "pronom cardinal",
    "defn": "article défini (définitif)",
}

# --- Genre (gn) ---
GENDER = {
    "m": "masculin",
    "f": "féminin",
    "b": "commun (m/f)",
    "NA": "—",
}

# --- Nombre (nu) ---
NUMBER = {
    "sg": "singulier",
    "pl": "pluriel",
    "du": "dual",
    "NA": "—",
}

# --- Personne (ps) ---
PERSON = {
    "p1": "1re personne",
    "p2": "2e personne",
    "p3": "3e personne",
    "NA": "—",
    "unknown": "—",
}

# --- État (st) ---
STATE = {
    "a": "état absolu",
    "c": "état construit",
    "e": "état emphatique",
    "NA": "—",
}

# --- Type verbal / temps (vt) ---
VERB_TENSE = {
    "perf": "perfectif (qatal)",
    "impf": "imperfectif (yiqtol)",
    "wayq": "wayyiqtol (narratif)",
    "impv": "impératif",
    "infq": "infinitif construit",
    "infc": "infinitif absolu",
    "ptca": "participe actif",
    "ptcp": "participe passif",
    "NA": "—",
    "unknown": "—",
}

# --- Binyan / stem (vs) ---
# Codes effectivement présents dans la base BHSA (version c) : qal, nif, piel,
# pual, hit, hif, hof (les 7 binyanim hébreux) + formes rares/araméennes.
STEM = {
    # 7 binyanim de base (hébreu)
    "qal": "qal (paal)",
    "nif": "nifal",
    "piel": "piel",
    "pual": "pual",
    "hit": "hitpael",
    "hif": "hifil",
    "hof": "hofal",
    # binyanim rares / dérivés (hébreu)
    "hsht": "hithpalpel (hsht)",
    "nit": "nithpaal (nit, rare)",
    "shaf": "shafel (rare)",
    "poal": "poal (rare)",
    "poel": "poel (rare)",
    "htpa": "hithpaal (htpa, rare)",
    "htpe": "hithpeal (htpe, rare)",
    "htpo": "hithpoal (htpo, rare)",
    "hotp": "hithpolel (hotp, rare)",
    # binyanim araméens
    "peal": "peal (araméen)",
    "pael": "pael (araméen)",
    "peil": "peil (araméen passif)",
    "afel": "afel (araméen)",
    "haf": "haphel (haf, araméen)",
    "etpa": "ethpaal (araméen)",
    "etpe": "ethpeal (araméen)",
    "tif": "ithpaal (tif, araméen)",
    "pasq": "pasq (araméen, rare)",
    "NA": "—",
    "unknown": "—",
}

# --- Sous-classification lexicale (ls) ---
LEX_SET = {
    "card": "nombre cardinal",
    "ord": "nombre ordinal",
    "ques": "interrogatif",
    "intj": "interjection",
    "mod": "particule modale",
    "nega": "négation",
    "none": "—",
    "NA": "—",
}

# --- Fonction de la phrase (function) ---
PHRASE_FUNCTION = {
    "Adju": "adjunct (circonstanciel)",
    "Cmpl": "complément",
    "Conj": "conjonction",
    "EPPr": "pronom enclitique / apposition",
    "Frnt": "frontalisé (antéposé)",
    "Intj": "interjection",
    "IntS": "phrase interrogative",
    "Modi": "modificateur",
    "ModS": "phrase modifiée",
    "NCoS": "clause nominale (non-verbal)",
    "Nega": "négation",
    "Objc": "objet (complément direct)",
    "PrAd": "prédicat adverbial",
    "PrcS": "phrase prépositionnelle de circonstance",
    "PreC": "prédicat complétif (sujet-complément)",
    "Pred": "prédicat (verbal)",
    "PreO": "prédicat + objet suffixé",
    "PreS": "prédicat + suffixe",
    "Prio": "priorité",
    "Ques": "question",
    "Rela": "relative",
    "Sfxs": "suffixes",
    "Subj": "sujet",
    "Supp": "supplément",
    "Time": "circconstance de temps",
    "Unkn": "inconnu",
    "Voct": "vocatif",
    "NA": "—",
}

# --- Type de phrase (typ) ---
PHRASE_TYPE = {
    "NP": "syntagme nominal",
    "PP": "syntagme prépositionnel",
    "VP": "syntagme verbal",
    "PrNP": "syntagme nominal propre",
    "AdvP": "syntagme adverbial",
    "CP": "syntagme conjonctif",
    "PPrev": "syntagme prépositionnel (préposition inversée)",
    "PPrP": "syntagme pronominal personnel",
    "DPrP": "syntagme pronominal démonstratif",
    "IPrP": "syntagme pronominal interrogatif",
    "InjP": "syntagme interjectionnel",
    "NegP": "syntagme de négation",
    "InrP": "syntagme interrogatif",
    "ModP": "syntagme modal",
    "MX": "syntagme mixte",
    "FrP": "syntagme frontalisé",
    "NA": "—",
}

# --- Détermination de la phrase (det) ---
PHRASE_DET = {
    "und": "indéterminé",
    "det": "déterminé",
    "def": "défini",
    "NA": "—",
}

# --- Type de clause (typ) ---
# Codes effectivement présents dans la base BHSA (version c) :
# AjCl CPen Ellp InfA InfC MSyn NmCl Ptcp Reop Voct WIm0 WImX WQt0 WQtX WXIM
# WXQt WXYq WYq0 WYqX Way0 WayX WxI0 WxQ0 WxQX WxY0 WxYX XImp XPos XQtl XYqt
# ZIm0 ZImX ZQt0 ZQtX ZYq0 ZYqX xIm0 xImX xQt0 xQtX xYq0 xYqX
CLAUSE_TYPE = {
    # Wayyiqtol (narratif)
    "Way0": "clause wayyiqtol",
    "WayX": "clause wayyiqtol (X avant)",
    # we + qatal (continuatif / apodose)
    "WQt0": "clause we-qatal",
    "WQtX": "clause we-qatal (X avant)",
    "WXQt": "clause we-X-qatal",
    "WxQ0": "clause we-X-qatal",
    "WxQX": "clause we-X-qatal (X)",
    "ZQt0": "clause qatal (repris/coordonné)",
    "ZQtX": "clause qatal (X, repris)",
    # we + yiqtol
    "WIm0": "clause we-yiqtol",
    "WImX": "clause we-yiqtol (X avant)",
    "WXIM": "clause we-X-yiqtol",
    "WxI0": "clause we-X-yiqtol",
    "WYq0": "clause we-yiqtol",
    "WYqX": "clause we-yiqtol (X avant)",
    "WXYq": "clause we-X-yiqtol",
    "ZIm0": "clause yiqtol (repris)",
    "ZImX": "clause yiqtol (repris, X)",
    "ZYq0": "clause yiqtol (repris)",
    "ZYqX": "clause yiqtol (repris, X)",
    # X + temps verbal
    "xQt0": "clause X-qatal",
    "xQtX": "clause X-qatal-X",
    "xYq0": "clause X-yiqtol",
    "xYqX": "clause X-yiqtol-X",
    "xIm0": "clause X-yiqtol",
    "xImX": "clause X-yiqtol-X",
    "WxY0": "clause we-X-yiqtol",
    "WxYX": "clause we-X-yiqtol-X",
    "XQtl": "clause X-qatal",
    "XYqt": "clause X-yiqtol",
    # Impératif / souhait
    "XImp": "clause X + impératif",
    "XPos": "clause X + jussif/cohéortif",
    # Nominal / autres
    "NmCl": "clause nominale",
    "AjCl": "clause asyndétique (sans conjonction)",
    "Voct": "clause vocative",
    "Ptcp": "clause participiale",
    "InfA": "clause infinitive absolue",
    "InfC": "clause infinitive construite",
    "MSyn": "clause à syntaxe marquée",
    "Ellp": "clause elliptique",
    "CPen": "clause pénale / parenthétique",
    "Reop": "clause réouverture / reprise",
    "NA": "—",
}

# --- Relation de clause (rela) ---
# Codes réels : Adju Attr Cmpl Coor NA Objc PrAd PreC ReVo Resu RgRc Spec Subj
CLAUSE_RELA = {
    "NA": "principale",
    "Adju": "adjointe (circconstance)",
    "Attr": "attributive",
    "Cmpl": "complément",
    "Coor": "coordonnée",
    "Objc": "objet",
    "PrAd": "prédicat adverbial",
    "PreC": "prédicat complétif",
    "ReVo": "relative/vocative",
    "Resu": "reprise/résumé",
    "RgRc": "régente-régie",
    "Spec": "spécification",
    "Subj": "sujet",
}

# --- Suffixe pronominal (prs) présence ---
PRS_PERSON = {"p1": "1re", "p2": "2e", "p3": "3e", "n/a": "—", "NA": "—", "unknown": "—"}


def t(d, code):
    """Traduit un code via le dictionnaire ; renvoie le code brut si inconnu.

    ``None`` (absence de valeur) renvoie « — », mais les codes effectifs comme
    "NA" sont traduits via le dictionnaire (par ex. CLAUSE_RELA["NA"] = "principale").
    """
    if code is None:
        return "—"
    return d.get(code, code)
