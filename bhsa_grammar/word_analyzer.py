"""Analyse d'un mot hébreu isolé (avec nikkud, sans teamim) hors contexte.

La base BHSA segmente les mots avec leurs préfixes prépositionnels/conjonctifs
(ב, כ, ל, מ, ו, ה, ש) comme des nœuds séparés. L'analyse d'un mot saisi isolé
doit donc :
  1. normaliser la forme (retirer les teamim, garder le nikkud) ;
  2. chercher la forme exacte (g_word_utf8 normalisé) ;
  3. sinon, chercher la forme consonantique (g_cons_utf8) ;
  4. sinon, détacher les préfixes possibles et chercher le reste.

On renvoie alors les analyses morphologiques distinctes trouvées dans la base
(ces analyses reflètent les occurrences réelles du mot dans la Bible, ce qui
donne les règles grammaticales possibles pour cette forme).
"""

import unicodedata
from . import morph_fr as M
from . import lex_fr as FR


def _strip_teamim(s):
    """Retire les signes de cantillation (teamim, U+0591..U+05AF)."""
    return "".join(c for c in s if not (0x0591 <= ord(c) <= 0x05AF))


def _normalize(s):
    """Normalise : NFC + retrait des teamim."""
    return unicodedata.normalize("NFC", _strip_teamim(s))


def _strip_nikkud(s):
    """Retire le nikkud (points-voyelles U+05B0..U+05BC, U+05C7), les teamim
    et le point de shin/sin (U+05C1/U+05C2).

    Le point de shin/sin n'est pas une voyelle : il distingue שׁ (shin) de
    שׂ (sin). La base BHSA le conserve dans g_cons_utf8, mais un utilisateur
    saisissant ש (sans point) doit quand même retrouver les formes avec shin
    ou sin. On le retire donc de la forme consonantique de fallback ; la
    recherche exacte (g_word_utf8) conserve le point.
    """
    return "".join(
        c
        for c in s
        if not (
            0x05B0 <= ord(c) <= 0x05BC
            or ord(c) == 0x05C7
            or ord(c) in (0x05C1, 0x05C2)
            or 0x0591 <= ord(c) <= 0x05AF
        )
    )


# Préfixes prépositionnels/conjonctifs/articulaires courants, en lettres
# hébraïques (la forme consonantique de l'input est en hébreu, pas en
# translittération). On retire d'abord les combinaisons les plus longues pour
# éviter les ambiguïtés (ex. ה article vs ה interrogatif).
_W = "ו"   # waw
_H = "ה"   # article / interrogatif
_B = "ב"   # בְּ
_K = "כ"   # כְּ
_L = "ל"   # לְ
_M = "מ"   # מִן
_C = "ש"   # שֶׁ (relatif)
_MN = _M + "ן"   # מן complet (avec nun final ; rare comme préfixe)
_PREFIXES = [
    _MN,                                   # combinaisons longues d'abord
    _W + _B + _H, _W + _K + _H, _W + _L + _H, _W + _M + _H,  # waw + prép + article
    _W + _B, _W + _K, _W + _L, _W + _M, _W + _H, _W + _C,    # waw + préposition
    _C + _B, _C + _K, _C + _L, _C + _M, _C + _H,            # ש + préposition
    _B + _H, _K + _H, _L + _H, _M + _H,                     # préposition + article
    _W, _H, _B, _K, _L, _M, _C,                             # préfixes simples
]

# Étiquettes explicatives pour les préfixes détachés.
_PREFIX_LABELS = {
    _W: "waw conjonctif (ו)",
    _H: "article/interrogatif (ה)",
    _B: "préposition בְּ (dans/avec)",
    _K: "préposition כְּ (comme)",
    _L: "préposition לְ (à/pour)",
    _M: "préposition מִן (de)",
    _C: "relatif שֶׁ",
    _MN: "préposition מִן",
}


def _candidate_forms(form):
    """Génère les formes candidates à partir de l'entrée utilisateur.

    Renvoie une liste de (méthode, forme) où 'méthode' indique le niveau
    de matching : 'word', 'cons', puis 'cons+prefix' avec le préfixe détaché.
    """
    candidates = []
    norm = _normalize(form)
    cons = _strip_nikkud(norm)
    candidates.append(("word", norm, None))
    if cons and cons != norm:
        candidates.append(("cons", cons, None))
    # Détachement de préfixes sur la forme consonantique
    if cons:
        for pfx in _PREFIXES:
            if len(cons) > len(pfx) and cons.startswith(pfx):
                remainder = cons[len(pfx):]
                candidates.append(("prefix", remainder, pfx))
    return candidates


def search_word(F, form, limit=20):
    """Cherche les occurrences d'un mot dans la base BHSA.

    Renvoie une liste d'objets 'word' (dict avec features) correspondant à la
    forme demandée. La recherche essaie : forme complète (g_word_utf8), puis
    forme consonantique (g_cons_utf8), puis forme sans préfixe.
    """
    # Index construits à la demande (et mis en cache sur l'API).
    idx = getattr(F, "_hebrew_word_index", None)
    if idx is None:
        idx = {"word": {}, "cons": {}}
        for w in F.otype.s("word"):
            gword = _normalize(F.g_word_utf8.v(w))
            idx["word"].setdefault(gword, []).append(w)
            gcons = _strip_nikkud(_normalize(F.g_cons_utf8.v(w)))
            if gcons:
                idx["cons"].setdefault(gcons, []).append(w)
        F._hebrew_word_index = idx

    results = []
    seen = set()
    for method, key, pfx in _candidate_forms(form):
        bucket = idx["word"] if method == "word" else idx["cons"]
        for w in bucket.get(key, [])[:limit]:
            if w not in seen:
                seen.add(w)
                results.append((method, w, pfx))
        if results:
            break
    return results


def word_features(F, w):
    """Renvoie un dict des features morphologiques d'un nœud word."""
    def g(name):
        feat = getattr(F, name, None)
        return feat.v(w) if feat is not None else None
    return {
        "text": F.g_word_utf8.v(w),
        "lex": g("lex_utf8"),
        "lex_id": g("lex"),
        "gloss": g("gloss"),
        "gloss_fr": FR.best_gloss(g("lex"), g("gloss")),
        "sp": g("sp"),
        "pdp": g("pdp"),
        "ls": g("ls"),
        "gn": g("gn"),
        "nu": g("nu"),
        "ps": g("ps"),
        "st": g("st"),
        "vt": g("vt"),
        "vs": g("vs"),
        "pfm": g("pfm"),
        "vbs": g("vbs"),
        "vbe": g("vbe"),
        "nme": g("nme"),
        "prs": g("prs"),
        "prs_gn": g("prs_gn"),
        "prs_nu": g("prs_nu"),
        "prs_ps": g("prs_ps"),
    }


def describe_word(F, L, w):
    """Produit une description en français des règles grammaticales d'un mot."""
    from .rules import word_rules
    feats = word_features(F, w)
    rules = word_rules(F, L, w)
    return {
        "features": feats,
        "rules": rules,
    }


def analyze_word(F, L, form, limit=20):
    """Analyse un mot isolé et renvoie une structure décrivant les analyses.

    Renvoie :
        {
            "input": "<forme saisie>",
            "matches": [
                {
                    "method": "word"|"cons"|"prefix",
                    "prefix": "<préfixe détaché ou null>",
                    "text": "<forme du node>",
                    "lex": "<lemme>",
                    "features": {...},
                    "rules": [...],
                    "count": <nombre d'occurrences de cette analyse>,
                    "reference_example": ["Livre", chap, verset],
                },
                ...
            ],
            "found": bool,
        }
    """
    matches = []
    raw = search_word(F, form, limit=limit)
    # Regrouper par analyse morphologique identique (lemme + sp + vt + vs + gn+nu+ps+st)
    by_key = {}
    for method, w, pfx in raw:
        desc = describe_word(F, L, w)
        key = (
            desc["features"].get("lex"),
            desc["features"].get("sp"),
            desc["features"].get("vt"),
            desc["features"].get("vs"),
            desc["features"].get("gn"),
            desc["features"].get("nu"),
            desc["features"].get("ps"),
            desc["features"].get("st"),
            desc["features"].get("prs"),
        )
        if key not in by_key:
            # Première occurrence = exemple de référence
            book_node = L.u(w, "book")[0] if L.u(w, "book") else None
            chap = F.chapter.v(L.u(w, "chapter")[0]) if L.u(w, "chapter") else None
            verse = F.verse.v(L.u(w, "verse")[0]) if L.u(w, "verse") else None
            book = F.book.v(book_node) if book_node else None
            by_key[key] = {
                "method": method,
                "prefix": pfx,
                "text": F.g_word_utf8.v(w),
                "lex": desc["features"].get("lex"),
                "gloss": desc["features"].get("gloss"),
                "gloss_fr": desc["features"].get("gloss_fr"),
                "features": desc["features"],
                "rules": desc["rules"],
                "count": 0,
                "reference_example": [book, chap, verse],
            }
        by_key[key]["count"] += 1

    # Tri : par nombre d'occurrences décroissant
    matches = sorted(by_key.values(), key=lambda m: -m["count"])

    # Règle spéciale si un préfixe a été détaché
    for m in matches:
        if m["prefix"]:
            pfx_label = _PREFIX_LABELS.get(m["prefix"], f"préfixe {m['prefix']}")
            m["rules"] = [f"Préfixe détaché : {pfx_label}."] + m["rules"]

    return {
        "input": form,
        "matches": matches,
        "found": len(matches) > 0,
    }
